"""八字合盘匹配系统 — 排盘模块（sxtwl 封装）"""

import datetime

from sxtwl import Day

from backend import config
from backend.models import BaziData


def _handle_zishi(hour: int, year: int, month: int, day: int) -> tuple[int, int, int]:
    """处理子时跨日：hour=23 时，日期+1（sxtwl 用次日排日柱）。

    子时跨越两日，传统八字以子时初（23:00）归属次日日柱。
    sxtwl 库 fromSolar 的日柱以传入日期为准，因此子时需传入次日日期。

    Args:
        hour: 出生小时（0-23）
        year: 出生年份
        month: 出生月份
        day: 出生日期

    Returns:
        (year, month, day) 调整后的日期
    """
    # 子时（23:00-01:00）需要用次日排日柱
    if hour == 23:
        dt = datetime.date(year, month, day) + datetime.timedelta(days=1)
        return dt.year, dt.month, dt.day

    return year, month, day


def _calc_wuxing_dist(tiangan_list: list[str], dizhi_list: list[str]) -> dict[str, int]:
    """统计五行分布（八字 8 个字的五行计数）。

    Args:
        tiangan_list: 四天干列表
        dizhi_list: 四地支列表

    Returns:
        五行计数字典，如 {"金": 1, "木": 2, "水": 1, "火": 2, "土": 2}
    """
    dist = {wx: 0 for wx in config.WUXING_ORDER}
    for tg in tiangan_list:
        wuxing = config.TIANGAN_WUXING[tg]
        dist[wuxing] += 1
    for dz in dizhi_list:
        wuxing = config.DIZHI_WUXING[dz]
        dist[wuxing] += 1
    return dist


def _calc_nayin(year_pillar: str) -> tuple[str, str]:
    """根据年柱计算纳音。

    Args:
        year_pillar: 年柱字符串，如 "庚辰"

    Returns:
        (纳音名称, 纳音五行)，如 ("白蜡金", "金")
    """
    tg_char = year_pillar[0]
    dz_char = year_pillar[1]
    tg_index = config.TIANGAN.index(tg_char)
    dz_index = config.DIZHI.index(dz_char)
    result = config.NAYIN_TABLE.get((tg_index, dz_index))
    if result is None:
        return ("未知", "未知")
    return result


def get_sizhu(year: int, month: int, day: int, hour: int, minute: int = 0) -> BaziData:
    """根据阳历出生日期时间计算四柱八字。

    sxtwl v2 API:
    - Day.fromSolar(year, month, day) → Day 对象
    - day.getYearGZ() / getMonthGZ() / getDayGZ() → GZ 对象
    - GZ 对象属性: .tg (天干索引 0-9), .dz (地支索引 0-11)
    - day.getHourGZ(hour) → 时柱 GZ，hour 为 0-23 的小时数

    Args:
        year: 出生年份（阳历）
        month: 出生月份（阳历）
        day: 出生日期（阳历）
        hour: 出生小时（0-23）
        minute: 出生分钟（默认0）

    Returns:
        BaziData 对象，包含四柱、日主、五行分布、纳音等完整信息
    """
    # Step 1: 处理子时跨日
    adj_year, adj_month, adj_day = _handle_zishi(hour, year, month, day)

    # Step 2: 调用 sxtwl 排盘
    day_obj = Day.fromSolar(adj_year, adj_month, adj_day)

    # Step 3: 提取年/月/日柱
    year_gz = day_obj.getYearGZ()
    month_gz = day_obj.getMonthGZ()
    day_gz = day_obj.getDayGZ()

    # Step 4: 提取时柱（getHourGZ 接收 hour 参数 0-23）
    # 对于子时(23:00)，isZaoWanZiShi 需设为 True
    is_zaowan_zishi = (hour == 23 or hour == 0)
    hour_gz = day_obj.getHourGZ(hour, is_zaowan_zishi)

    # Step 5: 转换为中文天干地支
    year_pillar = config.TIANGAN[year_gz.tg] + config.DIZHI[year_gz.dz]
    month_pillar = config.TIANGAN[month_gz.tg] + config.DIZHI[month_gz.dz]
    day_pillar = config.TIANGAN[day_gz.tg] + config.DIZHI[day_gz.dz]
    hour_pillar = config.TIANGAN[hour_gz.tg] + config.DIZHI[hour_gz.dz]

    # Step 6: 提取天干地支列表
    tiangan_list = [
        config.TIANGAN[year_gz.tg],
        config.TIANGAN[month_gz.tg],
        config.TIANGAN[day_gz.tg],
        config.TIANGAN[hour_gz.tg],
    ]
    dizhi_list = [
        config.DIZHI[year_gz.dz],
        config.DIZHI[month_gz.dz],
        config.DIZHI[day_gz.dz],
        config.DIZHI[hour_gz.dz],
    ]

    # Step 7: 日主（日柱天干）
    day_master = tiangan_list[2]

    # Step 8: 五行分布统计
    wuxing_dist = _calc_wuxing_dist(tiangan_list, dizhi_list)

    # Step 9: 纳音计算（基于年柱）
    nayin, nayin_wuxing = _calc_nayin(year_pillar)

    return BaziData(
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
        day_master=day_master,
        wuxing_dist=wuxing_dist,
        nayin=nayin,
        nayin_wuxing=nayin_wuxing,
        tiangan_list=tiangan_list,
        dizhi_list=dizhi_list,
    )
