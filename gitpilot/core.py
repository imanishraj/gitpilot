import os
import sys
import json
import subprocess
import requests
from pathlib import Path

# ─────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────
CONFIG_FILE  = Path.home() / ".gitpilot_config.json"
OLLAMA_MODEL = "granite3.3:8b"
OLLAMA_URL   = "http://localhost:11434/api/generate"

SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv",
             "venv", "dist", "build", ".next", ".idea"}
CODE_EXTS  = {".py", ".js", ".ts", ".jsx", ".tsx",
              ".html", ".css", ".java", ".go", ".md",
              ".json", ".txt", ".env.example"}


# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    CONFIG_FILE.chmod(0o600)


def setup_config(cfg: dict) -> dict:
    changed = False
    header("GitHub Setup")
    print("  Your credentials are saved locally at:")
    print(f"  {CONFIG_FILE}")
    print("  They are NEVER stored inside your project.\n")

    if not cfg.get("github_token"):
        print("  Get your token:")
        print("  github.com → Settings → Developer Settings")
        print("  → Personal Access Tokens → Tokens (classic)")
        print("  → Generate new token → check 'repo' scope\n")
        cfg["github_token"] = input("  Paste GitHub token: ").strip()
        changed = True

    if not cfg.get("github_username"):
        cfg["github_username"] = input("  GitHub username  : ").strip()
        changed = True

    if changed:
        save_config(cfg)
        print("\n  Credentials saved!\n")

    return cfg


def reset_config():
    cfg = load_config()
    cfg.pop("github_token", None)
    cfg.pop("github_username", None)
    save_config(cfg)
    print("  Credentials cleared. Run gitpilot again to re-enter.")


# ─────────────────────────────────────────
#  UTILS
# ─────────────────────────────────────────

def run(cmd, cwd=None):
    r = subprocess.run(
        cmd, shell=True, cwd=cwd or os.getcwd(),
        capture_output=True, text=True
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def header(text):
    print(f"\n{'─' * 45}")
    print(f"  {text}")
    print(f"{'─' * 45}")


def ask(prompt, default=None):
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val or default


def confirm(prompt):
    val = input(f"  {prompt} (y/n): ").strip().lower()
    return val in ("y", "yes", "")


def ollama_running() -> bool:
    try:
        requests.get("http://localhost:11434", timeout=3)
        return True
    except Exception:
        return False


def ask_ollama(prompt: str, max_tokens: int = 300) -> str | None:
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": max_tokens}
        }, timeout=180)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception:
        return None


def explain_error(error: str, cmd: str) -> str | None:
    if not ollama_running():
        return None
    print("  Asking Ollama to diagnose the error...")
    prompt = f"""A git command failed.
Command : {cmd}
Error   : {error}

In 3 lines max:
1. What does this error mean in simple words?
2. Exact command to fix it?
Be direct, no fluff."""
    return ask_ollama(prompt, 150)


def safe_run(cmd: str, cwd: str, label: str = "") -> bool:
    code, out, err = run(cmd, cwd)
    if out:
        for line in out.splitlines():
            print(f"  {line}")
    if code != 0:
        error = err or out or "Unknown error"
        print(f"\n  Failed: {error}")
        fix = explain_error(error, cmd)
        if fix:
            print("\n  Ollama diagnosis:\n")
            for line in fix.splitlines():
                print(f"    {line}")
        return False
    return True


def current_branch(cwd: str) -> str:
    _, out, _ = run("git branch --show-current", cwd)
    return out or "main"


def is_git_repo(cwd: str) -> bool:
    code, _, _ = run("git rev-parse --is-inside-work-tree", cwd)
    return code == 0


def ensure_gitignore(path: str):
    gi = Path(path) / ".gitignore"
    if not gi.exists():
        gi.write_text(
            "node_modules/\n__pycache__/\n.env\n.venv/\nvenv/\n"
            "dist/\nbuild/\n*.pyc\n.DS_Store\n"
            "*.wav\n*.mp3\n*.mp4\n*.avi\n*.mkv\n"
            "*.zip\n*.rar\n*.exe\n*.bin\n",
            encoding="utf-8"
        )
        print("  Created .gitignore")


def collect_code(path: str) -> str:
    snippets = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = Path(root) / f
            if fp.suffix.lower() not in CODE_EXTS:
                continue
            rel = fp.relative_to(path)
            try:
                content = fp.read_text(encoding="utf-8", errors="ignore")
                if content.strip():
                    snippets.append(f"### {rel}\n{content[:2000]}")
            except Exception:
                pass
    return "\n\n".join(snippets) or "No code files found."


def generate_readme(code: str, repo_name: str, username: str) -> str:
    print("  Generating README with Ollama...")
    prompt = f"""Write a clean professional README.md for a GitHub project called "{repo_name}".
Based on the code below, include: description, tech stack, features, installation, usage, license (MIT).
Use proper Markdown. Be concise.

CODE:
{code[:4000]}

README.md:"""
    result = ask_ollama(prompt, 1024)
    return result or f"# {repo_name}\n\nA project by {username}.\n\n## License\nMIT"


def generate_commit_msg(cwd: str) -> str:
    _, diff, _   = run("git diff --cached --stat", cwd)
    _, detail, _ = run(
        "git diff --cached -- . "
        "':(exclude)package-lock.json' ':(exclude)*.lock'", cwd
    )
    text = (diff + "\n" + detail)[:2000]
    prompt = f"""Write a short git commit message (max 8 words).
Output ONLY the commit message, nothing else.

Changes:
{text}

Commit message:"""
    msg = ask_ollama(prompt, 50)
    if msg:
        return msg.strip().strip('"').strip("'").split("\n")[0]
    return "Update project files"


# ─────────────────────────────────────────
#  GITHUB API
# ─────────────────────────────────────────

def gh_headers(token: str) -> dict:
    return {"Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"}


def repo_exists(name: str, token: str, username: str) -> bool:
    r = requests.get(
        f"https://api.github.com/repos/{username}/{name}",
        headers=gh_headers(token)
    )
    return r.status_code == 200


def create_repo(name: str, token: str) -> bool:
    r = requests.post(
        "https://api.github.com/user/repos",
        headers=gh_headers(token),
        json={"name": name, "private": False, "auto_init": False}
    )
    return r.status_code in (200, 201)


def remote_url(name: str, token: str, username: str) -> str:
    return f"https://{token}@github.com/{username}/{name}.git"


# ─────────────────────────────────────────
#  FLOWS
# ─────────────────────────────────────────

def flow_push(cwd: str, token: str, username: str):
    header("Push Project to GitHub")

    is_git   = is_git_repo(cwd)
    branch   = current_branch(cwd) if is_git else "main"
    default  = Path(cwd).name.replace(" ", "-").lower()
    repo_name = ask("Repo name", default).replace(" ", "-").lower()

    exists = repo_exists(repo_name, token, username)
    if exists:
        print(f"\n  Repo '{repo_name}' found on GitHub.")
        if is_git and confirm("Push to a different branch?"):
            branch = ask("Branch name", branch)
    else:
        print(f"\n  Repo '{repo_name}' not found — will create it.")

    # README
    use_ollama = ollama_running()
    readme_path = Path(cwd) / "README.md"
    readme_exists = readme_path.exists()

    if readme_exists:
        print(f"\n  README.md already exists in this project.")
        generate = confirm("Overwrite it with a new AI-generated README?")
    else:
        print(f"\n  No README.md found.")
        generate = confirm("Generate one with Ollama?") if use_ollama else False

    if generate:
        if not use_ollama:
            print("  Ollama is offline — cannot generate README.")
        else:
            print("  Reading project files...")
            code = collect_code(cwd)
            print(f"  Collected {len(code)} characters.")
            readme = generate_readme(code, repo_name, username)
            readme_path.write_text(readme, encoding="utf-8")
            print("  README.md written.")
    elif not readme_exists:
        # No readme and user said no — write a minimal one so repo isn't empty
        readme_path.write_text(
            f"# {repo_name}\n\nA project by {username}.\n\n## License\nMIT",
            encoding="utf-8"
        )
        print("  Minimal README.md created.")
    else:
        print("  Keeping existing README.md.")

    if not exists:
        print(f"\n  Creating GitHub repo '{repo_name}'...")
        if not create_repo(repo_name, token):
            print("  Failed to create repo. Check your token.")
            return

    if not is_git:
        print("\n  Initializing git...")
        run("git init", cwd)
        run('git config user.email "gitpilot@local"', cwd)
        run('git config user.name "GitPilot"', cwd)

    ensure_gitignore(cwd)
    run("git add .", cwd)

    _, status, _ = run("git status --porcelain", cwd)
    if status.strip():
        if use_ollama:
            print("\n  Generating commit message...")
            msg = generate_commit_msg(cwd)
        else:
            msg = ask("Commit message", "Initial commit")
        print(f"  Commit: {msg}")
        run(f'git commit -m "{msg}"', cwd)
    else:
        print("\n  Nothing new to commit.")

    url = remote_url(repo_name, token, username)
    run("git branch -M main", cwd)
    run("git remote remove origin", cwd)
    run(f"git remote add origin {url}", cwd)

    print(f"\n  Pushing to origin/{branch}...")
    if branch != "main":
        ok = safe_run(f"git push -u origin HEAD:{branch}", cwd, "push")
    else:
        ok = safe_run("git push -u origin main", cwd, "push")

    if ok:
        print(f"\n  Live at: https://github.com/{username}/{repo_name}/tree/{branch}")


def flow_branch(cwd: str, token: str, username: str):
    header("Create New Branch")
    if not is_git_repo(cwd):
        print("  Not a git repo. Use option 1 first.")
        return
    print(f"  Current branch: {current_branch(cwd)}")
    name = ask("New branch name")
    if not name:
        return
    ok = safe_run(f"git checkout -b {name}", cwd, "branch")
    if ok:
        print(f"  Switched to: {name}")
        if confirm("Push this branch to GitHub now?"):
            run("git add .", cwd)
            _, status, _ = run("git status --porcelain", cwd)
            if status.strip():
                msg = ask("Commit message", f"Init branch {name}")
                run(f'git commit -m "{msg}"', cwd)
            safe_run(f"git push -u origin {name}", cwd, "push")
            repo_name = Path(cwd).name.replace(" ", "-").lower()
            print(f"\n  Branch live: https://github.com/{username}/{repo_name}/tree/{name}")


def flow_pull(cwd: str):
    header("Pull from GitHub")
    if not is_git_repo(cwd):
        print("  Not a git repo.")
        return
    branch = current_branch(cwd)
    print(f"  Current branch: {branch}")
    target = ask("Pull from branch", branch)
    run(f"git branch --set-upstream-to=origin/{target} {target}", cwd)
    ok = safe_run(f"git pull origin {target}", cwd, "pull")
    if ok:
        print(f"  Up to date with origin/{target}")


def flow_switch(cwd: str):
    header("Switch Branch")
    _, branches, _ = run("git branch -a", cwd)
    print("\n  Available branches:\n")
    for b in branches.splitlines():
        print(f"    {b}")
    name = ask("\n  Switch to branch")
    if name:
        safe_run(f"git checkout {name}", cwd, "switch")


def flow_clone(cwd: str, token: str, username: str):
    header("Clone a Repository")

    print("  Clone options:\n")
    print("  1. From your own GitHub repos")
    print("  2. From any GitHub URL\n")

    choice = input("  Choose (1-2): ").strip()

    if choice == "1":
        # List user's repos from GitHub API
        print(f"\n  Fetching your repos from GitHub...")
        r = requests.get(
            "https://api.github.com/user/repos?per_page=50&sort=updated",
            headers=gh_headers(token)
        )
        if r.status_code != 200:
            print("  Failed to fetch repos. Check your token.")
            return

        repos = r.json()
        if not repos:
            print("  No repos found on your GitHub.")
            return

        print(f"\n  Your repos:\n")
        for i, repo in enumerate(repos, 1):
            private = "🔒" if repo.get("private") else "🌐"
            print(f"  {i:2}. {private} {repo['name']}")

        print()
        choice_num = input("  Enter repo number: ").strip()
        try:
            selected = repos[int(choice_num) - 1]
            clone_url = selected["clone_url"].replace(
                "https://", f"https://{token}@"
            )
            repo_name = selected["name"]
        except (ValueError, IndexError):
            print("  Invalid selection.")
            return

    elif choice == "2":
        raw_url = ask("Paste GitHub repo URL")
        if not raw_url:
            return
        # Support both https and git formats
        raw_url = raw_url.strip().rstrip("/")
        if raw_url.endswith(".git"):
            clone_url = raw_url.replace("https://github.com", f"https://{token}@github.com")
        else:
            clone_url = raw_url.replace("https://github.com", f"https://{token}@github.com") + ".git"
        repo_name = raw_url.rstrip("/").split("/")[-1].replace(".git", "")
    else:
        print("  Invalid choice.")
        return

    # Ask where to clone
    default_dest = str(Path(cwd) / repo_name)
    dest = ask("Clone into folder", default_dest).strip()
    dest = dest or default_dest

    if Path(dest).exists():
        print(f"\n  Folder '{dest}' already exists.")
        if not confirm("Clone into it anyway?"):
            return

    print(f"\n  Cloning '{repo_name}' into {dest}...")
    parent = str(Path(dest).parent)
    folder = Path(dest).name
    ok = safe_run(f'git clone "{clone_url}" "{folder}"', parent, "clone")

    if ok:
        print(f"\n  Cloned successfully to: {dest}")

        # Ask if they want to open in VS Code or Cursor
        if confirm("Open in Cursor?"):
            run(f'cursor "{dest}"', cwd)
        elif confirm("Open in VS Code?"):
            run(f'code "{dest}"', cwd)


def flow_status(cwd: str):
    header("Project Status")
    if not is_git_repo(cwd):
        print("  Not a git repo yet.")
        return
    print(f"  Branch: {current_branch(cwd)}\n")
    _, status, _ = run("git status --short", cwd)
    if status:
        print("  Changed files:")
        for line in status.splitlines():
            print(f"    {line}")
    else:
        print("  Working tree clean.")
    _, log, _ = run("git log --oneline -5", cwd)
    if log:
        print("\n  Recent commits:")
        for line in log.splitlines():
            print(f"    {line}")
