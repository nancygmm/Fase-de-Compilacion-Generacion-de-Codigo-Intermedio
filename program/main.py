import sys
import os
from antlr4 import *
from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser
from analizador_semantico import CompiscriptSemanticVisitor

def print_ast(node, depth=0):
    if node is None:
        return
    
    indent = "  " * depth
    class_name = node.__class__.__name__
    
    if hasattr(node, 'getText') and node.getChildCount() == 0:
        print(f"{indent}{class_name}: {node.getText()}")
    else:
        print(f"{indent}{class_name}")
    
    if hasattr(node, 'getChildCount'):
        for i in range(node.getChildCount()):
            child = node.getChild(i)
            print_ast(child, depth + 1)


def main():    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "archivo.cps"
    
    try:
        print(f"Analizando archivo: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            codigo_fuente = file.read()
        
        input_stream = InputStream(codigo_fuente)
        lexer = CompiscriptLexer(input_stream)
        
        if hasattr(lexer, '_errHandler') and hasattr(lexer._errHandler, 'errorCount'):
            if lexer._errHandler.errorCount > 0:
                print(f"Se encontraron errores léxicos")
                return False
        
        tokens = CommonTokenStream(lexer)
        parser = CompiscriptParser(tokens)
        
        parser.removeErrorListeners()
        
        ast = parser.program()
        print_ast(ast, 0)
        
        if parser.getNumberOfSyntaxErrors() > 0:
            print(f"Se encontraron {parser.getNumberOfSyntaxErrors()} errores sintácticos")
            return False
        
        print(f"AST generado: {type(ast).__name__}")
        
        semantic_visitor = CompiscriptSemanticVisitor()
        
        try:
            semantic_visitor.visit(ast)
        except Exception as e:
            print(f"Error durante el análisis semántico: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        result = semantic_visitor.get_analysis_result()
        
        print("Tabla de símbolos")
        semantic_visitor.analyzer.symbol_table.print_table()
        
        print("Estadísticas")
        
        total_errors = len(result['errors'])
        print(f"Errores semánticos: {total_errors}")
        
        if result['success']:
            print("Éxito")
            return True
        else:
            print(f"Errores encontrados: {total_errors}")
            return False
            
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo '{file_path}'")
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    
    success = main()
    
    sys.exit(0 if success else 1)

