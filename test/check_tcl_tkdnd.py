import tkinter

root = tkinter.Tk()
try:
    # Attempt to load the tkdnd Tcl package
    root.tk.eval('package require tkdnd')
    print("SUCCESS: Tcl command 'package require tkdnd' executed without error.")
    
    # If successful, try to get its version (if available)
    try:
        tkdnd_version = root.tk.eval('package provide tkdnd')
        print(f"tkdnd Tcl package version reported: {tkdnd_version}")
    except tkinter.TclError as e_ver:
        print(f"Could not get tkdnd version via 'package provide tkdnd': {e_ver} (This might be okay if package loaded)")

    # Check if a known tkdnd command exists
    # Example: dnd::drag_source (this is a low-level Tcl command from tkdnd)
    try:
        root.tk.eval('dnd::drag_source') # This will error because args are missing, but if command exists, it won't be "invalid command name"
    except tkinter.TclError as e_cmd:
        if "invalid command name" in str(e_cmd):
            print(f"ERROR: Tcl command 'dnd::drag_source' is an invalid command name. tkdnd might not be fully loaded or available to Tcl.")
        else:
            print(f"INFO: Tcl command 'dnd::drag_source' exists (expected error due to missing args: {e_cmd})")

except tkinter.TclError as e:
    print(f"ERROR: Tcl command 'package require tkdnd' failed: {e}")
    print("This suggests Tcl cannot find or load the tkdnd extension installed by dnf.")
    print("Possible reasons:")
    print("- Tcl's auto_path is not configured to find where dnf installed tkdnd's Tcl files.")
    print("- Mismatch between the Tcl version Python's tkinter is using and the Tcl version tkdnd was built for.")
finally:
    root.destroy()

# Print Tcl/Tk versions for context
root_check = tkinter.Tk()
print(f"\n--- Tcl/Tk Info ---")
print(f"Tcl Patch Level: {root_check.tk.eval('info patchlevel')}")
print(f"Tkinter TclVersion constant: {tkinter.TclVersion}")
print(f"Tkinter TkVersion constant: {tkinter.TkVersion}")
print(f"Tcl Library Dir: {root_check.tk.eval('info library')}")
print(f"Tcl auto_path:\n{root_check.tk.eval('set auto_path')}")
root_check.destroy()