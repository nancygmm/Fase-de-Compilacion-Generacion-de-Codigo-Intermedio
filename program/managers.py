from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

class TempType(Enum):
    INTEGER = "integer"
    STRING = "string"
    BOOLEAN = "boolean"
    ARRAY = "array"
    CLASS = "class"
    UNKNOWN = "unknown"

class TempManager:
    
    def __init__(self):
        self.counter = 0
        self.free = []
        self.temp_types: Dict[str, TempType] = {}
        self.temp_scopes: Dict[str, str] = {}  
        self.active_temps: List[str] = []
        
    def new_temp(self, temp_type: Optional[TempType] = None, scope_name: str = "global") -> str:
        if self.free:
            temp = self.free.pop()
        else:
            self.counter += 1
            temp = f"t{self.counter}"
        
        
        if temp_type:
            self.temp_types[temp] = temp_type
        else:
            self.temp_types[temp] = TempType.UNKNOWN
            
        self.temp_scopes[temp] = scope_name
        self.active_temps.append(temp)
        
        return temp
    
    def new_temp_from_type_string(self, type_str: str, scope_name: str = "global") -> str:
        try:
            temp_type = TempType(type_str.lower())
        except ValueError:
            temp_type = TempType.UNKNOWN
            
        return self.new_temp(temp_type, scope_name)
    
    def release_temp(self, temp: str) -> None:
        if temp in self.active_temps:
            self.active_temps.remove(temp)
            self.free.append(temp)
            
    
    def get_temp_type(self, temp: str) -> TempType:
        return self.temp_types.get(temp, TempType.UNKNOWN)
    
    def get_temp_scope(self, temp: str) -> str:
        return self.temp_scopes.get(temp, "unknown")
    
    def cleanup_scope(self, scope_name: str) -> List[str]:
        released = []
        temps_to_release = [temp for temp, scope in self.temp_scopes.items() 
                           if scope == scope_name and temp in self.active_temps]
        
        for temp in temps_to_release:
            self.release_temp(temp)
            released.append(temp)
            
        return released
    
    def get_active_temps(self) -> List[str]:

        return self.active_temps.copy()

class LabelType(Enum):
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    LOOP_CONTINUE = "loop_continue"
    IF_ELSE = "if_else"
    IF_END = "if_end"
    SWITCH_CASE = "switch_case"
    SWITCH_DEFAULT = "switch_default"
    SWITCH_END = "switch_end"
    FUNCTION_START = "function_start"
    FUNCTION_END = "function_end"
    GENERAL = "general"

class ControlContext:
    
    def __init__(self, context_type: str, break_label: str, continue_label: Optional[str] = None):
        self.context_type = context_type  
        self.break_label = break_label
        self.continue_label = continue_label

class LabelManager:
    
    def __init__(self):
        self.counter = 0
        self.label_stack: List[ControlContext] = []
        self.label_types: Dict[str, LabelType] = {}
        self.function_labels: Dict[str, Tuple[str, str]] = {}  
        
    def new_label(self, prefix: str = "L", label_type: LabelType = LabelType.GENERAL) -> str:
        self.counter += 1
        label = f"{prefix}{self.counter}"
        self.label_types[label] = label_type
        return label
    
    def new_loop_labels(self) -> Tuple[str, str, str]:
        start_label = self.new_label("LOOP_START_", LabelType.LOOP_START)
        end_label = self.new_label("LOOP_END_", LabelType.LOOP_END)
        continue_label = self.new_label("LOOP_CONTINUE_", LabelType.LOOP_CONTINUE)
        
        return start_label, end_label, continue_label
    
    def new_if_labels(self) -> Tuple[str, str]:
        else_label = self.new_label("IF_ELSE_", LabelType.IF_ELSE)
        end_label = self.new_label("IF_END_", LabelType.IF_END)
        
        return else_label, end_label
    
    def new_switch_labels(self, num_cases: int) -> Tuple[List[str], str, str]:
        case_labels = []
        for i in range(num_cases):
            case_label = self.new_label(f"CASE_{i}_", LabelType.SWITCH_CASE)
            case_labels.append(case_label)
            
        default_label = self.new_label("DEFAULT_", LabelType.SWITCH_DEFAULT)
        end_label = self.new_label("SWITCH_END_", LabelType.SWITCH_END)
        
        return case_labels, default_label, end_label
    
    def new_function_labels(self, function_name: str) -> Tuple[str, str]:
        start_label = self.new_label(f"FUNC_{function_name}_START_", LabelType.FUNCTION_START)
        end_label = self.new_label(f"FUNC_{function_name}_END_", LabelType.FUNCTION_END)
        
        self.function_labels[function_name] = (start_label, end_label)
        return start_label, end_label
    
    def push_loop_context(self, break_label: str, continue_label: str) -> None:
        context = ControlContext("loop", break_label, continue_label)
        self.label_stack.append(context)
    
    def push_switch_context(self, break_label: str) -> None:
        context = ControlContext("switch", break_label)
        self.label_stack.append(context)
    
    def push_function_context(self, return_label: str) -> None:
        context = ControlContext("function", return_label)
        self.label_stack.append(context)
    
    def pop_context(self) -> Optional[ControlContext]:
        if self.label_stack:
            return self.label_stack.pop()
        return None
    
    def get_current_break_label(self) -> Optional[str]:
        if self.label_stack:
            return self.label_stack[-1].break_label
        return None
    
    def get_current_continue_label(self) -> Optional[str]:
        
        for context in reversed(self.label_stack):
            if context.context_type == "loop" and context.continue_label:
                return context.continue_label
        return None
    
    def get_current_return_label(self) -> Optional[str]:
        
        for context in reversed(self.label_stack):
            if context.context_type == "function":
                return context.break_label
        return None
    
    def get_function_labels(self, function_name: str) -> Optional[Tuple[str, str]]:
        return self.function_labels.get(function_name)
    
    def get_label_type(self, label: str) -> LabelType:
        return self.label_types.get(label, LabelType.GENERAL)
    
    def is_in_loop(self) -> bool:
        return any(ctx.context_type == "loop" for ctx in self.label_stack)
    
    def is_in_switch(self) -> bool:
        return any(ctx.context_type == "switch" for ctx in self.label_stack)
    
    def is_in_function(self) -> bool:
        return any(ctx.context_type == "function" for ctx in self.label_stack)
    
    def get_context_stack_info(self) -> List[str]:
        info = []
        for i, ctx in enumerate(self.label_stack):
            ctx_info = f"Level {i}: {ctx.context_type} (break: {ctx.break_label}"
            if ctx.continue_label:
                ctx_info += f", continue: {ctx.continue_label}"
            ctx_info += ")"
            info.append(ctx_info)
        return info


@dataclass
class ActivationRecord:
    function_name: str
    parameters: List[str]
    local_variables: List[str]
    return_address: Optional[str] = None
    control_link: Optional[str] = None
    access_link: Optional[str] = None
    return_value: Optional[str] = None
    
class ActivationManager:
    
    def __init__(self):
        self.activation_stack: List[ActivationRecord] = []
        self.current_record: Optional[ActivationRecord] = None
        
    def create_activation_record(self, function_name: str, parameters: List[str]) -> ActivationRecord:
        record = ActivationRecord(
            function_name=function_name,
            parameters=parameters,
            local_variables=[]
        )
        return record
    
    def push_activation_record(self, record: ActivationRecord) -> None:
        if self.current_record:
            record.control_link = self.current_record.function_name
        
        self.activation_stack.append(record)
        self.current_record = record
    
    def pop_activation_record(self) -> Optional[ActivationRecord]:
        if not self.activation_stack:
            return None
            
        popped = self.activation_stack.pop()
        self.current_record = self.activation_stack[-1] if self.activation_stack else None
        return popped
    
    def add_local_variable(self, var_name: str) -> None:
        if self.current_record:
            self.current_record.local_variables.append(var_name)
    
    def get_current_function(self) -> Optional[str]:
        return self.current_record.function_name if self.current_record else None