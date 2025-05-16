# test/test_dnd_transform.py
import tkinter
import sys 
import os

try:
    import tkinterdnd2
    print("tkinterdnd2 imported successfully.")
except ImportError:
    print("Failed to import tkinterdnd2. Please install it.")
    exit()

root = None
fake_file_path_global = None
test_file_dir_global = None

try:
    root = tkinterdnd2.Tk()
    root.title("TkDND2 dnd_transform Test")
    
    test_file_dir = "/tmp"
    if sys.platform == "win32":
        # Use user's temp directory for better permissions
        temp_dir_base = os.environ.get("TEMP", "C:\\Temp")
        test_file_dir = os.path.join(temp_dir_base, "My Test Dir With Spaces") # Ensure space in path
        try:
            os.makedirs(test_file_dir, exist_ok=True)
        except Exception as e_mkdir:
            print(f"Warning: Could not create directory {test_file_dir}: {e_mkdir}. Using simpler temp dir.")
            test_file_dir = temp_dir_base # Fallback to just TEMP

    # Ensure filename also has a space if possible, for thorough testing
    fake_file_path = os.path.join(test_file_dir, "fake file test.txt") 
    
    # Store globally for cleanup
    fake_file_path_global = fake_file_path
    test_file_dir_global = test_file_dir if "My Test Dir With Spaces" in test_file_dir else None


    try:
        with open(fake_file_path, "w") as f:
            f.write("test content for drag and drop")
        print(f"Created test file: {fake_file_path}")
    except Exception as e_file:
        print(f"ERROR: Could not create test file {fake_file_path}: {e_file}")
        # Critical for test, so exit or raise
        raise

    paths_tuple = (fake_file_path,)

    if hasattr(root, 'dnd_transform'):
        print(f"INFO: root ({type(root)}) has 'dnd_transform' method.")
        try:
            formatted_path_data = root.dnd_transform(paths_tuple, tkinterdnd2.DND_FILES)
            print(f"SUCCESS: root.dnd_transform call worked. Input: {paths_tuple}, Output: {formatted_path_data}")
            tkinter.Label(root, text=f"SUCCESS: root.dnd_transform exists and callable.\nInput: {paths_tuple}\nOutput: {formatted_path_data}", fg="green", wraplength=480).pack(pady=10, padx=10)
        except Exception as e_transform:
            print(f"ERROR: root.dnd_transform exists but call failed: {e_transform}")
            tkinter.Label(root, text=f"ERROR: root.dnd_transform exists but call failed:\n{e_transform}", fg="red", wraplength=480).pack(pady=10, padx=10)
    else:
        print(f"WARNING: root ({type(root)}) DOES NOT have 'dnd_transform' method. Attempting manual format.")
        
        formatted_paths_manual_for_tcl = []
        for p in paths_tuple:
            if sys.platform == "win32" and " " in p:
                formatted_paths_manual_for_tcl.append("{%s}" % p)
            else:
                formatted_paths_manual_for_tcl.append(p)
        
        # This tuple is what our app's fallback would return to tkinterdnd2 internals
        manual_output_tuple = tuple(formatted_paths_manual_for_tcl)
        
        # For display, show how Tcl might represent this as a list string
        # (tkinterdnd2 usually handles the conversion from tuple to Tcl list string)
        tcl_list_string_representation = " ".join(formatted_paths_manual_for_tcl)
        
        print(f"Manual format attempt for DND_FILES. Input: {paths_tuple}, Tuple for tkinterdnd2: {manual_output_tuple}, Approx Tcl list string: '{tcl_list_string_representation}'")
        tkinter.Label(root, text=f"WARNING: root DOES NOT have 'dnd_transform'.\nManual format for {paths_tuple}\n -> Tuple for tkinterdnd2: {manual_output_tuple}\n(Approx. Tcl list string: '{tcl_list_string_representation}')", fg="orange", wraplength=480).pack(pady=10, padx=10)

        # Try a simple drag source with manual formatting if dnd_transform is missing
        def on_drag_init_manual_test(event_dnd):
            print("Drag init (manual test in test_dnd_transform.py)")
            # Use the manually formatted tuple
            return manual_output_tuple 

        try:
            test_label = tkinter.Label(root, text="Drag Me (Manual Fallback Test - Drop on text editor)", cursor="hand2", relief=tkinter.RAISED, padx=10, pady=5)
            test_label.pack(pady=10)
            test_label.drag_source_register(tkinterdnd2.DND_FILES)
            test_label.dnd_bind('<<DragInitCmd>>', on_drag_init_manual_test)
            print("INFO: Registered a test drag source using manual path formatting approach.")
            tkinter.Label(root, text="Drag source registered with manual fallback. Try dragging 'Drag Me' label.", fg="blue").pack(pady=5)
        except Exception as e_ds:
            print(f"ERROR setting up manual drag source test: {e_ds}")
            tkinter.Label(root, text=f"Error setting up manual drag: {e_ds}", fg="red").pack(pady=5)


except Exception as e:
    error_msg = f"General error during TkDND2 setup or test: {e}"
    print(error_msg)
    if root is None: 
        root = tkinter.Tk() 
    tkinter.Label(root, text=error_msg, fg="red", wraplength=480).pack(padx=10,pady=10)

if root:
    root.geometry("500x400") 
    root.mainloop()

# Cleanup dummy file and directory
try:
    if fake_file_path_global and os.path.exists(fake_file_path_global):
        os.remove(fake_file_path_global)
        print(f"Cleaned up test file: {fake_file_path_global}")
    if test_file_dir_global and os.path.exists(test_file_dir_global):
        # Check if directory is empty before removing
        if not os.listdir(test_file_dir_global):
            os.rmdir(test_file_dir_global)
            print(f"Cleaned up test directory: {test_file_dir_global}")
        else:
            print(f"Warning: Test directory {test_file_dir_global} not empty, not removed.")
except Exception as e_clean:
    print(f"Warning: Error cleaning up test file/directory: {e_clean}")