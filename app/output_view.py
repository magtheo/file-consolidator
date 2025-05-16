# app/output_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import tempfile 
import os       
from utils import clipboard_helper

_tkinterdnd2_module_available_globally = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD 
    _tkinterdnd2_module_available_globally = True
except ImportError:
    DND_FILES = "DND_FILES" 
    print("Warning: tkinterdnd2 module not found. File dragging will be disabled globally.")
    print("Install it with: pip install tkinterdnd2")


class OutputView(tk.Frame):
    def __init__(self, master=None, root_window=None, **kwargs):
        super().__init__(master, **kwargs)

        self.root_window = root_window
        self._dnd_enabled_for_instance = False # Initialize to False

        # Attempt to determine root_window if not passed (though it is passed in this app's current structure)
        if _tkinterdnd2_module_available_globally and not self.root_window:
            # print("OutputView __init__: root_window not passed, attempting to find it.")
            current = self.master
            while current:
                # Safely access TkinterDnD attributes
                dnd_tk_class = getattr(TkinterDnD, 'Tk', None) if 'TkinterDnD' in globals() else None
                dnd_wrapper_class = getattr(TkinterDnD, 'DnDWrapper', None) if 'TkinterDnD' in globals() else None
                
                is_dnd_tk = dnd_tk_class and isinstance(current, dnd_tk_class)
                is_dnd_wrapper = dnd_wrapper_class and isinstance(current, dnd_wrapper_class)

                if is_dnd_tk or is_dnd_wrapper:
                    self.root_window = current
                    # print(f"OutputView __init__: Found DND-aware root in hierarchy: {self.root_window} (type: {type(self.root_window)})")
                    break
                current = current.master
            # if not self.root_window:
                # print("OutputView __init__: Could not find DND-aware root in hierarchy.")

        # --- Create Widgets First (including drag_handle_label) ---
        self.text_area = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, height=10, font=("Courier New", 10))
        self.text_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=self.text_scrollbar.set)

        self.btn_copy = ttk.Button(self, text="Copy to Clipboard", command=self.copy_content)
        
        # Initialize drag_handle_label before attempting DND setup on it
        self.drag_handle_label = ttk.Label(self, text="Drag as File", relief=tk.RAISED, padding=(5,3), anchor=tk.CENTER)

        # --- DND Setup ---
        # Setup DND bindings if module is available and we have a root_window
        if _tkinterdnd2_module_available_globally and self.root_window:
            # We no longer check for dnd_transform here. Assume it might be available at runtime.
            try:
                self.drag_handle_label.drag_source_register(DND_FILES) 
                self.drag_handle_label.dnd_bind('<<DragInitCmd>>', self.dnd_provide_file_path_callback)
                self.drag_handle_label.dnd_bind('<<DragEndCmd>>', self.dnd_cleanup_temp_file_callback)
                self._dnd_enabled_for_instance = True # DND is tentatively enabled
                self.drag_handle_label.config(cursor="hand2") # Set cursor if DND setup is successful
                # print("OutputView __init__: DND bindings successfully set up.")
            except tk.TclError as e:
                print(f"TkDND Error in OutputView: Could not initialize drag source. Error: {e}")
                # self._dnd_enabled_for_instance remains False
            except Exception as e: 
                print(f"Unexpected DND Setup Error in OutputView: {e}")
                # self._dnd_enabled_for_instance remains False
        # else: # Debugging prints for why DND might not be set up
            # if not _tkinterdnd2_module_available_globally:
            #    print("OutputView __init__: tkinterdnd2 module not available. DND setup skipped.")
            # if not self.root_window:
            #    print("OutputView __init__: No root_window for DND. DND setup skipped.")
            # self._dnd_enabled_for_instance remains False
        
        self._temp_drag_file_path = None 

        # Configure drag_handle_label's state and text based on whether DND was successfully set up
        if not self._dnd_enabled_for_instance:
            self.drag_handle_label.config(state=tk.DISABLED, text="Drag N/A")
        
        # --- Layout Widgets ---
        self.text_area.grid(row=0, column=0, columnspan=2, sticky='nsew')
        self.text_scrollbar.grid(row=0, column=2, sticky='ns') 
        
        self.btn_copy.grid(row=1, column=0, sticky='ew', pady=(5,0), padx=(0,2)) 
        self.drag_handle_label.grid(row=1, column=1, sticky='ew', pady=(5,0), padx=(2,0))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0)


    def _prepare_temp_file_for_drag(self) -> bool:
        content = self.get_text()
        if not content:
            messagebox.showinfo("Drag File", "Output is empty, nothing to drag.", parent=self)
            return False
        self._cleanup_temp_drag_file() 
        try:
            # Suffix should be .txt, prefix can be more descriptive
            fd, self._temp_drag_file_path = tempfile.mkstemp(suffix=".txt", prefix="consolidated_output_", text=False) 
            with os.fdopen(fd, "wb") as f: # Open in binary mode to write UTF-8 bytes
                f.write(content.encode('utf-8'))
            return True
        except Exception as e:
            messagebox.showerror("Drag File Error", f"Could not create temporary file for dragging: {e}", parent=self)
            self._temp_drag_file_path = None
            return False

    def _cleanup_temp_drag_file(self):
        if self._temp_drag_file_path:
            path_to_remove = self._temp_drag_file_path
            self._temp_drag_file_path = None 
            try:
                if os.path.exists(path_to_remove):
                    os.remove(path_to_remove)
            except Exception as e:
                print(f"Error cleaning up temporary drag file {path_to_remove}: {e}")
    
    def dnd_provide_file_path_callback(self, event):
        # This callback is only triggered if DND bindings were successful.
        if not self.root_window:
             print("Error: OutputView DND callback: root_window is None. Drag will fail.")
             return None

        if self._prepare_temp_file_for_drag():
            # The data returned by this callback will be processed by TkinterDnD.
            # It expects a string (for single path or custom data) or a sequence (tuple/list) of paths.
            # If a sequence, it converts it to a Tcl list string.
            paths_tuple = (self._temp_drag_file_path,)

            if hasattr(self.root_window, 'dnd_transform'):
                 # dnd_transform handles platform-specific path formatting (e.g., braces for spaces on Windows)
                 # and returns data in the format TkDND Tcl layer expects.
                 return self.root_window.dnd_transform(paths_tuple, DND_FILES)
            else:
                # Fallback if dnd_transform is not available
                print(f"Runtime Warning: OutputView's root_window ({type(self.root_window)}) "
                      "does not have 'dnd_transform'. Attempting to provide path directly. Drag may not work as expected on all platforms.")
                # Returning the tuple directly is often the correct fallback, as tkinterdnd2 will convert it to a Tcl list.
                # This is what dnd_transform would do for non-Windows or paths without spaces.
                return paths_tuple
        return None # Temp file preparation failed

    def dnd_cleanup_temp_file_callback(self, event):
        self._cleanup_temp_drag_file()
    
    def destroy(self):
        self._cleanup_temp_drag_file()
        super().destroy()

    def set_text(self, content: str):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', content)
        self.text_area.config(state=tk.DISABLED)

    def get_text(self) -> str:
        # Ensure text ends with a newline for .strip() to not remove the last line if it's empty
        # but also handle if text_area is empty.
        content = self.text_area.get('1.0', tk.END)
        if content == '\n': # Tk.Text widget has a default newline if empty
            return ""
        return content.strip()


    def copy_content(self):
        text_to_copy = self.get_text()
        if text_to_copy:
            clipboard_helper.copy_to_clipboard(text_to_copy)
            original_text = self.btn_copy.cget("text")
            self.btn_copy.config(text="Copied!")
            self.after(2000, lambda: self.btn_copy.config(text=original_text))
        else:
            messagebox.showinfo("Clipboard", "Nothing to copy.", parent=self)