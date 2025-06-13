import customtkinter
import threading

def print_name():
    for i in range(4):
        print(f"NAME {i}")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x500")
        self.title("CTK APP")

        # add widgets to app
        self.button = customtkinter.CTkButton(self, text="DETECT", command=print_name)
        self.button.grid(row=0, column=0, padx=20, pady=10)

        self.button2 = customtkinter.CTkButton(self, text="Success Button", command=self.button_click)
        self.button2.grid(row=1, column=0, padx=20, pady=10)
    
    # add methods to app
    def button_click(self):
        print("Sucess")

app = App()
app.mainloop()