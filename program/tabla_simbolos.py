from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

class SymbolType(Enum):
    VARIABLE = "variable"
    CONSTANT = "constant" 
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    PARAMETER = "parameter"
    ATTRIBUTE = "attribute" 

class DataType(Enum):
    INTEGER = "integer"
    STRING = "string"
    BOOLEAN = "boolean"
    ARRAY = "array"
    CLASS_TYPE = "class"
    VOID = "void"
    METHOD_TYPE = "method"

class ContextType(Enum):
    GLOBAL = "global"
    FUNCTION = "function"
    CLASS = "class"
    LOOP = "loop"          
    METHOD = "method"      

def sizeof(dt: DataType) -> int:
    return {
        DataType.INTEGER: 4,
        DataType.BOOLEAN: 1,
        DataType.STRING: 8,      
        DataType.ARRAY: 8,       
        DataType.CLASS_TYPE: 8,  
        DataType.VOID: 0,
        DataType.METHOD_TYPE: 0,
    }.get(dt, 0)

def align(n: int, a: int = 4) -> int:
    return (n + (a - 1)) & ~(a - 1)

@dataclass
class Symbol:
    name: str
    symbol_type: SymbolType
    data_type: DataType
    scope_level: int
    line_number: int
    column_number: int  
    scope_name: str = "global"  
    is_initialized: bool = False
    is_used: bool = False
    array_element_type: Optional[DataType] = None
    array_size: Optional[int] = None
    parameters: List['Symbol'] = None
    return_type: Optional[DataType] = None
    methods: Dict[str, 'Symbol'] = None      
    attributes: Dict[str, 'Symbol'] = None     
    parent_class: Optional[str] = None        
    class_type: Optional[str] = None 
    value: Any = None  
    is_constructor: bool = False              
    access_modifier: str = "public"  
    offset: int = 0          
    size_bytes: int = 0
    address: Optional[int] = None
    offset: int = 0                 
    size_bytes: int = 0             
    address: Optional[int] = None 
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.methods is None:
            self.methods = {}
        if self.attributes is None:
            self.attributes = {}

class Scope:
    def __init__(self, scope_name: str, scope_level: int, context_type: ContextType, 
                 parent_scope: Optional['Scope'] = None):
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.context_type = context_type
        self.parent_scope = parent_scope
        self.symbols: Dict[str, Symbol] = {}
        self.current_function: Optional[str] = None  
        self.current_class: Optional[str] = None  
        self.fp: int = 0            
        self.param_next_offset: int = 16  
        self.local_next_offset: int = 0    
        
    def insert(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False  
        symbol.scope_name = self.scope_name  
        self.symbols[symbol.name] = symbol
        return True
        
    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)
        
    def get_all_symbols(self) -> Dict[str, Symbol]:
        return self.symbols.copy()

class CompiscriptSymbolTable:

    def _print_class_summary(self, class_symbol: Symbol):
        print(f"    Resumen de clase: {class_symbol.name}")
        if class_symbol.parent_class:
            print(f"    Hereda de: {class_symbol.parent_class}")

        if class_symbol.attributes:
            print("    Atributos:")
            for attr_name, attr_sym in class_symbol.attributes.items():
                if attr_sym.data_type == DataType.ARRAY and attr_sym.array_element_type:
                    t = f"{attr_sym.array_element_type.value}[]"
                elif attr_sym.data_type == DataType.CLASS_TYPE:
                    t = attr_sym.class_type or attr_sym.value or "class"
                else:
                    t = attr_sym.data_type.value
                print(f"      - {attr_name}: {t} (línea {attr_sym.line_number})")
        else:
            print("    Atributos: (ninguno)")

        if class_symbol.methods:
            print("    Métodos:")
            for m_name, m_sym in class_symbol.methods.items():
                params = ", ".join(f"{p.name}:{p.data_type.value}" for p in m_sym.parameters)
                ctor = " [CONSTRUCTOR]" if m_sym.is_constructor else ""
                ret = m_sym.return_type.value if m_sym.return_type else "void"
                print(f"      - {m_name}({params}) -> {ret}{ctor} (línea {m_sym.line_number})")
        else:
            print("    Métodos: (ninguno)")

    
    def __init__(self):
        self.current_scope_level = 0
        self.scope_stack: List[Scope] = []
        self.global_scope = Scope("global", 0, ContextType.GLOBAL)
        self.scope_stack.append(self.global_scope)
        self.all_symbols: List[Symbol] = []
        self.all_scopes_history: List[Dict] = []
        self.current_function = None
        self.current_class = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def enter_scope(self, scope_name: str, context_type: ContextType = ContextType.GLOBAL):
        self.current_scope_level += 1
        parent_scope = self.scope_stack[-1] if self.scope_stack else None
        new_scope = Scope(scope_name, self.current_scope_level, context_type, parent_scope)
        
        if parent_scope:
            new_scope.current_function = parent_scope.current_function
            new_scope.current_class = parent_scope.current_class
        if context_type == ContextType.FUNCTION:
            new_scope.current_function = scope_name
            self.current_function = scope_name
        elif context_type == ContextType.CLASS:
            new_scope.current_class = scope_name
            self.current_class = scope_name
        elif context_type == ContextType.METHOD:
            new_scope.current_function = scope_name
            self.current_function = scope_name
      
        if context_type in (ContextType.FUNCTION, ContextType.METHOD):
            new_scope.fp = 0
            new_scope.param_next_offset = 16  
            new_scope.local_next_offset = 0

            func_sym = self.lookup(new_scope.current_function)
            if func_sym and func_sym.parameters:
                for p in func_sym.parameters:
                    p.size_bytes = sizeof(p.data_type)
                    new_scope.param_next_offset = align(new_scope.param_next_offset, 4)
                    p.offset = new_scope.param_next_offset     
                    p.address = None                             
                    new_scope.param_next_offset += p.size_bytes
        else:
            parent = parent_scope
            if parent:
                new_scope.fp = parent.fp
                new_scope.param_next_offset = parent.param_next_offset
                new_scope.local_next_offset = parent.local_next_offset

            
        self.scope_stack.append(new_scope)
        
    def declare_method(self, class_name: str, method_name: str, return_type: DataType, 
                      parameters: List[tuple], line: int, col: int, 
                      is_constructor: bool = False) -> bool:

        class_symbol = self.lookup(class_name)
        if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
            self.add_error(f"Clase '{class_name}' no encontrada para declarar método", line, col)
            return False
        
        if method_name in class_symbol.methods:
            self.add_error(f"Método '{method_name}' ya está declarado en clase '{class_name}'", line, col)
            return False
        
        param_symbols = []
        for param_name, param_type in parameters:
            param_symbol = Symbol(
                name=param_name,
                symbol_type=SymbolType.PARAMETER,
                data_type=param_type,
                scope_level=self.current_scope_level + 1,
                line_number=line,
                column_number=col,
                is_initialized=True
            )
            param_symbols.append(param_symbol)
        
        method_symbol = Symbol(
            name=method_name,
            symbol_type=SymbolType.METHOD,
            data_type=return_type,
            scope_level=self.current_scope_level,
            line_number=line,
            column_number=col,
            parameters=param_symbols,
            return_type=return_type,
            is_constructor=is_constructor,
            class_type=class_name
        )
        
        class_symbol.methods[method_name] = method_symbol
        
        return True
    
    def declare_attribute(self, class_name: str, attr_name: str, attr_type: DataType, 
                         line: int, col: int, is_constant: bool = False) -> bool:
        
        class_symbol = self.lookup(class_name)
        if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
            self.add_error(f"Clase '{class_name}' no encontrada para declarar atributo", line, col)
            return False
        
        if attr_name in class_symbol.attributes:
            self.add_error(f"Atributo '{attr_name}' ya está declarado en clase '{class_name}'", line, col)
            return False
        
        attr_symbol = Symbol(
            name=attr_name,
            symbol_type=SymbolType.CONSTANT if is_constant else SymbolType.ATTRIBUTE,
            data_type=attr_type,
            scope_level=self.current_scope_level,
            line_number=line,
            column_number=col,
            class_type=class_name
        )
        
        class_symbol.attributes[attr_name] = attr_symbol
        
        return True
    
    def declare_class_instance(self, var_name: str, class_name: str, line: int, col: int) -> bool:
       
        class_symbol = self.lookup(class_name)
        if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
            self.add_error(f"Clase '{class_name}' no está declarada", line, col)
            return False
        
        if self.lookup_current_scope(var_name):
            self.add_error(f"Variable '{var_name}' ya está declarada en este ámbito", line, col)
            return False
        
        instance_symbol = Symbol(
            name=var_name,
            symbol_type=SymbolType.VARIABLE,
            data_type=DataType.CLASS_TYPE,
            scope_level=self.current_scope_level,
            line_number=line,
            column_number=col,
            class_type=class_name,  
            value=class_name       
        )
        
        return self.insert(instance_symbol)
    
    def lookup_class_member(self, class_name: str, member_name: str, member_type: str = "any") -> Optional[Symbol]:
        def search_member_in_hierarchy(current_class_name: str, visited: set = None):
            if visited is None:
                visited = set()
            
            if current_class_name in visited:
                return None
            
            visited.add(current_class_name)
            
            class_symbol = self.lookup(current_class_name)
            if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
                return None
            
            if member_type in ["method", "any"] and member_name in class_symbol.methods:
                return class_symbol.methods[member_name]
            
            if member_type in ["attribute", "any"] and member_name in class_symbol.attributes:
                return class_symbol.attributes[member_name]
            
            if class_symbol.parent_class:
                return search_member_in_hierarchy(class_symbol.parent_class, visited)
            
            return None
        
        return search_member_in_hierarchy(class_name)
    
    def validate_class_access(self, object_var: str, member_name: str) -> tuple[bool, str, Optional[Symbol]]:
        
        var_symbol = self.lookup(object_var)
        if not var_symbol:
            return False, "error", None
        
        if var_symbol.data_type != DataType.CLASS_TYPE:
            return False, "error", None
        
        class_name = var_symbol.class_type or var_symbol.value
        if not class_name:
            return False, "error", None
        
        member_symbol = self.lookup_class_member(class_name, member_name)
        if not member_symbol:
            return False, "error", None
        if member_symbol.symbol_type == SymbolType.METHOD:
            return True, "method", member_symbol
        elif member_symbol.symbol_type in [SymbolType.ATTRIBUTE, SymbolType.VARIABLE]:
            return True, member_symbol.data_type.value, member_symbol
        else:
            return False, "error", None
        
    def print_class_details(self, class_name: str):
        class_symbol = self.lookup(class_name)
        if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
            print(f"Clase '{class_name}' no encontrada")
            return
        
        print(f"\n Detalle/nombre de la clase: {class_name} ")
        
        if class_symbol.parent_class:
            print(f"Hereda de: {class_symbol.parent_class}")
        
        print(f"Declarada en línea: {class_symbol.line_number}")
        
        if class_symbol.attributes:
            print(f"\n Atributos de clase ({len(class_symbol.attributes)}) ")
            for attr_name, attr_symbol in class_symbol.attributes.items():
                print(f"  {attr_name}: {attr_symbol.data_type.value} (línea {attr_symbol.line_number})")
        else:
            print("\n Atributos de clase: ")
            print("Esta clase no tiene atributos")
        
        if class_symbol.methods:
            print(f"\n Métodos de la clase: ({len(class_symbol.methods)}) ---")
            for method_name, method_symbol in class_symbol.methods.items():
                params = [f"{p.name}:{p.data_type.value}" for p in method_symbol.parameters]
                constructor_info = " [CONSTRUCTOR]" if method_symbol.is_constructor else ""
                print(f"  {method_name}({', '.join(params)}) -> {method_symbol.return_type.value}{constructor_info}")
                print(f"    Declarado en línea: {method_symbol.line_number}")
        else:
            print("\n Métodos de la clase:")
            print("Esta clase no tiene métodos")
    
    def exit_scope(self):
        if len(self.scope_stack) > 1:  
            exiting_scope = self.scope_stack.pop()
            self.current_scope_level -= 1
            
            scope_info = {
                'name': exiting_scope.scope_name,
                'level': exiting_scope.scope_level,
                'context': exiting_scope.context_type,
                'symbols': exiting_scope.get_all_symbols().copy()
            }
            self.all_scopes_history.append(scope_info)
            
            for symbol in exiting_scope.symbols.values():
                self.all_symbols.append(symbol)
            
            for symbol in exiting_scope.symbols.values():
                if (symbol.symbol_type == SymbolType.VARIABLE and 
                    not symbol.is_used and symbol.name != "this"):
                    self.add_warning(f"Variable '{symbol.name}' declarada pero no usada "
                                   f"(línea {symbol.line_number})")
            
            if self.scope_stack:
                current_scope = self.scope_stack[-1]
                self.current_function = current_scope.current_function
                self.current_class = current_scope.current_class
    
    def insert(self, symbol: Symbol) -> bool:
        if not self.scope_stack:
            return False
            
        current_scope = self.scope_stack[-1]
        symbol.scope_level = self.current_scope_level
        return current_scope.insert(symbol)
        
    def lookup(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scope_stack):
            symbol = scope.lookup_local(name)
            if symbol:
                symbol.is_used = True
                return symbol
        return None
        
    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        if self.scope_stack:
            return self.scope_stack[-1].lookup_local(name)
        return None
    
    def declare_variable(self, name: str, data_type: DataType, line: int, col: int, 
                    is_constant: bool = False, initial_value: Any = None,
                    array_element_type: Optional[DataType] = None) -> bool:
        
        if self.lookup_current_scope(name):
            self.add_error(f"Identificador '{name}' ya está declarado en este ámbito", line, col)
            return False
        
        if is_constant and initial_value is None:
            self.add_error(f"Constante '{name}' debe ser inicializada en su declaración", line, col)
            return False
            
        symbol_type = SymbolType.CONSTANT if is_constant else SymbolType.VARIABLE
        
        symbol = Symbol(
            name=name,
            symbol_type=symbol_type,
            data_type=data_type,
            scope_level=self.current_scope_level,
            line_number=line,
            column_number=col,
            is_initialized=initial_value is not None,
            value=initial_value if is_constant else None,
            array_element_type=array_element_type
        )
        current_scope = self.scope_stack[-1]
        sym_size = sizeof(data_type)
        current_scope.local_next_offset = align(current_scope.local_next_offset, 4)
        current_scope.local_next_offset += sym_size

        symbol.size_bytes = sym_size
        symbol.offset = -current_scope.local_next_offset   # FP-4, FP-8, ...
        symbol.address = None
        
        return self.insert(symbol)
        
    def declare_function(self, name: str, return_type: DataType, parameters: List[tuple],
                        line: int, col: int, array_element_type: Optional[DataType] = None) -> bool:
        
        if self.lookup_current_scope(name):
            self.add_error(f"Función '{name}' ya está declarada", line, col)
            return False
        
        param_symbols = []
        param_names = set()
        
        for param_name, param_type in parameters:
            if param_name in param_names:
                self.add_error(f"Parámetro '{param_name}' duplicado en función '{name}'", line, col)
                return False
            param_names.add(param_name)
            
            param_symbol = Symbol(
                name=param_name,
                symbol_type=SymbolType.PARAMETER,
                data_type=param_type,
                scope_level=self.current_scope_level + 1,
                line_number=line,
                column_number=col,
                is_initialized=True
            )
            param_symbols.append(param_symbol)
        
        symbol = Symbol(
            name=name,
            symbol_type=SymbolType.FUNCTION,
            data_type=return_type,
            scope_level=self.current_scope_level,
            line_number=line,
            column_number=col,
            parameters=param_symbols,
            return_type=return_type,
            array_element_type=array_element_type  
        )
        
        return self.insert(symbol)
        
    def declare_class(self, name: str, parent_class: Optional[str], line: int, col: int) -> bool:
        
        if self.lookup_current_scope(name):
            self.add_error(f"Clase '{name}' ya está declarada", line, col)
            return False
        
        if parent_class and not self.lookup(parent_class):
            self.add_error(f"Clase padre '{parent_class}' no está declarada", line, col)
            return False
        
        symbol = Symbol(
            name=name,
            symbol_type=SymbolType.CLASS,
            data_type=DataType.CLASS_TYPE,
            scope_level=self.current_scope_level,
            line_number=line,
            column_number=col,
            parent_class=parent_class
        )
        
        return self.insert(symbol)
    
    
    def add_error(self, message: str, line: int, col: int = 0):
        error_msg = f"Error semántico en línea {line}, columna {col}: {message}"
        self.errors.append(error_msg)
    
    def add_warning(self, message: str):
        self.warnings.append(f"Warning: {message}")
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        return self.warnings.copy()
    
    def print_table(self):
        print("Tabla de símbolos")
        print(f"\n Ámbito 0: global (Nivel 0, Contexto: {ContextType.GLOBAL.value}) ")
        if self.global_scope.symbols:
            for name, symbol in self.global_scope.symbols.items():
                self._print_symbol(symbol)
                if symbol.symbol_type == SymbolType.CLASS:
                    self._print_class_summary(symbol)
        else:
            print("  (vacío)")

        for scope_info in self.all_scopes_history:
            print(f"\n--- Ámbito: {scope_info['name']} (Nivel {scope_info['level']}, "
                  f"Contexto: {scope_info['context'].value}) ---")
            
            if scope_info['symbols']:
                for name, symbol in scope_info['symbols'].items():
                    self._print_symbol(symbol)
            else:
                print("  (vacío)")
        
        if len(self.scope_stack) > 1:
            for scope in self.scope_stack[1:]:
                print(f"\n--- Ámbito ACTIVO: {scope.scope_name} (Nivel {scope.scope_level}, "
                      f"Contexto: {scope.context_type.value}) ---")
                if scope.symbols:
                    for name, symbol in scope.symbols.items():
                        self._print_symbol(symbol)
                else:
                    print("  (vacío)")
        
        print(f"\n Resumen ")
        total_symbols = len(self.all_symbols) + len(self.global_scope.symbols)
        classes = [s for s in self.global_scope.symbols.values() if s.symbol_type == SymbolType.CLASS]
        
        print(f"Total de símbolos declarados: {total_symbols}")
        print(f"Clases declaradas: {len(classes)}")
        print(f"Errores: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
    
    def _print_symbol(self, symbol: Symbol):
        usage_status = "Usado: True" if symbol.is_used else "Usado: False"
        symbol_info = f"  {symbol.name}: {symbol.symbol_type.value} | {symbol.data_type.value} | Línea {symbol.line_number} | {usage_status}"
        addr_txt = f"0x{symbol.address:X}" if isinstance(symbol.address, int) else str(symbol.address)
        extra_mem = f" | offset={symbol.offset} | size={symbol.size_bytes}B"
        if symbol.address is not None:
            extra_mem += f" | addr={addr_txt}"
        symbol_info += extra_mem
        
        if symbol.symbol_type == SymbolType.FUNCTION:
            params = [f"{p.name}:{p.data_type.value}" for p in symbol.parameters]
            symbol_info += f"\n    Parámetros: ({', '.join(params)}) -> {symbol.return_type.value}"
        
        elif symbol.symbol_type == SymbolType.METHOD:
            params = [f"{p.name}:{p.data_type.value}" for p in symbol.parameters]
            constructor_info = " [CONSTRUCTOR]" if symbol.is_constructor else ""
            symbol_info += f"\n    Método: ({', '.join(params)}) -> {symbol.return_type.value}{constructor_info}"
            if symbol.class_type:
                symbol_info += f"\n    Pertenece a clase: {symbol.class_type}"
        
        elif symbol.symbol_type == SymbolType.CLASS:
            methods_count = len(symbol.methods)
            attributes_count = len(symbol.attributes)
            symbol_info += f"\n    Métodos: {methods_count}, Atributos: {attributes_count}"
            if symbol.parent_class:
                symbol_info += f", Hereda de: {symbol.parent_class}"
        
        elif symbol.symbol_type == SymbolType.CONSTANT and symbol.value is not None:
            symbol_info += f"\n    Valor: {symbol.value}"
        
        elif symbol.data_type == DataType.CLASS_TYPE:
            symbol_info += f"\n    Instancia de clase: {symbol.class_type or symbol.value}"
        
        elif symbol.data_type == DataType.ARRAY:
            array_info = f"Array de {symbol.array_element_type.value if symbol.array_element_type else 'unknown'}"
            if symbol.array_size:
                array_info += f"[{symbol.array_size}]"
            symbol_info += f"\n    {array_info}"
        
        print(symbol_info)
    
    def clear_errors(self):
        self.errors.clear()
        self.warnings.clear()
