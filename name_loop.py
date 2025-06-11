# Import necessary libraries
import cv2
from pyzbar import pyzbar

def run_data_matrix_detector():
    """
    Initializes the camera, detects and decodes Data Matrix codes in real-time,
    and displays the results on the live feed and in the terminal.
    """
    print("Starting Data Matrix Code Detector...")
    print("Press 'q' to quit the application.")

    # Open the default camera
    # The argument '0' refers to the default camera. If you have multiple cameras,
    # you might need to try '1', '2', etc.
    cap = cv2.VideoCapture(1)

    # Check if the camera was opened successfully
    if not cap.isOpened():
        print("Error: Could not open video stream. Please ensure your camera is connected and not in use.")
        return

    try:
        while True:
            # Read a frame from the camera
            ret, frame = cap.read()

            # Check if the frame was read successfully
            if not ret:
                print("Error: Could not read frame from camera. Exiting...")
                break

            # Convert the frame to grayscale for better barcode detection
            # Pyzbar often performs better on grayscale images.
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect and decode barcodes in the frame
            # pyzbar.decode() returns a list of detected barcodes.
            barcodes = pyzbar.decode(gray_frame)

            # Iterate over all detected barcodes
            for barcode in barcodes:
                # Check if the detected barcode is a Data Matrix
                if barcode.type == "DATAMATRIX":
                    # Extract the barcode data and type
                    barcode_data = barcode.data.decode("utf-8") # Decode bytes to string
                    barcode_type = barcode.type

                    # Print the decoded data to the terminal
                    print(f"Detected {barcode_type}: {barcode_data}")

                    # Draw a rectangle around the barcode on the live feed
                    # The 'rect' attribute contains the bounding box (x, y, width, height)
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) # Green rectangle, thickness 2

                    # Put the decoded text on the frame
                    # Position the text slightly above the rectangle.
                    cv2.putText(frame, barcode_data, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2) # Red text, thickness 2

            # Display the resulting frame
            cv2.imshow("Live Data Matrix Code Detector", frame)

            # Wait for a key press (1ms delay). If 'q' is pressed, exit the loop.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("'q' pressed. Exiting application.")
                break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Release the camera and destroy all OpenCV windows when done
        cap.release()
        cv2.destroyAllWindows()
        print("Application stopped.")

if __name__ == "__main__":
    # Ensure you have the required libraries installed.
    # You can install them using pip:
    # pip install opencv-python pyzbar

    run_data_matrix_detector()
