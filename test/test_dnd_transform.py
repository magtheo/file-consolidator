# test/test_dnd_transform.py
import tkinter
import sys
import os

print(f"--- Python Environment ---")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"\n--- sys.path (Python's module search paths) ---")
for i, p in enumerate(sys.path):
    print(f"{i}: {p}")

print(f"\n--- PYTHONPATH environment variable ---")
pythonpath_env = os.environ.get('PYTHONPATH')
if pythonpath_env:
    print(f"PYTHONPATH is set to: {pythonpath_env}")
else:
    print(f"PYTHONPATH is not set.")

print(f"\n--- Attempting to import tkinterdnd2 ---")
try:
    import tkinterdnd2
    print(f"tkinterdnd2 imported successfully.")
    print(f"  tkinterdnd2.__version__: {getattr(tkinterdnd2, '__version__', 'N/A')}")
    print(f"  tkinterdnd2.__file__: {getattr(tkinterdnd2, '__file__', 'N/A')}")
    
    tkinterdnd2_path_attr = getattr(tkinterdnd2, '__path__', None)
    print(f"  tkinterdnd2.__path__: {tkinterdnd2_path_attr}") # For packages
    print(f"  type(tkinterdnd2): {type(tkinterdnd2)}")
    
    if tkinterdnd2_path_attr and isinstance(tkinterdnd2_path_attr, list) and tkinterdnd2_path_attr:
        print("  tkinterdnd2 is being imported as a package.")
        package_dir = tkinterdnd2_path_attr[0]
        if os.path.isdir(package_dir):
            print(f"  Contents of package directory ({package_dir}):")
            try:
                for item in sorted(os.listdir(package_dir)): # sorted for consistent output
                    print(f"    - {item}")
            except Exception as e_ls:
                print(f"    Could not list contents of {package_dir}: {e_ls}")
        else:
            print(f"  tkinterdnd2.__path__[0] ('{package_dir}') is not a valid directory.")
    elif tkinterdnd2_path_attr is None and getattr(tkinterdnd2, '__file__', None):
         print("  tkinterdnd2 is being imported as a single module file (no __path__ attribute).")
    else:
        print("  tkinterdnd2.__path__ is not as expected for a typical package or module with a file.")

except ImportError as e_imp:
    print(f"ERROR: Failed to import tkinterdnd2: {e_imp}")
    print("Please ensure it is installed and accessible in your Python environment.")
    # Attempt to show error in a basic Tk window if tkinter is available
    try:
        err_root = tkinter.Tk()
        err_root.title("TkDND2 Import Error")
        tkinter.Label(err_root, text=f"Failed to import tkinterdnd2:\n{e_imp}\n\nCheck console output for details.", fg="red", wraplength=480).pack(padx=20, pady=20)
        err_root.geometry("500x200")
        err_root.mainloop()
    except Exception:
        pass # If Tk itself fails, console output is the only way
    exit()
except Exception as e_gen_imp:
    print(f"ERROR: An unexpected error occurred during tkinterdnd2 import: {e_gen_imp}")
    exit()

print(f"\n--- TkinterDND2 Test Initialization ---")
root = None
fake_file_path_global = None
test_file_dir_global = None

try:
    # This is where tkinterdnd2.Tk is crucial. Its type will tell us a lot.
    root = tkinterdnd2.Tk()
    print(f"Successfully created tkinterdnd2.Tk() object.")
    print(f"  root object type: {type(root)}")
    print(f"  tkinterdnd2.Tk module: {getattr(type(root), '__module__', 'N/A')}") # Helps identify origin
    
    root.title("TkDND2 dnd_transform Test")
    
    test_file_dir = "/tmp"
    if sys.platform == "win32":
        temp_dir_base = os.environ.get("TEMP", "C:\\Temp")
        test_file_dir = os.path.join(temp_dir_base, "My Test Dir With Spaces")
        try:
            os.makedirs(test_file_dir, exist_ok=True)
        except Exception as e_mkdir:
            print(f"Warning: Could not create directory {test_file_dir}: {e_mkdir}. Using simpler temp dir.")
            test_file_dir = temp_dir_base 

    fake_file_path = os.path.join(test_file_dir, "fake file test.txt") 
    fake_file_path_global = fake_file_path
    test_file_dir_global = test_file_dir if sys.platform == "win32" and "My Test Dir With Spaces" in test_file_dir else None


    try:
        with open(fake_file_path, "w") as f:
            f.write("test content for drag and drop")
        print(f"Created test file: {fake_file_path}")
    except Exception as e_file:
        print(f"ERROR: Could not create test file {fake_file_path}: {e_file}")
        raise

    paths_tuple = (fake_file_path,)

    # Test for dnd_transform
    print(f"\n--- Checking for 'dnd_transform' method on root ({type(root)}) ---")
    if hasattr(root, 'dnd_transform'):
        print(f"INFO: root has 'dnd_transform' method.")
        try:
            formatted_path_data = root.dnd_transform(paths_tuple, tkinterdnd2.DND_FILES)
            print(f"SUCCESS: root.dnd_transform call worked. Input: {paths_tuple}, Output: {formatted_path_data}")
            tkinter.Label(root, text=f"SUCCESS: root.dnd_transform exists and callable.\nInput: {paths_tuple}\nOutput: {formatted_path_data}", fg="green", wraplength=480).pack(pady=10, padx=10)
        except Exception as e_transform:
            print(f"ERROR: root.dnd_transform exists but call failed: {e_transform}")
            tkinter.Label(root, text=f"ERROR: root.dnd_transform exists but call failed:\n{e_transform}", fg="red", wraplength=480).pack(pady=10, padx=10)
    else:
        print(f"WARNING: root DOES NOT have 'dnd_transform' method. Attempting manual format.")
        
        formatted_paths_manual_for_tcl = []
        for p in paths_tuple:
            # More robust manual quoting for Tcl (though not as good as dnd_transform)
            # This is a simplified version; Tcl's list rules are more complex.
            if " " in p or "{" in p or "}" in p or "\\" in p:
                 # Basic Tcl list element quoting: wrap in braces.
                 # If path contains braces, they need to be escaped, but dnd_transform handles this better.
                 # For this test, simple brace wrapping for paths with spaces is a common manual approach.
                p_formatted = f"{{{p}}}"
            else:
                p_formatted = p
            formatted_paths_manual_for_tcl.append(p_formatted)

        manual_output_tuple_for_dnd_call = paths_tuple # dnd call still takes the raw Python tuple
        
        # This string is for display of what Tcl *might* see if this list were converted
        tcl_list_string_representation = " ".join(formatted_paths_manual_for_tcl)
        
        print(f"Manual format attempt for DND_FILES. Input: {paths_tuple}, Approx Tcl list string: '{tcl_list_string_representation}'")
        tkinter.Label(root, text=f"WARNING: root DOES NOT have 'dnd_transform'.\nManual format for {paths_tuple}\n -> (Approx. Tcl list string: '{tcl_list_string_representation}')", fg="orange", wraplength=480).pack(pady=10, padx=10)

        # Try a simple drag source with manual formatting if dnd_transform is missing
        def on_drag_init_manual_test(event_dnd):
            print("Drag init (manual test in test_dnd_transform.py)")
            # For drag source, provide the Python tuple. tkinter/tkinterdnd2 handles Tcl conversion.
            # The 'manual_output_tuple_for_dnd_call' is just 'paths_tuple' here.
            # The point of dnd_transform would be to pre-format this tuple if needed.
            return paths_tuple # Use the original Python tuple

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
    error_msg = f"General error during TkDND2 setup or test: {e}\n(Check console for detailed import logs)"
    print(f"ERROR: {error_msg}") # Also print to console
    if root is None and 'tkinter' in sys.modules:
        try:
            # Create a basic Tk window to show the error if possible
            err_display_root = tkinter.Tk()
            err_display_root.title("TkDND2 Test Error")
            tkinter.Label(err_display_root, text=error_msg, fg="red", wraplength=480).pack(padx=10,pady=10)
            err_display_root.geometry("500x200") # Ensure some size
            err_display_root.mainloop()
        except Exception as e_tk_err_display:
            print(f"Could not create Tk window for error display: {e_tk_err_display}")
    elif root: # If root was partially initialized
         tkinter.Label(root, text=error_msg, fg="red", wraplength=480).pack(padx=10,pady=10)
         root.mainloop() # Try to show the error on the existing root

if root and not root.winfo_exists(): # If root was created but mainloop not reached/window closed early
    pass # Avoid error if mainloop was in the except block and already ran
elif root:
    print("\n--- Starting Tkinter mainloop ---")
    root.geometry("500x450") # Adjusted for potentially more text
    root.mainloop()
    print("--- Tkinter mainloop finished ---")

# Cleanup dummy file and directory
print("\n--- Starting Cleanup ---")
try:
    if fake_file_path_global and os.path.exists(fake_file_path_global):
        os.remove(fake_file_path_global)
        print(f"Cleaned up test file: {fake_file_path_global}")
    if test_file_dir_global and os.path.exists(test_file_dir_global):
        if not os.listdir(test_file_dir_global): # Check if directory is empty
            os.rmdir(test_file_dir_global)
            print(f"Cleaned up test directory: {test_file_dir_global}")
        else:
            print(f"Warning: Test directory {test_file_dir_global} not empty, not removed.")
    elif test_file_dir_global and not os.path.exists(test_file_dir_global):
        print(f"Info: Test directory {test_file_dir_global} was not created or already cleaned up.")

except Exception as e_clean:
    print(f"Warning: Error cleaning up test file/directory: {e_clean}")

print("--- Script Finished ---")