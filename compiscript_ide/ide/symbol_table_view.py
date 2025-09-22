import tkinter as tk
from tkinter import ttk

class SymbolTableView:
    COLS = ("name", "kind", "type", "scope", "line", "used", "extra")

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        ttk.Label(self.frame, text="Tabla de símbolos", anchor="w").pack(fill=tk.X, pady=(0, 4))
        self.tree = ttk.Treeview(self.frame, columns=self.COLS, show="headings", height=12)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        yscroll = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        headings = {
            "name": "Nombre",
            "kind": "Clase de símbolo",
            "type": "Tipo",
            "scope": "Ámbito",
            "line": "Línea",
            "used": "Usado",
            "extra": "Extra"
        }
        for key, title in headings.items():
            self.tree.heading(key, text=title)
            self.tree.column(key, width=110 if key != "extra" else 220, anchor="w")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _enum_to_str(self, e):
        try:
            return e.value
        except Exception:
            return str(e)

    def _sym_to_row(self, sym, scope_name):
        name = getattr(sym, "name", "")
        kind = self._enum_to_str(getattr(sym, "symbol_type", ""))
        dtype = self._enum_to_str(getattr(sym, "data_type", ""))
        line = getattr(sym, "line_number", "")
        used = "Sí" if getattr(sym, "is_used", False) else "No"
        extra_parts = []
        params = getattr(sym, "parameters", None)
        if params:
            ptxt = ", ".join(f"{p.name}:{self._enum_to_str(p.data_type)}" for p in params)
            extra_parts.append(f"params({ptxt})")
        ret = getattr(sym, "return_type", None)
        if ret:
            extra_parts.append(f"ret:{self._enum_to_str(ret)}")
        class_type = getattr(sym, "class_type", None) or getattr(sym, "value", None)
        if class_type and dtype == "class":
            extra_parts.append(f"instancia:{class_type}")
        if getattr(sym, "is_constructor", False):
            extra_parts.append("constructor")
        extra = " | ".join(extra_parts)
        return (name, kind, dtype, scope_name, line, used, extra)

    def load_from_symbol_table(self, symbol_table):
        self.clear()
        global_syms = getattr(symbol_table.global_scope, "symbols", {})
        for sym in global_syms.values():
            self.tree.insert("", "end", values=self._sym_to_row(sym, "global"))
        history = getattr(symbol_table, "all_scopes_history", [])
        for sc in history:
            scope_name = f"{sc['name']} (nivel {sc['level']})"
            for sym in sc['symbols'].values():
                self.tree.insert("", "end", values=self._sym_to_row(sym, scope_name))
        active_scopes = getattr(symbol_table, "scope_stack", [])[1:]
        for sc in active_scopes:
            scope_name = f"{sc.scope_name} (nivel {sc.scope_level})"
            for sym in sc.symbols.values():
                self.tree.insert("", "end", values=self._sym_to_row(sym, scope_name))
