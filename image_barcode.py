import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from _collections_abc import Iterable
from dynamsoft_barcode_reader_bundle import (
    CaptureVisionRouter,
    EnumBarcodeFormat,
    LicenseManager,
    EnumErrorCode
)

LICENSE_KEY = 't0083YQEAAKqisPaOrLvM0tGYIFZd04VlwkQPvSCAZ4R2+kDWpFzDsEKVbxLkbhN4noJKQL+E0fMaU/Pmjx9bxkBIbeFwualmfM803jOjFTODC/izSGg=;t0082YQEAAEOa7iWLgmj5HwcSP7J0uNaMQ/kZ/x8HgwPBUpUE8rgwZj8s7nrHomUArjOIL611KRz1gqlYYYTZ98clI+D2lvWM75vifTOySIIddlJJAg==;t0082YQEAAA/YSn4DjmzJcu2C2qrVkNFVQ3pbrfwAi+IqrxbxV31mVURD6/IhsMOj+eYszSaE4PXkcuJ0GyOjRmygD4xAkHAZ3zfF+2bULAkOfcdJCQ=='
TEMPLATE_PATH  = os.path.join(os.path.dirname(__file__), 'template.json')

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
    # 1) Init license
    err, msg = LicenseManager.init_license(LICENSE_KEY)
    print("License init:", msg)
    if err not in (EnumErrorCode.EC_OK, EnumErrorCode.EC_LICENSE_CACHE_USED):
        raise RuntimeError(f"License init failed ({err}): {msg}")

    # 2) Create router
    router = CaptureVisionRouter()

    # 3) Load your full JSON config
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    # 4) Apply it
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

    # Create XML root
    root = ET.Element('Barcodes')
    root.set('image', os.path.basename(image_path))
    root.set('timestamp', datetime.now().isoformat())

    for idx, res in enumerate(results):
        try:
            print("")  # blank space for readability
            text = res.get_text()
            fmt = res.get_format_string()
            confidence = res.get_confidence()
            location = res.get_location()  # quadrilateral
            points = [(pt.x, pt.y) for pt in location.points]

            decoded.append({
                'text': text,
                'format': fmt,
                'confidence': confidence,
                'localization': points
            })

            # XML entry
            bc_elem = ET.SubElement(root, 'Barcode', id=str(len(decoded)))
            ET.SubElement(bc_elem, 'Text').text = text
            ET.SubElement(bc_elem, 'Format').text = fmt
            ET.SubElement(bc_elem, 'Confidence').text = str(confidence)
            loc_elem = ET.SubElement(bc_elem, 'Localization')
            for i, (x, y) in enumerate(points):
                pt_elem = ET.SubElement(loc_elem, 'Point', index=str(i))
                ET.SubElement(pt_elem, 'X').text = str(x)
                ET.SubElement(pt_elem, 'Y').text = str(y)

            # Console log
            print(f"Detected code {len(decoded)}:")
            print(f"  Text        : {text}")
            print(f"  Format      : {fmt}")
            print(f"  Confidence  : {confidence}")
            print(f"  Localization: {points}")

            # Write XML to file
            xml_path = os.path.splitext(image_path)[0] + '_results.xml'
            tree = ET.ElementTree(root)
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            print(f"Results saved to XML: {xml_path}")

        except Exception as e:
            print(f"Failed {idx}: {e}")

    if not decoded:
        print("No barcodes detected.")

    return decoded