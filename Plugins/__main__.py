import os
import json
import hashlib

folder = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(folder, "index.json")

dep_folders = ("Deps", "Dependencys")


def has_deps(name):
    return any(os.path.isdir(os.path.join(folder, name, d)) for d in dep_folders)


def read_help(name):
    help_path = None
    for filename in ("help.json", "hilfe.json"):
        candidate = os.path.join(folder, name, filename)
        if os.path.isfile(candidate):
            help_path = candidate
            break
    if help_path is None:
        return {"beschreibung": "Keine Beschreibung vorhanden", "funktionen": {}}
    try:
        with open(help_path, "r") as f:
            data = json.load(f)
        return {
            "beschreibung": data.get("beschreibung", "Keine Beschreibung vorhanden"),
            "funktionen": data.get("funktionen", {}),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"beschreibung": "help.json fehlerhaft", "funktionen": {}}


plugins = {}
for entry in os.scandir(folder):
    if entry.is_dir() and not entry.name.startswith(".") and entry.name not in ("__pycache__", "__build__"):
        plugins[entry.name] = read_help(entry.name)

plugins = {name: plugins[name] for name in sorted(plugins, key=has_deps, reverse=True)}

content = json.dumps(plugins, indent=2)
new_hash = hashlib.sha256(content.encode()).hexdigest()

if os.path.exists(index_path):
    try:
        with open(index_path, "r") as f:
            data = json.load(f)
        old_hash = data.get("hash")
    except (json.JSONDecodeError, AttributeError):
        old_hash = None
    if old_hash == new_hash:
        print("index.json ist aktuell")
    else:
        with open(index_path, "w") as f:
            json.dump({"hash": new_hash, "plugins": plugins}, f, indent=2)
        print("index.json wurde aktualisiert")
else:
    with open(index_path, "w") as f:
        json.dump({"hash": new_hash, "plugins": plugins}, f, indent=2)
    print("index.json wurde erstellt")
