import cv2
import numpy as np
from pylibdmtx import pylibdmtx
from threading import Thread

class VideoStream:
    def __init__(self, src=1, width=640, height=480, buffer_size=1):
        self.cap = cv2.VideoCapture(src, cv2.CAP_ANY)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
        self.stopped = False
        self.grabbed, self.frame = self.cap.read()
        Thread(target=self._update, daemon=True).start()

    def _update(self):
        while not self.stopped:
            self.grabbed, self.frame = self.cap.read()

    def read(self):
        return self.grabbed, self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()


def detect_candidates(gray):
    # Preprocess: bilateral filter preserves edges
    blur = cv2.bilateralFilter(gray, 10, 75, 75)
    # Adaptive threshold for varying illumination
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    # Morphological close to fill small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    h, w = gray.shape
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100 or area > w*h*0.2:
            continue
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
        if len(approx) == 4 and cv2.isContourConvex(approx):
            # Bounding rect
            x, y, cw, ch = cv2.boundingRect(approx)
            aspect = cw/ch
            if 0.8 < aspect < 1.2:
                candidates.append((x, y, cw, ch))
    return candidates


def main():
    vs = VideoStream(src=1, width=640, height=480)
    print("Starting optimized PCB DataMatrix scanner. Press 'q' to quit.")

    try:
        while True:
            ret, frame = vs.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Detect potential DataMatrix regions
            rois = detect_candidates(gray)
            for (x, y, cw, ch) in rois:
                roi = gray[y:y+ch, x:x+cw]
                # Upscale small ROIs for better decoding
                scale = max(1, int(200 / max(cw, ch)))
                if scale > 1:
                    roi = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

                decoded = pylibdmtx.decode(roi)
                for result in decoded:
                    data = result.data.decode('utf-8')
                    # Draw on original frame
                    cv2.rectangle(frame, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
                    cv2.putText(frame, data, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 255, 0), 2)
                    print(f"Decoded DataMatrix: {data}")

            cv2.imshow('PCB DataMatrix Scanner', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        vs.stop()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()

# Requirements:
# pip install opencv-python pylibdmtx numpy
# Usage:
# python optimized_pcb_dmtx.py
