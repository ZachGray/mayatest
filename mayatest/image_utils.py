"""
Use PIL to compare two images and assert if they are similar within a threshold.

Example:
compare_and_assert(EXPECTED, ACTUAL, 0.1, 'shaded')
"""

import os
from PIL import Image, ImageChops  # type: ignore


def compare_images(expected_image_path, actual_image_path):
    '''Compare two images and return the percentage difference between them.'''
    with Image.open(expected_image_path) as expected_image, Image.open(
        actual_image_path
    ) as actual_image:
        # Calculate the difference between images
        diff = ImageChops.difference(expected_image, actual_image)
        # Calculate the percentage difference
        percentage_diff = (
            sum(sum(pixel) for pixel in diff.getdata())
            / (255.0 * expected_image.width * expected_image.height)
        ) * 100

    return percentage_diff


def compare_and_assert(expected_image_path, actual_image_path, threshold, view_type):
    '''Compare two images and assert if they are similar within a threshold.'''
    percentage_diff = compare_images(expected_image_path, actual_image_path)
    if percentage_diff <= threshold:
        message = f"{view_type.capitalize()} view: Images match! Difference in Percentage: {percentage_diff:.2f}%"
        print("Pass:", message)
        return True
    else:
        message = f"{view_type.capitalize()} view: Images do not match. Difference in Percentage: {percentage_diff:.2f}%"
        print("Fail:", message)
        return False


def cleanup_images(image_paths):
    '''Remove images from the file system.'''
    # Check if image_paths is a list and make it a list if it is not
    if not isinstance(image_paths, list):
        image_paths = [image_paths]

    removed_paths = []

    for path in image_paths:
        try:
            os.remove(path)
            removed_paths.append(path)
        except (FileNotFoundError, PermissionError) as e:
            print(f"Failed to remove: {path}. Error: {str(e)}")

    if len(removed_paths) == len(image_paths):
        return True  # All images were successfully removed
    else:
        return False  # Some images could not be removed
