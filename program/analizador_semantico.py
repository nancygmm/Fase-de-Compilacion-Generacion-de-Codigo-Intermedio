from typing import List, Optional
from dataclasses import dataclass

from sistema_tipos import TypeChecker
from tabla_simbolos import CompiscriptSymbolTable, DataType, ContextType, SymbolType, Symbol
from managers import TempManager, LabelManager

from CompiscriptParser import CompiscriptParser
from CompiscriptVisitor import CompiscriptVisitor
from managers import ActivationManager

@dataclass
class SemanticError:
    line: int
    column: int
    message: str
    error_type: str
    
    def __str__(self) -> str:
        return f"Error Semántico [Línea {self.line}, Columna {self.column}]: {self.message}"

@dataclass
class TACInstruction:
    op: str
    arg1: Optional[str]
    arg2: Optional[str]
    result: str
    line_number: Optional[int] = None
    
    def __str__(self) -> str:
        if self.op == "=":
            return f"{self.result} = {self.arg1}"
        elif self.op == "goto":
            return f"goto {self.result}"
        elif self.op == "if_false":
            return f"if_false {self.arg1} goto {self.result}"
        elif self.op == "if_true":
            return f"if_true {self.arg1} goto {self.result}"
        elif self.op == "label":
            return f"{self.result}:"
        elif self.op == "PushParam":
            return f"PushParam {self.arg1}"
        elif self.op == "LCall":
            return f"{self.result} = LCall {self.arg1}"
        elif self.op == "PopParams":
            return f"PopParams {self.arg1}"
        elif self.op == "BeginFunc":
            return f"BeginFunc {self.result} {self.arg1}"
        elif self.op == "EndFunc":
            return f"EndFunc {self.arg1}"
        elif self.op == "LoadParam":
            return f"{self.result} = LoadParam {self.arg1}"
        elif self.op == "SetReturn":
            return f"SetReturn {self.arg1}"
        elif self.op == "ActivationRecord":
            return f"ActivationRecord {self.arg1}"
        elif self.op == "return":
            if self.arg1:
                return f"return {self.arg1}"
            else:
                return f"return"
        elif self.op == "[]":
            return f"{self.result} = {self.arg1}[{self.arg2}]"
        elif self.op == "[]=":
            return f"{self.result}[{self.arg1}] = {self.arg2}"
        elif self.op == "new_array":
            return f"{self.result} = new_array[{self.arg1}]"
        elif self.op == "length":
            return f"{self.result} = length {self.arg1}"
        elif self.op in ["+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=", "&&", "||"]:
            if self.arg2:
                return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
            else:
                return f"{self.result} = {self.op} {self.arg1}"
        else:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2 or ''}"

class SemanticAnalyzer:
    def __init__(self):
        self.type_checker = TypeChecker()
        self.symbol_table = CompiscriptSymbolTable()
        
        self.errors: List[SemanticError] = []
        self.warnings: List[str] = []
        
        self.current_function = None
        self.current_class = None
        self.loop_depth = 0
        self.return_found = False

        self.function_ctx_stack: List[tuple] = []

        self.loop_depth = 0
        self.switch_depth = 0 
        
        self.unreachable_code = False  
        self.unreachable_stack: List[bool] = []  
        
        self._initialize_builtin_functions()
        
    def _initialize_builtin_functions(self):
        self.symbol_table.declare_function(
        "print", DataType.VOID, [("message", DataType.STRING)], 0, 0, None)
        
    def add_error(self, line: int, column: int, message: str, error_type: str = "SEMANTIC"):
        error = SemanticError(line, column, message, error_type)
        self.errors.append(error)
        self.symbol_table.add_error(message, line, column)
        
    def add_warning(self, message: str):
        self.warnings.append(message)
        self.symbol_table.add_warning(message)
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0 or self.symbol_table.has_errors()
    
    def get_total_errors(self) -> int:
        return len(self.symbol_table.get_errors())

class CompiscriptSemanticVisitor(CompiscriptVisitor):
    def __init__(self):
        self.analyzer = SemanticAnalyzer()
        
        
        self.temp_manager = TempManager()
        self.label_manager = LabelManager()
        self.tac_code: List[TACInstruction] = []
        self.current_scope_name = "global"
        self.activation_manager = ActivationManager()
        
    def emit_tac(self, op: str, arg1: Optional[str], arg2: Optional[str], result: str, line: Optional[int] = None) -> TACInstruction:
        instruction = TACInstruction(op, arg1, arg2, result, line)
        self.tac_code.append(instruction)
        return instruction
    
    def emit_label(self, label: str) -> TACInstruction:
        return self.emit_tac("label", None, None, label)
    
    def emit_goto(self, label: str) -> TACInstruction:
        return self.emit_tac("goto", None, None, label)
    
    def emit_conditional_jump(self, condition: str, label: str, is_true: bool = False) -> TACInstruction:
        op = "if_true" if is_true else "if_false"
        return self.emit_tac(op, condition, None, label)
    
    def get_place_from_ctx(self, ctx) -> Optional[str]:
        return getattr(ctx, 'place', None)
    
    def set_place_to_ctx(self, ctx, place: str) -> None:
        setattr(ctx, 'place', place)
    
    def print_tac(self):
        print("\n" + "="*60)
        print("         CÓDIGO TAC GENERADO")
        print("="*60)
        
        if not self.tac_code:
            print("No se generó código TAC.")
            return
        
        
        current_function = "global"
        for i, instruction in enumerate(self.tac_code):
            
            if instruction.op == "BeginFunc":
                if current_function != "global":
                    print()  
                current_function = instruction.result
                print(f"// Función: {current_function}")
            
            
            print(f"{i:3}: {instruction}")
            
            
            if instruction.op == "EndFunc":
                print(f"// Fin función: {current_function}")
                current_function = "global"
        
        print("="*60)
        print(f"Total de instrucciones: {len(self.tac_code)}")
        print("="*60)
    
    def check_dead_code(self, ctx, statement_type="declaración"):
        if self.analyzer.unreachable_code:
            self.analyzer.add_error(
                ctx.start.line, ctx.start.column,
                f"Código muerto detectado: {statement_type} después de una declaración de control de flujo",
                "DEAD_CODE"
            )
            return True
        return False   
    
    def mark_unreachable(self):
        self.analyzer.unreachable_code = True
    
    def push_reachability_state(self):
        self.analyzer.unreachable_stack.append(self.analyzer.unreachable_code)
    
    def pop_reachability_state(self):
        if self.analyzer.unreachable_stack:
            self.analyzer.unreachable_code = self.analyzer.unreachable_stack.pop()
        else:
            self.analyzer.unreachable_code = False
    
    def reset_reachability_in_scope(self):
        self.analyzer.unreachable_code = False
    
    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        self.analyzer.symbol_table.enter_scope("global", ContextType.GLOBAL)
        self.current_scope_name = "global"
        
        
        self.emit_label("PROGRAM_START")
        
        if ctx.statement():
            for stmt in ctx.statement():
                self.safe_visit(stmt)
        
        
        self.emit_label("PROGRAM_END")
        
        self.analyzer.symbol_table.exit_scope()
        
        total_errors = self.analyzer.get_total_errors()
        total_warnings = len(self.analyzer.symbol_table.get_warnings())
        
        errors = self.analyzer.symbol_table.get_errors()
        if errors:
            print("\nErrores semanticos")
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")
        
        print(f"Errores: {total_errors}, Warnings: {total_warnings}")
        return None
    
    def visitStatement(self, ctx: CompiscriptParser.StatementContext):
        return self.visitChildren(ctx)
    
    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        self.analyzer.symbol_table.enter_scope("block", ContextType.GLOBAL)
        self.push_reachability_state()
        
        if ctx.statement():
            for stmt in ctx.statement():
                self.safe_visit(stmt)
        
        
        self.temp_manager.cleanup_scope("block")
        
        self.pop_reachability_state()
        self.analyzer.symbol_table.exit_scope()
        return None
    
    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        func_name = ctx.Identifier().getText()
        line = ctx.start.line
        column = ctx.start.column

        
        array_element_type = None
        if ctx.type_():
            return_type_str = self.safe_visit(ctx.type_())
            
            if return_type_str and return_type_str.endswith("[]"):
                base_type = return_type_str[:-2]  
                try:
                    array_element_type = DataType(base_type)
                    return_type = DataType.ARRAY
                except ValueError:
                    self.analyzer.add_error(line, column, f"Tipo de retorno de array inválido: '{base_type}'")
                    return_type = DataType.VOID
                    array_element_type = None
            else:
                try:
                    return_type = DataType(return_type_str)
                except ValueError:
                    self.analyzer.add_error(line, column, f"Tipo de retorno inválido: '{return_type_str}'")
                    return_type = DataType.VOID
        else:
            return_type = DataType.VOID

        parameters = []
        param_array_info = {}  
        
        if ctx.parameters():
            for param in ctx.parameters().parameter():
                param_name = param.Identifier().getText()
                param_array_element_type = None
                
                if param.type_():
                    param_type_str = self.safe_visit(param.type_())
                    
                    if param_type_str and param_type_str.endswith("[]"):
                        base_type = param_type_str[:-2]
                        try:
                            param_array_element_type = DataType(base_type)
                            param_type = DataType.ARRAY
                            param_array_info[param_name] = param_array_element_type
                        except ValueError:
                            self.analyzer.add_error(param.start.line, param.start.column,
                                                    f"Tipo de elemento de array inválido en parámetro: '{base_type}'")
                            param_type = DataType.INTEGER
                    else:
                        try:
                            param_type = DataType(param_type_str)
                        except ValueError:
                            self.analyzer.add_error(param.start.line, param.start.column,
                                                    f"Tipo de parámetro inválido: '{param_type_str}'")
                            param_type = DataType.INTEGER
                else:
                    param_type = DataType.INTEGER
                
                parameters.append((param_name, param_type))

        success = self.analyzer.symbol_table.declare_function(
            func_name, return_type, parameters, line, column, array_element_type)
                
        if not success:
            return None

        
        func_start_label, func_end_label = self.label_manager.new_function_labels(func_name)

        
        self.emit_label(func_start_label)
        self.emit_tac("BeginFunc", str(len(parameters)), None, func_name, line)

        
        self.emit_tac("ActivationRecord", func_name, None, "", line)

        prev_context = (self.analyzer.current_function, self.analyzer.return_found)
        self.analyzer.function_ctx_stack.append(prev_context)

        self.analyzer.symbol_table.enter_scope(func_name, ContextType.FUNCTION)
        self.analyzer.current_function = func_name
        self.analyzer.return_found = False
        self.current_scope_name = func_name

        
        self.label_manager.push_function_context(func_end_label)

        self.push_reachability_state()
        self.reset_reachability_in_scope()

        
        param_offset = 0
        for param_name, param_type in parameters:
            param_array_element_type = param_array_info.get(param_name, None)
            
            self.analyzer.symbol_table.declare_variable(
                param_name, param_type, line, column, False, None, param_array_element_type
            )
            
            
            self.emit_tac("LoadParam", str(param_offset), None, param_name, line)
            param_offset += 1

        
        if ctx.block() and ctx.block().statement():
            for stmt in ctx.block().statement():
                self.safe_visit(stmt)

        
        if return_type != DataType.VOID and not self.analyzer.return_found:
            self.analyzer.add_error(
                line, column,
                f"Función '{func_name}' de tipo '{return_type.value}' debe contener al menos una declaración 'return'",
                "MISSING_RETURN"
            )

        
        self.emit_label(func_end_label)

        
        if return_type == DataType.VOID and not self.analyzer.return_found:
            self.emit_tac("EndFunc", func_name, None, "", line)
        else:
            self.emit_tac("EndFunc", func_name, None, "", line)

        
        self.label_manager.pop_context()
        self.temp_manager.cleanup_scope(func_name)
        
        self.analyzer.symbol_table.exit_scope()
        self.pop_reachability_state()

        if self.analyzer.function_ctx_stack:
            prev_func, prev_return_found = self.analyzer.function_ctx_stack.pop()
            self.analyzer.current_function = prev_func
            self.analyzer.return_found = prev_return_found
        else:
            self.analyzer.current_function = None
            self.analyzer.return_found = False

        self.current_scope_name = "global"
        return None

    def visitParameters(self, ctx: CompiscriptParser.ParametersContext):
        return self.visitChildren(ctx)
    
    def visitParameter(self, ctx: CompiscriptParser.ParameterContext):
        return self.visitChildren(ctx)
    
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        if self.check_dead_code(ctx, "declaración de variable"):
            return None
            
        var_name = ctx.Identifier().getText()
        line = ctx.start.line
        column = ctx.start.column
        
        
        array_element_type = None
        declared_type = None
        if ctx.typeAnnotation():
            declared_type = self.safe_visit(ctx.typeAnnotation())
            if declared_type and declared_type.endswith("[]"):
                base_type = declared_type[:-2]  
                try:
                    array_element_type = DataType(base_type)
                    declared_type = "array"  
                except ValueError:
                    self.analyzer.add_error(line, column, f"Tipo de elemento de array inválido: '{base_type}'")
                    return None
        
        init_type = None
        init_place = None
        if ctx.initializer():
            init_type = self.safe_visit(ctx.initializer())
            init_place = self.get_place_from_ctx(ctx.initializer().expression())
        
        if not declared_type and init_type:
            declared_type = init_type
        elif not declared_type and not init_type:
            self.analyzer.add_error(
                line, column,
                f"Variable '{var_name}' debe tener tipo explícito o inicializador",
                "TYPE_INFERENCE"
            )
            return None
        
        if declared_type and init_type:
            if not self.analyzer.type_checker.is_compatible(declared_type, init_type):
                self.analyzer.add_error(
                    line, column,
                    f"Tipo incompatible: no se puede asignar '{init_type}' a '{declared_type}'",
                    "TYPE_MISMATCH"
                )
                return None
        
        if declared_type and self.is_class_type(declared_type):
            data_type_enum = DataType.CLASS_TYPE
            success = self.analyzer.symbol_table.declare_class_instance(
                var_name, declared_type, line, column
            )
            if not success:
                return None
        else:
            try:
                data_type_enum = DataType(declared_type)
            except ValueError:
                self.analyzer.add_error(
                    line, column,
                    f"Tipo inválido: '{declared_type}'",
                    "INVALID_TYPE"
                )
                return None
            
            success = self.analyzer.symbol_table.declare_variable(
                var_name, data_type_enum, line, column, False, None, array_element_type)  
            
            if not success:
                return None

        
        if ctx.initializer() and init_place:
            self.emit_tac("=", init_place, None, var_name, line)
        elif ctx.initializer():
            
            init_text = ctx.initializer().expression().getText().strip()
            self.emit_tac("=", init_text, None, var_name, line)
        
        
        if ctx.initializer():
            init_text = ctx.initializer().expression().getText().strip()
            while init_text.startswith('(') and init_text.endswith(')'):
                init_text = init_text[1:-1].strip()
            if init_text == "0":
                sym = self.analyzer.symbol_table.lookup_current_scope(var_name)
                if sym:
                    sym.value = 0
                    sym.is_initialized = True
        
        return declared_type

    def is_class_type(self, type_name: str) -> bool:
        if not type_name or type_name in ["error", "null"]:
            return False
        
        symbol = self.analyzer.symbol_table.lookup(type_name)
        return symbol is not None and symbol.symbol_type == SymbolType.CLASS
    
    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        if self.check_dead_code(ctx, "declaración de constante"):
            return None
        const_name = ctx.Identifier().getText()
        line = ctx.start.line
        column = ctx.start.column
        
        if not ctx.expression():
            self.analyzer.add_error(
                line, column,
                f"Constante '{const_name}' debe ser inicializada en su declaración",
                "CONST_INITIALIZATION"
            )
            return None
        
        
        declared_type = None
        array_element_type = None
        if ctx.typeAnnotation():
            declared_type = self.safe_visit(ctx.typeAnnotation())
            
            if declared_type and declared_type.endswith("[]"):
                base_type = declared_type[:-2]  
                try:
                    array_element_type = DataType(base_type)
                    declared_type = "array"  
                except ValueError:
                    self.analyzer.add_error(line, column, f"Tipo de elemento de array inválido: '{base_type}'")
                    return None
        
        init_type = self.safe_visit(ctx.expression())
        init_place = self.get_place_from_ctx(ctx.expression())
        
        if not declared_type:
            declared_type = init_type
        
        if declared_type and init_type:
            if not self.analyzer.type_checker.is_compatible(declared_type, init_type):
                self.analyzer.add_error(
                    line, column,
                    f"Tipo incompatible: no se puede asignar '{init_type}' a constante '{declared_type}'",
                    "TYPE_MISMATCH"
                )
                return None
        
        try:
            data_type_enum = DataType(declared_type)
        except ValueError:
            self.analyzer.add_error(
                line, column,
                f"Tipo inválido: '{declared_type}'",
                "INVALID_TYPE"
            )
            return None
        
        success = self.analyzer.symbol_table.declare_variable(
            const_name, data_type_enum, line, column, True, "valor_constante"
        )
        
        if not success:
            return None
        
        
        if init_place:
            self.emit_tac("=", init_place, None, const_name, line)
        else:
            init_text = ctx.expression().getText().strip()
            self.emit_tac("=", init_text, None, const_name, line)
        
        return declared_type
    
    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        line = ctx.start.line
        
        if ctx.expression():
            condition_type = self.safe_visit(ctx.expression())
            if condition_type and condition_type != "boolean":
                self.analyzer.add_error(line, 0, 
                    f"Condición del if debe ser boolean, encontrado: '{condition_type}'")
            
            
            condition_place = self.get_place_from_ctx(ctx.expression())
            if not condition_place:
                condition_place = ctx.expression().getText()
            
            else_label, end_label = self.label_manager.new_if_labels()
            
            
            self.emit_conditional_jump(condition_place, else_label, is_true=False)
            
            blocks = ctx.block()
            if blocks:
                
                if len(blocks) > 0:
                    current_unreachable = self.analyzer.unreachable_code
                    self.push_reachability_state()
                    self.safe_visit(blocks[0])
                    then_unreachable = self.analyzer.unreachable_code
                    self.pop_reachability_state()
                    
                    
                    if len(blocks) > 1:
                        self.emit_goto(end_label)
                
                
                self.emit_label(else_label)
                
                
                if len(blocks) > 1:
                    self.analyzer.unreachable_code = current_unreachable
                    self.push_reachability_state()
                    self.safe_visit(blocks[1])
                    else_unreachable = self.analyzer.unreachable_code
                    self.pop_reachability_state()
                    
                    
                    self.emit_label(end_label)
                    
                    
                    if then_unreachable and else_unreachable:
                        self.analyzer.unreachable_code = True
                    else:
                        self.analyzer.unreachable_code = current_unreachable
                else:
                    self.analyzer.unreachable_code = current_unreachable
        
        return None
    
    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        line = ctx.start.line        
        
        self.analyzer.symbol_table.enter_scope("while", ContextType.LOOP)
        self.analyzer.loop_depth += 1
        
        
        start_label, end_label, continue_label = self.label_manager.new_loop_labels()
        self.label_manager.push_loop_context(end_label, continue_label)
        
        self.push_reachability_state()
        
        try:
            
            self.emit_label(start_label)
            
            if ctx.expression():
                condition_type = self.safe_visit(ctx.expression())
                if condition_type and condition_type != "boolean":
                    self.analyzer.add_error(line, 0, 
                        f"Condición del while debe ser boolean, encontrado: '{condition_type}'")
                
                
                condition_place = self.get_place_from_ctx(ctx.expression())
                if not condition_place:
                    condition_place = ctx.expression().getText()
                
                self.emit_conditional_jump(condition_place, end_label, is_true=False)
            
            if ctx.block():
                self.reset_reachability_in_scope()
                self.safe_visit(ctx.block())
            
            
            self.emit_label(continue_label)
            self.emit_goto(start_label)
            
            
            self.emit_label(end_label)
        
        finally:
            self.label_manager.pop_context()
            self.temp_manager.cleanup_scope("while")
            self.pop_reachability_state()
            self.analyzer.loop_depth -= 1
            self.analyzer.symbol_table.exit_scope()
        
        return None
    
    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        line = ctx.start.line
        
        self.analyzer.symbol_table.enter_scope("do-while", ContextType.LOOP)
        self.analyzer.loop_depth += 1
        
        
        start_label, end_label, continue_label = self.label_manager.new_loop_labels()
        self.label_manager.push_loop_context(end_label, continue_label)
        
        self.push_reachability_state()
        
        try:
            
            self.emit_label(start_label)
            
            if ctx.block():
                self.reset_reachability_in_scope()
                self.safe_visit(ctx.block())
            
            
            self.emit_label(continue_label)
            
            if ctx.expression():
                condition_type = self.safe_visit(ctx.expression())
                if condition_type and condition_type != "boolean":
                    self.analyzer.add_error(line, 0, 
                        f"Condición del do-while debe ser boolean, encontrado: '{condition_type}'")
                
                
                condition_place = self.get_place_from_ctx(ctx.expression())
                if not condition_place:
                    condition_place = ctx.expression().getText()
                
                self.emit_conditional_jump(condition_place, start_label, is_true=True)
            
            
            self.emit_label(end_label)
        
        finally:
            self.label_manager.pop_context()
            self.temp_manager.cleanup_scope("do-while")
            self.pop_reachability_state()
            self.analyzer.loop_depth -= 1
            self.analyzer.symbol_table.exit_scope()
        
        return None
    
    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        line = ctx.start.line
        
        self.analyzer.symbol_table.enter_scope("for", ContextType.LOOP)
        self.analyzer.loop_depth += 1
        
        
        start_label, end_label, continue_label = self.label_manager.new_loop_labels()
        self.label_manager.push_loop_context(end_label, continue_label)
        
        self.push_reachability_state()
        
        try:
            
            if ctx.variableDeclaration():
                self.safe_visit(ctx.variableDeclaration())
            elif ctx.assignment():
                self.safe_visit(ctx.assignment())
            
            
            self.emit_label(start_label)
            
            
            expressions = ctx.expression()
            if expressions and len(expressions) >= 1:
                cond_type = self.safe_visit(expressions[0])
                if cond_type and cond_type != "boolean":
                    self.analyzer.add_error(line, 0, 
                        f"Condición del for debe ser boolean, encontrado: '{cond_type}'")
                
                condition_place = self.get_place_from_ctx(expressions[0])
                if not condition_place:
                    condition_place = expressions[0].getText()
                
                self.emit_conditional_jump(condition_place, end_label, is_true=False)
            
            
            if ctx.block():
                self.reset_reachability_in_scope()
                self.safe_visit(ctx.block())
            
            
            self.emit_label(continue_label)
            if expressions and len(expressions) >= 2:
                self.safe_visit(expressions[1])
            
            
            self.emit_goto(start_label)
            
            
            self.emit_label(end_label)
        
        finally:
            self.label_manager.pop_context()
            self.temp_manager.cleanup_scope("for")
            self.pop_reachability_state()
            self.analyzer.loop_depth -= 1
            self.analyzer.symbol_table.exit_scope()
        
        return None
    
    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        line = ctx.start.line
        column = ctx.start.column
        
        self.analyzer.symbol_table.enter_scope("foreach", ContextType.LOOP)
        self.analyzer.loop_depth += 1
        
        
        start_label, end_label, continue_label = self.label_manager.new_loop_labels()
        self.label_manager.push_loop_context(end_label, continue_label)
        
        self.push_reachability_state()
        
        try:
            iter_var = ctx.Identifier().getText()
            
            iterable_type_str = self.safe_visit(ctx.expression())
            
            if iterable_type_str == "array":
                element_type = DataType.INTEGER
            elif iterable_type_str and iterable_type_str.endswith("[]"):
                base_type = iterable_type_str[:-2]
                try:
                    element_type = DataType(base_type)
                except ValueError:
                    element_type = DataType.INTEGER
            else:
                element_type = DataType.INTEGER
                if iterable_type_str != "error":
                    self.analyzer.add_error(line, column, 
                                        f"No se puede iterar sobre tipo '{iterable_type_str}'")
            
            self.analyzer.symbol_table.declare_variable(
                iter_var, element_type, line, column, False, "auto_generated"
            )
            
            
            array_place = self.get_place_from_ctx(ctx.expression())
            if not array_place:
                array_place = ctx.expression().getText()
            
            index_temp = self.temp_manager.new_temp_from_type_string("integer", "foreach")
            length_temp = self.temp_manager.new_temp_from_type_string("integer", "foreach")
            
            
            self.emit_tac("=", "0", None, index_temp)
            
            
            self.emit_tac("length", array_place, None, length_temp)
            
            
            self.emit_label(start_label)
            
            
            condition_temp = self.temp_manager.new_temp_from_type_string("boolean", "foreach")
            self.emit_tac("<", index_temp, length_temp, condition_temp)
            self.emit_conditional_jump(condition_temp, end_label, is_true=False)
            
            
            self.emit_tac("[]", array_place, index_temp, iter_var)
            
            if ctx.block():
                self.reset_reachability_in_scope()
                self.safe_visit(ctx.block())
            
            
            self.emit_label(continue_label)
            increment_temp = self.temp_manager.new_temp_from_type_string("integer", "foreach")
            self.emit_tac("+", index_temp, "1", increment_temp)
            self.emit_tac("=", increment_temp, None, index_temp)
            
            
            self.emit_goto(start_label)
            
            
            self.emit_label(end_label)
        
        finally:
            self.label_manager.pop_context()
            self.temp_manager.cleanup_scope("foreach")
            self.pop_reachability_state()
            self.analyzer.loop_depth -= 1
            self.analyzer.symbol_table.exit_scope()
        
        return None
    
    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        line = ctx.start.line
        column = ctx.start.column
        
        blocks = ctx.block()
        
        
        try_label = self.label_manager.new_label("TRY_")
        catch_label = self.label_manager.new_label("CATCH_")
        end_label = self.label_manager.new_label("TRY_END_")
        
        self.emit_label(try_label)
        
        if blocks and len(blocks) > 0:
            current_unreachable = self.analyzer.unreachable_code
            self.push_reachability_state()
            self.safe_visit(blocks[0])
            try_unreachable = self.analyzer.unreachable_code
            self.pop_reachability_state()
        
        self.emit_goto(end_label)
        self.emit_label(catch_label)
        
        self.analyzer.symbol_table.enter_scope("catch", ContextType.GLOBAL)
        
        try:
            error_var = ctx.Identifier().getText()
            self.analyzer.symbol_table.declare_variable(
                error_var, DataType.STRING, line, column, False, "exception"
            )
            
            if blocks and len(blocks) > 1:
                self.analyzer.unreachable_code = current_unreachable
                self.push_reachability_state()
                
                if blocks[1].statement():
                    for stmt in blocks[1].statement():
                        self.safe_visit(stmt)
                
                catch_unreachable = self.analyzer.unreachable_code
                self.pop_reachability_state()
                
                self.analyzer.unreachable_code = current_unreachable
        
        finally:
            self.analyzer.symbol_table.exit_scope()
        
        self.emit_label(end_label)
        return None
    
    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        line = ctx.start.line
        
        if self.check_dead_code(ctx, "switch"):
            return None
        
        self.analyzer.switch_depth += 1
        
        try:
            switch_type = None
            switch_place = None
            if ctx.expression():
                switch_type = self.safe_visit(ctx.expression())
                switch_place = self.get_place_from_ctx(ctx.expression())
                if not switch_place:
                    switch_place = ctx.expression().getText()
            
            
            num_cases = len(ctx.switchCase()) if ctx.switchCase() else 0
            case_labels, default_label, end_label = self.label_manager.new_switch_labels(num_cases)
            
            self.label_manager.push_switch_context(end_label)
            
            
            if ctx.switchCase():
                for i, case in enumerate(ctx.switchCase()):
                    if case.expression():
                        case_type = self.safe_visit(case.expression())
                        case_place = self.get_place_from_ctx(case.expression())
                        if not case_place:
                            case_place = case.expression().getText()
                        
                        
                        compare_temp = self.temp_manager.new_temp_from_type_string("boolean", "switch")
                        self.emit_tac("==", switch_place, case_place, compare_temp)
                        self.emit_conditional_jump(compare_temp, case_labels[i], is_true=True)
            
            
            self.emit_goto(default_label)
            
            current_unreachable = self.analyzer.unreachable_code
            has_default = ctx.defaultCase() is not None
            all_cases_unreachable = True
            
            
            if ctx.switchCase():
                for i, case in enumerate(ctx.switchCase()):
                    self.emit_label(case_labels[i])
                    self.analyzer.unreachable_code = current_unreachable
                    self.push_reachability_state()
                    self.safe_visit(case)
                    case_unreachable = self.analyzer.unreachable_code
                    self.pop_reachability_state()
                    
                    if not case_unreachable:
                        all_cases_unreachable = False
            
            
            self.emit_label(default_label)
            if ctx.defaultCase():
                self.analyzer.unreachable_code = current_unreachable
                self.push_reachability_state()
                self.safe_visit(ctx.defaultCase())
                default_unreachable = self.analyzer.unreachable_code
                self.pop_reachability_state()
                
                if not default_unreachable:
                    all_cases_unreachable = False
            
            self.emit_label(end_label)
            
            if all_cases_unreachable and has_default:
                self.analyzer.unreachable_code = True
            else:
                self.analyzer.unreachable_code = current_unreachable
        
        finally:
            self.label_manager.pop_context()
            self.analyzer.switch_depth -= 1
        
        return None
    
    def visitSwitchCase(self, ctx: CompiscriptParser.SwitchCaseContext):
        self.analyzer.symbol_table.enter_scope("case", ContextType.GLOBAL)
        
        try:
            if ctx.expression():
                self.safe_visit(ctx.expression())
            
            if ctx.statement():
                for stmt in ctx.statement():
                    self.safe_visit(stmt)
        
        finally:
            self.analyzer.symbol_table.exit_scope()
        
        return None
    
    def visitDefaultCase(self, ctx: CompiscriptParser.DefaultCaseContext):
        self.analyzer.symbol_table.enter_scope("default", ContextType.GLOBAL)
        
        try:
            if ctx.statement():
                for stmt in ctx.statement():
                    self.safe_visit(stmt)
        
        finally:
            self.analyzer.symbol_table.exit_scope()
        
        return None
    
    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        line = ctx.start.line
        column = ctx.start.column
        
        self.check_dead_code(ctx, "break")
        
        if self.analyzer.loop_depth == 0 and self.analyzer.switch_depth == 0:
            self.analyzer.add_error(line, column, 
                "'break' solo puede usarse dentro de bucles o switch statements")
        
        
        break_label = self.label_manager.get_current_break_label()
        if break_label:
            self.emit_goto(break_label)
        
        self.mark_unreachable()
        return None
    
    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        line = ctx.start.line
        column = ctx.start.column
        
        self.check_dead_code(ctx, "continue")
        
        if self.analyzer.loop_depth == 0:
            self.analyzer.add_error(line, column, 
                "'continue' solo puede usarse dentro de bucles")
        
        
        continue_label = self.label_manager.get_current_continue_label()
        if continue_label:
            self.emit_goto(continue_label)
        
        self.mark_unreachable()
        return None
    
    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        line = ctx.start.line
        column = ctx.start.column
        
        self.check_dead_code(ctx, "return")
        
        if not self.analyzer.current_function:
            self.analyzer.add_error(line, column, "'return' solo puede usarse dentro de funciones")
            return None

        function_symbol = self.analyzer.symbol_table.lookup(self.analyzer.current_function)
        if not function_symbol:
            self.analyzer.add_error(line, column, 
                f"No se puede encontrar información de la función '{self.analyzer.current_function}'")
            return None

        expected_return_type = function_symbol.return_type
        expected_element_type = function_symbol.array_element_type

        if ctx.expression():
            actual_return_type_str = self.safe_visit(ctx.expression())
            
            if actual_return_type_str == "error":
                self.mark_unreachable()
                return None
            
            
            if expected_return_type == DataType.ARRAY and expected_element_type:
                expected_full_type = f"{expected_element_type.value}[]"
                
                if actual_return_type_str != expected_full_type:
                    self.analyzer.add_error(line, column, 
                        f"Tipo de retorno incompatible en función '{self.analyzer.current_function}': "
                        f"esperado '{expected_full_type}', encontrado '{actual_return_type_str}'",
                        "TYPE_MISMATCH")
                    self.analyzer.return_found = True
                    self.mark_unreachable()
                    return None

            elif not self.analyzer.type_checker.is_compatible(expected_return_type.value, actual_return_type_str):
                if expected_return_type == DataType.ARRAY and expected_element_type:
                    expected_display = f"{expected_element_type.value}[]"
                else:
                    expected_display = expected_return_type.value
                    
                self.analyzer.add_error(line, column, 
                    f"Tipo de retorno incompatible en función '{self.analyzer.current_function}': "
                    f"esperado '{expected_display}', encontrado '{actual_return_type_str}'",
                    "TYPE_MISMATCH")
                self.analyzer.return_found = True
                self.mark_unreachable()
                return None
            
            
            if ctx.expression():
                return_place = self.get_place_from_ctx(ctx.expression())
                if return_place:
                    self.emit_tac("SetReturn", return_place, None, "", line)
                else:
                    return_value = ctx.expression().getText()
                    self.emit_tac("SetReturn", return_value, None, "", line)
        else:
            
            self.emit_tac("SetReturn", "void", None, "", line)
        
        func_end_label = self.label_manager.get_current_return_label()
        if func_end_label:
            self.emit_goto(func_end_label)

        self.analyzer.return_found = True
        self.mark_unreachable()
        return None
    
    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        try:
            class_name = ctx.Identifier(0).getText()  
            parent_class = None
            
            if len(ctx.Identifier()) > 1:
                parent_class = ctx.Identifier(1).getText()
            
            line = ctx.start.line
            column = ctx.start.column
            
            if parent_class:
                parent_symbol = self.analyzer.symbol_table.lookup(parent_class)
                if not parent_symbol or parent_symbol.symbol_type != SymbolType.CLASS:
                    self.analyzer.add_error(line, column, 
                        f"Clase padre '{parent_class}' no existe o no es una clase")
                    return None
            
            success = self.analyzer.symbol_table.declare_class(
                class_name, parent_class, line, column
            )
            
            if not success:
                return None
            
            
            class_start_label = self.label_manager.new_label(f"CLASS_{class_name}_START_")
            class_end_label = self.label_manager.new_label(f"CLASS_{class_name}_END_")
            
            self.emit_label(class_start_label)
            
            self.analyzer.symbol_table.enter_scope(class_name, ContextType.CLASS)
            self.analyzer.current_class = class_name
            
            self.push_reachability_state()
            self.reset_reachability_in_scope()
            
            self.analyzer.symbol_table.declare_variable(
                "this", DataType.CLASS_TYPE, line, column, True, class_name
            )
            
            class_symbol = self.analyzer.symbol_table.lookup(class_name)
            
            if ctx.classMember():
                for member in ctx.classMember():
                    if member.functionDeclaration():
                        self.safe_visit(member.functionDeclaration())
                        
                        method_ctx = member.functionDeclaration()
                        method_name = method_ctx.Identifier().getText()
                        
                        method_symbol = self.analyzer.symbol_table.lookup_current_scope(method_name)
                        if method_symbol:
                            class_symbol.methods[method_name] = method_symbol
                    
                    elif member.variableDeclaration() or member.constantDeclaration():
                        self.safe_visit(member)
                        
                        if member.variableDeclaration():
                            attr_name = member.variableDeclaration().Identifier().getText()
                        else:
                            attr_name = member.constantDeclaration().Identifier().getText()
                        
                        attr_symbol = self.analyzer.symbol_table.lookup_current_scope(attr_name)
                        if attr_symbol:
                            class_symbol.attributes[attr_name] = attr_symbol
            
            self.emit_label(class_end_label)
            self.pop_reachability_state()
            
            self.analyzer.symbol_table.exit_scope()
            self.analyzer.current_class = None
            
        except Exception as e:
            self.analyzer.add_error(ctx.start.line, ctx.start.column, 
                f"Error en declaración de clase: {str(e)}")
        
        return None
    
    def visitClassMember(self, ctx: CompiscriptParser.ClassMemberContext):
        return self.visitChildren(ctx)
    
    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        line = ctx.start.line
        column = ctx.start.column
        
        if self.check_dead_code(ctx, "asignación"):
            return None
        
        try:
            expressions = ctx.expression()
            identifier_node = ctx.Identifier()
            
            if identifier_node is not None and len(expressions) == 1:
                var_name = identifier_node.getText()
                
                symbol = self.analyzer.symbol_table.lookup(var_name)
                if not symbol:
                    self.analyzer.add_error(line, column, 
                        f"Variable '{var_name}' no está declarada")
                    return None
                
                if symbol.symbol_type == SymbolType.CONSTANT:
                    self.analyzer.add_error(line, column, 
                        f"No se puede reasignar la constante '{var_name}'")
                    return None
                
                expected_type = symbol.data_type.value
                if symbol.data_type == DataType.CLASS_TYPE:
                    expected_type = symbol.class_type or symbol.value
                elif symbol.data_type == DataType.ARRAY and symbol.array_element_type:
                    expected_type = f"{symbol.array_element_type.value}[]"
                
                expr_type = self.safe_visit(expressions[0])
                if expr_type and not self.analyzer.type_checker.is_compatible(expected_type, expr_type):
                    self.analyzer.add_error(line, column, 
                        f"Tipo incompatible: no se puede asignar '{expr_type}' a '{expected_type}'")
                
                
                expr_place = self.get_place_from_ctx(expressions[0])
                if expr_place:
                    self.emit_tac("=", expr_place, None, var_name, line)
                else:
                    expr_value = expressions[0].getText()
                    self.emit_tac("=", expr_value, None, var_name, line)
            
            elif identifier_node is not None and len(expressions) == 2:
                property_name = identifier_node.getText()
                obj_type = self.safe_visit(expressions[0])
                value_type = self.safe_visit(expressions[1])
                                
                if self.is_class_type(obj_type):
                    result_tuple = self.handle_class_property_access(
                        obj_type, property_name, line, column, is_this=False)
                    
                    if result_tuple[0] != "error":
                        attr_symbol = result_tuple[1]
                        
                        if attr_symbol and attr_symbol.symbol_type == SymbolType.CONSTANT:
                            self.analyzer.add_error(line, column,
                                f"No se puede reasignar la constante '{property_name}'")
                            return None
                        
                        expected_type = result_tuple[0]
                        
                        if not self.analyzer.type_checker.is_compatible(expected_type, value_type):
                            self.analyzer.add_error(line, column,
                                f"Tipo incompatible: no se puede asignar '{value_type}' a '{property_name}' de tipo '{expected_type}'")
                        else:
                            
                            obj_place = self.get_place_from_ctx(expressions[0])
                            value_place = self.get_place_from_ctx(expressions[1])
                            
                            if not obj_place:
                                obj_place = expressions[0].getText()
                            if not value_place:
                                value_place = expressions[1].getText()
                            
                            
                            property_access = f"{obj_place}.{property_name}"
                            self.emit_tac("=", value_place, None, property_access, line)
                else:
                    self.analyzer.add_error(line, column,
                        f"No se puede acceder a propiedades del tipo '{obj_type}'")
            
            else:
                if expressions:
                    for expr in expressions:
                        self.safe_visit(expr)
        
        except Exception as e:
            self.analyzer.add_error(line, column, f"Error en asignación: {str(e)}")
        
        return None
    
    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        if self.check_dead_code(ctx, "expresión"):
            return None
            
        if ctx.expression():
            return self.safe_visit(ctx.expression())
        return None
    
    def visitPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        if self.check_dead_code(ctx, "print"):
            return None
        
        if ctx.expression():
            expr_type = self.safe_visit(ctx.expression())
            
            
            expr_place = self.get_place_from_ctx(ctx.expression())
            if expr_place:
                self.emit_tac("call", "print", expr_place, "_", ctx.start.line)
            else:
                expr_value = ctx.expression().getText()
                self.emit_tac("call", "print", expr_value, "_", ctx.start.line)
            
            return expr_type
        return None
    
    def visitTypeAnnotation(self, ctx: CompiscriptParser.TypeAnnotationContext):
        return self.safe_visit(ctx.type_())
    
    def visitType(self, ctx: CompiscriptParser.TypeContext):
        base_type = self.safe_visit(ctx.baseType())
        
        array_dimensions = 0
        for child in ctx.getChildren():
            if child.getText() == '[':
                array_dimensions += 1
        
        if array_dimensions > 0:
            return f"{base_type}[]"

        return base_type
    
    def visitBaseType(self, ctx: CompiscriptParser.BaseTypeContext):
        return ctx.getText()
    
    def visitInitializer(self, ctx: CompiscriptParser.InitializerContext):
        return self.safe_visit(ctx.expression())
    
    def visitExpression(self, ctx: CompiscriptParser.ExpressionContext):
        result = self.safe_visit(ctx.assignmentExpr())
        
        
        place = self.get_place_from_ctx(ctx.assignmentExpr())
        if place:
            self.set_place_to_ctx(ctx, place)
        
        return result
    
    def visitAssignmentExpr(self, ctx: CompiscriptParser.AssignmentExprContext):
        return self.visitChildren(ctx)
    
    def visitExprNoAssign(self, ctx: CompiscriptParser.ExprNoAssignContext):
        result = self.safe_visit(ctx.conditionalExpr())
        
        
        place = self.get_place_from_ctx(ctx.conditionalExpr())
        if place:
            self.set_place_to_ctx(ctx, place)
        
        return result
    
    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        condition_type = self.safe_visit(ctx.logicalOrExpr())
        
        if ctx.expression() and len(ctx.expression()) == 2:
            if condition_type != "boolean":
                self.analyzer.add_error(
                    ctx.start.line, ctx.start.column,
                    f"Condición del operador ternario debe ser de tipo 'boolean', no '{condition_type}'"
                )
            
            expr1_type = self.safe_visit(ctx.expression(0))
            expr2_type = self.safe_visit(ctx.expression(1))
            
            if expr1_type != expr2_type:
                self.analyzer.add_error(
                    ctx.start.line, ctx.start.column,
                    f"Ambas ramas del operador ternario deben ser del mismo tipo: '{expr1_type}' vs '{expr2_type}'"
                )
                return "error"
            
            
            condition_place = self.get_place_from_ctx(ctx.logicalOrExpr())
            expr1_place = self.get_place_from_ctx(ctx.expression(0))
            expr2_place = self.get_place_from_ctx(ctx.expression(1))
            
            if not condition_place:
                condition_place = ctx.logicalOrExpr().getText()
            if not expr1_place:
                expr1_place = ctx.expression(0).getText()
            if not expr2_place:
                expr2_place = ctx.expression(1).getText()
            
            else_label = self.label_manager.new_label("TERNARY_ELSE_")
            end_label = self.label_manager.new_label("TERNARY_END_")
            result_temp = self.temp_manager.new_temp_from_type_string(expr1_type, self.current_scope_name)
            
            self.emit_conditional_jump(condition_place, else_label, is_true=False)
            self.emit_tac("=", expr1_place, None, result_temp)
            self.emit_goto(end_label)
            self.emit_label(else_label)
            self.emit_tac("=", expr2_place, None, result_temp)
            self.emit_label(end_label)
            
            self.set_place_to_ctx(ctx, result_temp)
            return expr1_type
        
        
        place = self.get_place_from_ctx(ctx.logicalOrExpr())
        if place:
            self.set_place_to_ctx(ctx, place)
        
        return condition_type
    
    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        left_type = self.safe_visit(ctx.logicalAndExpr(0))
        left_place = self.get_place_from_ctx(ctx.logicalAndExpr(0))
        
        if ctx.logicalAndExpr() and len(ctx.logicalAndExpr()) > 1:
            for i in range(1, len(ctx.logicalAndExpr())):
                right_type = self.safe_visit(ctx.logicalAndExpr(i))
                right_place = self.get_place_from_ctx(ctx.logicalAndExpr(i))
                
                operator = ctx.getChild(2*i - 1).getText()
                result_type = self.analyzer.type_checker.check_binary_operation(
                    left_type, operator, right_type
                )
                if result_type == "error":
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Operación inválida: '{left_type}' || '{right_type}'"
                    )
                
                
                if not left_place:
                    left_place = ctx.logicalAndExpr(i-1).getText()
                if not right_place:
                    right_place = ctx.logicalAndExpr(i).getText()
                
                temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
                self.emit_tac(operator, left_place, right_place, temp)
                
                left_type = result_type
                left_place = temp
        
        self.set_place_to_ctx(ctx, left_place)
        return left_type
    
    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        left_type = self.safe_visit(ctx.equalityExpr(0))
        left_place = self.get_place_from_ctx(ctx.equalityExpr(0))
        
        if ctx.equalityExpr() and len(ctx.equalityExpr()) > 1:
            for i in range(1, len(ctx.equalityExpr())):
                right_type = self.safe_visit(ctx.equalityExpr(i))
                right_place = self.get_place_from_ctx(ctx.equalityExpr(i))
                
                operator = ctx.getChild(2*i - 1).getText()
                result_type = self.analyzer.type_checker.check_binary_operation(
                    left_type, operator, right_type
                )
                if result_type == "error":
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Operación inválida: '{left_type}' && '{right_type}'"
                    )
                
                
                if not left_place:
                    left_place = ctx.equalityExpr(i-1).getText()
                if not right_place:
                    right_place = ctx.equalityExpr(i).getText()
                
                temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
                self.emit_tac(operator, left_place, right_place, temp)
                
                left_type = result_type
                left_place = temp
        
        self.set_place_to_ctx(ctx, left_place)
        return left_type
    
    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        left_type = self.safe_visit(ctx.relationalExpr(0))
        left_place = self.get_place_from_ctx(ctx.relationalExpr(0))
        
        if ctx.relationalExpr() and len(ctx.relationalExpr()) > 1:
            for i in range(1, len(ctx.relationalExpr())):
                right_type = self.safe_visit(ctx.relationalExpr(i))
                right_place = self.get_place_from_ctx(ctx.relationalExpr(i))
                
                operator = ctx.getChild(2*i - 1).getText() 
                
                result_type = self.analyzer.type_checker.check_binary_operation(
                    left_type, operator, right_type
                )
                if result_type == "error":
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Operación inválida: '{left_type}' {operator} '{right_type}'"
                    )
                
                
                if not left_place:
                    left_place = ctx.relationalExpr(i-1).getText()
                if not right_place:
                    right_place = ctx.relationalExpr(i).getText()
                
                temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
                self.emit_tac(operator, left_place, right_place, temp)
                
                left_type = result_type
                left_place = temp
        
        self.set_place_to_ctx(ctx, left_place)
        return left_type
    
    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        left_type = self.safe_visit(ctx.additiveExpr(0))
        left_place = self.get_place_from_ctx(ctx.additiveExpr(0))
        
        if ctx.additiveExpr() and len(ctx.additiveExpr()) > 1:
            for i in range(1, len(ctx.additiveExpr())):
                right_type = self.safe_visit(ctx.additiveExpr(i))
                right_place = self.get_place_from_ctx(ctx.additiveExpr(i))
                
                operator = ctx.getChild(2*i - 1).getText()  
                
                result_type = self.analyzer.type_checker.check_binary_operation(
                    left_type, operator, right_type
                )
                if result_type == "error":
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Operación inválida: '{left_type}' {operator} '{right_type}'"
                    )
                
                
                if not left_place:
                    left_place = ctx.additiveExpr(i-1).getText()
                if not right_place:
                    right_place = ctx.additiveExpr(i).getText()
                
                temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
                self.emit_tac(operator, left_place, right_place, temp)
                
                left_type = result_type
                left_place = temp
        
        self.set_place_to_ctx(ctx, left_place)
        return left_type
    
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        left_type = self.safe_visit(ctx.multiplicativeExpr(0))
        left_place = self.get_place_from_ctx(ctx.multiplicativeExpr(0))
        
        if ctx.multiplicativeExpr() and len(ctx.multiplicativeExpr()) > 1:
            for i in range(1, len(ctx.multiplicativeExpr())):
                right_type = self.safe_visit(ctx.multiplicativeExpr(i))
                right_place = self.get_place_from_ctx(ctx.multiplicativeExpr(i))
                
                operator = ctx.getChild(2*i - 1).getText() 
                
                result_type = self.analyzer.type_checker.check_binary_operation(
                    left_type, operator, right_type
                )
                if result_type == "error":
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Operación inválida: '{left_type}' {operator} '{right_type}'"
                    )
                
                
                if not left_place:
                    left_place = ctx.multiplicativeExpr(i-1).getText()
                if not right_place:
                    right_place = ctx.multiplicativeExpr(i).getText()
                
                temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
                self.emit_tac(operator, left_place, right_place, temp)
                
                left_type = result_type
                left_place = temp
        
        self.set_place_to_ctx(ctx, left_place)
        return left_type
    
    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        left_type = self.safe_visit(ctx.unaryExpr(0))
        left_place = self.get_place_from_ctx(ctx.unaryExpr(0))
        
        if ctx.unaryExpr() and len(ctx.unaryExpr()) > 1:
            for i in range(1, len(ctx.unaryExpr())):
                right_expr = ctx.unaryExpr(i)
                right_type = self.safe_visit(right_expr)
                right_place = self.get_place_from_ctx(right_expr)
                
                operator = ctx.getChild(2*i - 1).getText()
                
                
                if operator in ["/", "%"]:
                    txt = right_expr.getText().strip()
                    while txt.startswith('(') and txt.endswith(')'):
                        txt = txt[1:-1].strip()
                    is_zero_literal = (txt == "0")
                    is_zero_identifier = False
                    if not is_zero_literal and txt.isidentifier():
                        sym = self.analyzer.symbol_table.lookup(txt)
                        if sym and getattr(sym, "value", None) == 0:
                            is_zero_identifier = True
                    if is_zero_literal or is_zero_identifier:
                        self.analyzer.add_error(ctx.start.line, ctx.start.column, "No se puede dividir entre 0")
                        return "error"
                
                result_type = self.analyzer.type_checker.check_binary_operation(
                    left_type, operator, right_type
                )
                if result_type == "error":
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Operación inválida: '{left_type}' {operator} '{right_type}'"
                    )
                
                
                if not left_place:
                    left_place = ctx.unaryExpr(i-1).getText()
                if not right_place:
                    right_place = right_expr.getText()
                
                temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
                self.emit_tac(operator, left_place, right_place, temp)
                
                left_type = result_type
                left_place = temp
        
        self.set_place_to_ctx(ctx, left_place)
        return left_type

    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        text = ctx.getText()
        
        if text.startswith('-') or text.startswith('!'):
            operator = text[0]
            operand_type = self.safe_visit(ctx.unaryExpr())
            operand_place = self.get_place_from_ctx(ctx.unaryExpr())
            
            if operand_type is None:
                operand_type = "error"
            
            result_type = self.analyzer.type_checker.check_unary_operation(operator, operand_type)
            if result_type == "error":
                self.analyzer.add_error(
                    ctx.start.line, ctx.start.column,
                    f"Operación unaria inválida: '{operator}' sobre '{operand_type}'"
                )
            
            
            if not operand_place:
                operand_place = ctx.unaryExpr().getText()
            
            temp = self.temp_manager.new_temp_from_type_string(result_type, self.current_scope_name)
            self.emit_tac(operator, operand_place, None, temp)
            
            self.set_place_to_ctx(ctx, temp)
            return result_type
        
        
        result = self.safe_visit(ctx.primaryExpr())
        place = self.get_place_from_ctx(ctx.primaryExpr())
        if place:
            self.set_place_to_ctx(ctx, place)
        
        return result
    
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        if ctx.literalExpr():
            result = self.safe_visit(ctx.literalExpr())
            place = self.get_place_from_ctx(ctx.literalExpr())
            if place:
                self.set_place_to_ctx(ctx, place)
            return result
        elif ctx.leftHandSide():
            result = self.safe_visit(ctx.leftHandSide())
            place = self.get_place_from_ctx(ctx.leftHandSide())
            if place:
                self.set_place_to_ctx(ctx, place)
            return result
        elif ctx.expression():
            result = self.safe_visit(ctx.expression())
            place = self.get_place_from_ctx(ctx.expression())
            if place:
                self.set_place_to_ctx(ctx, place)
            return result
        return "error"
    
    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        if ctx.Literal():
            literal_text = ctx.Literal().getText()
            literal_type = self.analyzer.type_checker.get_literal_type(literal_text)
            
            
            self.set_place_to_ctx(ctx, literal_text)
            return literal_type
        elif ctx.arrayLiteral():
            return self.safe_visit(ctx.arrayLiteral())
        elif ctx.getText() == "null":
            self.set_place_to_ctx(ctx, "null")
            return "null"
        elif ctx.getText() == "true" or ctx.getText() == "false":
            self.set_place_to_ctx(ctx, ctx.getText())
            return "boolean"
        
        literal_text = ctx.getText()
        literal_type = self.analyzer.type_checker.get_literal_type(literal_text)
        self.set_place_to_ctx(ctx, literal_text)
        return literal_type
    
    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        try:
            if not ctx.expression():
                
                temp = self.temp_manager.new_temp_from_type_string("array", self.current_scope_name)
                self.emit_tac("new_array", "0", None, temp)
                self.set_place_to_ctx(ctx, temp)
                return "array"  
            
            expressions = ctx.expression()
            first_type = self.safe_visit(expressions[0])
            
            
            for i in range(1, len(expressions)):
                element_type = self.safe_visit(expressions[i])
                if element_type != first_type:
                    self.analyzer.add_error(
                        ctx.start.line, ctx.start.column,
                        f"Todos los elementos del array deben ser del mismo tipo. "
                        f"Esperado: '{first_type}', encontrado: '{element_type}'"
                    )
            
            
            temp = self.temp_manager.new_temp_from_type_string("array", self.current_scope_name)
            size = str(len(expressions))
            self.emit_tac("new_array", size, None, temp)
            
            
            for i, expr in enumerate(expressions):
                expr_place = self.get_place_from_ctx(expr)
                if not expr_place:
                    expr_place = expr.getText()
                
                self.emit_tac("[]=", str(i), expr_place, temp)
            
            self.set_place_to_ctx(ctx, temp)
            return "array"
        
        except Exception as e:
            self.analyzer.add_error(ctx.start.line, ctx.start.column, 
                f"Error en array literal: {str(e)}")
            return "array"
    
    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        primary_result = self.safe_visit(ctx.primaryAtom())
        
        if not ctx.suffixOp():
            
            place = self.get_place_from_ctx(ctx.primaryAtom())
            if place:
                self.set_place_to_ctx(ctx, place)
            return primary_result
        
        primary_symbol = None
        primary_identifier = None
        if hasattr(ctx.primaryAtom(), 'Identifier') and ctx.primaryAtom().Identifier():
            primary_identifier = ctx.primaryAtom().Identifier().getText()
            primary_symbol = self.analyzer.symbol_table.lookup(primary_identifier)
        
        current_result = primary_result
        current_symbol = primary_symbol
        current_object_type = primary_result if self.is_class_type(primary_result) else None
        last_property_name = None
        current_place = self.get_place_from_ctx(ctx.primaryAtom()) or primary_identifier
        
        for i, suffix in enumerate(ctx.suffixOp()):
            if hasattr(suffix, 'arguments'):  
                if current_object_type and last_property_name and current_result == "method":
                    
                    current_result = self.validate_method_call(
                        current_object_type,
                        last_property_name,
                        suffix.arguments() if hasattr(suffix, 'arguments') else None,
                        suffix.start.line,
                        suffix.start.column
                    )
                    current_symbol = None
                    current_object_type = None  
                    last_property_name = None
                    
                    
                    result_temp = self.temp_manager.new_temp_from_type_string(current_result, self.current_scope_name)
                    current_place = result_temp
                
                elif primary_identifier and i == 0:  
                    current_result = self.validate_function_call(
                        primary_identifier, 
                        suffix.arguments() if hasattr(suffix, 'arguments') else None,
                        suffix.start.line, 
                        suffix.start.column
                    )
                    
                    if current_result != "error":
                        current_symbol = self.analyzer.symbol_table.lookup(primary_identifier)
                        
                        
                        result_temp = self.temp_manager.new_temp_from_type_string(current_result, self.current_scope_name)
                        current_place = result_temp
                    else:
                        current_symbol = None
                        current_place = "error"
                
                else:
                    self.analyzer.add_error(
                        suffix.start.line, suffix.start.column,
                        "Llamada a función/método no válida"
                    )
                    current_result = "error"
                    current_symbol = None
                    current_place = "error"
            
            elif hasattr(suffix, 'expression') and suffix.expression():  
                if current_result != "array" and not current_result.endswith("[]"):
                    self.analyzer.add_error(
                        suffix.start.line, suffix.start.column,
                        f"No se puede indexar tipo '{current_result}'. Solo se pueden indexar arrays"
                    )
                    return "error"
                
                index_result = self.visitIndexExpr(suffix)
                if index_result == "error":
                    return "error"
                
                
                index_place = self.get_place_from_ctx(suffix.expression())
                if not index_place:
                    index_place = suffix.expression().getText()
                
                if current_symbol and current_symbol.array_element_type:
                    element_type = current_symbol.array_element_type.value
                    current_result = element_type
                elif current_result.endswith("[]"):
                    element_type = current_result[:-2]
                    current_result = element_type
                else:
                    current_result = "integer"
                
                element_temp = self.temp_manager.new_temp_from_type_string(current_result, self.current_scope_name)
                self.emit_tac("[]", current_place, index_place, element_temp)
                
                current_symbol = None
                current_object_type = current_result if self.is_class_type(current_result) else None
                current_place = element_temp
            
            elif hasattr(suffix, 'Identifier') and suffix.Identifier():  
                property_name = suffix.Identifier().getText()
                line = suffix.start.line
                column = suffix.start.column
                
                object_type = None
                if self.is_class_type(current_result):
                    object_type = current_result
                elif current_symbol and current_symbol.data_type == DataType.CLASS_TYPE:
                    object_type = current_symbol.class_type or current_symbol.value
                
                if object_type:
                    result_tuple = self.handle_class_property_access(
                        object_type, property_name, line, column, is_this=False)
                    
                    if result_tuple[0] != "error":
                        current_result = result_tuple[0]
                        current_symbol = result_tuple[1]
                        current_object_type = object_type
                        last_property_name = property_name
                        
                        if current_result == "method":
                            
                            current_place = f"{current_place}.{property_name}"
                        else:
                            
                            prop_temp = self.temp_manager.new_temp_from_type_string(current_result, self.current_scope_name)
                            self.emit_tac(".", current_place, property_name, prop_temp)
                            current_place = prop_temp
                            
                    else:
                        current_result = "error"
                        current_symbol = None
                        current_object_type = None
                        last_property_name = None
                        current_place = "error"
                else:
                    self.analyzer.add_error(line, column,
                        f"Tipo '{current_result}' no soporta acceso a propiedades")
                    current_result = "error"
                    current_symbol = None
                    current_object_type = None
                    last_property_name = None
                    current_place = "error"
        
        self.set_place_to_ctx(ctx, current_place)
        return current_result

    def handle_class_property_access(self, class_name: str, property_name: str, 
                line: int, column: int, is_this: bool = False):
        def search_in_class_hierarchy(current_class_name: str, property_name: str, visited_classes: set = None):
            if visited_classes is None:
                visited_classes = set()
            
            if current_class_name in visited_classes:
                return None, None
            
            visited_classes.add(current_class_name)
            
            class_symbol = self.analyzer.symbol_table.lookup(current_class_name)
            if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
                return None, None
            
            if property_name in class_symbol.attributes:
                attr_symbol = class_symbol.attributes[property_name]
                attr_symbol.is_used = True
                
                if attr_symbol.data_type == DataType.ARRAY and attr_symbol.array_element_type:
                    return f"{attr_symbol.array_element_type.value}[]", attr_symbol
                elif attr_symbol.data_type == DataType.CLASS_TYPE:
                    return attr_symbol.class_type or attr_symbol.value, attr_symbol
                else:
                    return attr_symbol.data_type.value, attr_symbol
            
            if property_name in class_symbol.methods:
                method_symbol = class_symbol.methods[property_name]
                method_symbol.is_used = True
                return "method", method_symbol
            
            if class_symbol.parent_class:
                return search_in_class_hierarchy(class_symbol.parent_class, property_name, visited_classes)
            
            return None, None
        
        initial_class_symbol = self.analyzer.symbol_table.lookup(class_name)
        if not initial_class_symbol or initial_class_symbol.symbol_type != SymbolType.CLASS:
            self.analyzer.add_error(line, column,
                f"Clase '{class_name}' no encontrada")
            return "error", None
        
        result_type, result_symbol = search_in_class_hierarchy(class_name, property_name)
        
        if result_type is not None and result_symbol is not None:
            return result_type, result_symbol
        else:
            hierarchy = []
            current_class = class_name
            while current_class:
                hierarchy.append(current_class)
                class_sym = self.analyzer.symbol_table.lookup(current_class)
                if class_sym and class_sym.parent_class:
                    current_class = class_sym.parent_class
                else:
                    break
            
            hierarchy_str = " -> ".join(hierarchy)
            self.analyzer.add_error(line, column,
                f"La clase '{class_name}' (jerarquía: {hierarchy_str}) no tiene un atributo o método llamado '{property_name}'")
            return "error", None

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
    
    def visitPrimaryAtom(self, ctx: CompiscriptParser.PrimaryAtomContext):
        return self.visitChildren(ctx)
    
    def check_array_index_operation(self, array_symbol, index_type: str) -> str:
        if not array_symbol:
            return "error"
        
        if array_symbol.data_type != DataType.ARRAY:
            return "error"
        
        if index_type != "integer":
            return "error"
        
        if array_symbol.array_element_type:
            return array_symbol.array_element_type.value
        else:
            return "integer"  
    
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        var_name = ctx.Identifier().getText()
        line = ctx.start.line
        column = ctx.start.column
        
        symbol = self.analyzer.symbol_table.lookup(var_name)
        if not symbol:
            self.analyzer.add_error(
                line, column,
                f"Variable '{var_name}' no está declarada",
                "UNDECLARED_VARIABLE"
            )
            return "error"

        
        self.set_place_to_ctx(ctx, var_name)

        if symbol.data_type == DataType.CLASS_TYPE:
            return symbol.class_type or symbol.value  

        if symbol.data_type == DataType.ARRAY and symbol.array_element_type:
            return f"{symbol.array_element_type.value}[]"

        return symbol.data_type.value
    
    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        try:
            class_name = ctx.Identifier().getText()
            line = ctx.start.line
            column = ctx.start.column
                        
            class_symbol = self.analyzer.symbol_table.lookup(class_name)
            if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
                self.analyzer.add_error(line, column, f"Clase '{class_name}' no está declarada")
                return "error"
            
            def find_constructor_in_hierarchy(current_class: str, visited: set = None):
                if visited is None:
                    visited = set()
                
                if current_class in visited:
                    return None
                
                visited.add(current_class)
                
                current_symbol = self.analyzer.symbol_table.lookup(current_class)
                if not current_symbol or current_symbol.symbol_type != SymbolType.CLASS:
                    return None
                
                if "constructor" in current_symbol.methods:
                    return current_symbol.methods["constructor"]
                
                if current_symbol.parent_class:
                    return find_constructor_in_hierarchy(current_symbol.parent_class, visited)
                
                return None
            
            constructor = find_constructor_in_hierarchy(class_name)
            
            if constructor:
                if ctx.arguments():
                    arg_types = []
                    for expr in ctx.arguments().expression():
                        arg_type = self.safe_visit(expr)
                        arg_types.append(arg_type)
                    
                    expected_params = len(constructor.parameters)
                    actual_args = len(arg_types)
                    
                    if expected_params != actual_args:
                        self.analyzer.add_error(line, column,
                            f"Constructor de '{class_name}' espera {expected_params} argumentos, pero recibió {actual_args}")
                        return "error"
                    
                    for i, (expected_param, actual_arg) in enumerate(zip(constructor.parameters, arg_types)):
                        if not self.analyzer.type_checker.is_compatible(expected_param.data_type.value, actual_arg):
                            self.analyzer.add_error(line, column,
                                f"Argumento {i+1} del constructor: esperado '{expected_param.data_type.value}', encontrado '{actual_arg}'")
                            return "error"
            else:
                if ctx.arguments() and ctx.arguments().expression():
                    self.analyzer.add_error(line, column,
                        f"Clase '{class_name}' no tiene constructor, pero se proporcionaron argumentos")
                    return "error"
            
            
            instance_temp = self.temp_manager.new_temp_from_type_string("class", self.current_scope_name)
            
            if ctx.arguments() and ctx.arguments().expression():
                
                for expr in ctx.arguments().expression():
                    arg_place = self.get_place_from_ctx(expr)
                    if not arg_place:
                        arg_place = expr.getText()
                    self.emit_tac("param", arg_place, None, "")
                
                num_args = str(len(ctx.arguments().expression()))
                self.emit_tac("new", class_name, num_args, instance_temp)
            else:
                self.emit_tac("new", class_name, "0", instance_temp)
            
            self.set_place_to_ctx(ctx, instance_temp)
            return class_name
            
        except Exception as e:
            self.analyzer.add_error(ctx.start.line, ctx.start.column, 
                f"Error en new: {str(e)}")
            return "error"
    
    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        line = ctx.start.line
        column = ctx.start.column
        
        if not self.analyzer.current_class:
            self.analyzer.add_error(line, column,
                "'this' solo puede usarse dentro de métodos de clase")
            return "error"
        
        
        self.set_place_to_ctx(ctx, "this")
        return self.analyzer.current_class
    
    def validate_method_call(self, object_type: str, method_name: str, arguments_ctx, line: int, column: int) -> str:
        def find_method_in_hierarchy(class_name: str, method_name: str, visited: set = None):
            if visited is None:
                visited = set()
            
            if class_name in visited:
                return None
            
            visited.add(class_name)
            
            class_symbol = self.analyzer.symbol_table.lookup(class_name)
            if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
                return None
            
            if method_name in class_symbol.methods:
                return class_symbol.methods[method_name]
            
            if class_symbol.parent_class:
                return find_method_in_hierarchy(class_symbol.parent_class, method_name, visited)
            
            return None
        
        class_symbol = self.analyzer.symbol_table.lookup(object_type)
        if not class_symbol or class_symbol.symbol_type != SymbolType.CLASS:
            self.analyzer.add_error(line, column,
                f"'{object_type}' no es una clase válida")
            return "error"
        
        method_symbol = find_method_in_hierarchy(object_type, method_name)
        if not method_symbol:
            self.analyzer.add_error(line, column,
                f"La clase '{object_type}' no tiene un método llamado '{method_name}'")
            return "error"
        
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
            
            if not self.analyzer.type_checker.is_compatible(expected_param.data_type.value, actual_arg_type):
                self.analyzer.add_error(line, column,
                    f"Argumento {i+1} del método '{method_name}': esperado '{expected_param.data_type.value}', encontrado '{actual_arg_type}'")
                return "error"
        
        
        if arguments_ctx and arguments_ctx.expression():
            for expr in arguments_ctx.expression():
                arg_place = self.get_place_from_ctx(expr)
                if not arg_place:
                    arg_place = expr.getText()
                self.emit_tac("PushParam", arg_place, None, "", line)

        result_temp = self.temp_manager.new_temp_from_type_string("unknown", self.current_scope_name)
        self.emit_tac("LCall", f"{object_type}.{method_name}", None, result_temp, line)

        if actual_count > 0:
            self.emit_tac("PopParams", str(actual_count), None, "", line)
        
        return method_symbol.return_type.value if method_symbol.return_type else "void"
    
    def validate_function_call(self, function_name: str, arguments_ctx, line: int, column: int) -> str:
        function_symbol = self.analyzer.symbol_table.lookup(function_name)
        if not function_symbol:
            self.analyzer.add_error(line, column, 
                f"Función '{function_name}' no está declarada", "UNDECLARED_FUNCTION")
            return "error"
        
        if function_symbol.symbol_type != SymbolType.FUNCTION:
            self.analyzer.add_error(line, column, 
                f"'{function_name}' no es una función", "NOT_A_FUNCTION")
            return "error"
        
        expected_params = function_symbol.parameters  
        expected_count = len(expected_params)
        
        actual_args = []
        actual_count = 0
        
        if arguments_ctx and arguments_ctx.expression():
            actual_count = len(arguments_ctx.expression())
            for expr in arguments_ctx.expression():
                arg_type = self.safe_visit(expr)
                actual_args.append(arg_type)
        
        if actual_count != expected_count:
            expected_names = [f"{p.name}:{p.data_type.value}" for p in expected_params]
            self.analyzer.add_error(line, column, 
                f"Función '{function_name}' espera {expected_count} parámetros ({', '.join(expected_names)}) "
                f"pero recibió {actual_count} argumentos", "WRONG_ARGUMENT_COUNT")
            return "error"
        
        for i in range(actual_count):
            expected_param = expected_params[i]
            actual_arg_type = actual_args[i]
            expected_type = expected_param.data_type.value
                        
            if not self.analyzer.type_checker.is_compatible(expected_type, actual_arg_type):
                self.analyzer.add_error(line, column, 
                    f"Argumento {i+1} de función '{function_name}': "
                    f"esperado '{expected_type}' (parámetro '{expected_param.name}'), "
                    f"encontrado '{actual_arg_type}'", "TYPE_MISMATCH")
                return "error"
        
        
        if arguments_ctx and arguments_ctx.expression():
            
            for expr in arguments_ctx.expression():
                arg_place = self.get_place_from_ctx(expr)
                if not arg_place:
                    arg_place = expr.getText()
                self.emit_tac("PushParam", arg_place, None, "", line)
        
        
        result_temp = self.temp_manager.new_temp_from_type_string("unknown", self.current_scope_name)
        self.emit_tac("LCall", function_name, None, result_temp, line)
        
        if actual_count > 0:
            self.emit_tac("PopParams", str(actual_count), None, "", line)
        
        
        self.set_place_to_ctx(arguments_ctx, result_temp)
        
        if function_symbol.return_type == DataType.ARRAY and function_symbol.array_element_type:
            return f"{function_symbol.array_element_type.value}[]"
        else:
            return function_symbol.return_type.value
    
    def visitArguments(self, ctx: CompiscriptParser.ArgumentsContext):
        argument_types = []
        if ctx.expression():
            for expr in ctx.expression():
                arg_type = self.safe_visit(expr)
                argument_types.append(arg_type)
        return argument_types

    def visitSuffixOp(self, ctx):
        try:
            if hasattr(ctx, 'arguments'):
                
                return "function_call"
            elif hasattr(ctx, 'expression') and ctx.expression():
                
                index_type = self.safe_visit(ctx.expression())
                if index_type != "integer":
                    self.analyzer.add_error(ctx.start.line, ctx.start.column,
                        f"Índice de array debe ser entero, encontrado: '{index_type}'")
                return "integer"  
            elif hasattr(ctx, 'Identifier') and ctx.Identifier():
                
                return "integer"  
        except Exception as e:
            if hasattr(ctx, 'start'):
                self.analyzer.add_error(ctx.start.line, ctx.start.column, 
                    f"Error en sufijo: {str(e)}")
        
        return "error"
    
    def visitIndexExpr(self, ctx):
        line = ctx.start.line
        column = ctx.start.column
                
        index_type = self.safe_visit(ctx.expression())
        
        if index_type != "integer":
            self.analyzer.add_error(
                line, column,
                f"Índice de array debe ser de tipo 'integer', encontrado: '{index_type}'",
                "INVALID_ARRAY_INDEX"
            )
            return "error"
        
        return "valid_index"
    
    def safe_visit(self, node):
        if node is None:
            return None
        
        try:
            return self.visit(node)
        except Exception as e:
            if hasattr(node, 'start'):
                line = node.start.line
                column = node.start.column
            else:
                line = 0
                column = 0
            
            self.analyzer.add_error(line, column, f"Error inesperado: {str(e)}")
            return "error"
    
    def visitChildren(self, node):
        result = None
        try:
            if node is None:
                return None
                
            for child in node.getChildren():
                if child is not None:
                    try:
                        child_result = self.safe_visit(child)
                        if child_result is not None:
                            result = child_result
                    except Exception as child_error:
                        if hasattr(child, 'start'):
                            line = child.start.line
                            column = child.start.column
                        else:
                            line = 0
                            column = 0
                        
                        print(f"Error visitando nodo hijo: {str(child_error)} (línea {line})")
                        continue
        
        except Exception as e:
            if hasattr(node, 'start'):
                line = node.start.line
                column = node.start.column
            else:
                line = 0
                column = 0
            
            self.analyzer.add_error(line, column, f"Error visitando nodo: {str(e)}")
        
        return result
    
    def get_analysis_result(self):
        total_errors = self.analyzer.get_total_errors()
        
        return {
            'success': total_errors == 0,
            'errors': self.analyzer.symbol_table.get_errors(),
            'warnings': self.analyzer.symbol_table.get_warnings(),
            'symbol_table': self.analyzer.symbol_table,
            'tac_code': self.tac_code,
            'tac_count': len(self.tac_code)
        }