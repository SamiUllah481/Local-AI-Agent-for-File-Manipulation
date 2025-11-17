"""
Push CI/CD configuration and updates to GitHub repository.
"""
import os
from dotenv import load_dotenv
from github import Github

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = "SamiUllah481/Local-AI-Agent-for-File-Manipulation"

print(f"Connecting to GitHub repository: {REPO_NAME}")
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Files to push with commit messages
files_to_push = {
    ".github/workflows/ci.yml": {
        "message": "Add CI/CD pipeline with automated testing and linting",
        "local_path": ".github/workflows/ci.yml"
    },
    ".github/workflows/dependencies.yml": {
        "message": "Add weekly dependency security audit workflow",
        "local_path": ".github/workflows/dependencies.yml"
    },
    ".gitignore": {
        "message": "Add .gitignore to protect sensitive files and environment",
        "local_path": ".gitignore"
    },
    "README.md": {
        "message": "Add CI/CD status badges and Python version requirements",
        "local_path": "README.md"
    }
}

print(f"\n{'='*60}")
print("Pushing CI/CD configuration to GitHub...")
print(f"{'='*60}\n")

for github_path, info in files_to_push.items():
    try:
        # Read local file
        with open(info["local_path"], 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            # Try to get existing file
            existing_file = repo.get_contents(github_path)
            # Update if exists
            repo.update_file(
                github_path,
                info["message"],
                content,
                existing_file.sha
            )
            print(f"✅ Updated: {github_path}")
        except:
            # Create if doesn't exist
            repo.create_file(
                github_path,
                info["message"],
                content
            )
            print(f"✅ Created: {github_path}")
        
        print(f"   Message: {info['message']}")
        
    except Exception as e:
        print(f"❌ Error with {github_path}: {e}")

print(f"\n{'='*60}")
print("CI/CD setup complete! 🎉")
print(f"{'='*60}")
print("\nNext steps:")
print("1. Go to: https://github.com/SamiUllah481/Local-AI-Agent-for-File-Manipulation/actions")
print("2. You'll see the CI workflow running automatically")
print("3. Green checkmark = all tests passed ✅")
print("4. Red X = tests failed, click to see details ❌")
