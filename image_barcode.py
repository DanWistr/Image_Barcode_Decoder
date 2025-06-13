import json
import os
from _collections_abc import Iterable
from dynamsoft_barcode_reader_bundle import (
    CaptureVisionRouter,
    EnumBarcodeFormat,
    LicenseManager,
    EnumErrorCode
)

LICENSE_KEY = 't0083YQEAAKqisPaOrLvM0tGYIFZd04VlwkQPvSCAZ4R2+kDWpFzDsEKVbxLkbhN4noJKQL+E0fMaU/Pmjx9bxkBIbeFwualmfM803jOjFTODC/izSGg=;t0082YQEAAEOa7iWLgmj5HwcSP7J0uNaMQ/kZ/x8HgwPBUpUE8rgwZj8s7nrHomUArjOIL611KRz1gqlYYYTZ98clI+D2lvWM75vifTOySIIddlJJAg==;t0082YQEAAA/YSn4DjmzJcu2C2qrVkNFVQ3pbrfwAi+IqrxbxV31mVURD6/IhsMOj+eYszSaE4PXkcuJ0GyOjRmygD4xAkHAZ3zfF+2bULAkOfcdJCQ=='

SELECTED_FORMATS = (
    EnumBarcodeFormat.BF_ONED
    | EnumBarcodeFormat.BF_QR_CODE
    | EnumBarcodeFormat.BF_DATAMATRIX
    | EnumBarcodeFormat.BF_PDF417
    | EnumBarcodeFormat.BF_CODE_39
    | EnumBarcodeFormat.BF_CODE_128
)

#---------------------------------------API CONNECTION-------------------------------------------------------#
def init_router():
    # Initialize license (unified API)
    err, msg = LicenseManager.init_license(LICENSE_KEY)
    print("Errors:",err, ", Message:",msg)
    if err not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
        raise RuntimeError(f"License init failed ({err}): {msg}")

    # Configure router (unified API)
    router = CaptureVisionRouter()
    raw_settings = router.output_settings('default')

    if isinstance(raw_settings, tuple):
        settings_json = next((item for item in raw_settings if isinstance(item, str)), None)
        if not settings_json:
            raise RuntimeError("Unable to retrieve settings JSON from output_settings()")
    else:
        settings_json = raw_settings

    cfg = json.loads(settings_json)
    task_cfg = cfg.setdefault('BarcodeReaderTaskSetting', {})
    image_param = task_cfg.setdefault('ImageParameter', {})

    #Maximum DSLR resolution
    image_param['MaxWidth'] = 6000
    image_param['MaxHeight'] = 4000

    task_cfg['DeblurModes'] = [9]
    task_cfg['BarcodeFormatIds'] = int(SELECTED_FORMATS)

    router.init_settings(json.dumps(cfg))
    
    return router

#--------------------------------------DECODER FUNCTION-------------------------------------------------------#
def decode_barcodes(image_path):
    # Initialize the router
    try:
        router = init_router()
        print("Router initialized.")
    except Exception as e:
        print("Failed during init_router:", e)
        return

    try:
        results = router.capture(image_path)
        print("Capture complete.")
    except Exception as e:
        print("Failed during capture:", e)
        return
    
    decoded = []
    
    for idx, res in enumerate(results):
        try:
            print("") #blank Space for readability
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
            print(f"Failed {idx}: {e}")

        if decoded:
            last = decoded[-1]
            print(f"Detected code {len(decoded)}:")
            print(f"  Text        : {last['text']}")
            print(f"  Format      : {last['format']}")
            print(f"  Confidence  : {last['confidence']}")
            print(f"  Localization: {last['localization']}")     
        else:
            print("No barcodes detected.")
    
    return decoded