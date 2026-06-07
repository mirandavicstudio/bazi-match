"""八字合盘匹配系统 — 匹配引擎（六维度打分 + 汇总 + 等级映射）"""

from backend import config
from backend.models import BaziData, DimensionScore, MatchResult
from backend.paipan import calc_minggua_relation, calc_shengxiao_relation


# ---------------------------------------------------------------------------
# 维度名称映射（中文 → 配置 key）
# ---------------------------------------------------------------------------
DIM_NAME_TO_CONFIG_KEY = {
    "地支合冲": "dizhi_hechong",
    "五行互补": "wuxing_complement",
    "天干合": "tiangan_he",
    "日主关系": "rizhu_relation",
    "纳音": "nayin",
    "神煞": "shensha",
}

# 传统六合/六冲名称对照（用于生成可读命中项）
_LIUHE_NAMES = {
    ("丑", "子"): "子丑合",
    ("寅", "亥"): "寅亥合",
    ("卯", "戌"): "卯戌合",
    ("辰", "酉"): "辰酉合",
    ("巳", "申"): "巳申合",
    ("午", "未"): "午未合",
}

_LIUCHONG_NAMES = {
    ("午", "子"): "子午冲",
    ("未", "丑"): "丑未冲",
    ("申", "寅"): "寅申冲",
    ("酉", "卯"): "卯酉冲",
    ("戌", "辰"): "辰戌冲",
    ("亥", "巳"): "巳亥冲",
}

_WUHE_NAMES = {
    ("己", "甲"): "甲己合",
    ("庚", "乙"): "乙庚合",
    ("丙", "辛"): "丙辛合",
    ("丁", "壬"): "丁壬合",
    ("癸", "戊"): "戊癸合",
}


# ---------------------------------------------------------------------------
# 维度 1：地支合冲
# ---------------------------------------------------------------------------
def calc_dizhi_hechong(a: BaziData, b: BaziData) -> DimensionScore:
    """计算地支合冲维度得分。

    基础分50，六合+15/对，六冲-20/对，三合局+20/局，钳制0-100。

    Args:
        a: 用户 A 的八字
        b: 用户 B 的八字

    Returns:
        DimensionScore 对象
    """
    score = config.SCORE_CONFIG["base_score"]
    hits_he: list[tuple[str, str]] = []
    hits_chong: list[tuple[str, str]] = []
    hits_sanhe: list[str] = []

    a_dizhi = a.dizhi_list
    b_dizhi = b.dizhi_list

    # Step 1: 遍历 A × B 地支组合，检查六合和六冲
    for a_dz in a_dizhi:
        for b_dz in b_dizhi:
            pair = tuple(sorted([a_dz, b_dz]))
            # 六合检查
            if pair in config.DIZHI_LIUHE:
                if pair not in hits_he:
                    score += config.SCORE_CONFIG["dizhi_he_per_hit"]
                    hits_he.append(pair)
            # 六冲检查
            if pair in config.DIZHI_LIUCHONG:
                if pair not in hits_chong:
                    score += config.SCORE_CONFIG["dizhi_chong_per_hit"]
                    hits_chong.append(pair)

    # Step 2: 检查三合局
    combined_dizhi = set(a_dizhi + b_dizhi)
    sanhe_names = ["申子辰", "亥卯未", "寅午戌", "巳酉丑"]
    for i, ju in enumerate(config.SANHE_JU):
        if ju.issubset(combined_dizhi):
            score += config.SCORE_CONFIG["dizhi_sanhe_bonus"]
            hits_sanhe.append(sanhe_names[i])

    # Step 3: 钳制分数
    score = max(0, min(100, score))

    # 构建命中项列表
    hits: list[str] = []
    for pair in hits_he:
        wuxing = config.DIZHI_LIUHE[pair]
        name = _LIUHE_NAMES.get(pair, f"{pair[0]}{pair[1]}合")
        hits.append(f"{name}（{wuxing}）")
    for pair in hits_chong:
        name = _LIUCHONG_NAMES.get(pair, f"{pair[0]}{pair[1]}冲")
        hits.append(name)
    for name in hits_sanhe:
        ju_wuxing = config.SANHE_JU_NAME.get(name, "")
        hits.append(f"三合{name}{ju_wuxing}")

    detail = f"发现{len(hits_he)}组合，{len(hits_chong)}组冲，{len(hits_sanhe)}组三合局"
    return DimensionScore(name="地支合冲", score=score, detail=detail, hits=hits)


# ---------------------------------------------------------------------------
# 维度 2：五行互补
# ---------------------------------------------------------------------------
def calc_wuxing_complement(a: BaziData, b: BaziData) -> DimensionScore:
    """计算五行互补维度得分。

    弱项<0.15为缺、旺项>0.20为旺，A缺+B旺→互补，互补数/10*100。
    无互补→50分中性。

    Args:
        a: 用户 A 的八字
        b: 用户 B 的八字

    Returns:
        DimensionScore 对象
    """
    weak_threshold = config.SCORE_CONFIG["wuxing_weak_threshold"]
    strong_threshold = config.SCORE_CONFIG["wuxing_strong_threshold"]
    theoretical_max = 10  # 5行 × 2方向

    def to_ratio(dist: dict) -> dict[str, float]:
        total = sum(dist.values())
        if total == 0:
            return {wx: 0.0 for wx in config.WUXING_ORDER}
        return {wx: dist.get(wx, 0) / total for wx in config.WUXING_ORDER}

    a_ratio = to_ratio(a.wuxing_dist)
    b_ratio = to_ratio(b.wuxing_dist)

    a_complement = 0  # A 对 B 的互补满足数
    b_complement = 0  # B 对 A 的互补满足数
    hits: list[str] = []

    # Step 1: A 缺 + B 旺
    for wx in config.WUXING_ORDER:
        a_weak = a_ratio[wx] < weak_threshold
        b_strong = b_ratio[wx] > strong_threshold
        if a_weak and b_strong:
            a_complement += 1
            hits.append(f"A缺{wx}，B{wx}旺")

    # Step 2: B 缺 + A 旺
    for wx in config.WUXING_ORDER:
        b_weak = b_ratio[wx] < weak_threshold
        a_strong = a_ratio[wx] > strong_threshold
        if b_weak and a_strong:
            b_complement += 1
            hits.append(f"B缺{wx}，A{wx}旺")

    # Step 3: 计算互补得分
    total_complement = a_complement + b_complement
    if total_complement == 0:
        score = 50.0  # 无互补也无冲突，中性
    else:
        score = total_complement / theoretical_max * 100

    score = max(0, min(100, score))

    detail = f"互补满足数{total_complement}（A对B:{a_complement}，B对A:{b_complement}）"
    return DimensionScore(name="五行互补", score=score, detail=detail, hits=hits)


# ---------------------------------------------------------------------------
# 维度 3：天干合
# ---------------------------------------------------------------------------
def calc_tiangan_he(a: BaziData, b: BaziData) -> DimensionScore:
    """计算天干合维度得分。

    基础分50，五合+20/对，钳制0-100。

    Args:
        a: 用户 A 的八字
        b: 用户 B 的八字

    Returns:
        DimensionScore 对象
    """
    score = config.SCORE_CONFIG["base_score"]
    hits_pairs: list[tuple[str, str]] = []

    a_tiangan = a.tiangan_list
    b_tiangan = b.tiangan_list

    for a_tg in a_tiangan:
        for b_tg in b_tiangan:
            pair = tuple(sorted([a_tg, b_tg]))
            if pair in config.TIANGAN_WUHE:
                if pair not in hits_pairs:
                    score += config.SCORE_CONFIG["tiangan_he_per_hit"]
                    hits_pairs.append(pair)

    score = max(0, min(100, score))

    hits: list[str] = []
    for pair in hits_pairs:
        wuxing = config.TIANGAN_WUHE[pair]
        name = _WUHE_NAMES.get(pair, f"{pair[0]}{pair[1]}合")
        hits.append(f"{name}（{wuxing}）")

    detail = f"发现{len(hits_pairs)}组天干五合"
    return DimensionScore(name="天干合", score=score, detail=detail, hits=hits)


# ---------------------------------------------------------------------------
# 维度 4：日主关系
# ---------------------------------------------------------------------------
def _get_rizhu_score(a_wuxing: str, b_wuxing: str) -> float:
    """根据五行生克关系动态计算日主关系分。

    Args:
        a_wuxing: A 日主五行
        b_wuxing: B 日主五行

    Returns:
        关系分数
    """
    sc = config.SCORE_CONFIG
    if a_wuxing == b_wuxing:
        return sc["rizhu_bijian_score"]  # 比肩 50
    # 我生（A 生 B）
    if config.WUXING_SHENG[a_wuxing] == b_wuxing:
        return sc["rizhu_wosheng_score"]  # 我生 60
    # 我克（A 克 B）
    if config.WUXING_KE[a_wuxing] == b_wuxing:
        return sc["rizhu_woke_score"]  # 我克 70
    # 克我（B 克 A）
    if config.WUXING_KE[b_wuxing] == a_wuxing:
        return sc["rizhu_kewo_score"]  # 克我 55
    # 生我（B 生 A）
    if config.WUXING_SHENG[b_wuxing] == a_wuxing:
        return sc["rizhu_shengwo_score"]  # 生我 75
    return sc["base_score"]  # fallback


def calc_rizhu_relation(a: BaziData, b: BaziData) -> DimensionScore:
    """计算日主关系维度得分。

    生我75、我克70、我生60、克我55、比肩50，双向取平均。

    Args:
        a: 用户 A 的八字
        b: 用户 B 的八字

    Returns:
        DimensionScore 对象
    """
    a_wuxing = config.TIANGAN_WUXING[a.day_master]
    b_wuxing = config.TIANGAN_WUXING[b.day_master]

    score_a_to_b = _get_rizhu_score(a_wuxing, b_wuxing)
    score_b_to_a = _get_rizhu_score(b_wuxing, a_wuxing)

    score = (score_a_to_b + score_b_to_a) / 2
    score = max(0, min(100, score))

    # 描述关系
    def describe_relation(from_wx: str, to_wx: str) -> str:
        if from_wx == to_wx:
            return "比肩"
        if config.WUXING_SHENG[from_wx] == to_wx:
            return "我生（食伤）"
        if config.WUXING_KE[from_wx] == to_wx:
            return "我克（财星）"
        if config.WUXING_KE[to_wx] == from_wx:
            return "克我（官杀）"
        if config.WUXING_SHENG[to_wx] == from_wx:
            return "生我（印星）"
        return "无关系"

    rel_ab = describe_relation(a_wuxing, b_wuxing)
    rel_ba = describe_relation(b_wuxing, a_wuxing)

    hits = [
        f"A日主{a.day_master}({a_wuxing})→B日主{b.day_master}({b_wuxing}): {rel_ab} ({score_a_to_b:.0f}分)",
        f"B日主{b.day_master}({b_wuxing})→A日主{a.day_master}({a_wuxing}): {rel_ba} ({score_b_to_a:.0f}分)",
    ]
    detail = f"A→B:{rel_ab}({score_a_to_b:.0f}分)，B→A:{rel_ba}({score_b_to_a:.0f}分)"
    return DimensionScore(name="日主关系", score=score, detail=detail, hits=hits)


# ---------------------------------------------------------------------------
# 维度 5：纳音
# ---------------------------------------------------------------------------
def calc_nayin_score(a: BaziData, b: BaziData) -> DimensionScore:
    """计算纳音五行维度得分。

    相生80、同类60、相克30、无关系50。

    Args:
        a: 用户 A 的八字
        b: 用户 B 的八字

    Returns:
        DimensionScore 对象
    """
    sc = config.SCORE_CONFIG
    a_nw = a.nayin_wuxing
    b_nw = b.nayin_wuxing
    hits: list[str] = []

    if a_nw == b_nw:
        score = sc["nayin_same_score"]
        relation = "同类"
        hits.append(f"纳音五行同为{a_nw}")
    elif config.WUXING_SHENG[a_nw] == b_nw:
        score = sc["nayin_sheng_score"]
        relation = "相生"
        hits.append(f"{a_nw}生{b_nw}")
    elif config.WUXING_SHENG[b_nw] == a_nw:
        score = sc["nayin_sheng_score"]
        relation = "相生"
        hits.append(f"{b_nw}生{a_nw}")
    elif config.WUXING_KE[a_nw] == b_nw:
        score = sc["nayin_ke_score"]
        relation = "相克"
        hits.append(f"{a_nw}克{b_nw}")
    elif config.WUXING_KE[b_nw] == a_nw:
        score = sc["nayin_ke_score"]
        relation = "相克"
        hits.append(f"{b_nw}克{a_nw}")
    else:
        score = sc["nayin_neutral_score"]
        relation = "无关系"

    score = max(0, min(100, score))
    detail = f"A纳音{a.nayin}({a_nw})，B纳音{b.nayin}({b_nw})，{relation}"
    return DimensionScore(name="纳音", score=score, detail=detail, hits=hits)


# ---------------------------------------------------------------------------
# 维度 6：神煞
# ---------------------------------------------------------------------------
def calc_shensha(a: BaziData, b: BaziData) -> DimensionScore:
    """计算神煞维度得分。

    基础分50，天乙贵人+20/条，钳制0-100。

    Args:
        a: 用户 A 的八字
        b: 用户 B 的八字

    Returns:
        DimensionScore 对象
    """
    score = config.SCORE_CONFIG["base_score"]
    hits: list[str] = []

    a_dizhi = a.dizhi_list
    b_dizhi = b.dizhi_list

    # Step 1: 查 A 的天乙贵人地支，看是否在 B 的地支中
    a_guiren = config.TIANYI_GUIREN.get(a.day_master, [])
    for dz in a_guiren:
        if dz in b_dizhi:
            score += config.SCORE_CONFIG["shensha_per_hit"]
            hits.append(f"A日主{a.day_master}的贵人{dz}在B地支中")

    # Step 2: 查 B 的天乙贵人地支，看是否在 A 的地支中
    b_guiren = config.TIANYI_GUIREN.get(b.day_master, [])
    for dz in b_guiren:
        if dz in a_dizhi:
            score += config.SCORE_CONFIG["shensha_per_hit"]
            hits.append(f"B日主{b.day_master}的贵人{dz}在A地支中")

    score = max(0, min(100, score))
    detail = f"天乙贵人命中{len(hits)}条"
    return DimensionScore(name="神煞", score=score, detail=detail, hits=hits)


# ---------------------------------------------------------------------------
# 总分汇总
# ---------------------------------------------------------------------------
def calc_total_score(dimensions: list[DimensionScore]) -> float:
    """加权汇总六维度得分。

    Args:
        dimensions: 六维度得分列表

    Returns:
        总分（保留1位小数）
    """
    dim_map = {dim.name: dim.score for dim in dimensions}
    total = 0.0
    for dim_name, weight in config.WEIGHTS.items():
        # 通过中文维度名查找对应的配置 key
        found = False
        for cn_name, cfg_key in DIM_NAME_TO_CONFIG_KEY.items():
            if cfg_key == dim_name and cn_name in dim_map:
                total += dim_map[cn_name] * weight
                found = True
                break
        if not found:
            total += 50 * weight  # 缺失维度默认50分
    return round(total, 1)


# ---------------------------------------------------------------------------
# 等级映射
# ---------------------------------------------------------------------------
def map_grade(total_score: float) -> tuple[str, str]:
    """根据总分映射等级和星级。

    Args:
        total_score: 总分

    Returns:
        (等级名称, 星级显示)
    """
    if total_score >= 85:
        return "天作之合", "★★★★★"
    elif total_score >= 70:
        return "情投意合", "★★★★☆"
    elif total_score >= 55:
        return "尚可相处", "★★★☆☆"
    elif total_score >= 40:
        return "需多磨合", "★★☆☆☆"
    else:
        return "相克较重", "★☆☆☆☆"


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def calc_match(bazi_a: BaziData, bazi_b: BaziData) -> MatchResult:
    """计算两个八字的合盘匹配结果。

    Args:
        bazi_a: 用户 A 的八字
        bazi_b: 用户 B 的八字

    Returns:
        MatchResult 对象
    """
    dimensions = [
        calc_dizhi_hechong(bazi_a, bazi_b),
        calc_wuxing_complement(bazi_a, bazi_b),
        calc_tiangan_he(bazi_a, bazi_b),
        calc_rizhu_relation(bazi_a, bazi_b),
        calc_nayin_score(bazi_a, bazi_b),
        calc_shensha(bazi_a, bazi_b),
    ]

    total_score = calc_total_score(dimensions)
    grade, grade_stars = map_grade(total_score)

    # 计算命卦关系（如果双方都有命卦数据）
    minggua_relation = {}
    if bazi_a.minggua and bazi_b.minggua:
        minggua_relation = calc_minggua_relation(bazi_a.minggua, bazi_b.minggua)

    # 计算生肖关系（取年支）
    year_zhi_a = bazi_a.dizhi_list[0] if bazi_a.dizhi_list else ""
    year_zhi_b = bazi_b.dizhi_list[0] if bazi_b.dizhi_list else ""
    shengxiao_relation = {}
    if year_zhi_a and year_zhi_b:
        shengxiao_relation = calc_shengxiao_relation(year_zhi_a, year_zhi_b)

    return MatchResult(
        total_score=total_score,
        grade=grade,
        grade_stars=grade_stars,
        dimensions=dimensions,
        interpretation="",
        minggua_relation=minggua_relation,
        shengxiao_relation=shengxiao_relation,
    )
