import customtkinter
import os
import customtkinter
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
        self.geometry("600x500")
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
            text="Success Button",
            command=lambda: print("Success")
        )
        self.success_button.grid(row=1, column=0, padx=20, pady=10)

    def safe_decode_barcodes(self):
        # Spawn a new process that runs decode_worker()
        p = Process(target=decode_worker, args=(IMAGE_PATH,), daemon=True)
        p.start()

if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()

    except SystemExit as e:
        print(e)