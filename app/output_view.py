# app/output_view.py
import tkinter as tk
from tkinter import ttk
from utils import clipboard_helper # Import from sibling package 'utils'

class OutputView(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.text_area = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, height=10, font=("Courier New", 10))
        
        # Scrollbar for text_area
        text_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=text_scrollbar.set)

        self.btn_copy = ttk.Button(self, text="Copy to Clipboard", command=self.copy_content)

        # Layout
        self.text_area.grid(row=0, column=0, sticky='nsew')
        text_scrollbar.grid(row=0, column=1, sticky='ns')
        self.btn_copy.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5,0))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def set_text(self, content: str):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', content)
        self.text_area.config(state=tk.DISABLED)

    def get_text(self) -> str:
        return self.text_area.get('1.0', tk.END).strip()

    def copy_content(self):
        text_to_copy = self.get_text()
        if text_to_copy:
            clipboard_helper.copy_to_clipboard(text_to_copy)
            # Optionally provide feedback like changing button text temporarily
            # self.btn_copy.config(text="Copied!")
            # self.after(2000, lambda: self.btn_copy.config(text="Copy to Clipboard"))
        else:
            # You can use tkinter.messagebox here if you want a popup for "nothing to copy"
            print("Nothing to copy from output view.")