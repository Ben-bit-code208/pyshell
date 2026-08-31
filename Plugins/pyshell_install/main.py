import json
import os
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_DIR = os.path.dirname(PLUGIN_DIR)
SOURCES_FILE = os.path.join(PLUGIN_DIR, "sources.json")
DEFAULT_SOURCES = {"sources": ["https://api.github.com/search/repositories?q={query}"]}


def make_new_source_file():
    with open(SOURCES_FILE, "w") as f:
        json.dump(DEFAULT_SOURCES, f, indent=2)
    print("sources.json wurde erstellt")


def load_sources():
    try:
        with open(SOURCES_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("keine sources.json gefunden, erstelle neue ...")
        make_new_source_file()
        return DEFAULT_SOURCES["sources"]
    raw = data.get("sources", [])
    return list(raw.values()) if isinstance(raw, dict) else raw


def fetch_search(source, query):
    url = source.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": "pyshell-install"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["items"]


def pick_repo(items):
    for i, item in enumerate(items, 1):
        desc = item.get("description") or "keine Beschreibung"
        print(f"[{i}] {item['full_name']} - {desc}")
    try:
        choice = int(input("Welches Repo (Nummer)? "))
    except ValueError:
        print("Ungültige Eingabe")
        return None
    if not (1 <= choice <= len(items)):
        print("Nummer außerhalb des Bereichs")
        return None
    return items[choice - 1]


def download_repo(repo, target_dir):
    name = repo["name"]
    full_name = repo["full_name"]
    zip_path = None
    for branch in ("main", "master"):
        url = f"https://github.com/{full_name}/archive/refs/heads/{branch}.zip"
        print(f"Downloade {full_name} (Branch: {branch}) ...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pyshell-install"})
            with urllib.request.urlopen(req) as r, tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                shutil.copyfileobj(r, tmp)
                zip_path = tmp.name
        except urllib.error.HTTPError:
            continue
        break
    if zip_path is None:
        print("Kein main/master Branch gefunden")
        return

    with zipfile.ZipFile(zip_path) as z:
        top = z.namelist()[0].split("/")[0]
        z.extractall(target_dir)
    os.remove(zip_path)

    src = os.path.join(target_dir, top)
    dst = os.path.join(target_dir, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    print(f"Fertig: {dst}")


def install(install):
    query = install[len("install"):].strip()
    if not query:
        print("Benutzung: install <suchbegriff>")
        return

    all_items = []
    for source in load_sources():
        try:
            all_items.extend(fetch_search(source, query))
        except Exception as e:
            print("Fehler bei Quelle:", source, "-", e)

    if not all_items:
        print("Keine Ergebnisse gefunden")
        return

    repo = pick_repo(all_items[:10])
    if repo is None:
        return
    download_repo(repo, PLUGINS_DIR)
