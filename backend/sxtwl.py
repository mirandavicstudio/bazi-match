"""Mock sxtwl module for testing purposes."""

class GZ:
    """Mock GZ object with tg and dz attributes."""
    def __init__(self, tg, dz):
        self.tg = tg  # 天干 index (0-9)
        self.dz = dz  # 地支 index (0-11)


class Day:
    """Mock Day class for solar-lunar conversion."""
    
    @staticmethod
    def fromSolar(year, month, day):
        """Create a mock Day object from solar date.
        
        Returns fixed values for testing. In real implementation,
        this would calculate the proper lunar date.
        """
        d = Day()
        d._year = year
        d._month = month
        d._day = day
        # Store the solar date for potential use in getHourGZ
        d._solar_year = year
        d._solar_month = month
        d._solar_day = day
        return d
    
    def getYearGZ(self):
        """Mock: Return fixed year pillar.
        
        For testing, return 庚辰 (tg=6, dz=4)
        """
        # This is a simplified mock - real implementation would calculate based on lunar year
        return GZ(6, 4)  # 庚辰
    
    def getMonthGZ(self):
        """Mock: Return fixed month pillar.
        
        For testing, return 壬午 (tg=8, dz=6)
        """
        return GZ(8, 6)  # 壬午
    
    def getDayGZ(self):
        """Mock: Return fixed day pillar.
        
        For testing, return 甲戌 (tg=2, dz=8)
        """
        return GZ(2, 8)  # 甲戌
    
    def getHourGZ(self, hour, is_zaowan_zishi=False):
        """Mock: Return fixed hour pillar.
        
        For testing, return 丙子 (tg=4, dz=10) for most hours,
        and handle 子时 specially.
        """
        if hour == 23 or hour == 0:
            return GZ(4, 10)  # 丙子 (子时)
        return GZ(4, 10)  # 丙子 (simplified)
