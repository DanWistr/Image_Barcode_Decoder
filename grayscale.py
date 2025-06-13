import cv2
from rembg import remove
import numpy as np
import os
import sys

to_convert = "image_5.jpg"

def remove_background(input_image_path):
    """…same as before…"""
    try:
        with open(input_image_path, 'rb') as f:
            input_bytes = f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_image_path}")
        return None

    output_bytes = remove(input_bytes)
    arr = np.frombuffer(output_bytes, np.uint8)
    rgba = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
    if rgba is None or rgba.shape[2] != 4:
        print("ERROR: Failed to process image.")
        return None

    base_dir = os.path.dirname(input_image_path)
    name, _  = os.path.splitext(os.path.basename(input_image_path))
    out_path = os.path.join(base_dir, name + "_bg_removed.png")

    if cv2.imwrite(out_path, rgba):
        print(f"Saved background-removed image to: {out_path}")
        return out_path
    else:
        print("ERROR: Could not save the output image.")
        return None

def get_color_dominance(hsv_img):
    """…same as before…"""
    h = hsv_img[:, :, 0]
    green_mask = cv2.inRange(h, 35, 85)
    blue_mask  = cv2.inRange(h, 90, 130)
    return int(cv2.countNonZero(green_mask)), int(cv2.countNonZero(blue_mask))

def rembg_and_invert():
    # 1. Remove background and reload
    rbg_path = remove_background("venv/sample_images/" + to_convert)
    if not rbg_path:
        sys.exit(1)

    img = cv2.imread(rbg_path)
    if img is None:
        print("NO FILE after background removal")
        sys.exit(1)

    # 2. Grayscale + HSV dominance
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    green_count, blue_count = get_color_dominance(hsv)
    thresh_val = 60 if green_count > blue_count else 60
    print(f"{'Green' if green_count>blue_count else 'Blue'} is dominant → using threshold = {thresh_val}")

    # 3. Threshold & invert
    _, bw = cv2.threshold(gray, thresh_val, 200, cv2.THRESH_BINARY)
    bw_inverted = cv2.bitwise_not(bw)

    # 4. Save result
    out_dir = "venv/sample_images_inverted"
    name, _ = os.path.splitext(to_convert)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_inverted.jpg")
    cv2.imwrite(out_path, bw_inverted)
    print(f"Saved inverted image to {out_path}")

rembg_and_invert()
