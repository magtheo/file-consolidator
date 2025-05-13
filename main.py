# main.py
import tkinter as tk
from app.main_window import AppMainWindow # Import from 'app' package

if __name__ == "__main__":
    root = tk.Tk()
    app = AppMainWindow(master=root)
    # app.pack(fill="both", expand=True) # AppMainWindow is now a Frame managing itself
    root.mainloop()