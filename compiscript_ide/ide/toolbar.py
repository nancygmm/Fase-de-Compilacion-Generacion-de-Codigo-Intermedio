import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import os
import sys
import threading
from pathlib import Path

class Toolbar(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.analyzer_path = None  
        self.is_compiling = False

        self.save_btn = tk.Button(self, text="Guardar", command=self.guardar)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.compile_btn = tk.Button(self, text="Compilar", command=self.compilar)
        self.compile_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(self, text="Configurar Analizador", command=self.configurar_analizador).pack(side=tk.LEFT, padx=5)

    def configurar_analizador(self):
        folder = filedialog.askdirectory(
            title="Selecciona la carpeta PROGRAM del Analizador Semántico",
            initialdir=os.getcwd()
        )
        if folder:
            main_py = Path(folder) / "main.py"
            analizador_py = Path(folder) / "analizador_semantico.py"
            
            if main_py.exists() and analizador_py.exists():
                self.analyzer_path = Path(folder)
                self.app.console.log(f"Analizador configurado: {folder}")
                messagebox.showinfo("Configuración exitosa", 
                                  f"Analizador semántico configurado correctamente:\n{folder}")
            else:
                messagebox.showerror("Error", 
                                   f"No se encontró main.py y analizador_semantico.py en:\n{folder}\n"
                                   f"Asegúrate de seleccionar la carpeta 'program'")

    def _find_analyzer_automatically(self) -> Path:
        
        possible_locations = [
            
            Path.cwd() / "program",
            
            
            Path.cwd().parent / "program",
            
            
            Path.cwd().parent / "ANALIZADOR-SEMANTICO" / "program",
            Path.cwd().parent / "analizador-semantico" / "program", 
            Path.cwd().parent / "semantic-analyzer" / "program",
            
            
            Path(__file__).parent.parent.parent / "program",
            
            
            Path.cwd() / "analizador" / "program",
            Path.cwd() / "semantico" / "program",
        ]
        
        for location in possible_locations:
            main_py = location / "main.py"
            analizador_py = location / "analizador_semantico.py"
            
            
            if main_py.exists() and analizador_py.exists():
                self.app.console.log(f"Analizador encontrado automáticamente: {location}")
                return location
        
        return None

    def _get_analyzer_dir(self) -> Path:
        
        if self.analyzer_path and self.analyzer_path.exists():
            return self.analyzer_path
        
        
        auto_found = self._find_analyzer_automatically()
        if auto_found:
            self.analyzer_path = auto_found
            return auto_found
        
        
        fallback = Path(__file__).parent.parent.parent / "program"
        if fallback.exists():
            return fallback
            
        
        return Path.cwd() / "program"

    def guardar(self):
        file = self.app.get_current_path()
        if not file:
            messagebox.showwarning("Sin archivo", "No se ha abierto ningún archivo.")
            return
        try:
            with open(file, "w", encoding="utf-8") as f:
                f.write(self.app.get_code())
            self.app.console.log(f"Archivo guardado: {Path(file).name}")
        except Exception as e:
            self.app.console.log(f"Error al guardar: {str(e)}")
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{str(e)}")

    def _set_compiling_state(self, compiling: bool):
        self.is_compiling = compiling
        self.compile_btn.config(
            text="Compilando..." if compiling else "Compilar",
            state="disabled" if compiling else "normal"
        )
        self.save_btn.config(state="disabled" if compiling else "normal")

    def _compile_thread(self, analyzer_dir: Path, cps_file: Path):
        try:
            
            main_py = analyzer_dir / "main.py"
            if not main_py.exists():
                self.app.root.after(0, self._handle_compile_error, 
                    f"No se encontró main.py en {analyzer_dir}")
                return
                
            command = [sys.executable, str(main_py), str(cps_file.resolve())]
            
            self.app.console.log(f"Iniciando análisis...")
            self.app.console.log(f"Archivo: {cps_file.name}")
            self.app.console.log(f"Analizador: {analyzer_dir}")
            self.app.console.log(f"Comando: {' '.join(command)}")

            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(analyzer_dir),  
                timeout=10
            )

            
            self.app.root.after(0, self._handle_compile_result, result, analyzer_dir, cps_file)

        except subprocess.TimeoutExpired:
            self.app.root.after(0, self._handle_timeout)
        except Exception as e:
            self.app.root.after(0, self._handle_compile_error, str(e))

    def _handle_compile_result(self, result, analyzer_dir: Path, cps_file: Path):
        try:
            
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    self.app.console.log(line)
            
            if result.stderr.strip():
                for line in result.stderr.strip().split('\n'):
                    self.app.console.log(f"Error: {line}")

            if result.returncode != 0:
                self.app.console.log(f"El analizador terminó con código de error: {result.returncode}")
            else:
                self.app.console.log("Fin")

            
            self._load_analysis_views(analyzer_dir, cps_file)
            
        finally:
            self._set_compiling_state(False)

    def _handle_timeout(self):
        self._set_compiling_state(False)

    def _handle_compile_error(self, error_msg: str):
        self.app.console.log(f"Error al ejecutar el analizador: {error_msg}")
        messagebox.showerror("Error de ejecución", f"Error al ejecutar el analizador:\n{error_msg}")
        self._set_compiling_state(False)

    def _load_analysis_views(self, analyzer_dir: Path, cps_file: Path):
        try:
            
            
            modules_to_clear = [
                'analizador_semantico', 'CompiscriptLexer', 
                'CompiscriptParser', 'CompiscriptVisitor'
            ]
            for module in modules_to_clear:
                if module in sys.modules:
                    del sys.modules[module]
            
            analyzer_str = str(analyzer_dir)
            if analyzer_str not in sys.path:
                sys.path.insert(0, analyzer_str)

            required_files = [
                analyzer_dir / "analizador_semantico.py",
                analyzer_dir / "CompiscriptLexer.py", 
                analyzer_dir / "CompiscriptParser.py"
            ]
            
            missing_files = [f for f in required_files if not f.exists()]
            if missing_files:
                self.app.console.log("Archivos faltantes para las vistas:")
                for f in missing_files:
                    self.app.console.log(f" {f.name}")
                self.app.console.log("Genera los archivos ANTLR con: antlr4 -Dlanguage=Python3 Compiscript.g4")
                return

            
            try:
                
                import analizador_semantico
                from analizador_semantico import CompiscriptSemanticVisitor
                
                
                from antlr4 import FileStream, CommonTokenStream
                
                
                
                import CompiscriptLexer
                import CompiscriptParser
                from CompiscriptLexer import CompiscriptLexer as LexerClass
                from CompiscriptParser import CompiscriptParser as ParserClass
                
                
            except ImportError as e:
                self.app.console.log(f"Error importando módulos: {e}")
                self.app.console.log("Posibles soluciones:")
                self.app.console.log("1. Genera archivos ANTLR: antlr4 -Dlanguage=Python3 Compiscript.g4")
                self.app.console.log("2. Instala antlr4: pip install antlr4-python3-runtime")
                self.app.console.log("3. Verifica que estés en el directorio correcto")
                return

            
            self.app.console.log(f"Procesando archivo: {cps_file}")
            
            input_stream = FileStream(str(cps_file.resolve()), encoding="utf-8")
            lexer = LexerClass(input_stream)
            tokens = CommonTokenStream(lexer)
            parser = ParserClass(tokens)
            
            
            parser.removeErrorListeners()
            
            ast = parser.program()

            
            if parser.getNumberOfSyntaxErrors() > 0:
                self.app.console.log(f"{parser.getNumberOfSyntaxErrors()} errores sintácticos encontrados")
                return


            
            visitor = CompiscriptSemanticVisitor()
            visitor.visit(ast)
            result_analysis = visitor.get_analysis_result()
            symbol_table = result_analysis["symbol_table"]


            
            self.app.syntax_tree_view.load_from_ast(ast)
            self.app.symbol_table_view.load_from_symbol_table(symbol_table)
            

        except Exception as e:
            import traceback
            self.app.console.log(f"Error cargando vistas: {str(e)}")
            self.app.console.log("Detalles del error:")
            
            
            error_lines = traceback.format_exc().split('\n')
            for line in error_lines[-10:]:  
                if line.strip():
                    self.app.console.log(f"  {line}")
            
            self.app.console.log("La compilación principal funcionó, pero las vistas no se pudieron cargar")

    def compilar(self):
        
        if self.is_compiling:
            self.app.console.log("Ya hay una compilación en proceso...")
            return

        analyzer_dir = self._get_analyzer_dir()
        main_py = analyzer_dir / "main.py"
        analizador_py = analyzer_dir / "analizador_semantico.py"

        
        if not main_py.exists() or not analizador_py.exists():
            self.app.console.log(f"No se encontró el analizador completo en: {analyzer_dir}")
            self.app.console.log(f"main.py existe: {main_py.exists()}")
            self.app.console.log(f"analizador_semantico.py existe: {analizador_py.exists()}")
            

        current_path = self.app.get_current_path()
        if not current_path:
            messagebox.showwarning("Sin archivo", "No hay ningún archivo abierto. Abre un archivo .cps primero.")
            return
        
        if not current_path.endswith(".cps"):
            messagebox.showwarning("Archivo inválido", "El archivo actual no es un archivo .cps. Selecciona un archivo .cps.")
            return

        cps_file = Path(current_path)
        if not cps_file.exists():
            messagebox.showerror("Archivo no encontrado", f"No existe el archivo .cps:\n{cps_file}")
            return

        
        self.guardar()

        
        self.app.syntax_tree_view.clear()
        self.app.symbol_table_view.clear()

        
        self._set_compiling_state(True)
        
        compile_thread = threading.Thread(
            target=self._compile_thread, 
            args=(analyzer_dir, cps_file),
            daemon=True
        )
        compile_thread.start()