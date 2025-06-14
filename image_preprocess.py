import cv2
from rembg import remove
import numpy as np
import os
import sys

to_convert = "new_sample.jpg"

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

def rembg_and_process():
    # 1. Remove background and reload
    rbg_path = remove_background("venv/sample_images/" + to_convert)
    if not rbg_path:
        sys.exit(1)

    img = cv2.imread(rbg_path)
    if img is None:
        print("NO FILE after background removal")
        sys.exit(1)

    # 2. Desaturate: convert to HSV, zero out S channel, back to BGR
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s[:] = 0  # set saturation to zero (minimum)
    hsv_min_sat = cv2.merge([h, s, v])
    desat_img = cv2.cvtColor(hsv_min_sat, cv2.COLOR_HSV2BGR)

    # 3. Black & White: convert desaturated image to grayscale
    gray = cv2.cvtColor(desat_img, cv2.COLOR_BGR2GRAY)

    # 4. Invert the grayscale image
    inverted = cv2.bitwise_not(gray)

    # 5. Save result
    out_dir = "venv/sample_images_processed"
    name, _ = os.path.splitext(to_convert)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_bw_inverted.jpg")
    if cv2.imwrite(out_path, inverted):
        print(f"Saved B&W inverted image to: {out_path}")
    else:
        print("ERROR: Could not save the processed image.")

if __name__ == "__main__":
    rembg_and_process()
