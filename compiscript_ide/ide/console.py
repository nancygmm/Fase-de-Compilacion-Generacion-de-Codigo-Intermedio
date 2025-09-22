import tkinter as tk

class Console(tk.Text):
    def __init__(self, parent):
        super().__init__(parent, height=8, bg="black", fg="lime", insertbackground="white", font=("Consolas", 10))
        self.config(state="disabled")

    def log(self, message):
        self.config(state="normal")
        self.insert(tk.END, message + "\n")
        self.config(state="disabled")
        self.see(tk.END)
