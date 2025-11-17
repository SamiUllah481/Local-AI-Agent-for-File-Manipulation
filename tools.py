"""
tools.py

Shared utilities for the local AI agent:
- File/folder search
- Text replace in files
- CSV/Excel modification with a Pandas agent (Ollama)
- GitHub push utilities

These functions are imported by googlemain.py which provides the CLI menu.
"""

from typing import List, Optional
import os
import json
import fnmatch
import pandas as pd

# LangChain / Ollama (local LLM) for the Pandas agent
from langchain_community.llms import Ollama
from langchain_experimental.agents import create_pandas_dataframe_agent

# GitHub API
from github import Github


# ------------------------------
# File search helpers
# ------------------------------
def default_search_roots() -> List[str]:
    """Return a conservative set of default search roots on Windows.

    You can override by setting the SEARCH_ROOTS env var to a semicolon-separated list of absolute paths.
    """
    env = os.environ.get("SEARCH_ROOTS")
    if env:
        roots = [p.strip().strip('"') for p in env.split(";") if p.strip()]
        return [os.path.abspath(p) for p in roots if os.path.exists(p)]

    roots: List[str] = []
    home = os.path.expanduser("~")
    for sub in ("Desktop", "Documents", "Downloads"):
        p = os.path.join(home, sub)
        if os.path.isdir(p):
            roots.append(p)
    # Include current workspace
    try:
        cwd = os.path.abspath(os.getcwd())
        roots.append(cwd)
    except Exception:
        pass
    # Add other drives if present
    for drive in ("D:\\", "E:\\"):
        if os.path.isdir(drive):
            roots.append(drive)
    # De-dup, preserve order
    seen = set()
    uniq: List[str] = []
    for r in roots:
        if r not in seen:
            uniq.append(r)
            seen.add(r)
    return uniq


def find_paths_by_name(
    name_query: str,
    extensions: Optional[List[str]] = None,
    max_results: int = 25,
    roots: Optional[List[str]] = None,
) -> List[str]:
    """Search for files or folders by fuzzy name across configured roots.

    - name_query: pattern like "notes*" or "report.xlsx" (case-insensitive)
    - extensions: if provided, only return files with these extensions (e.g., [".txt", ".csv"]).
    - Will return both files and directories if extensions is None.
    """
    patterns = [name_query]
    if not any(ch in name_query for ch in "*?["):
        patterns.append(f"*{name_query}*")

    roots = roots or default_search_roots()
    results: List[str] = []
    lowered_exts = {e.lower() for e in (extensions or [])}

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            # Directories
            if not extensions:
                for d in dirnames:
                    dn = d.lower()
                    if any(fnmatch.fnmatch(dn, p.lower()) for p in patterns):
                        results.append(os.path.join(dirpath, d))
                        if len(results) >= max_results:
                            return results

            # Files
            for f in filenames:
                fn = f.lower()
                if any(fnmatch.fnmatch(fn, p.lower()) for p in patterns):
                    full = os.path.join(dirpath, f)
                    if extensions and os.path.splitext(f)[1].lower() not in lowered_exts:
                        continue
                    results.append(full)
                    if len(results) >= max_results:
                        return results
    return results


def search_paths(name_query: str, extensions_json: str = "", max_results: int = 10) -> str:
    """Search for files or folders by fuzzy name across configured roots.

    Returns a JSON string with key: results: [paths]
    """
    try:
        exts = json.loads(extensions_json) if extensions_json else []
    except Exception:
        exts = []
    results = find_paths_by_name(name_query, exts or None, max_results=max_results)
    return json.dumps({"results": results})


# ------------------------------
# Text file operations
# ------------------------------
def replace_in_text_file(file_path: str, find_text: str, replace_text: str, make_backup: bool = True) -> str:
    """Replace occurrences of find_text with replace_text in a UTF-8 text file. Creates .bak if make_backup is True."""
    if not os.path.isfile(file_path):
        return f"File not found: {file_path}"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if make_backup:
            with open(file_path + ".bak", 'w', encoding='utf-8') as b:
                b.write(content)
        new_content = content.replace(find_text, replace_text)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Replaced {content.count(find_text)} occurrence(s) in {file_path}. Backup: {make_backup}"
    except Exception as e:
        return f"Error updating file {file_path}: {e}"


# ------------------------------
# Tabular ops (CSV/Excel) with Pandas and Ollama
# ------------------------------
def setup_dummy_csv(file_path: str) -> None:
    """Create a small dummy CSV if the path does not exist (for quick demos)."""
    if not os.path.exists(file_path):
        data = {
            'OrderID': [101, 102, 103, 104, 105],
            'Product': ['Laptop', 'Monitor', 'Mouse', 'Keyboard', 'Webcam'],
            'Price': [1200, 300, 25, 75, 50],
            'Status': ['Shipped', 'Pending', 'Shipped', 'Pending', 'Delivered'],
        }
        pd.DataFrame(data).to_csv(file_path, index=False)


def run_pandas_agent(file_path: str, model: str = "llama3.2:3b") -> None:
    """Run a Pandas agent (LangChain + Ollama) to modify a CSV via natural language.

    Includes guard rails and fallbacks to handle small-model formatting issues.
    """
    # Initialize LLM
    try:
        llm = Ollama(temperature=0, model=model)
    except Exception as e:
        print(f"Error initializing Ollama: {e}")
        return

    # Load DataFrame (create dummy if missing)
    setup_dummy_csv(file_path)
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV file at {file_path}: {e}")
        return

    print("\n--- Original DataFrame Head ---")
    print(df.head())
    print("-----------------------------")

    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        allow_dangerous_code=True,
    )

    ai_instruction = (
        "Find 'notes' column and write 'pending' in it. "
        "After the modification, print the resulting DataFrame's head."
    )
    print(f"\n>>> Running Instruction: '{ai_instruction}'")

    # Keep a copy to detect no-op
    df_original = df.copy()

    try:
        result = agent.invoke({"input": ai_instruction})

        # If DF didn't change, attempt simple fallbacks
        if df.equals(df_original):
            print("\n⚠️ DataFrame was not modified by agent. Attempting fallback...")
            result_str = str(result)

            # Direct fallback for known instruction
            try:
                print("Executing: df['Notes'] = 'pending'")
                df['Notes'] = 'pending'
            except Exception as e:
                # Generic pattern-based extraction (best-effort)
                import re
                patterns = [
                    r"df\['(\w+)'\]\s*=\s*'(\w+)'",
                    r"df\.loc\([^\)]*\)\s*=\s*.+",
                    r"df\.loc\[[^\]]+\]\s*=\s*.+",
                ]
                executed = False
                for pattern in patterns:
                    matches = re.findall(pattern, result_str)
                    if matches:
                        try:
                            if isinstance(matches[0], tuple) and len(matches[0]) == 2:
                                col, val = matches[0]
                                print(f"Executing: df['{col}'] = '{val}'")
                                df[col] = val
                                executed = True
                                break
                        except Exception:
                            continue
                if not executed:
                    print("❌ Could not extract or execute pandas code from agent output.")
                    return

        # Persist
        df.to_csv(file_path, index=False)
        print(f"\n✅ Modification complete and file saved to {file_path}!")
        print("\n--- Final Saved DataFrame Head ---")
        print(pd.read_csv(file_path).head())

    except Exception as e:
        # Handle frequent small-model formatting failures (ReAct parse errors)
        error_msg = str(e)
        print(f"\n⚠️ Agent error: {error_msg[:200]}...")
        if "Could not parse LLM output" in error_msg or "is not a valid tool" in error_msg:
            import re
            match = re.search(r"`(df\.loc\[[^\`]+\])\s*(\*=|=)\s*([^\`]+)`", error_msg)
            if match:
                try:
                    code = f"{match.group(1)} {match.group(2)} {match.group(3)}"
                    print(f"Executing extracted code: {code}")
                    exec(code)
                    df.to_csv(file_path, index=False)
                    print(f"\n✅ Modification complete and file saved to {file_path} (via fallback)!")
                    print("\n--- Final Saved DataFrame Head ---")
                    print(pd.read_csv(file_path).head())
                    return
                except Exception as fb_e:
                    print(f"Fallback execution failed: {fb_e}")
        print("❌ Unhandled agent error. Try option 3 instead.")


def modify_tabular_file(file_path: str, instruction: str) -> str:
    """Use a Pandas Code Agent with Ollama to modify a CSV/XLSX per instruction. Saves in-place.

    Accepts clear instructions like: "Set Status='Closed' where OrderID==105" or
    "Increase Price by 10% where Status=='Pending'".
    """
    if not os.path.isfile(file_path):
        return f"File not found: {file_path}"
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        return f"Unsupported file type: {ext}. Only .csv, .xlsx, .xls supported."

    try:
        # Smaller model for general compatibility (adjust if you have more RAM)
        llm = Ollama(temperature=0, model="llama3.2:1b")
    except Exception as e:
        return f"Error initializing Ollama: {e}"

    # Load DataFrame
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            import pandas as _pd
            df = _pd.read_excel(file_path)
    except Exception as e:
        return f"Error reading {file_path}: {e}"

    agent = create_pandas_dataframe_agent(llm, df, verbose=True, allow_dangerous_code=True)
    try:
        agent.invoke({"input": instruction})
        if ext == ".csv":
            df.to_csv(file_path, index=False)
        else:
            with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
                df.to_excel(writer, index=False)
        return f"✅ Updated and saved: {file_path}"
    except Exception as e:
        # Fallback: parse common df.loc assignment patterns
        error_msg = str(e)
        if "Could not parse LLM output" in error_msg and "df.loc[" in error_msg:
            import re
            match = re.search(r"`(df\.loc\[[^\`]+\])\s*=\s*([^\`]+)`", error_msg)
            if match:
                try:
                    code = f"{match.group(1)} = {match.group(2)}"
                    exec(code)
                    if ext == ".csv":
                        df.to_csv(file_path, index=False)
                    else:
                        with pd.ExcelWriter(file_path, engine="openpyxl", mode="w") as writer:
                            df.to_excel(writer, index=False)
                    return f"✅ Updated and saved (via fallback): {file_path}"
                except Exception as fb_e:
                    return f"Error in fallback execution: {fb_e}"
        return f"Error modifying file via agent: {e}"


# ------------------------------
# GitHub operations
# ------------------------------
def push_folder_to_github(
    repo_name: str,
    local_folder_path: str,
    commit_message: str,
    create_if_missing: bool = True,
) -> None:
    """Push all text files from a local folder to a GitHub repo.

    Requires environment variable GITHUB_TOKEN to be set.
    """
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Please set it to your Personal Access Token.")
        return

    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    try:
        repo = user.get_repo(repo_name)
        print(f"Successfully connected to repo: {repo.full_name}")
    except Exception:
        if create_if_missing:
            try:
                repo = user.create_repo(repo_name, private=False)
                print(f"Created new repository: {repo.full_name}")
            except Exception as e:
                print(f"Error: Could not access or create repo '{repo_name}'. Details: {e}")
                return
        else:
            print(f"Error: Repo '{repo_name}' not found and create_if_missing is False.")
            return

    folder_path = os.path.abspath(local_folder_path)
    if not os.path.isdir(folder_path):
        print(f"Error: Local folder not found at {folder_path}")
        return

    # Files and directories to ignore (similar to .gitignore)
    ignore_patterns = {
        '.env', '.env.local', '.env.*.local',
        'venv', '.venv', 'env', '.env',
        '__pycache__', '*.pyc', '*.pyo', '*.pyd',
        'node_modules', '.git', '.vscode', '.idea',
        '*.log', '*.bak', '*.swp', '*.tmp',
        '.DS_Store', 'Thumbs.db'
    }
    
    def should_ignore(path: str, name: str) -> bool:
        """Check if file/folder should be ignored."""
        # Ignore by directory name
        path_parts = path.split(os.sep)
        if any(part in ignore_patterns for part in path_parts):
            return True
        # Ignore by file name or pattern
        if name in ignore_patterns:
            return True
        # Ignore by extension pattern (*.pyc, etc.)
        for pattern in ignore_patterns:
            if pattern.startswith('*') and name.endswith(pattern[1:]):
                return True
        return False

    print(f"Starting push from '{folder_path}' to '{repo_name}'...")
    print(f"Ignoring: .env, venv, __pycache__, node_modules, .git, and other common files")
    
    for root, dirs, files in os.walk(folder_path):
        # Filter out ignored directories to prevent walking into them
        dirs[:] = [d for d in dirs if not should_ignore(root, d)]
        
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            github_path = os.path.relpath(local_file_path, folder_path).replace("\\", "/")
            
            # Skip ignored files
            if should_ignore(local_file_path, file_name):
                print(f"Ignoring: {github_path}")
                continue

            # Read as text; skip binary for simplicity
            try:
                with open(local_file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except Exception:
                print(f"Skipping non-text or unreadable file: {local_file_path}")
                continue

            try:
                # Update existing file
                contents = repo.get_contents(github_path)
                repo.update_file(contents.path, commit_message, content, contents.sha)
                print(f"Updated file: {github_path}")
            except Exception as get_error:
                # Create if missing (404)
                if "404" in str(get_error) or "empty" in str(get_error).lower():
                    try:
                        repo.create_file(github_path, commit_message, content)
                        print(f"Created file: {github_path}")
                    except Exception as create_error:
                        print(f"Error creating file {github_path}: {create_error}")
                else:
                    print(f"Error processing file {github_path}: {get_error}")

    print(f"\n✅ Successfully pushed files from '{local_folder_path}' to '{repo_name}'.")


def find_folder_and_push_to_github(folder_query: str, repo_name: str, commit_message: str) -> None:
    """Find a local folder by name (fuzzy) and push it to GitHub."""
    matches = find_paths_by_name(folder_query, extensions=None, max_results=5)
    dirs = [m for m in matches if os.path.isdir(m)]
    if not dirs:
        print(f"No folders found matching '{folder_query}'.")
        return
    target = dirs[0]
    print(f"Found folder: {target}")
    push_folder_to_github(repo_name, target, commit_message)
