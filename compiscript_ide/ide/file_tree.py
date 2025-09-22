import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

class FileTree:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)
        self.tree = ttk.Treeview(self.frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.load_project()

    def load_project(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta ANALIZADOR-SEMANTICO")
        if folder:
            self.project_path = folder
            self.tree.delete(*self.tree.get_children())
            self.insert_folder("", folder)

    def insert_folder(self, parent, path):
        basename = os.path.basename(path)
        node = self.tree.insert(parent, 'end', text=basename, open=False, values=[path])
        if os.path.isdir(path):
            for item in sorted(os.listdir(path)):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path) or full_path.endswith(('.py', '.txt', '.md', '.cps', '.g4')):
                    self.insert_folder(node, full_path)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            path = self.tree.item(selected[0])['values'][0]
            if os.path.isfile(path):
                self.app.open_file(path)
