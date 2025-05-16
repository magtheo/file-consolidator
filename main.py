# main.py
import tkinter as tk
from app.main_window import AppMainWindow

_tkinterdnd2_module_imported = False
try:
    import tkinterdnd2 # Step 1: Try to import the module
    _tkinterdnd2_module_imported = True
except ImportError:
    print("Warning: tkinterdnd2 module not found. File dragging will not be available.")
    print("Install it with: pip install tkinterdnd2")


if __name__ == "__main__":
    if _tkinterdnd2_module_imported:
        # Step 2: If import succeeded, use tkinterdnd2.Tk() to create the root window.
        # This is the standard way to get a DND-enabled root.
        root = tkinterdnd2.Tk()
        print("Using tkinterdnd2.Tk() as root window for DND.")
    else:
        # Fallback to standard tk.Tk if tkinterdnd2 module couldn't be imported.
        root = tk.Tk()
        print("Using standard tk.Tk(). File dragging will be disabled.")
    
    app = AppMainWindow(master=root)
    root.mainloop()
