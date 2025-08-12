import cv2
from shmoopy.tunables import *
from shmoopy.metrics import metric
from typing import Dict, Any


class ToneMapShmoo:
    def __init__(self, save_images=False):
        self.save_images = save_images

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

    @tunable_range(None, None)
    def gamma(self, value=1):
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

    @metric
    def stats(self, values: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate image statistics for the LDR output
        """
        return {
            'mean': np.mean(values['image_output']),
            'std': np.std(values['image_output']),
            'min': np.min(values['image_output']),
            'max': np.max(values['image_output'])
        }

    def _get_image(self, row) -> np.ndarray:
        """
        Load the input HDR image from the specified source

        Args:
            row: DataFrame row containing the image source path

        Returns:
            Loaded image as a numpy array
        """
        return cv2.imread(row.image_src, cv2.IMREAD_UNCHANGED)

    def run(self, irow, row) -> Dict[str, Any]:
        """
        Main execution block for this shmoo
        """
        # Load the test image
        image_input = self._get_image(row)

        # Apply the tone mapping algorithm
        if row.algorithm == 'drago':
            tonemap = cv2.createTonemapDrago(bias=row.bias, saturation=row.saturation)
        elif row.algorithm == 'reinhard':
            tonemap = cv2.createTonemapReinhard(color_adapt=row.color_adapt, intensity=row.intensity, gamma=row.gamma)
        else:
            tonemap = cv2.createTonemapMantiuk(scale=row.scale, gamma=row.gamma)

        # Apply the tonemap to the image
        ldr = tonemap.process(image_input)

        # Convert to 8-bit image for display
        image_output = np.clip(ldr * 255, 0, 255).astype('uint8')

        # Save the output image if required
        if self.save_images:
            ##UPDATE TO ROW NUMBER
            output_path = row['image_src'].with_suffix('.tonemapped.jpg')
            cv2.imwrite(str(output_path), image_output)

        # Return all local variables for metric calculations
        return locals()


