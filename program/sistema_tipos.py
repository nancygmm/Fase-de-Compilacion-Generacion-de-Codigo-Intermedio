from tabla_simbolos import DataType, SymbolType
from typing import Optional, List

class TypeChecker:
    def __init__(self):
        self.arithmetic_operators = {'+', '-', '*', '/', '%'}
        self.comparison_operators = {'==', '!=', '<', '<=', '>', '>='}
        self.logical_operators = {'&&', '||'}
        self.unary_operators = {'-', '!'}
    
    def check_binary_operation(self, left_type: str, operator: str, right_type: str) -> str:

        if left_type is None or right_type is None:
            return "error"
        
        if left_type == "error" or right_type == "error":
            return "error"
        
        if operator in self.arithmetic_operators:
            return self._check_arithmetic_operation(left_type, operator, right_type)
        
        elif operator in self.comparison_operators:
            return self._check_comparison_operation(left_type, operator, right_type)
        
        elif operator in self.logical_operators:
            return self._check_logical_operation(left_type, operator, right_type)
        
        else:
            return "error"
    
    def _check_arithmetic_operation(self, left_type: str, operator: str, right_type: str) -> str:
        if left_type == "boolean" or right_type == "boolean":
            return "error"

        if left_type == "array" or right_type == "array":
            return "error"

        numeric_types = {"integer"}

        if operator in {"*", "/", "%"}:
            if left_type == "integer" and right_type == "integer":
                return "integer"
            return "error"

        if operator in {"+", "-"}:
            if operator == "+":
                
                if left_type == "string" and right_type == "string":
                    return "string"
                
                
                if left_type == "string" and right_type == "integer":
                    return "string"  
                
                if left_type == "integer" and right_type == "string":
                    return "string"  
                
                
                if left_type in numeric_types and right_type in numeric_types:
                    if left_type == "integer" and right_type == "integer":
                        return "integer"
                return "error"
            else:  
                
                if left_type in numeric_types and right_type in numeric_types:
                    if left_type == "integer" and right_type == "integer":
                        return "integer"
                return "error"

        return "error"

    
    def _check_comparison_operation(self, left_type: str, operator: str, right_type: str) -> str:

        numeric_types = {"integer"}
        if left_type in numeric_types and right_type in numeric_types:
            return "boolean"
        
        if left_type == "string" and right_type == "string":
            return "boolean"
        
        if left_type == "boolean" and right_type == "boolean":
            return "boolean"
        
        if operator in ["==", "!="]:
            if left_type == "null" or right_type == "null":
                return "boolean"
            
            if self.is_compatible(left_type, right_type) or self.is_compatible(right_type, left_type):
                return "boolean"
        
        return "error"
    
    def _check_logical_operation(self, left_type: str, operator: str, right_type: str) -> str:

        if left_type == "boolean" and right_type == "boolean":
            return "boolean"
        
        return "error"
    
    
    def check_unary_operation(self, operator: str, operand_type: str) -> str:

        if operand_type is None or operand_type == "error":
            return "error"
        
        if operator == '-':
            if operand_type in ["integer"]:
                return operand_type
            else:
                return "error"
        
        elif operator == '!':
            if operand_type == "boolean":
                return "boolean"
            else:
                return "error"
        
        else:
            return "error"
    
    def get_literal_type(self, literal_text: str) -> str:

        if literal_text is None:
            return "error"
        
        if literal_text.lower() in ['true', 'false']:
            return DataType.BOOLEAN.value
        
        elif literal_text.lower() == 'null':
            return "null"
        
        elif literal_text.startswith('"') and literal_text.endswith('"'):
            return DataType.STRING.value
        
        elif literal_text.startswith("'") and literal_text.endswith("'"):
            return DataType.STRING.value
        
        else:
            try:
                int(literal_text)
                return DataType.INTEGER.value
            except ValueError:
                return "identifier"
    
    def is_assignment_valid(self, var_type: str, value_type: str) -> bool:
        if var_type is None or value_type is None:
            return False
        if value_type == "error":
            return False
        if var_type == value_type:
            return True
        if var_type == "string":
            return False

        if var_type == "array" or value_type == "array":
            return var_type == "array" and value_type == "array"

        if (value_type, var_type) in {("integer"), ("integer")}:
            return True

        return False

    
    def is_compatible(self, expected_type: str, actual_type: str) -> bool:
        if expected_type is None or actual_type is None:
            return False
        if actual_type == "error":
            return False

        if expected_type == actual_type:
            return True
        
        if expected_type == "method" or actual_type == "method":
            return False  
        
        if self.is_class_name(expected_type) or self.is_class_name(actual_type):
            return self.handle_class_compatibility(expected_type, actual_type)

        if expected_type.endswith("[]") or actual_type.endswith("[]"):
            return expected_type == actual_type

        if expected_type == "string":
            return actual_type == "string"

        if expected_type == "boolean":
            return actual_type == "boolean"

        return False
    
    def is_class_name(self, type_name: str) -> bool:
       
        if not type_name:
            return False
        
        primitive_types = {
            "integer", "string", "boolean", "array", "void", 
            "null", "error", "method"
        }
        
        return type_name not in primitive_types

    def handle_class_compatibility(self, expected_type: str, actual_type: str) -> bool:

        if not (self.is_class_name(expected_type) and self.is_class_name(actual_type)):
            return False
        
        return expected_type == actual_type
    
    def validate_method_call_in_context(self, object_type: str, method_name: str, arguments_ctx, line: int, column: int) -> str:
        
        print(f"Validando llamada a método '{object_type}.{method_name}'")
        
        if not self.is_class_type(object_type):
            self.analyzer.add_error(line, column,
                f"'{object_type}' no es una clase, no puede tener métodos")
            return "error"
        
        class_symbol = self.analyzer.symbol_table.lookup(object_type)
        if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
            self.analyzer.add_error(line, column,
                f"Clase '{object_type}' no encontrada")
            return "error"
        
        if method_name not in class_symbol.methods:
            self.analyzer.add_error(line, column,
                f"La clase '{object_type}' no tiene un método llamado '{method_name}'")
            return "error"
        
        method_symbol = class_symbol.methods[method_name]
        expected_params = method_symbol.parameters
        expected_count = len(expected_params)
        
        actual_args = []
        actual_count = 0
        
        if arguments_ctx and arguments_ctx.expression():
            actual_count = len(arguments_ctx.expression())
            for expr in arguments_ctx.expression():
                arg_type = self.safe_visit(expr)
                actual_args.append(arg_type)
        
        if actual_count != expected_count:
            self.analyzer.add_error(line, column,
                f"Método '{method_name}' espera {expected_count} argumentos pero recibió {actual_count}")
            return "error"
        
        for i in range(actual_count):
            expected_param = expected_params[i]
            actual_arg_type = actual_args[i]
            
            expected_type = expected_param.data_type.value
            if expected_param.data_type == DataType.CLASS_TYPE:
                expected_type = expected_param.class_type or expected_param.value
            
            if not self.analyzer.type_checker.is_compatible(expected_type, actual_arg_type):
                self.analyzer.add_error(line, column,
                    f"Argumento {i+1} del método '{method_name}': esperado '{expected_type}', encontrado '{actual_arg_type}'")
                return "error"
        
        print(f"Llamada a método '{method_name}' validada correctamente")
        
        if method_symbol.return_type == DataType.ARRAY and method_symbol.array_element_type:
            return f"{method_symbol.array_element_type.value}[]"
        elif method_symbol.return_type == DataType.CLASS_TYPE:
            return method_symbol.class_type or "class"
        else:
            return method_symbol.return_type.value

    def validate_class_instantiation(self, class_name: str) -> bool:
        
        return self.is_class_name(class_name)

    def get_class_member_type(self, class_type: str, member_name: str, 
                             symbol_table) -> str:

        if not self.is_class_name(class_type):
            return "error"
        
        class_symbol = symbol_table.lookup(class_type)
        if not class_symbol or class_symbol.symbol_type.value != "class":
            return "error"
        
        if hasattr(class_symbol, 'attributes') and member_name in class_symbol.attributes:
            attr_symbol = class_symbol.attributes[member_name]
            if attr_symbol.data_type.value == "array" and attr_symbol.array_element_type:
                return f"{attr_symbol.array_element_type.value}[]"
            return attr_symbol.data_type.value
        
        if hasattr(class_symbol, 'methods') and member_name in class_symbol.methods:
            return "method"
        
        return "error"

    
    def validate_array_element_type(self, array_type: str, element_type: str) -> bool:
        
        return self.is_assignment_valid(array_type, element_type)
    
    def get_supported_operators(self) -> dict:
        
        return {
            'arithmetic': list(self.arithmetic_operators),
            'comparison': list(self.comparison_operators), 
            'logical': list(self.logical_operators),
            'unary': list(self.unary_operators)
        }
        
    def validate_array_access(self, array_type: str, index_type: str) -> bool:
        if array_type != "array":
            return False
        
        if index_type != "integer":
            return False
        
        return True
    
    def check_array_index_operation(self, base_type: str, index_type: str) -> str:
        if base_type != "array":
            return "error"
        
        if index_type != "integer":
            return "error"
        
        return "integer"
    
    def validate_operator_support(self, operator: str) -> bool:
        
        all_operators = (self.arithmetic_operators | 
                        self.comparison_operators | 
                        self.logical_operators | 
                        self.unary_operators)
        return operator in all_operators


class TypeUtils:
    
    @staticmethod
    def string_to_datatype(type_string: str) -> Optional[DataType]:
        
        try:
            return DataType(type_string)
        except ValueError:
            return None
    
    @staticmethod
    def datatype_to_string(data_type: DataType) -> str:
       
        return data_type.value
    
    @staticmethod
    def is_numeric_type(type_string: str) -> bool:
       
        try:
            dt = DataType(type_string)
            return dt == DataType.INTEGER
        except ValueError:
            return False
    
    @staticmethod
    def is_primitive_type(type_string: str) -> bool:
       
        try:
            dt = DataType(type_string)
            return dt in {DataType.INTEGER, DataType.STRING, DataType.BOOLEAN}
        except ValueError:
            return False
    
    @staticmethod
    def get_all_primitive_types() -> List[str]:
       
        return [DataType.INTEGER.value, DataType.STRING.value, DataType.BOOLEAN.value]

