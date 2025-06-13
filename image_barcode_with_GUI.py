import customtkinter
import os
import cv2
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from multiprocessing import Process

IMAGE_PATH = 'C:/Users/Admin/Desktop/Neww/venv/high_res_image.jpg'
THIS_DIR   = os.path.dirname(__file__)
RUN_DECODE = os.path.join(THIS_DIR, 'run_decode.py')

def decode_worker(image_path):
    # This runs in a totally separate Python interpreter.
    import image_barcode
    image_barcode.decode_barcodes(image_path)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1500x920")
        self.title("CTK APP")

        # DETECT button fires off a child process
        self.decode_button = customtkinter.CTkButton(
            self,
            text="DETECT",
            command=self.safe_decode_barcodes
        )
        self.decode_button.grid(row=0, column=0, padx=20, pady=10)

        self.success_button = customtkinter.CTkButton(
            self,
            text="DISPLAY IMAGE",
            command=self.draw_boxes_from_xml
        )
        self.success_button.grid(row=1, column=0, padx=20, pady=10)

        # placeholder for the image display
        self.image_label = customtkinter.CTkLabel(self)
        self.image_label.grid(row=2, column=0, padx=20, pady=10)

    def safe_decode_barcodes(self):
        # Spawn a new process that runs decode_worker()
        p = Process(target=decode_worker, args=(IMAGE_PATH,), daemon=True)
        p.start()

    def draw_boxes_from_xml(self):
        # locate your XML results file
        xml_path = os.path.splitext(IMAGE_PATH)[0] + '_results.xml'
        if not os.path.exists(xml_path):
            print("❌ XML results not found:", xml_path)
            return

        # parse points from XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # load image with OpenCV
        img = cv2.imread(IMAGE_PATH)
        if img is None:
            print("❌ Failed to load image:", IMAGE_PATH)
            return

        # draw each barcode polygon in green + label
        for bc in root.findall('Barcode'):
            # 1) collect the 4 corner points
            pts = []
            for pt in bc.find('Localization').findall('Point'):
                x = int(pt.find('X').text)
                y = int(pt.find('Y').text)
                pts.append([x, y])
            pts = np.array(pts, dtype=np.int32)

            # 2) draw the polygon
            cv2.polylines(img, [pts], isClosed=True, color=(0, 255, 0), thickness=6)

            # 3) figure out the top‑left corner of that polygon
            tl_x, tl_y = pts.min(axis=0)

            # 4) get the label text (e.g. the decoded string)
            label = bc.find('Text').text

            # 5) draw the text just above the box (or slightly inset)
            font       = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 2.0
            thickness  = 2
            # measure text size so we can optionally draw a background
            (w_text, h_text), _ = cv2.getTextSize(label, font, font_scale, thickness)

            # draw a filled rectangle behind the text for contrast (optional)
            cv2.rectangle(
                img,
                (tl_x, tl_y - h_text - 8),            # top-left of rectangle
                (tl_x + w_text + 8, tl_y),            # bottom-right of rectangle
                (0, 255, 0),                          # same green as box
                cv2.FILLED
            )

            # finally, draw the text in black (for readability)
            cv2.putText(
                img,
                label,
                (tl_x + 4, tl_y - 4),                # small margin in from rectangle
                font,
                font_scale,
                (0, 0, 0),                           # text color
                thickness,
                lineType=cv2.LINE_AA
            )

        # save a copy
        boxed_path = os.path.splitext(IMAGE_PATH)[0] + '_boxed.jpg'
        cv2.imwrite(boxed_path, img)
        print("✅ Boxed image saved to:", boxed_path)

        # display in the CTk window
        pil_img = Image.open(boxed_path)
        # scale down to fit if needed
        w, h = pil_img.size
        cap = 1450
        if w > cap:
            pil_img = pil_img.resize(
                (cap, int(cap * h / w)),
                resample=Image.Resampling.LANCZOS
            )

        self.photo = customtkinter.CTkImage(light_image=pil_img, size=pil_img.size)
        self.image_label.configure(image=self.photo)

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()

    except SystemExit as e:
        print(e)