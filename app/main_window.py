# app/main_window.py
import tkinter as tk
from tkinter import ttk, PhotoImage
from pathlib import Path

from .file_tree_view import FileTreeView
from .output_view import OutputView
from . import event_handlers # Import the module

from core.file_processor import FileProcessor # Import the class

class AppMainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("LLM Context Builder")
        
        # Attempt to set an icon
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        try:
            if icon_path.is_file():
                app_icon = PhotoImage(file=str(icon_path))
                self.master.iconphoto(True, app_icon)
            else:
                print(f"Icon not found at {icon_path}, using default.")
        except tk.TclError:
            print(f"Could not load icon {icon_path} (possibly invalid image format or Tk issue). Using default.")


        # Set a minimum size and make it resizable
        self.master.minsize(700, 500)
        self.master.geometry("900x700") # Default size

        self.selected_root_dir = None
        self.file_processor = FileProcessor() # Instantiate FileProcessor

        self._create_widgets()
        self._layout_widgets()

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(sticky='nsew') # Make the AppMainWindow frame expand


    def _create_widgets(self):
        # --- Top Controls Frame ---
        self.controls_frame = ttk.Frame(self, padding="10")
        
        self.btn_select_dir = ttk.Button(
            self.controls_frame,
            text="Select Root Directory",
            command=lambda: event_handlers.handle_select_directory(self) # Pass self
        )
        self.btn_consolidate = ttk.Button(
            self.controls_frame,
            text="Consolidate Selected Files",
            command=lambda: event_handlers.handle_consolidate_files(self) # Pass self
        )

        # --- Main Paned Window for resizable areas ---
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)

        # --- File Tree View (Left Pane) ---
        self.file_tree_frame = ttk.LabelFrame(self.main_paned_window, text="File Structure", padding="5")
        self.file_tree_view = FileTreeView(self.file_tree_frame)
        self.main_paned_window.add(self.file_tree_frame, weight=1) # Add to paned window

        # --- Output View (Right Pane) ---
        self.output_frame = ttk.LabelFrame(self.main_paned_window, text="Consolidated Output", padding="5")
        self.output_view = OutputView(self.output_frame)
        self.main_paned_window.add(self.output_frame, weight=2) # Add to paned window

        # --- Status Bar ---
        self.status_bar = ttk.Label(self, text="Ready", anchor='w', relief=tk.SUNKEN, padding="2 5")


    def _layout_widgets(self):
        # Main frame grid configuration
        self.grid_rowconfigure(0, weight=0)  # Controls frame
        self.grid_rowconfigure(1, weight=1)  # Paned window
        self.grid_rowconfigure(2, weight=0)  # Status bar
        self.grid_columnconfigure(0, weight=1)

        # Layout top controls
        self.controls_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.btn_select_dir.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_consolidate.pack(side=tk.LEFT)

        # Layout main paned window
        self.main_paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0,5))

        # Layout widgets within their frames (FileTreeView and OutputView handle their internal layout)
        self.file_tree_view.pack(fill=tk.BOTH, expand=True)
        self.output_view.pack(fill=tk.BOTH, expand=True)
        
        # Layout status bar
        self.status_bar.grid(row=2, column=0, sticky="ew")