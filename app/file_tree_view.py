# app/file_tree_view.py
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import os

class FileTreeView(ttk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.tree = ttk.Treeview(self, selectmode='extended', show='tree headings') # 'extended' for multi-select
        
        # Define columns
        self.tree["columns"] = ("fullpath", "type")

        # MODIFICATION 1: Increased width and minwidth for column #0
        self.tree.column("#0", width=350, minwidth=200, anchor='w', stretch=tk.YES) 
        self.tree.column("fullpath", width=0, stretch=tk.NO) 
        self.tree.column("type", width=0, stretch=tk.NO)     

        self.tree.heading("#0", text="Name", anchor='w')

        ysb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.file_icon = self._load_or_create_icon("file.png", "blue")
        self.folder_icon = self._load_or_create_icon("folder.png", "orange")
        self.folder_open_icon = self._load_or_create_icon("folder-open.png", "yellow")
        self.error_icon = self._load_or_create_icon("error.png", "red")

        self.tree.tag_configure('file', image=self.file_icon)
        self.tree.tag_configure('directory', image=self.folder_icon)
        self.tree.tag_configure('directory_open', image=self.folder_open_icon)
        self.tree.tag_configure('directory_error', image=self.error_icon)

        self.tree.bind("<<TreeviewOpen>>", self._on_open_dir)
        self.tree.bind("<<TreeviewClose>>", self._on_close_dir)
        

    def _load_or_create_icon(self, icon_name: str, default_color: str = "grey"):
        base_path = Path(__file__).parent.parent / "assets"
        icon_path = base_path / icon_name
        
        if icon_path.is_file():
            try:
                return tk.PhotoImage(file=str(icon_path))
            except tk.TclError as e:
                print(f"Warning: Could not load icon {icon_path}: {e}. Creating dummy icon.")
        
        # MODIFICATION 2: Make dummy PhotoImage smaller
        icon_size = 12 # Make icons 12x12 pixels
        img = tk.PhotoImage(width=icon_size, height=icon_size)
        
        if "file" in icon_name: color_to_use = "blue"
        elif "folder-open" in icon_name: color_to_use = "gold" # Brighter yellow
        elif "folder" in icon_name: color_to_use = "darkorange" # Darker orange
        elif "error" in icon_name: color_to_use = "red"
        else: color_to_use = default_color
        
        # Create a small filled square, e.g., 8x8 in the 12x12 canvas
        offset = (icon_size - 8) // 2 
        img.put(color_to_use, to=(offset, offset, offset + 7, offset + 7)) 
        return img



    def _on_open_dir(self, event):
        item_id = self.tree.focus() 
        if item_id and self.tree.tag_has('directory', item_id): # Check if item_id is valid
            self.tree.item(item_id, tags=('directory_open',))

    def _on_close_dir(self, event):
        item_id = self.tree.focus()
        if item_id and self.tree.tag_has('directory_open', item_id): # Check if item_id is valid
            self.tree.item(item_id, tags=('directory',))


    def _insert_item(self, parent_node_id, item_data):
        item_type = item_data['type']
        
        # Determine tags based on item_type
        if item_type == 'file':
            tags_to_apply = ('file',)
        elif item_type == 'directory':
            tags_to_apply = ('directory',)
        elif item_type == 'directory_error':
            tags_to_apply = ('directory_error',)
            item_data['name'] = f"[Err] {item_data['name']}" # Make error more visible
        else:
            tags_to_apply = ()

        has_children = 'children' in item_data and item_data['children']
        
        node_id = self.tree.insert(
            parent_node_id,
            'end',
            text=item_data['name'],
            values=(item_data['path'], item_type),
            open=False, 
            tags=tags_to_apply
        )

        if item_type == 'directory' and has_children:
            for child_item in item_data['children']:
                self._insert_item(node_id, child_item)

    def populate_tree(self, directory_data_list):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for item_data in directory_data_list:
            self._insert_item('', item_data)

    def get_selected_files(self) -> list[str]:
        selected_file_paths = set()
        selected_item_ids = self.tree.selection()

        for item_id in selected_item_ids:
            item_values = self.tree.item(item_id, 'values')
            if not item_values or len(item_values) < 2: continue

            item_path_str = item_values[0]
            item_type = item_values[1]

            if item_type == 'file':
                selected_file_paths.add(item_path_str)
            elif item_type == 'directory':
                self._add_files_from_directory(item_id, selected_file_paths)
        
        return sorted(list(selected_file_paths))

    def _add_files_from_directory(self, dir_item_id, selected_file_paths_set):
        for child_id in self.tree.get_children(dir_item_id):
            child_values = self.tree.item(child_id, 'values')
            if not child_values or len(child_values) < 2: continue

            child_path_str = child_values[0]
            child_type = child_values[1]

            if child_type == 'file':
                selected_file_paths_set.add(child_path_str)
            elif child_type == 'directory':
                self._add_files_from_directory(child_id, selected_file_paths_set)