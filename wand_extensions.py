from sys import float_info
from wand.api import library
import ctypes

class ChannelStatistics(ctypes.Structure):
    _fields_ = [('depth', ctypes.c_size_t),
                ('minima', ctypes.c_double),
                ('maxima', ctypes.c_double),
                ('sum', ctypes.c_double),
                ('sum_squared', ctypes.c_double),
                ('sum_cubed', ctypes.c_double),
                ('sum_fourth_power', ctypes.c_double),
                ('mean', ctypes.c_double),
                ('variance', ctypes.c_double),
                ('standard_deviation', ctypes.c_double),
                ('kurtosis', ctypes.c_double),
                ('skewness', ctypes.c_double),
                ('entropy', ctypes.c_double)]

library.MagickGetImageChannelStatistics.argtypes = [ctypes.c_void_p]
library.MagickGetImageChannelStatistics.restype = ctypes.POINTER(ChannelStatistics)

from wand.image import Image

class StatisticsImage(Image):
    def my_statistics(self):
        """Calculate & return tuple of stddev, mean, max, & min."""

        GRAY_CHANNEL = 1
        SCALE = 100
        MAX = 65535

        s = library.MagickGetImageChannelStatistics(self.wand)

        channel_stats = s[GRAY_CHANNEL]

        return [
            SCALE * channel_stats.minima / MAX,
            SCALE * channel_stats.maxima / MAX,
            SCALE * channel_stats.mean / MAX,
            SCALE * channel_stats.standard_deviation / MAX
        ]
