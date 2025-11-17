# Local AI Agent with Ollama

[![CI - Test and Validate](https://github.com/SamiUllah481/Local-AI-Agent-for-File-Manipulation/actions/workflows/ci.yml/badge.svg)](https://github.com/SamiUllah481/Local-AI-Agent-for-File-Manipulation/actions/workflows/ci.yml)
[![Python 3.9-3.14](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project demonstrates a local AI agent using Ollama to perform various operations on local files and GitHub repositories.

## 📁 Project Structure

```
Local AI Agent/
├── googlemain.py       # CLI entrypoint - menu and user interaction
├── tools.py            # Reusable utilities - all core functions
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .env               # Environment variables (create this)
```

**Clean Architecture:**
- `googlemain.py` - Lightweight CLI menu that handles user input/output
- `tools.py` - All reusable functions (search, modify, GitHub operations)

## 🚀 Setup

### 1. Install Ollama
Download and install from https://ollama.ai/

Pull a model (recommended: `llama3.2:3b` for balance of speed/quality):
```powershell
ollama pull llama3.2:3b
```

### 2. Install Python Dependencies
```powershell
# Activate virtual environment (if using one)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Set up GitHub Token (for GitHub operations)
Create a `.env` file in the project root:
```
GITHUB_TOKEN=your_github_personal_access_token_here
```

Or set it in PowerShell:
```powershell
$env:GITHUB_TOKEN="your_token_here"
```

## 💻 Usage

Run the main script:
```powershell
python googlemain.py
```

You'll see a menu with 4 options:

### Option 1: Modify CSV Files
- Modify CSV files using natural language with Pandas agent
- Example: "Increase Price by 10% where Status is Pending"
- Uses Ollama (llama3.2:3b) with robust fallbacks for parsing errors
- Automatically creates backup and saves changes

### Option 2: Push Folder to GitHub
- Push entire folder contents to a GitHub repository
- Creates repository if it doesn't exist
- Updates existing files or creates new ones
- Requires GITHUB_TOKEN environment variable

### Option 3: Replace Text in Files
- Search for files by name or pattern
- Find and replace text with automatic .bak backup
- Supports multiple file types (.txt, .py, .md, .json, .csv)
- Interactive file selection from search results

### Option 4: Find Folder and Push to GitHub
- Search for a folder by name or pattern
- Push it to GitHub in one step
- Combines fuzzy search + GitHub push functionality
- Creates repository if missing

## 🔧 Features

### File Operations
- **Fuzzy search** across configurable roots (Desktop, Documents, Downloads, workspace, D:\, E:\)
- **Text replacement** with automatic `.bak` backup
- **CSV/Excel modification** via natural language with Ollama

### AI-Powered Modifications
- Uses LangChain's Pandas DataFrame agent
- Automatic fallbacks for small model parsing errors
- Direct code extraction and execution when agent output is malformed

### GitHub Integration
- Push folders to new or existing repositories
- Automatic repository creation
- Handles file updates and creation
- Skips binary/unreadable files

## ⚙️ Configuration

### Search Roots
Override default search locations via environment variable:
```powershell
$env:SEARCH_ROOTS="C:\Projects;D:\Documents"
```

### Model Selection
Edit `tools.py` to change models:
- `run_pandas_agent()` uses `llama3.2:3b` (recommended)
- `modify_tabular_file()` uses `llama3.2:1b` (lightweight)

## 🐛 Troubleshooting

### "Could not parse LLM output" errors
- **Normal behavior** with small models (llama3.2:1b, llama3.2:3b)
- Fallback automatically extracts and executes pandas code
- For better reliability, use larger models if you have RAM

### "Error initializing Ollama"
- Ensure Ollama is running: Check http://localhost:11434
- Restart Ollama: `ollama serve`
- Verify model is pulled: `ollama list`

### Memory errors with llama3.1:8b
- Use smaller models: `llama3.2:3b` (recommended) or `llama3.2:1b`
- Close other applications to free RAM

### GitHub push fails
- Check `GITHUB_TOKEN` is set: `echo $env:GITHUB_TOKEN`
- Verify token has `repo` scope in GitHub settings
- Ensure token is valid and not expired

### File permission errors
- Close CSV/Excel files before modifying
- Run PowerShell as Administrator if needed

### Python 3.14 deprecation warnings
- Safe to ignore Pydantic V1 warnings
- No impact on functionality

## 📦 Dependencies

Core packages:
- `langchain` (1.0.5) - Framework for LLM applications
- `langchain-community` (0.4.1) - Community LangChain integrations
- `langchain-experimental` (0.4.0) - Experimental features (Pandas agent)
- `ollama` - Python client for Ollama
- `pandas` (2.3.3) - Data manipulation
- `openpyxl` (3.1.5) - Excel file support
- `PyGithub` (2.8.1) - GitHub API client
- `python-dotenv` - Environment variable management
- `tabulate` (0.9.0) - Pretty-print tables

## 🎯 Model Recommendations

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `llama3.2:1b` | 1B params | Fast | Basic | Low RAM systems |
| `llama3.2:3b` | 3B params | Medium | Good | **Recommended** balance |
| `llama3.1:8b` | 8B params | Slow | Best | High RAM systems (16GB+) |

## 🔮 Future Improvements

- [ ] Migrate to `langchain-ollama` package (current uses deprecated `langchain_community.llms.Ollama`)
- [ ] Support for binary file uploads to GitHub
- [ ] Interactive agent mode with conversation history
- [ ] Batch file operations
- [ ] Custom instruction templates for common tasks

## 📝 Known Issues

1. **Small model formatting issues**: llama3.2:1b and llama3.2:3b sometimes produce invalid ReAct output. Fallbacks handle this gracefully.
2. **GitHub binary files**: Currently skips non-text files. Could be extended with base64 encoding.
3. **Agent "Final Answer" without execution**: Agent returns answer but doesn't modify DataFrame. Fallback detects this and executes directly.

## 🤝 Contributing

This is a personal project demonstrating local AI agent capabilities. Feel free to fork and adapt for your needs!

## 📄 License

Free to use and modify. No warranty provided.
