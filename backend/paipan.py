"""八字合盘匹配系统 — 排盘模块（sxtwl 封装）"""

import datetime

from sxtwl import Day

from backend import config
from backend.models import BaziData

# =============================================================================
# 十神计算相关常量
# =============================================================================

# 天干阴阳：True = 阳干, False = 阴干
TIANGAN_YINYANG = {
    "甲": True,   # 阳
    "乙": False,  # 阴
    "丙": True,   # 阳
    "丁": False,  # 阴
    "戊": True,   # 阳
    "己": False,  # 阴
    "庚": True,   # 阳
    "辛": False,  # 阴
    "壬": True,   # 阳
    "癸": False,  # 阴
}

# 地支藏干表（主气、中气、余气）
# 格式：地支 → [主气, 中气, 余气]（None 表示无）
DIZHI_ZANGGAN = {
    "子": ["癸", None, None],      # 主气：癸（阴水）
    "丑": ["己", "辛", "癸"],      # 主气：己（阴土），中气：辛（阴金），余气：癸（阴水）
    "寅": ["甲", "丙", "戊"],      # 主气：甲（阳木），中气：丙（阳火），余气：戊（阳土）
    "卯": ["乙", None, None],      # 主气：乙（阴木）
    "辰": ["戊", "乙", "癸"],      # 主气：戊（阳土），中气：乙（阴木），余气：癸（阴水）
    "巳": ["丙", "庚", "戊"],      # 主气：丙（阳火），中气：庚（阳金），余气：戊（阳土）
    "午": ["丁", "己", None],      # 主气：丁（阴火），中气：己（阴土）
    "未": ["己", "丁", "乙"],      # 主气：己（阴土），中气：丁（阴火），余气：乙（阴木）
    "申": ["庚", "壬", "戊"],      # 主气：庚（阳金），中气：壬（阳水），余气：戊（阳土）
    "酉": ["辛", None, None],      # 主气：辛（阴金）
    "戌": ["戊", "辛", "丁"],      # 主气：戊（阳土），中气：辛（阴金），余气：丁（阴火）
    "亥": ["壬", "甲", None],      # 主气：壬（阳水），中气：甲（阳木）
}


def _get_shishen(day_master: str, target_gan: str) -> str:
    """根据日主和目标天干，计算十神名称。
    
    Args:
        day_master: 日主天干，如 "壬"
        target_gan: 目标天干，如 "甲"
        
    Returns:
        十神名称，如 "伤官"
    """
    # 获取日主和目标的五行
    dm_wuxing = config.TIANGAN_WUXING[day_master]
    tg_wuxing = config.TIANGAN_WUXING[target_gan]
    
    # 获取日主和目标的阴阳
    dm_yinyang = TIANGAN_YINYANG[day_master]
    tg_yinyang = TIANGAN_YINYANG[target_gan]
    
    # 判断关系
    if dm_wuxing == tg_wuxing:
        # 同我
        return "比肩" if dm_yinyang == tg_yinyang else "劫财"
    
    # 我生
    if config.WUXING_SHENG[dm_wuxing] == tg_wuxing:
        return "食神" if dm_yinyang == tg_yinyang else "伤官"
    
    # 生我
    if config.WUXING_SHENG[tg_wuxing] == dm_wuxing:
        return "正印" if dm_yinyang != tg_yinyang else "偏印"
    
    # 我克
    if config.WUXING_KE[dm_wuxing] == tg_wuxing:
        return "正财" if dm_yinyang != tg_yinyang else "偏财"
    
    # 克我
    if config.WUXING_KE[tg_wuxing] == dm_wuxing:
        return "正官" if dm_yinyang != tg_yinyang else "七杀"
    
    return "未知"


def calc_shishen_list(bazi_data: BaziData) -> list:
    """计算八字四柱的十神列表。
    
    Args:
        bazi_data: BaziData 对象
        
    Returns:
        十神列表，每个元素包含 zhu, gan, zhi, gan_shishen, zhi_shishen
    """
    day_master = bazi_data.day_master
    tiangan_list = bazi_data.tiangan_list
    dizhi_list = bazi_data.dizhi_list
    
    pillar_names = ["年柱", "月柱", "日柱", "时柱"]
    shishen_list = []
    
    for i, pillar_name in enumerate(pillar_names):
        gan = tiangan_list[i]
        zhi = dizhi_list[i]
        
        # 日柱的天干就是日主，十神为"日主"
        if i == 2:  # 日柱
            gan_shishen = "日主"
        else:
            gan_shishen = _get_shishen(day_master, gan)
        
        # 地支十神：取地支的主气藏干计算
        main_zanggan = DIZHI_ZANGGAN[zhi][0]
        zhi_shishen = _get_shishen(day_master, main_zanggan)
        
        shishen_list.append({
            "zhu": pillar_name,
            "gan": gan,
            "zhi": zhi,
            "gan_shishen": gan_shishen,
            "zhi_shishen": zhi_shishen,
        })
    
    return shishen_list


# =============================================================================
# 命卦计算相关常量
# =============================================================================

# 命卦查表：男性（余数 → 卦名）
# 余数计算：(出生年份 - 3) ÷ 9 取余数
# 余数 0 = 离卦，余数 5 寄坤卦
MINGGUA_MALE = {
    1: "坎卦", 2: "坤卦", 3: "震卦", 4: "巽卦",
    5: "坤卦",  # 男命 5 寄坤
    6: "乾卦", 7: "兑卦", 8: "艮卦", 9: "离卦",
    0: "离卦",  # 余数 0
}

# 命卦查表：女性（余数 → 卦名）
# 余数计算：(出生年份 + 3) ÷ 9 取余数
# 余数 0 = 离卦，余数 5 寄艮卦
MINGGUA_FEMALE = {
    1: "坎卦", 2: "坤卦", 3: "震卦", 4: "巽卦",
    5: "艮卦",  # 女命 5 寄艮
    6: "乾卦", 7: "兑卦", 8: "艮卦", 9: "离卦",
    0: "离卦",  # 余数 0
}

# 命卦类型：东四命/西四命
MINGGUA_TYPE = {
    "坎卦": "东四命", "离卦": "东四命", "震卦": "东四命", "巽卦": "东四命",
    "乾卦": "西四命", "坤卦": "西四命", "艮卦": "西四命", "兑卦": "西四命",
}

# 地支生肖映射
DIZHI_SHENGXIAO = {
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔",
    "辰": "龙", "巳": "蛇", "午": "马", "未": "羊",
    "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
}

# 地支六合表（用于生肖关系判定）
DIZHI_LIUHE_SET = [
    {"子", "丑"}, {"寅", "亥"}, {"卯", "戌"},
    {"辰", "酉"}, {"巳", "申"}, {"午", "未"},
]

# 地支六冲表
DIZHI_LIUCHONG_SET = [
    {"子", "午"}, {"丑", "未"}, {"寅", "申"},
    {"卯", "酉"}, {"辰", "戌"}, {"巳", "亥"},
]


def calc_minggua(year: int, is_male: bool) -> dict:
    """计算命卦（八宅命卦）。
    
    Args:
        year: 农历年份
        is_male: 是否男性
        
    Returns:
        命卦信息字典，包含 gua（卦名）和 type（东四命/西四命）
    """
    if is_male:
        # 男性：(出生年份 - 3) ÷ 9，取余数
        remainder = (year - 3) % 9
        gua = MINGGUA_MALE[remainder]
    else:
        # 女性：(出生年份 + 3) ÷ 9，取余数
        remainder = (year + 3) % 9
        gua = MINGGUA_FEMALE[remainder]
    
    gua_type = MINGGUA_TYPE[gua]
    return {"gua": gua, "type": gua_type, "remainder": remainder}


def calc_shengxiao(zhi: str) -> str:
    """根据地支计算生肖。
    
    Args:
        zhi: 地支，如 "戌"
        
    Returns:
        生肖字符串，如 "戌(狗)"
    """
    shengxiao = DIZHI_SHENGXIAO.get(zhi, "未知")
    return f"{zhi}({shengxiao})"


def calc_shengxiao_relation(zhi1: str, zhi2: str) -> dict:
    """计算两个地支的生肖关系。
    
    Args:
        zhi1: 第一个地支
        zhi2: 第二个地支
        
    Returns:
        关系字典，包含 relation（关系类型）和 desc（描述）
    """
    dz_set = {zhi1, zhi2}
    
    # 检查六合
    for he_set in DIZHI_LIUHE_SET:
        if he_set == dz_set:
            return {"relation": "合", "desc": "六合，情投意合"}
    
    # 检查六冲
    for chong_set in DIZHI_LIUCHONG_SET:
        if chong_set == dz_set:
            return {"relation": "冲", "desc": "六冲，需要多磨合"}
    
    # 无特殊关系
    return {"relation": "一般", "desc": "无特殊冲合关系"}


def calc_minggua_relation(minggua1: dict, minggua2: dict) -> dict:
    """计算两个命卦的关系。
    
    Args:
        minggua1: 第一个命卦信息
        minggua2: 第二个命卦信息
        
    Returns:
        关系字典，包含 relation（关系类型）和 desc（描述）
    """
    type1 = minggua1["type"]
    type2 = minggua2["type"]
    
    if type1 == type2:
        return {"relation": "相合", "desc": f"同属{type1}，性格相投"}
    else:
        return {"relation": "互补", "desc": f"{type1}与{type2}互补，互相扶持"}


# =============================================================================
# 格局判定相关常量
# =============================================================================

# 地支四库（杂气月令）
DIZHI_SIKU = {"辰", "戌", "丑", "未"}

# 建禄格：日主天干对应的禄地（日主 = 月令地支）
# 甲禄在寅，乙禄在卯，丙戊禄在巳，丁己禄在午，庚禄在申，辛禄在酉，壬禄在亥，癸禄在子
JIANLU_MAP = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}

# 羊刃格：日主对应的羊刃地支
# 甲羊刃在卯，乙羊刃在寅，丙戊羊刃在午，丁己羊刃在巳，庚羊刃在酉，辛羊刃在申，壬羊刃在子，癸羊刃在亥
YANGREN_MAP = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
    "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
    "壬": "子", "癸": "亥",
}


def calc_pattern(bazi_data: BaziData) -> str:
    """计算八字格局（如"杂气正官格"）。
    
    格局判定算法：
    1. 取月令（月柱地支）
    2. 查月令藏干（用 DIZHI_ZANGGAN 常量）
    3. 对每个藏干，计算它相对于日主的十神
    4. 检查这些十神对应的天干是否在四柱天干中透出
    5. 确定格局：
       - 如果透出，取透出的十神为格局
       - 如果没有透出，取主气十神为格局（不透也可成格）
    6. 特殊规则：
       - 月令是辰戌丑未（四库），格局名加"杂气"前缀
       - 日主禄在月令，为"建禄格"
       - 月令是日主羊刃，为"羊刃格"
    
    Args:
        bazi_data: BaziData 对象
        
    Returns:
        格局名称字符串，如 "正官格"、"杂气正官格"、"建禄格"
    """
    day_master = bazi_data.day_master
    tiangan_list = bazi_data.tiangan_list
    dizhi_list = bazi_data.dizhi_list
    
    # 月令 = 月柱地支
    yue_ling = dizhi_list[1]  # 月柱是第二个地支
    
    # 特殊格局判断
    
    # 1. 建禄格：日主禄在月令
    if JIANLU_MAP.get(day_master) == yue_ling:
        return "建禄格"
    
    # 2. 羊刃格：月令是日主羊刃
    if YANGREN_MAP.get(day_master) == yue_ling:
        return "羊刃格"
    
    # 普通格局判断
    
    # 获取月令藏干
    zanggan_list = DIZHI_ZANGGAN.get(yue_ling, [])
    
    # 计算月令藏干对应的十神
    shishen_for_zanggan = []
    for zg in zanggan_list:
        if zg is not None:
            shishen = _get_shishen(day_master, zg)
            shishen_for_zanggan.append((zg, shishen))
    
    # 检查藏干是否透出（对应的天干是否在四柱天干中）
    revealed_shishen = []
    for zg, shishen in shishen_for_zanggan:
        if zg in tiangan_list:
            revealed_shishen.append(shishen)
    
    # 确定格局
    if revealed_shishen:
        # 如果透出，取透出的十神为格局（优先取第一个透出的）
        pattern_shishen = revealed_shishen[0]
    else:
        # 如果没有透出，取主气十神为格局
        main_zanggan = zanggan_list[0]  # 主气
        pattern_shishen = _get_shishen(day_master, main_zanggan)
    
    # 构建格局名称
    pattern_name = f"{pattern_shishen}格"
    
    # 特殊规则：月令是辰戌丑未（四库），加"杂气"前缀
    if yue_ling in DIZHI_SIKU:
        pattern_name = f"杂气{pattern_shishen}格"
    
    return pattern_name


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


def get_sizhu(year: int, month: int, day: int, hour: int, minute: int = 0, gender: str = "男") -> BaziData:
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
        gender: 性别（"男"或"女"），用于计算命卦

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

    # Step 10: 创建 BaziData 对象
    bazi_data = BaziData(
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

    # Step 11: 计算十神列表
    bazi_data.shishen_list = calc_shishen_list(bazi_data)

    # Step 12: 计算命卦（需要农历年份，这里简化使用公历年）
    # 注意：完整实现需要处理立春前后的农历年份转换
    lunar_year = year  # 简化处理，实际应使用 sxtwl 转换
    is_male = (gender == "男")
    bazi_data.minggua = calc_minggua(lunar_year, is_male)

    # Step 13: 计算生肖（取年支）
    year_zhi = dizhi_list[0]
    bazi_data.shengxiao = calc_shengxiao(year_zhi)

    # Step 14: 计算格局
    bazi_data.pattern = calc_pattern(bazi_data)

    return bazi_data
