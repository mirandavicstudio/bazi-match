"""Mock sxtwl 模块，用于测试环境"""

class GZ:
    """干支对象，包含 tg (天干索引) 和 dz (地支索引) 属性"""
    def __init__(self, tg: int, dz: int):
        self.tg = tg
        self.dz = dz


class Day:
    """Mock Day 类，模拟 sxtwl.Day 对象"""
    
    @staticmethod
    def fromSolar(year: int, month: int, day: int):
        """模拟 fromSolar 方法，返回 Mock Day 对象"""
        return Day()
    
    def getYearGZ(self) -> GZ:
        """返回预设的年柱干支索引"""
        # 默认返回 庚辰年: 庚=6, 辰=4
        return GZ(6, 4)
    
    def getMonthGZ(self) -> GZ:
        """返回预设的月柱干支索引"""
        # 默认返回 己卯月: 己=5, 卯=3
        return GZ(5, 3)
    
    def getDayGZ(self) -> GZ:
        """返回预设的日柱干支索引"""
        # 默认返回 壬申日: 壬=8, 申=8
        return GZ(8, 8)
    
    def getHourGZ(self, hour: int, zaowan_zishi: bool = False) -> GZ:
        """返回预设的时柱干支索引"""
        # 默认返回 甲辰时: 甲=0, 辰=4
        return GZ(0, 4)
