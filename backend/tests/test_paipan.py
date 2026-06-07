"""排盘模块测试（使用 mock sxtwl）"""

import pytest
from backend.paipan import get_sizhu, _handle_zishi, _calc_wuxing_dist, _calc_nayin, calc_pattern, calc_minggua, calc_shengxiao, calc_minggua_relation, calc_shengxiao_relation
from backend.models import BaziData


class TestHandleZishi:
    """测试子时跨日处理。"""

    def test_normal_hour_no_shift(self):
        """普通时段不跨日。"""
        y, m, d = _handle_zishi(14, 2000, 3, 15)
        assert y == 2000
        assert m == 3
        assert d == 15

    def test_hour_23_cross_day(self):
        """23:00 子时跨日。"""
        y, m, d = _handle_zishi(23, 2000, 3, 15)
        assert y == 2000
        assert m == 3
        assert d == 16  # 次日

    def test_hour_0_no_shift(self):
        """00:00 不跨日（已在当日）。"""
        y, m, d = _handle_zishi(0, 2000, 3, 15)
        assert y == 2000
        assert m == 3
        assert d == 15

    def test_hour_23_month_cross(self):
        """23:00 跨月。"""
        y, m, d = _handle_zishi(23, 2000, 3, 31)
        assert y == 2000
        assert m == 4
        assert d == 1

    def test_hour_23_year_cross(self):
        """23:00 跨年。"""
        y, m, d = _handle_zishi(23, 1999, 12, 31)
        assert y == 2000
        assert m == 1
        assert d == 1


class TestCalcWuxingDist:
    """测试五行分布统计。"""

    def test_basic_distribution(self):
        """基本五行统计。"""
        tg = ["甲", "丙", "庚", "壬"]  # 木、火、金、水
        dz = ["子", "午", "申", "辰"]  # 水、火、金、土
        dist = _calc_wuxing_dist(tg, dz)
        assert dist["金"] == 2  # 庚 + 申
        assert dist["木"] == 1  # 甲
        assert dist["水"] == 2  # 壬 + 子
        assert dist["火"] == 2  # 丙 + 午
        assert dist["土"] == 1  # 辰

    def test_total_count_is_8(self):
        """八字 8 个字的总计数应为 8。"""
        tg = ["甲", "乙", "丙", "丁"]
        dz = ["子", "丑", "寅", "卯"]
        dist = _calc_wuxing_dist(tg, dz)
        total = sum(dist.values())
        assert total == 8


class TestCalcNayin:
    """测试纳音计算。"""

    def test_jiazi_haizhongjin(self):
        """甲子 → 海中金。"""
        name, wuxing = _calc_nayin("甲子")
        assert name == "海中金"
        assert wuxing == "金"

    def test_gengchen_bailajin(self):
        """庚辰 → 白蜡金。"""
        name, wuxing = _calc_nayin("庚辰")
        assert name == "白蜡金"
        assert wuxing == "金"

    def test_renxu_dahaishui(self):
        """壬戌 → 大海水。"""
        name, wuxing = _calc_nayin("壬戌")
        assert name == "大海水"
        assert wuxing == "水"


class TestGetSizhu:
    """测试完整排盘（使用 mock sxtwl）。"""

    def test_normal_date(self):
        """普通日期排盘 - 检查结构。"""
        result = get_sizhu(2000, 3, 15, 14, 30)
        assert isinstance(result, BaziData)
        assert len(result.year_pillar) == 2
        assert len(result.month_pillar) == 2
        assert len(result.day_pillar) == 2
        assert len(result.hour_pillar) == 2
        assert result.day_master in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        assert len(result.tiangan_list) == 4
        assert len(result.dizhi_list) == 4
        total_wuxing = sum(result.wuxing_dist.values())
        assert total_wuxing == 8

    def test_zishi_23(self):
        """23:00 子时排盘 - 检查时柱格式。"""
        result = get_sizhu(2000, 3, 15, 23, 0)
        assert isinstance(result, BaziData)
        assert len(result.hour_pillar) == 2
        # mock 返回固定值，时支索引=4 对应 "辰"
        assert result.hour_pillar[1] == "辰"

    def test_zishi_0(self):
        """00:00 子时排盘。"""
        result = get_sizhu(2000, 3, 15, 0, 0)
        assert isinstance(result, BaziData)
        assert len(result.hour_pillar) == 2

    def test_known_case_2000_0315(self):
        """已知案例：使用 mock 固定值验证。"""
        result = get_sizhu(2000, 3, 15, 14, 0)
        assert isinstance(result, BaziData)
        # mock 返回值：年柱=庚辰, 月柱=己卯, 日柱=壬申, 时柱=甲辰
        assert result.year_pillar == "庚辰"
        assert result.month_pillar == "己卯"
        assert result.day_pillar == "壬申"
        assert result.hour_pillar == "甲辰"
        # 日主应该是日柱天干
        assert result.day_master == result.day_pillar[0]

    def test_nayin_populated(self):
        """纳音字段应有值。"""
        result = get_sizhu(1995, 8, 20, 10, 0)
        assert result.nayin != ""
        assert result.nayin_wuxing in ["金", "木", "水", "火", "土"]

    def test_wuxing_dist_complete(self):
        """五行分布应覆盖所有五行。"""
        result = get_sizhu(1985, 12, 25, 8, 0)
        for wx in ["金", "木", "水", "火", "土"]:
            assert wx in result.wuxing_dist


class TestCalcPattern:
    """测试格局判定。"""

    def test_jianlu_pattern(self):
        """建禄格测试。"""
        # 甲禄在寅，如果月令=寅，为建禄格
        bazi = BaziData(
            year_pillar="庚辰", month_pillar="戊寅", day_pillar="甲子", hour_pillar="甲子",
            day_master="甲", wuxing_dist={"金": 1, "木": 2, "水": 2, "火": 1, "土": 2},
            nayin="白蜡金", nayin_wuxing="金",
            tiangan_list=["庚", "戊", "甲", "甲"],
            dizhi_list=["辰", "寅", "子", "子"],
        )
        pattern = calc_pattern(bazi)
        assert pattern == "建禄格"

    def test_yangren_pattern(self):
        """羊刃格测试。"""
        # 甲羊刃在卯，如果月令=卯，为羊刃格
        bazi = BaziData(
            year_pillar="庚辰", month_pillar="丁卯", day_pillar="甲子", hour_pillar="甲子",
            day_master="甲", wuxing_dist={"金": 1, "木": 2, "水": 2, "火": 1, "土": 2},
            nayin="白蜡金", nayin_wuxing="金",
            tiangan_list=["庚", "丁", "甲", "甲"],
            dizhi_list=["辰", "卯", "子", "子"],
        )
        pattern = calc_pattern(bazi)
        assert pattern == "羊刃格"

    def test_normal_pattern(self):
        """普通格局测试（透出）。"""
        bazi = BaziData(
            year_pillar="庚辰", month_pillar="己卯", day_pillar="壬申", hour_pillar="甲辰",
            day_master="壬", wuxing_dist={"金": 2, "木": 1, "水": 2, "火": 1, "土": 2},
            nayin="白蜡金", nayin_wuxing="金",
            tiangan_list=["庚", "己", "壬", "甲"],
            dizhi_list=["辰", "卯", "申", "辰"],
        )
        pattern = calc_pattern(bazi)
        assert pattern.endswith("格")  # 应以"格"结尾


class TestCalcMinggua:
    """测试命卦计算。"""

    def test_male_minggua(self):
        """男性命卦测试。"""
        result = calc_minggua(2000, True)
        assert "gua" in result
        assert "type" in result
        assert result["type"] in ["东四命", "西四命"]

    def test_female_minggua(self):
        """女性命卦测试。"""
        result = calc_minggua(2000, False)
        assert "gua" in result
        assert "type" in result
        assert result["type"] in ["东四命", "西四命"]


class TestCalcShengxiao:
    """测试生肖计算。"""

    def test_shengxiao_format(self):
        """生肖格式测试。"""
        result = calc_shengxiao("子")
        assert result == "子(鼠)"

    def test_shengxiao_all(self):
        """所有地支的生肖测试。"""
        dizhi_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        expected = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
        for dz, exp in zip(dizhi_list, expected):
            result = calc_shengxiao(dz)
            assert result == f"{dz}({exp})"


class TestCalcMingguaRelation:
    """测试命卦关系计算。"""

    def test_same_type(self):
        """同类型命卦 → 相合。"""
        m1 = {"gua": "坎卦", "type": "东四命"}
        m2 = {"gua": "离卦", "type": "东四命"}
        result = calc_minggua_relation(m1, m2)
        assert result["relation"] == "相合"

    def test_diff_type(self):
        """不同类型命卦 → 互补。"""
        m1 = {"gua": "坎卦", "type": "东四命"}
        m2 = {"gua": "乾卦", "type": "西四命"}
        result = calc_minggua_relation(m1, m2)
        assert result["relation"] == "互补"


class TestCalcShengxiaoRelation:
    """测试生肖关系计算。"""

    def test_liuhe(self):
        """六合测试。"""
        result = calc_shengxiao_relation("子", "丑")
        assert result["relation"] == "合"

    def test_liuchong(self):
        """六冲测试。"""
        result = calc_shengxiao_relation("子", "午")
        assert result["relation"] == "冲"

    def test_normal(self):
        """无特殊关系测试。"""
        result = calc_shengxiao_relation("子", "寅")
        assert result["relation"] == "一般"
