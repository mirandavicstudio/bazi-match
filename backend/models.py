"""八字合盘匹配系统 — Pydantic v2 数据模型"""

from typing import Literal

from pydantic import BaseModel, Field


class BaziData(BaseModel):
    """八字全数据。"""
    year_pillar: str = Field(..., description="年柱，如'庚辰'")
    month_pillar: str = Field(..., description="月柱，如'己卯'")
    day_pillar: str = Field(..., description="日柱，如'壬申'")
    hour_pillar: str = Field(..., description="时柱，如'甲辰'")
    day_master: str = Field(..., description="日主（日干），如'壬'")
    wuxing_dist: dict = Field(..., description="五行分布，如{'金':1,'木':1,'水':1,'火':2,'土':3}")
    nayin: str = Field(..., description="纳音名称，如'白蜡金'")
    nayin_wuxing: str = Field(..., description="纳音五行，如'金'")
    tiangan_list: list = Field(..., description="四天干列表，如['庚','己','壬','甲']")
    dizhi_list: list = Field(..., description="四地支列表，如['辰','卯','申','辰']")


class DimensionScore(BaseModel):
    """单维度得分。"""
    name: str = Field(..., description="维度名称")
    score: float = Field(..., description="维度分数 0-100")
    detail: str = Field(..., description="分数说明")
    hits: list[str] = Field(default_factory=list, description="命中项列表")


class MatchResult(BaseModel):
    """匹配合盘结果。"""
    total_score: float = Field(..., description="总分 0-100")
    grade: str = Field(..., description="等级名称")
    grade_stars: str = Field(..., description="星级显示")
    dimensions: list[DimensionScore] = Field(..., description="六维度得分")
    interpretation: str = Field(default="", description="解读文案")


class MatchRequest(BaseModel):
    """匹配请求。"""
    birth_year: int = Field(..., ge=1940, le=2010, description="出生年份")
    birth_month: int = Field(..., ge=1, le=12, description="出生月份")
    birth_day: int = Field(..., ge=1, le=31, description="出生日期")
    birth_hour: int = Field(..., ge=0, le=23, description="出生小时")
    birth_minute: int = Field(default=0, ge=0, le=59, description="出生分钟")
    gender: Literal["男", "女"] = Field(..., description="性别")
    top_n: int = Field(default=5, ge=1, le=20, description="返回 Top-N 结果")


class MatchedUser(BaseModel):
    """匹配到的用户。"""
    id: int = Field(..., description="用户 ID")
    name: str = Field(..., description="姓名")
    gender: str = Field(..., description="性别")
    birth_date: str = Field(..., description="出生日期，如'1990-05-15'")
    sizhu: BaziData = Field(..., description="四柱八字数据")
    match_score: float = Field(..., description="匹配总分")
    match_grade: str = Field(..., description="匹配等级")
    match_stars: str = Field(..., description="星级显示")
    dimensions: list[DimensionScore] = Field(..., description="六维度得分")
    interpretation: str = Field(default="", description="解读文案")


class MatchResponse(BaseModel):
    """匹配响应。"""
    success: bool = Field(..., description="是否成功")
    user_bazi: BaziData = Field(..., description="当前用户八字")
    matches: list[MatchedUser] = Field(default_factory=list, description="匹配结果列表")
    total_time_ms: int = Field(..., description="接口耗时（毫秒）")
