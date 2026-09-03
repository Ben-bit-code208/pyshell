import ast
import datetime
import importlib
import importlib.util
import json
import operator
import os
import subprocess
import sys
import pdb
import shutil


try:
    import pty
except ImportError:
    pty = None


def update_index():
    indexer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Plugins", "__main__.py")
    subprocess.run([sys.executable, indexer_path])
update_index()


def load_plugins():
    plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Plugins")
    index_path = os.path.join(plugins_dir, "index.json")
    try:
        with open(index_path, "r") as f:
            plugins = json.load(f)["plugins"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print("Fehler beim Laden der Plugin-Liste:", e)
        return

    dep_folders = ("Deps", "Dependencys")

    def has_deps(name):
        return any(os.path.isdir(os.path.join(plugins_dir, name, d)) for d in dep_folders)

    def load_plugin(name, has_deps_flag):
        for d in dep_folders:
            deps_dir = os.path.join(plugins_dir, name, d)
            if os.path.isdir(deps_dir):
                sys.path.insert(0, deps_dir)
        main_path = os.path.join(plugins_dir, name, "main.py")
        spec = importlib.util.spec_from_file_location(f"Plugins.{name}", main_path)
        if spec is None:
            raise ImportError(f"Kein main.py im Plugin '{name}' gefunden")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        print(f"Plugin '{name}' geladen" + (" (Deps)" if has_deps_flag else ""))

    for name in plugins:
        if has_deps(name):
            try:
                load_plugin(name, True)
            except Exception as e:
                print(f"Fehler beim Laden von Plugin '{name}': {e}")

    for name in plugins:
        if not has_deps(name):
            try:
                load_plugin(name, False)
            except Exception as e:
                print(f"Fehler beim Laden von Plugin '{name}': {e}")

    return plugins



plugin_info = load_plugins()

plugin_commands = {}
if plugin_info:
    for name, info in plugin_info.items():
        for cmd, func_path in info.get("funktionen", {}).items():
            plugin_commands[cmd] = func_path


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calc(expr):
    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](evaluate(node.operand))
        raise ValueError("Nicht unterstützter Ausdruck")

    return evaluate(ast.parse(expr, mode="eval"))


print("PyShell Gestartet. Tippe 'help' für Hilfe")

while True:
    command = input("PyShell> ")

    if command == "help":
        print("""'help' - Zeigt diese Hilfe
                 'time' - zeigt Zeit und Datum
                 'clear' - leert den Bildschirm
                 'echo' - gibt Text aus
                 'exit' - Beendet PyShell
                 'calc' - rechnet eine Rechnung aus
                 'rm' - entfernt Dateien (nutze rm für genauere hilfe)
                 'rd' - entfernt Ordner (nutze rd für genauere hilfe)
                 'mkdir' - macht einen ordner
                 'mk' - Erstellt eine Datei
                 'cat' - zeigt inhalte einer datei an""")
        if plugin_info:
            print("\nPlugins:")
            for name, info in plugin_info.items():
                befehle = ", ".join(info["funktionen"].keys()) if info["funktionen"] else "keine"
                print(f"  {name}: {info['beschreibung']} (Befehle: {befehle})")

    elif command == "time":
        print(datetime.datetime.now())

    elif command.startswith("echo"):
        print(command[5:])

    elif command == "clear":
        if os.name == "posix":
            os.system("clear")
        else:
            try:
                os.system("cls")
            except Exception as e:
                print(e + os.name)

    elif command.startswith("calc"):
        expr = command[len("calc"):].strip()
        if not expr:
            print("Bitte füge eine Rechenoperation ein")
        else:
            try:
                print(calc(expr))
            except Exception as e:
                print("Fehler:", e)

    elif command.startswith("rm"):
        to_be_rmd = command[len("rm"):].strip()
        if not to_be_rmd:
            print("Tippe einfach einfach 'rm <dateipfad_zum_entfernen>' z.b 'rm ./test.txt' um im lokalen ordner die datei test.txt zu löschen")
        else:
            try:
                os.remove(to_be_rmd)
            except Exception as e:
                    print("Fehler:", e, "OS NAME", os.name)

    elif command.startswith("rd"):
        to_be_rdd = command[len("rd"):].strip()
        if not to_be_rdd:
            print("Tippe einfach 'rd <ordnerpfad_zum_entfernen>' z.b 'rd ./test' um im lokalen Verzeichnis den ordner test zu löschen")
        else:
            try:
                shutil.rmtree(to_be_rdd)
            except Exception as e:
                print("Fehler:", e, "OS NAME", os.name)

    elif command.startswith("mkdir"):
        to_be_mkdird = command[len("mkdir"):].strip
        if not to_be_mkdird:
            print("Bitte füge den ort ein wo der Ordner erstellt wird und wie er Heißen soll")
        else:
            try:
                # Source - https://stackoverflow.com/a/273227
                # Posted by Blair Conrad, modified by community and the Skript creator. See post 'Timeline' for change history
                # Retrieved 2026-08-01, License - CC BY-SA 4.0

                from pathlib import Path
                Path(to_be_mkdird).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print("Fehler:", e, "OS NAME", os.name)

    elif command.startswith("mk"):
        to_be_mkd = command[len("mk"):].strip
        if not to_be_mkd:
            print("Bitte füge ein wo die Datei erstellt werden soll")
        else:
            try:
                if not os.path.exists(to_be_mkd):
                    with open(to_be_mkd, 'x'): pass
                else:
                    print("Datei (", to_be_mkd ,") Exisitert Schon")
            except Exception as e:
                print("Fehler:", e ,"OS NAME:", os.name)

    elif command.startswith("cat"):
        to_be_catett = command[len("cat"):].strip
        try:
            with open(to_be_catett, "r") as f:
                inhalt = f.read()
            print(inhalt)
        except Exception as e:
            print("Fehler:", e ,"OS NAME:", os.name)

    elif command == "exit":
        break

    else:
        cmd_name = command.split()[0] if command.split() else command
        if cmd_name in plugin_commands:
            mod_name, func_name = plugin_commands[cmd_name].split(":")
            module = None
            base = mod_name
            while base:
                if base in sys.modules and hasattr(sys.modules[base], func_name):
                    module = sys.modules[base]
                    break
                base = base.rsplit(".", 1)[0] if "." in base else ""
            if module is None:
                print(f"Plugin-Funktion '{func_name}' aus '{mod_name}' nicht gefunden")
            else:
                try:
                    getattr(module, func_name)(command)
                except Exception as e:
                    print("Fehler:", e)
        else:
            print("Ungültiger Command, bitte probiere es nochmal")
