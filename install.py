"""One-time setup: Python environment, Rhubarb lip-sync, config.json, and the Claude Code skills.

    python install.py            (Python 3.10+; standard library only)
    python install.py --force    also replace skills of the same name that this repo didn't install

Safe to re-run. Your data (config.json, my/, jobs/, reels/) is never touched or committed.
"""
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent
VENV = REPO / ".venv"
PY = VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
RHUBARB = "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-{}.zip"
MARK = "<!-- installed by MTP-clone-YT-Automation-pipeline -->"
SKILLS = Path.home() / ".claude" / "skills"


def step(msg):
    print(f"\n== {msg}", flush=True)


def main():
    if sys.version_info < (3, 10):
        sys.exit("Python 3.10 or newer is needed.")

    step("Python environment (.venv)")
    if not PY.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    subprocess.run([str(PY), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run([str(PY), "-m", "pip", "install", "-q", "-r", str(REPO / "requirements.txt")], check=True)

    step("Rhubarb Lip Sync 1.14.0 (exact mouth shapes from the voice)")
    tools = REPO / "tools" / "rhubarb"
    if any(p.stem == "rhubarb" for p in tools.glob("*/rhubarb*")):
        print("already installed")
    else:
        name = {"win32": "Windows", "darwin": "macOS"}.get(sys.platform, "Linux")
        tools.mkdir(parents=True, exist_ok=True)
        zpath = tools / "rhubarb.zip"
        urllib.request.urlretrieve(RHUBARB.format(name), zpath)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(tools)
        zpath.unlink()
        for exe in tools.glob("*/rhubarb"):
            exe.chmod(0o755)
        if sys.platform == "darwin" and platform.machine() == "arm64":
            print("Apple Silicon: Rhubarb runs through Rosetta (softwareupdate --install-rosetta) if it fails to start.")

    step("config.json")
    cfg = REPO / "config.json"
    if cfg.exists():
        print("kept your existing config.json")
    else:
        shutil.copy(REPO / "config.example.json", cfg)
        print(f"created {cfg} - open it and fill in your channel, name and voice")

    step(f"Claude Code skills -> {SKILLS}")
    force = "--force" in sys.argv
    for src in sorted((REPO / "skills").glob("*/SKILL.md")):
        dest = SKILLS / src.parent.name / "SKILL.md"
        if dest.exists() and MARK not in dest.read_text(encoding="utf-8") and not force:
            print(f"SKIPPED {src.parent.name}: you already have a skill with that name (re-run with --force to replace it)")
            continue
        text = src.read_text(encoding="utf-8").replace("{{REPO}}", REPO.as_posix()).replace("{{PY}}", PY.as_posix())
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text + f"\n{MARK}\n", encoding="utf-8")
        print(f"installed {src.parent.name}")

    step("Self-tests")
    scripts = REPO / "skills" / "anime-talking-short" / "scripts"
    subprocess.run([str(PY), str(scripts / "render.py"), "--selftest"], check=True)
    subprocess.run([str(PY), str(scripts / "sound.py")], check=True)

    print(f"""
Done. Next (README has the details):
  1. Fill in {cfg.name}
  2. Put your character sheet at my/sheet.png + my/sheet.json, poses in my/poses/, sets in my/backgrounds/, then build:
     {PY.as_posix()} skills/anime-talking-short/scripts/build_poses.py my/sheet.png my/poses my/backgrounds my/built
  3. YouTube login: save client_secret.json to ~/.youtube-upload/, then
     {PY.as_posix()} skills/youtube-upload/scripts/upload.py --auth-only
  4. (Optional) Instagram token to ~/.instagram-upload/token.txt
  5. Restart Claude Code and type: /script-to-short <your rough script>""")


if __name__ == "__main__":
    main()
