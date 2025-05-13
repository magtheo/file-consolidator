import pyperclip
import tkinter.messagebox as messagebox

def copy_to_clipboard(text_to_copy: str):
    """
    Copies the given text to the system clipboard.
    Shows an error message if pyperclip encounters an issue.
    """
    if not text_to_copy:
        # messagebox.showinfo("Clipboard", "Nothing to copy.") # Optional: uncomment if you want a message for empty copy
        return
    try:
        pyperclip.copy(text_to_copy)
        print("Content copied to clipboard.") # Console feedback for dev
        # You could add a small status bar message in the GUI here too
    except pyperclip.PyperclipException as e:
        error_message = (
            f"Could not copy to clipboard: {e}\n\n"
            "Please ensure you have a copy/paste mechanism installed, such as:\n"
            "- xclip or xsel (on Linux)\n"
            "- pbcopy (comes with macOS)\n"
            "- clip (comes with Windows)"
        )
        print(error_message) # Print to console as GUI might not be fully available for this popup
        messagebox.showerror("Clipboard Error", error_message)
    except Exception as e: # Catch any other unexpected errors
        error_message = f"An unexpected error occurred while copying to clipboard: {e}"
        print(error_message)
        messagebox.showerror("Clipboard Error", error_message)