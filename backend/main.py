"""八字合盘匹配系统 — FastAPI 入口"""

import logging
import os
import time
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import db, matcher, interpreter
from backend.models import (
    BaziData,
    MatchRequest,
    MatchResponse,
    MatchedUser,
    DimensionScore,
)
from backend.paipan import get_sizhu, calc_pattern

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库。"""
    logger.info("[lifespan] 初始化数据库...")
    logger.info("[lifespan] 当前工作目录: %s", os.getcwd())
    db.init_db()
    user_count = db.count_users()
    logger.info("[lifespan] 数据库用户总数: %d", user_count)
    yield
    logger.info("[lifespan] 应用关闭")


app = FastAPI(title="八字合盘匹配", version="1.0.0", lifespan=lifespan)

# CORS 中间件：允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict:
    """健康检查端点。"""
    return {"status": "ok", "db_users": db.count_users()}


@app.post("/api/match")
def match(req: MatchRequest) -> MatchResponse:
    """核心匹配接口。

    流程：
    1. Pydantic 自动校验请求
    2. 排盘计算用户八字
    3. 全量读取用户库
    4. 遍历打分
    5. 排序取 Top-N
    6. 生成解读
    7. 组装响应
    """
    start_time = time.time()
    logger.info("[match] 收到请求: year=%d month=%d day=%d hour=%d gender=%s top_n=%d",
                req.birth_year, req.birth_month, req.birth_day, req.birth_hour, req.gender, req.top_n)

    # Step1: 计算用户八字
    user_bazi = get_sizhu(
        req.birth_year, req.birth_month, req.birth_day,
        req.birth_hour, req.birth_minute,
        gender=req.gender,
    )
    logger.info("[match] 用户八字: year=%s month=%s day=%s hour=%s day_master=%s",
                user_bazi.year_pillar, user_bazi.month_pillar, user_bazi.day_pillar,
                user_bazi.hour_pillar, user_bazi.day_master)

    # Step 2: 获取全量用户（仅匹配异性）
    opposite_gender = "女" if req.gender == "男" else "男"
    all_users = db.get_users_by_gender(opposite_gender)
    logger.info("[match] 数据库用户总数: %d, 匹配性别: %s, 可匹配数: %d",
                db.count_users(), opposite_gender, len(all_users))

    if all_users:
        sample = all_users[0]
        logger.info("[match] 第一条用户样例: id=%s name=%s year_pillar=%s wuxing_dist=%s tiangan_list=%s dizhi_list=%s",
                    sample.get("id"), sample.get("name"), sample.get("year_pillar"),
                    sample.get("wuxing_dist"), sample.get("tiangan_list"), sample.get("dizhi_list"))

    # Step 3: 遍历打分
    scored_results: list[tuple[dict, float, object]] = []
    error_count = 0
    for idx, user in enumerate(all_users):
        try:
            target_bazi = BaziData(
                year_pillar=user["year_pillar"],
                month_pillar=user["month_pillar"],
                day_pillar=user["day_pillar"],
                hour_pillar=user["hour_pillar"],
                day_master=user["day_master"],
                wuxing_dist=user["wuxing_dist"] if isinstance(user["wuxing_dist"], dict) else {},
                nayin=user["nayin"],
                nayin_wuxing=user["nayin_wuxing"],
                tiangan_list=user["tiangan_list"] if isinstance(user["tiangan_list"], list) else [],
                dizhi_list=user["dizhi_list"] if isinstance(user["dizhi_list"], list) else [],
                shishen_list=user.get("shishen_list", []) if isinstance(user.get("shishen_list"), list) else [],
                minggua=user.get("minggua", ""),
                shengxiao=user.get("shengxiao", ""),
                pattern=user.get("pattern", ""),
            )
            # 如果 pattern 为空，则计算
            if not target_bazi.pattern:
                target_bazi.pattern = calc_pattern(target_bazi)
            match_result = matcher.calc_match(user_bazi, target_bazi)
            scored_results.append((user, match_result.total_score, match_result))
        except Exception as e:
            error_count += 1
            if error_count <= 3:
                logger.error("[match] 第%d条用户匹配失败: %s", idx, e)
                traceback.print_exc()
            continue

    logger.info("[match] 成功匹配: %d / %d, 失败: %d", len(scored_results), len(all_users), error_count)

    # Step 4: 按 total_score 降序排序，取 Top-N
    scored_results.sort(key=lambda x: x[1], reverse=True)
    top_results = scored_results[:req.top_n]
    logger.info("[match] 取 Top-%d 结果", len(top_results))

    # Step 5: 对每条生成解读
    matched_users: list[MatchedUser] = []
    for user, score, match_result in top_results:
        interp = interpreter.generate_interpretation(match_result)
        birth_date = f"{user['birth_year']}-{user['birth_month']:02d}-{user['birth_day']:02d}"
        target_bazi = BaziData(
            year_pillar=user["year_pillar"],
            month_pillar=user["month_pillar"],
            day_pillar=user["day_pillar"],
            hour_pillar=user["hour_pillar"],
            day_master=user["day_master"],
            wuxing_dist=user["wuxing_dist"] if isinstance(user["wuxing_dist"], dict) else {},
            nayin=user["nayin"],
            nayin_wuxing=user["nayin_wuxing"],
            tiangan_list=user["tiangan_list"] if isinstance(user["tiangan_list"], list) else [],
            dizhi_list=user["dizhi_list"] if isinstance(user["dizhi_list"], list) else [],
            shishen_list=user.get("shishen_list", []) if isinstance(user.get("shishen_list"), list) else [],
            minggua=user.get("minggua", ""),
            shengxiao=user.get("shengxiao", ""),
            pattern=user.get("pattern", ""),
        )
        # 如果 pattern 为空，则计算
        if not target_bazi.pattern:
            target_bazi.pattern = calc_pattern(target_bazi)
        matched_users.append(MatchedUser(
            id=user["id"],
            name=user["name"],
            gender=user["gender"],
            birth_date=birth_date,
            sizhu=target_bazi,
            match_score=match_result.total_score,
            match_grade=match_result.grade,
            match_stars=match_result.grade_stars,
            dimensions=match_result.dimensions,
            interpretation=interp,
        ))

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info("[match] 响应完成: matches=%d, 耗时=%dms", len(matched_users), elapsed_ms)

    return MatchResponse(
        success=True,
        user_bazi=user_bazi,
        matches=matched_users,
        total_time_ms=elapsed_ms,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局异常处理。"""
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
