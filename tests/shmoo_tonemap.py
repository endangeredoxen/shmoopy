import cv2
from shmoopy.tunables import *


class ToneMapShmoo:
    def __init__(self):
        self.data = "Dummy data for testing"

    @tunable_values(['drago', 'reinhard', 'mantiuk'])
    def algorithm(self, value='drago'):
        return value

    @tunable_range(0, 1)
    def bias(self, value=0.85):
        """
        Used in Drago algorithm; values from 0.7 to 0.9 usually give best results, default value is 0.85
        """
        return value

    @tunable_values([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    def color_adapt(self, value=0):
        """
        Used in Reinhard algorithm; chromatic adaptation value from 0 to 1
        If 1 channels are treated independently, if 0 adaptation level is the same for each channel.
        """
        return value

    @tunable_range(-8, 8)
    def intensity(self, value=0):
        """
        Used in Reinhard algorithm; result intensity in [-8, 8] range. Greater intensity produces brighter results.
        """
        return value

    @tunable_load_array
    def gamma(self, value):
        """
        Used in all algorithms; gamma value for gamma correction
        """
        return value

    @tunable_path
    def image_src(self, value):
        """
        Path to the source image file to be processed
        """
        return value

    @tunable_range(0, None)
    def saturation(self, value=1.0):
        """
        Used in Drago algorithm; positive saturation enhancement value
        Value of 1.0 preserves saturation, values greater than 1 increase saturation and values less than 1 decrease it
        """
        return value

    @tunable_range(0, None)
    def scale(self, value=1.0):
        """
        Used in Mantiuk algorithm; contrast scale factor
        HVS response is multiplied by this parameter, thus compressing dynamic range.
        Values from 0.6 to 0.9 produce best results.
        """
        return value

    #@metric
    def stats(self):
        pass

    def process(self):
        return f"Processed: {self.data}"


