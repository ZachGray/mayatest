import os
import sys
import json
from maya import cmds as mc
from PIL import Image, ImageChops
from mayatest import capture


PRESET_PATH = 'Z:/sb/mayatest/'
PRESET_FILE = 'touch_preset.json'
EXPECTED ='E:/sb/EXPECTED_capture.png'
ACTUAL ='E:/sb/ACTUAL_capture.png'


viewport_options={
    "displayAppearance": "wireframe",
    "grid": False,
    "polymeshes": True,
}
def save_preset(path, preset):
    """Save options to path"""
    with open(path, "w") as f:
        json.dump(preset, f, indent=4)


def load_preset(path):
    """Load options json from path"""
    with open(path, "r") as f:    
        return json.load(f)
        
def save_view_preset(path, view_name):
    """Save view options to path"""
    options = capture.parse_view(view_name)
    save_preset(path, options)

# save_view_preset(os.path.join(PRESET_PATH, "touch_preset.json"), 'modelPanel1')



        

def compare_images(expected_image_path, actual_image_path):
    with Image.open(expected_image_path) as expected_image, Image.open(actual_image_path) as actual_image:
        # Calculate the difference between images
        diff = ImageChops.difference(expected_image, actual_image)
        # Calculate the percentage difference
        percentage_diff = (sum(sum(pixel) for pixel in diff.getdata()) / (
                255.0 * expected_image.width * expected_image.height)) * 100

    return percentage_diff

def compare_and_assert(expected_image_path, actual_image_path, threshold, view_type):
    percentage_diff = compare_images(expected_image_path, actual_image_path)
    if percentage_diff <= threshold:
        message = f"{view_type.capitalize()} view: Images match! Difference in Percentage: {percentage_diff:.2f}%"
        print("Pass:", message)
        return True, message
    else:
        message = f"{view_type.capitalize()} view: Images do not match. Difference in Percentage: {percentage_diff:.2f}%"
        print("Fail:", message)
        return False, message

def cleanup_images(image_paths):
    # Check if image_paths is a list and make it a list if it is not
    if not isinstance(image_paths, list):
        image_paths = [image_paths]
    
    removed_paths = []

    for path in image_paths:
        try:
            os.remove(path)
            removed_paths.append(path)
        except Exception as e:
            print(f"Failed to remove: {path}. Error: {str(e)}")

    if len(removed_paths) == len(image_paths):
        return True  # All images were successfully removed
    else:
        return False  # Some images could not be removed
    


if __name__ == "__main__":
    # Save the preset
    #  save_view_preset(os.path.join(PRESET_PATH, PRESET_FILE), 'modelPanel1')

    preset = load_preset(os.path.join(PRESET_PATH, PRESET_FILE))
    
    # Check camera
    if not mc.objectType(mc.listRelatives('camera1', s=True), isType='camera'):
        print('No camera found')
        sys.exit()

    # Capture the expected image
    # capture.snap('camera1', 800, 800,
    #     overwrite=True,
    #     display_options = preset['display_options'],
    #     viewport_options = preset['viewport_options'],
    #     complete_filename=EXPECTED)
    
    # Capture the actual image
    capture.snap('camera1', 800, 800,
        overwrite=True,
        display_options = preset['display_options'],
        viewport_options = preset['viewport_options'],
        complete_filename=ACTUAL)
    
    # Compare the images
    compare_and_assert(EXPECTED, ACTUAL, 0.1, 'shaded')
    
    # Cleanup the images
    # cleanup_images([EXPECTED, ACTUAL])