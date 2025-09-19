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


def parse_arguments():
    args = sys.argv[1:]
    
    if not args:
        sys.exit(0)
    
    file_path = None
    options = {
        'show_ast': False,
        'show_tac': True,  
        'generate_tac': True,
        'show_symbols': True,  
        'verbose': False
    }
    
    for arg in args:
        if arg.startswith('--'):
            if arg == '--show-ast':
                options['show_ast'] = True
            elif arg == '--show-tac':
                options['show_tac'] = True
            elif arg == '--no-tac':
                options['generate_tac'] = False
                options['show_tac'] = False
            elif arg == '--show-symbols':
                options['show_symbols'] = True
            elif arg == '--verbose':
                options['verbose'] = True
            else:
                sys.exit(1)
        elif arg.endswith('.cps') or not arg.startswith('-'):
            if file_path is None:
                file_path = arg
            else:
                print("Error: Solo se puede procesar un archivo a la vez")
                sys.exit(1)
    
    if file_path is None:
        file_path = "archivo.cps"  
    
    return file_path, options

def print_compilation_summary(result, options):
    print("\n" + "="*60)
    print("           RESUMEN DE COMPILACIÓN")
    print("="*60)
    
    
    if result['success']:
        print("COMPILACIÓN EXITOSA")
    else:
        print("COMPILACIÓN FALLIDA")
    
    
    print(f"\nEstadísticas:")
    print(f"  • Errores semánticos: {len(result['errors'])}")
    print(f"  • Advertencias: {len(result['warnings'])}")
    
    if options['generate_tac']:
        print(f"  • Instrucciones TAC generadas: {result['tac_count']}")
    
    
    if result['errors']:
        print(f"\nERRORES ENCONTRADOS ({len(result['errors'])}):")
        for i, error in enumerate(result['errors'][:10], 1):  
            print(f"  {i}. {error}")
        
        if len(result['errors']) > 10:
            print(f"  ... y {len(result['errors']) - 10} errores más")
    
    
    if result['warnings']:
        print(f"\nADVERTENCIAS ({len(result['warnings'])}):")
        for i, warning in enumerate(result['warnings'][:5], 1):  
            print(f"  {i}. {warning}")
        
        if len(result['warnings']) > 5:
            print(f"  ... y {len(result['warnings']) - 5} advertencias más")
    
    print("="*60)

def main():
    try:
        file_path, options = parse_arguments()
        
        if options['verbose']:
            print(f"Opciones activas: {[k for k, v in options.items() if v]}")
        
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                codigo_fuente = file.read()
        except FileNotFoundError:
            print(f"Error: No se pudo encontrar el archivo '{file_path}'")
            return False
        except Exception as e:
            print(f"Error al leer el archivo: {str(e)}")
            return False
        
        
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
        
        
        if parser.getNumberOfSyntaxErrors() > 0:
            print(f"Se encontraron {parser.getNumberOfSyntaxErrors()} errores sintácticos")
            return False
        
        print(f"✓ AST generado exitosamente: {type(ast).__name__}")
        
        
        if options['show_ast']:
            print("\n" + "="*50)
            print("           ÁRBOL SINTÁCTICO ABSTRACTO")
            print("="*50)
            print_ast(ast, 0)
        
        
        semantic_visitor = CompiscriptSemanticVisitor()
        
        try:
            semantic_visitor.visit(ast)
        except Exception as e:
            print(f"Error durante el análisis semántico: {e}")
            if options['verbose']:
                import traceback
                traceback.print_exc()
            return False
        
        
        result = semantic_visitor.get_analysis_result()
        
        
        if options['show_symbols']:
            print("\n" + "="*50)
            print("           TABLA DE SÍMBOLOS")
            print("="*50)
            semantic_visitor.analyzer.symbol_table.print_table()
        
        
        if options['show_tac'] and options['generate_tac'] and result['tac_count'] > 0:
            semantic_visitor.print_tac()
        elif options['show_tac'] and result['tac_count'] == 0:
            print("\nNo se generó código TAC")
        
        
        print_compilation_summary(result, options)
        
        return result['success']
            
    except KeyboardInterrupt:
        return False
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if options.get('verbose', False):
            import traceback
            traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        
        if len(sys.argv) == 1:
            print("Ingrese el archivo a compilar")
        else:
            success = main()
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)