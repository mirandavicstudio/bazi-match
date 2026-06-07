"""排盘模块测试"""

import pytest
from backend.paipan import get_sizhu, _handle_zishi, _calc_wuxing_dist, _calc_nayin
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
    """测试完整排盘。"""

    def test_normal_date(self):
        """普通日期排盘。"""
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
        """23:00 子时排盘。"""
        result = get_sizhu(2000, 3, 15, 23, 0)
        assert isinstance(result, BaziData)
        assert result.hour_pillar[1] == "子"  # 时支应为子

    def test_zishi_0(self):
        """00:00 子时排盘。"""
        result = get_sizhu(2000, 3, 15, 0, 0)
        assert isinstance(result, BaziData)
        assert result.hour_pillar[1] == "子"

    def test_known_case_1990_0515(self):
        """已知案例：1990年5月15日14时，应能正常排盘。"""
        result = get_sizhu(1990, 5, 15, 14, 0)
        assert isinstance(result, BaziData)
        # 验证年柱庚午
        assert result.year_pillar == "庚午"
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
