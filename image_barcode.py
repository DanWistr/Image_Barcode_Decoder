import json
# Install or upgrade the Dynamsoft bundle:
#    pip install --upgrade dynamsoft_barcode_reader_bundle

from dynamsoft_barcode_reader_bundle import (
    CaptureVisionRouter,
    EnumBarcodeFormat,
    LicenseManager,
    EnumErrorCode
)

# Your license key (v10+ unified API)
LICENSE_KEY = 't0083YQEAAKqisPaOrLvM0tGYIFZd04VlwkQPvSCAZ4R2+kDWpFzDsEKVbxLkbhN4noJKQL+E0fMaU/Pmjx9bxkBIbeFwualmfM803jOjFTODC/izSGg=;t0082YQEAAEOa7iWLgmj5HwcSP7J0uNaMQ/kZ/x8HgwPBUpUE8rgwZj8s7nrHomUArjOIL611KRz1gqlYYYTZ98clI+D2lvWM75vifTOySIIddlJJAg==;t0082YQEAAA/YSn4DjmzJcu2C2qrVkNFVQ3pbrfwAi+IqrxbxV31mVURD6/IhsMOj+eYszSaE4PXkcuJ0GyOjRmygD4xAkHAZ3zfF+2bULAkOfcdJCQ=='

# Restrict to common 1D + 2D symbologies:
SELECTED_FORMATS = (
    EnumBarcodeFormat.BF_ONED
    | EnumBarcodeFormat.BF_QR_CODE
    | EnumBarcodeFormat.BF_DATAMATRIX
    | EnumBarcodeFormat.BF_PDF417
    | EnumBarcodeFormat.BF_CODE_39
    | EnumBarcodeFormat.BF_CODE_128
)

# Hard-coded input image path
IMAGE_PATH = 'C:/Users/Admin/Desktop/Neww/venv/pcb_barcode_try.jpg'

def init_router():
    # Initialize license (unified API)
    err, msg = LicenseManager.init_license(LICENSE_KEY)
    if err not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
        raise RuntimeError(f"License init failed ({err}): {msg}")

    router = CaptureVisionRouter()
    # Get current settings for the 'default' template
    raw_settings = router.output_settings('default')
    # Extract JSON string if tuple returned
    if isinstance(raw_settings, tuple):
        settings_json = next((item for item in raw_settings if isinstance(item, str)), None)
        if not settings_json:
            raise RuntimeError("Unable to retrieve settings JSON from output_settings()")
    else:
        settings_json = raw_settings

    cfg = json.loads(settings_json)

    # Ensure BarcodeReaderTaskSetting exists
    task_cfg = cfg.setdefault('BarcodeReaderTaskSetting', {})

    # Ensure ImageParameter exists within task settings
    image_param = task_cfg.setdefault('ImageParameter', {})
    image_param['MaxWidth'] = 6000
    image_param['MaxHeight'] = 4000

    # Use modern deblur modes instead of deprecated deblur_level
    task_cfg['DeblurModes'] = [9]
    # Restrict to selected formats
    task_cfg['BarcodeFormatIds'] = int(SELECTED_FORMATS)

    # Apply updated settings back to the 'default' template
    router.init_settings(json.dumps(cfg))
    return router

def decode_barcodes():
    try:
        # Initialize the router
        router = init_router()

        # CaptureVisionRouter.capture() returns a list of BarcodeResultItem
        results = router.capture(IMAGE_PATH)

        decoded = []
        for res in results:
            try:
                text = res.get_text()
                fmt = res.get_format_string()
                confidence = res.get_confidence()
                location = res.get_location()  # Returns a quadrilateral object

                points = [(point.x, point.y) for point in location.points]

                decoded.append({
                    'text': text,
                    'format': fmt,
                    'confidence': confidence,
                    'localization': points
                })

            except Exception as e:
                print(f"Failed to parse result: {e}")

            # Print only the final (last) decoded result
            if decoded:
                last = decoded[-1]
                print(f"Detected {len(decoded)}th barcode:")
                print(f"[{len(decoded)}]") 
                print(f"  Text        : {last['text']}")
                print(f"  Format      : {last['format']}")
                print(f"  Confidence  : {last['confidence']}")
                print(f"  Localization: {last['localization']}")
            else:
                print("No barcodes detected.")

    except Exception as e:
        print(f"Error: {e}")


# Call decode_barcodes() when the script is executed
if __name__ == '__main__':
    barcodes = decode_barcodes()
    print(barcodes)