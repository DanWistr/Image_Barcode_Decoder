# PCB Barcode & QR/DataMatrix Scanner Pipeline
# --------------------------------------------
# This script captures live video from a camera, detects small code regions on PCBs,
# applies optional super-resolution via OpenCV or model-based upscaling, then decodes
# DataMatrix, QR, and barcodes in real time.

# --- Required Libraries ---
# Install via: pip install opencv-python numpy pillow pylibdmtx pyzbar imutils torch torchvision

import cv2
import numpy as np
from PIL import Image
from pylibdmtx.pylibdmtx import decode as dmtx_decode
from pyzbar.pyzbar import decode as zbar_decode
import threading
import queue
import time
import imutils

# --- Configuration ---
CAMERA_INDEX = 1            # Change to match your camera device
FRAME_WIDTH = 1920          # Desired capture resolution
FRAME_HEIGHT = 1080
MIN_CONTOUR_AREA = 100      # Minimum area to consider a candidate region
STACK_SIZE = 5              # Number of frames to stack for noise reduction
SR_SCALE = 2                # Upscaling factor for super-resolution fallback
USE_CV2_SR = True           # If True, use OpenCV cubic resize

# --- Optional Model-Based Super-Resolution Setup (comment out if unused) ---
# Uncomment below to enable a pretrained Real-ESRGAN via torch.hub
# import torch
# sr_model = torch.hub.load('xinntao/Real-ESRGAN', 'RealESRGAN_x2plus', pretrained=True)
# sr_model.eval()
# device = 'cuda' if torch.cuda.is_available() else 'cpu'
# sr_model.to(device)


def super_resolve(crop: np.ndarray) -> np.ndarray:
    """
    Upscales the crop by SR_SCALE.
    By default, uses OpenCV cubic interpolation as a fallback.
    If a model is loaded, you can replace this section with model inference.
    """
    h, w = crop.shape[:2]
    # Fallback: OpenCV resize
    return cv2.resize(crop, (w * SR_SCALE, h * SR_SCALE), interpolation=cv2.INTER_CUBIC)


def detect_code_regions(gray: np.ndarray) -> list:
    """Return bounding boxes of candidate code regions"""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cnts = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    boxes = []
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(approx) > MIN_CONTOUR_AREA:
            x, y, w, h = cv2.boundingRect(approx)
            boxes.append((x, y, w, h))
    return boxes


def stack_and_process(frames: list) -> np.ndarray:
    """Average-stacks a list of color frames to reduce noise."""
    arrs = [f.astype(np.float32) for f in frames]
    stack = np.mean(arrs, axis=0).astype(np.uint8)
    return stack


def decode_codes(crop: np.ndarray) -> list:
    """Decode DataMatrix & QR/barcodes from the crop"""
    pil = Image.fromarray(crop)
    results = []
    # DataMatrix
    for r in dmtx_decode(pil):
        results.append(r.data.decode('utf-8'))
    # QR & 1D barcodes
    for z in zbar_decode(pil):
        results.append(z.data.decode('utf-8'))
    return list(set(results))

# --- Threaded Pipeline Components ---
frame_queue = queue.Queue(maxsize=STACK_SIZE)
running = True


def camera_thread():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    while running:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_queue.full():
            frame_queue.get()
        frame_queue.put(frame)
    cap.release()


def processing_thread():
    cv2.namedWindow('PCB Scanner', cv2.WINDOW_NORMAL)
    while running:
        if frame_queue.qsize() < STACK_SIZE:
            time.sleep(0.01)
            continue
        frames = [frame_queue.get() for _ in range(STACK_SIZE)]
        stack = stack_and_process(frames)
        gray = cv2.cvtColor(stack, cv2.COLOR_BGR2GRAY)
        boxes = detect_code_regions(gray)
        display = stack.copy()
        for x, y, w, h in boxes:
            crop = stack[y:y+h, x:x+w]
            sr_crop = super_resolve(crop)
            texts = decode_codes(cv2.cvtColor(sr_crop, cv2.COLOR_BGR2RGB))
            if texts:
                cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(display, texts[0], (x, y-5), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 1)
        cv2.imshow('PCB Scanner', display)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

# --- Main Execution ---
if __name__ == '__main__':
    cam_t = threading.Thread(target=camera_thread, daemon=True)
    proc_t = threading.Thread(target=processing_thread, daemon=True)
    cam_t.start()
    proc_t.start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        cam_t.join()
        proc_t.join()
