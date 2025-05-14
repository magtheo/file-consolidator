# app/main_window.py
import tkinter as tk
from tkinter import ttk, PhotoImage
from pathlib import Path

from .file_tree_view import FileTreeView
from .output_view import OutputView
from . import event_handlers 

from core.file_processor import FileProcessor 

class AppMainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("LLM Context Builder")
        
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        try:
            if icon_path.is_file():
                app_icon = PhotoImage(file=str(icon_path))
                self.master.iconphoto(True, app_icon)
        except tk.TclError:
            print(f"Could not load icon {icon_path}. Using default.")

        self.master.minsize(700, 500)
        self.master.geometry("900x700") 

        self.selected_root_dir = None
        self.file_processor = FileProcessor()
        self.current_tree_data = None # <<< ADD THIS LINE to store tree data

        self._create_widgets()
        self._layout_widgets()

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew')

    # ... rest of the AppMainWindow class remains the same ...
    def _create_widgets(self):
        # --- Top Controls Frame ---
        self.controls_frame = ttk.Frame(self, padding="10")
        
        self.btn_select_dir = ttk.Button(
            self.controls_frame,
            text="Select Root Directory",
            command=lambda: event_handlers.handle_select_directory(self) 
        )
        self.btn_consolidate = ttk.Button(
            self.controls_frame,
            text="Consolidate Checked Files", # Updated button text
            command=lambda: event_handlers.handle_consolidate_files(self) 
        )

        # --- Main Paned Window for resizable areas ---
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)

        # --- File Tree View (Left Pane) ---
        self.file_tree_frame = ttk.LabelFrame(self.main_paned_window, text="File Structure (Click to Check/Uncheck)", padding="5") # Updated label
        self.file_tree_view = FileTreeView(self.file_tree_frame)
        self.main_paned_window.add(self.file_tree_frame, weight=1) 

        # --- Output View (Right Pane) ---
        self.output_frame = ttk.LabelFrame(self.main_paned_window, text="Consolidated Output", padding="5")
        self.output_view = OutputView(self.output_frame)
        self.main_paned_window.add(self.output_frame, weight=2)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text="Ready", anchor='w', relief=tk.SUNKEN, padding="2 5")


    def _layout_widgets(self):
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(2, weight=0) 
        self.grid_columnconfigure(0, weight=1)

        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.btn_select_dir.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_consolidate.pack(side=tk.LEFT)

        self.main_paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))
        self.file_tree_view.pack(fill=tk.BOTH, expand=True)
        self.output_view.pack(fill=tk.BOTH, expand=True)
        
        self.status_bar.grid(row=2, column=0, sticky="ew")