import cv2
from pyzbar import pyzbar

def main():
    # Open default camera (0)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Decode barcodes and QR codes in the frame
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            x, y, w, h = barcode.rect
            # Draw rectangle around code
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            data = barcode.data.decode('utf-8')
            typ = barcode.type
            label = f"{data} ({typ})"
            # Put decoded text above rectangle
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow("Barcode/QR Code Scanner", frame)

        # Exit loop on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()