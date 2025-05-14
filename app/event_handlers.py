# app/event_handlers.py
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from pathlib import Path # For getting root directory name
# from core.file_processor import FileProcessor # Already available via app_window
# from core import config

def handle_select_directory(app_window):
    directory = filedialog.askdirectory(mustexist=True, title="Select Project Root Directory")
    if directory:
        app_window.selected_root_dir = directory
        app_window.current_tree_data = None # Clear old tree data
        app_window.status_bar.config(text=f"Scanning: {directory}...")
        app_window.update_idletasks() # Ensure status bar updates

        try:
            # Store the generated tree data on the app_window for later use
            app_window.current_tree_data = app_window.file_processor.generate_file_tree(directory)
            app_window.file_tree_view.populate_tree(app_window.current_tree_data)
            app_window.output_view.set_text("") 
            app_window.status_bar.config(text=f"Selected: {directory}")
        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid directory selected: {ve}")
            app_window.status_bar.config(text=f"Error: Invalid directory.")
        except PermissionError as pe:
            messagebox.showerror("Permission Error", f"Cannot access directory or its contents: {pe}")
            app_window.status_bar.config(text=f"Error: Permission denied.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan directory: {e}")
            app_window.status_bar.config(text=f"Error: Failed to scan. {e}")


def handle_consolidate_files(app_window):
    if not app_window.selected_root_dir:
        messagebox.showinfo("Info", "Please select a root directory first.")
        return

    # Get checked files using the new method
    checked_files = app_window.file_tree_view.get_checked_files()

    if not checked_files:
        messagebox.showinfo("Info", "No files checked in the tree.")
        return

    try:
        output_parts = []
        
        # 1. Add selected directory path
        output_parts.append(f"Current Root Directory: {app_window.selected_root_dir}\n")

        # 2. Add full tree structure
        if hasattr(app_window, 'current_tree_data') and app_window.current_tree_data is not None:
            root_dir_name = Path(app_window.selected_root_dir).name
            formatted_tree = app_window.file_processor.format_tree_structure(
                app_window.current_tree_data,
                root_dir_name # Pass the name of the root for display
            )
            output_parts.append(f"File Structure:\n{formatted_tree}\n")
        else:
            output_parts.append("File Structure: (Not available - rescan directory if needed)\n")

        # 3. Add header for file contents
        output_parts.append("Selected File Contents:\n" + "="*30 + "\n")

        # 4. Get consolidated file content
        consolidated_content_str = app_window.file_processor.consolidate_files_content(
            checked_files,
            app_window.selected_root_dir
        )
        output_parts.append(consolidated_content_str)
        
        full_output = "".join(output_parts)
        app_window.output_view.set_text(full_output)
        app_window.status_bar.config(text=f"Consolidated {len(checked_files)} file(s).")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to consolidate files: {e}")
        app_window.status_bar.config(text=f"Error: Consolidation failed. {e}")