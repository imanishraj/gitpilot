import os
import sys
from pathlib import Path
from gitpilot.core import (
    load_config, setup_config, reset_config, ollama_running,
    flow_push, flow_branch, flow_pull, flow_switch, flow_status, flow_clone
)


def main():
    cwd = os.getcwd()

    if "--reset" in sys.argv:
        reset_config()
        return

    if "--version" in sys.argv or "-v" in sys.argv:
        from gitpilot import __version__
        print(f"gitpilot v{__version__}")
        return

    cfg      = load_config()
    cfg      = setup_config(cfg)
    token    = cfg["github_token"]
    username = cfg["github_username"]
    online   = ollama_running()

    print(f"""
╔══════════════════════════════════════════╗
║     GitPilot — your AI git wizard  ✈    ║
╚══════════════════════════════════════════╝
  Project : {Path(cwd).name}
  GitHub  : {username}
  Ollama  : {"running ✓" if online else "offline  (run: ollama serve)"}
""")

    print("  What do you want to do?\n")
    print("  1.  Push project to GitHub  (new or existing repo)")
    print("  2.  Create a new branch")
    print("  3.  Pull latest from GitHub")
    print("  4.  Switch branch")
    print("  5.  Project status")
    print("  6.  Clone a repo to your laptop")
    print("  7.  Reset GitHub credentials")
    print("  0.  Exit\n")

    choice = input("  Choose (0-7): ").strip()

    if   choice == "1": flow_push(cwd, token, username)
    elif choice == "2": flow_branch(cwd, token, username)
    elif choice == "3": flow_pull(cwd)
    elif choice == "4": flow_switch(cwd)
    elif choice == "5": flow_status(cwd)
    elif choice == "6": flow_clone(cwd, token, username)
    elif choice == "7": reset_config()
    elif choice == "0": print("  Bye!")
    else:               print("  Invalid choice.")


if __name__ == "__main__":
    main()
