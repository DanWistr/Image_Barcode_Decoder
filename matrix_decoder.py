import cv2
import subprocess
import tempfile
import os
import xml.etree.ElementTree as ET

# Path to BarcodeReader CLI
BARCODE_CLI_PATH = "C://Users//Admin//Downloads//BarcodeReaderCLI//bin//BarcodeReaderCLI.exe"

def parse_barcode_xml(xml_output):
    """
    Parses the XML output from BarcodeReader CLI
    Returns a list of dicts with barcode text and bounding box
    """
    results = []
    try:
        root = ET.fromstring(xml_output)
        for barcode in root.findall(".//Barcode"):
            text = barcode.find("Text").text
            rect = barcode.find("Rect")
            left = int(rect.get("Left"))
            top = int(rect.get("Top"))
            width = int(rect.get("Width"))
            height = int(rect.get("Height"))
            results.append({
                "text": text,
                "box": (left, top, left + width, top + height)
            })
    except Exception as e:
        print("XML Parse Error:", e)
    return results

def read_barcodes_from_image(image_path):
    args = []
    args.append(BARCODE_CLI_PATH)   # Full path or relative path to the CLI
    args.append("-type=code39")                     # (Optional) Restrict barcode type
    args.append(image_path)                          # The temp image saved from webcam
    args.append("-f")                                # Output format
    args.append("xml")                               # Use XML for structured parsing

    cp = subprocess.run(
        args,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return cp.stdout, cp.stderr

def main():
    cap = cv2.VideoCapture(1)  # Webcam index

    if not cap.isOpened():
        print("Cannot access camera.")
        return

    print("Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save current frame to a temp image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            frame_path = tmp.name
            cv2.imwrite(frame_path, frame)

        # Read barcodes from this frame
        stdout, stderr = read_barcodes_from_image(frame_path)
        barcodes = parse_barcode_xml(stdout)

        # Delete temp image
        os.remove(frame_path)

        # Draw boxes and text on frame
        for b in barcodes:
            x1, y1, x2, y2 = b["box"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, b["text"], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)
            print("Detected:", b["text"])

        # Show the video feed
        cv2.imshow("Barcode Reader", frame)

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
