from pathlib import Path

import shutil
import sys
import json

from configure import configure_ocr_model


working_dir = Path(__file__).parent
install_path = working_dir / Path("install")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.1.3"

def load_json_file(path): s = open(path, 'r', encoding='utf-8').read() try: return json.loads(s) except json.JSONDecodeError as e: # Print precise diagnostics and a snippet around the error to CI logs pos = e.pos line = e.lineno col = e.colno print(f"ERROR: JSON decode error parsing {path}: {e.msg} at line {line} column {col} (pos {pos})", file=sys.stderr) start = max(0, pos - 120) end = min(len(s), pos + 120) # show the snippet with the error location marker snippet = s[start:end] print("------ file snippet (context) ------", file=sys.stderr) print(snippet, file=sys.stderr) # show pointer line under snippet when possible pointer_index = pos - start print(" " * max(0, pointer_index) + "^", file=sys.stderr) raise SystemExit(1)
def install_deps():
    if not (working_dir / "deps" / "bin").exists():
        print("Please download the MaaFramework to \"deps\" first.")
        print("请先下载 MaaFramework 到 \"deps\"。")
        sys.exit(1)

    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        working_dir / "deps" / "share" / "MaaAgentBinary",
        install_path / "MaaAgentBinary",
        dirs_exist_ok=True,
    )


def install_resource():

    configure_ocr_model()

    shutil.copytree(
        working_dir / "assets" / "resource",
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        working_dir / "assets" / "interface.json",
        install_path,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)

    interface["version"] = version

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    shutil.copy2(
        working_dir / "README.md",
        install_path,
    )
    shutil.copy2(
        working_dir / "LICENSE",
        install_path,
    )

def install_agent():
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )

if __name__ == "__main__":
    install_deps()
    install_resource()
    install_chores()
    install_agent()

    print(f"Install to {install_path} successfully.")