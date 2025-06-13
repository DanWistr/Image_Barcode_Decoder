import sys
import image_barcode

def main():
    if len(sys.argv) != 2:
        print("Usage: run_decode.py <image_path>")
        sys.exit(1)
    image_path = sys.argv[1]
    decoded = image_barcode.decode_barcodes(image_path)
    print("Child decoded result:", decoded)

if __name__ == "__main__":
    main()