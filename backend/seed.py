"""八字合盘匹配系统 — 数据播种脚本"""

import calendar
import random
import sys

from backend import config, db
from backend.paipan import get_sizhu


def generate_name(gender: str) -> str:
    """生成随机中文姓名。

    Args:
        gender: "男" 或 "女"

    Returns:
        随机生成的姓名字符串
    """
    surname = random.choice(config.SURNAMES)
    if gender == "男":
        given = random.choice(config.MALE_NAMES)
    else:
        given = random.choice(config.FEMALE_NAMES)
    return surname + given


def generate_random_birth() -> dict:
    """生成随机出生日期（正态分布，均值1995，标准差8）。

    Returns:
        包含 birth_year, birth_month, birth_day, birth_hour, birth_minute 的字典
    """
    # 出生年份正态分布
    year = int(random.gauss(1995, 8))
    year = max(1940, min(2010, year))

    month = random.randint(1, 12)

    # 根据月份获取最大天数
    max_day = calendar.monthrange(year, month)[1]
    day = random.randint(1, max_day)

    hour = random.randint(0, 23)

    # 分钟取 0/15/30/45 四种
    minute = random.choice([0, 15, 30, 45])

    return {
        "birth_year": year,
        "birth_month": month,
        "birth_day": day,
        "birth_hour": hour,
        "birth_minute": minute,
    }


def main() -> None:
    """数据播种主函数：生成 SEED_COUNT 条虚拟用户并写入数据库。"""
    print(f"开始生成 {config.SEED_COUNT} 条虚拟用户数据...")

    # 初始化数据库
    db.init_db()

    # 幂等检查：有数据时清空后重建
    existing_count = db.count_users()
    if existing_count > 0:
        print(f"数据库已有 {existing_count} 条数据，将清空后重建。")
        db.clear_users()

    # 批量生成
    batch_size = 500
    all_users = []
    total = config.SEED_COUNT

    for i in range(1, total + 1):
        gender = random.choice(["男", "女"])
        name = generate_name(gender)
        birth = generate_random_birth()

        try:
            bazi = get_sizhu(
                birth["birth_year"],
                birth["birth_month"],
                birth["birth_day"],
                birth["birth_hour"],
                birth["birth_minute"],
            )
        except Exception as e:
            print(f"  排盘失败 [{name} {birth}]: {e}，跳过。")
            continue

        user_dict = {
            "name": name,
            "gender": gender,
            **birth,
            "year_pillar": bazi.year_pillar,
            "month_pillar": bazi.month_pillar,
            "day_pillar": bazi.day_pillar,
            "hour_pillar": bazi.hour_pillar,
            "day_master": bazi.day_master,
            "wuxing_dist": bazi.wuxing_dist,
            "nayin": bazi.nayin,
            "nayin_wuxing": bazi.nayin_wuxing,
            "tiangan_list": bazi.tiangan_list,
            "dizhi_list": bazi.dizhi_list,
        }
        all_users.append(user_dict)

        # 每批提交
        if len(all_users) >= batch_size:
            db.batch_insert_users(all_users)
            progress = min(i, total)
            pct = progress / total * 100
            print(f"  已插入 {progress}/{total} ({pct:.1f}%)")
            all_users = []

    # 插入剩余记录
    if all_users:
        db.batch_insert_users(all_users)

    final_count = db.count_users()
    print(f"数据播种完成！共插入 {final_count} 条记录。")


if __name__ == "__main__":
    main()
