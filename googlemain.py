"""
googlemain.py

CLI entrypoint for the local AI agent. This file provides the menu and orchestrates
calls into functions provided by tools.py. Keep this file light and focused on UX,
while reusable logic lives in tools.py.

Features:
1. Modify CSV files - Use Pandas agent with Ollama for natural language modifications
2. Push folder to GitHub - Push local folder contents to a GitHub repository
3. Replace text in files - Find and replace text with automatic backup
4. Find folder and push to GitHub - Search for folder by name and push in one step
"""

# --- Imports ---
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file (e.g., GITHUB_TOKEN)
load_dotenv()

# Import reusable utilities from tools.py
from tools import (
    run_pandas_agent,
    push_folder_to_github,
    find_folder_and_push_to_github,
    search_paths,
    replace_in_text_file,
    modify_tabular_file,
)


# ==============================================================================
# SECTION 1: PANDAS AGENT - CSV MODIFICATION
# ==============================================================================
def run_pandas_main():
    """Main entry point for the Pandas agent."""
    print("\n--- Pandas CSV Agent ---")
    file_path = input("Enter the path to your CSV file (e.g., sales_data.csv): ").strip()
    if not file_path:
        print("No file path entered. Using 'default_sales.csv'.")
        file_path = "default_sales.csv"
        
    # Delegate to tools.py
    run_pandas_agent(file_path)


# ==============================================================================
# SECTION 2: GITHUB FOLDER PUSH
# ==============================================================================
def run_github_main():
    """Main entry point for the GitHub utility."""
    print("\n--- GitHub Folder Push Utility ---")
    repo_name = input("Enter your GitHub repository name (e.g., 'my-project'): ").strip()
    local_folder_path = input("Enter the path to the local folder to push: ").strip()
    commit_message = input("Enter your commit message (e.g., 'Automated file update'): ").strip()

    if not repo_name or not local_folder_path or not commit_message:
        print("Error: All fields (repo, folder path, commit message) are required.")
        return
        
    # Delegate to tools.py
    push_folder_to_github(repo_name, local_folder_path, commit_message)


# ==============================================================================
# SECTION 3: TEXT FILE REPLACE
# ==============================================================================
def run_text_replace_main():
    """Find and replace text in files with automatic backup."""
    print("\n--- Replace Text in Files ---")
    q = input("File name or pattern to search: ").strip()
    
    # Search for text files
    res = json.loads(search_paths(q, json.dumps([".txt", ".py", ".md", ".json", ".csv"]), 10))
    candidates = res.get("results", [])
    
    if not candidates:
        print("No matching files found.")
        return
    
    print("Matches:")
    for i, p in enumerate(candidates, 1):
        print(f"  {i}. {p}")
    
    idx = input("Pick file number: ").strip()
    try:
        path = candidates[int(idx)-1]
    except Exception:
        print("Invalid selection.")
        return
    
    find_text = input("Text to find: ").strip()
    replace_text = input("Replace with: ").strip()
    
    # Delegate to tools.py
    print(replace_in_text_file(path, find_text, replace_text, True))


# ==============================================================================
# MAIN INTERACTIVE MENU
# ==============================================================================
if __name__ == "__main__":
    # Check for required environment variables
    if not os.environ.get('GITHUB_TOKEN'):
        print("Warning: 'GITHUB_TOKEN' environment variable is not set.")
        print("The GitHub utility will fail without it.")
    else:
        print("Ollama is assumed to be running locally on http://localhost:11434") 

    print("\n=== AI Agent Tools ===")
    print("What would you like to do?")
    print("  1: Modify CSV files (Pandas Agent with Ollama)")
    print("  2: Push folder to GitHub")
    print("  3: Replace text in files")
    print("  4: Find folder and push to GitHub")
    print("  q: Quit")
    
    choice = input("\nEnter 1, 2, 3, 4, or q: ").strip().lower()
    
    if choice == '1':
        run_pandas_main()
    elif choice == '2':
        run_github_main()
    elif choice == '3':
        run_text_replace_main()
    elif choice == '4':
        print("\n--- Find and Push Folder to GitHub ---")
        folder_query = input("Folder name or pattern to search: ").strip()
        repo_name = input("Target GitHub repo name (will create if missing): ").strip()
        commit_message = input("Commit message: ").strip() or "Automated update"
        if folder_query and repo_name:
            find_folder_and_push_to_github(folder_query, repo_name, commit_message)
        else:
            print("Folder query and repo name are required.")
    elif choice == 'q':
        print("Exiting. Goodbye!")
        sys.exit()
    else:
        print("Invalid choice. Please run the script again.")
