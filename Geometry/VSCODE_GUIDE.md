# VS Code Setup Guide - Running the Geometry Learning API Server

This guide will help you run and debug the Geometry Learning System directly in Visual Studio Code.

---

## Prerequisites

### 1. Install Python Extension for VS Code

1. Open VS Code
2. Click the **Extensions** icon (or press `Ctrl+Shift+X`)
3. Search for **"Python"**
4. Install the official **Python extension by Microsoft**
5. Restart VS Code if prompted

### 2. Install Dependencies

Open the integrated terminal in VS Code (`Ctrl+` ` or View → Terminal) and run:

```bash
pip install -r requirements.txt
```

---

## Running the API Server in VS Code

### Method 1: Using the Debug Panel (Recommended) 🎯

1. **Open the Debug Panel**
   - Click the **Run and Debug** icon on the left sidebar (or press `Ctrl+Shift+D`)
   - Or go to `View → Run`

2. **Select a Configuration**
   
   At the top of the Debug panel, you'll see a dropdown menu. Choose from:
   
   - **🚀 Run API Server** - Starts the API server on port 17654
   - **🐛 Run API Server (Debug Mode)** - Same but with debug mode enabled
   - **💻 Run CLI (Interactive Learning)** - Runs the CLI interface
   - **✅ Run Test Suite** - Runs all tests
   - **📊 View Database Tables** - Shows database contents
   - **🗂️ Manage Sessions** - Session management utility

3. **Start the Server**
   - Click the **green play button** (▶️) or press `F5`
   - The server will start in the integrated terminal
   - You'll see:
     ```
     ============================================================
     🚀 Geometry Learning API Server
     ============================================================
     📡 Server starting on http://localhost:17654
     🔧 Debug mode: False
     📚 API Documentation: See API_DOCUMENTATION.md
     ============================================================
     ```

4. **Test the Server**
   - Open a new terminal in VS Code (`Ctrl+Shift+` `)
   - Run: `curl http://localhost:17654/api/health`
   - Or open your browser to: `http://localhost:17654/api/health`

5. **Stop the Server**
   - Click the **red stop button** (⏹️) in the debug toolbar
   - Or press `Shift+F5`
   - Or press `Ctrl+C` in the terminal

---

### Method 2: Using the Integrated Terminal

1. **Open Terminal**
   - Press `Ctrl+` ` (backtick)
   - Or go to `View → Terminal`

2. **Navigate to the Project Directory**
   ```bash
   cd c:\Users\lahavor\am\thesis\Geometry
   ```

3. **Run the Server**
   ```bash
   python api_server.py
   ```

4. **Stop the Server**
   - Press `Ctrl+C` in the terminal

---

## Available Run Configurations

When you open the Debug panel (`Ctrl+Shift+D`), you'll see these configurations:

### 🖥️ Servers
- **Run API Server** - Normal mode on port 17654
- **Run API Server (Debug Mode)** - Debug mode with detailed error messages

### 📱 Apps  
- **Run CLI (Interactive Learning)** - Interactive command-line interface

### 🧪 Tests
- **Run Test Suite** - Automated tests to verify everything works

### 🛠️ Utilities
- **View Database Tables** - Browse database contents
- **Manage Sessions** - Create, view, clone, or delete sessions

---

## Debugging the API Server

### Setting Breakpoints

1. Open `api_server.py` in VS Code
2. Click to the left of a line number to set a breakpoint (red dot appears)
3. Run **"Run API Server (Debug Mode)"** configuration
4. When code hits your breakpoint, execution will pause
5. You can:
   - Inspect variables in the **Variables** panel
   - Step through code with `F10` (step over) or `F11` (step into)
   - View the call stack
   - Use the Debug Console to execute Python commands

### Useful Breakpoint Locations

- **Line ~120**: `def get_or_create_session_id()` - Session creation
- **Line ~280**: `def get_next_question()` - Question selection
- **Line ~340**: `def submit_answer()` - Answer processing
- **Line ~450**: `def get_relevant_theorems()` - Theorem retrieval

---

## Quick Testing in VS Code

### Test with PowerShell (in VS Code Terminal)

```powershell
# Create a session
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Start learning session
Invoke-RestMethod -Uri "http://localhost:17654/api/session/start" -Method POST -WebSession $session

# Get first question
$q = Invoke-RestMethod -Uri "http://localhost:17654/api/questions/first" -Method GET -WebSession $session
Write-Host "Question: $($q.question_text)"

# Get answer options
$answers = Invoke-RestMethod -Uri "http://localhost:17654/api/answers/options" -Method GET -WebSession $session
$answers.answers | Format-Table

# Submit an answer
$body = @{ question_id = $q.question_id; answer_id = 1 } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://localhost:17654/api/answers/submit" -Method POST -Body $body -ContentType "application/json" -WebSession $session

# Show theorems
$result.relevant_theorems | Select-Object -First 3 | Format-Table theorem_id, theorem_text, combined_score
```

### Test with Python (create test_api.py)

Create a new file `test_api_quick.py`:

```python
import requests

BASE_URL = "http://localhost:17654/api"
s = requests.Session()

# Start session
print("✓ Starting session...")
s.post(f"{BASE_URL}/session/start")

# Get question
print("✓ Getting first question...")
q = s.get(f"{BASE_URL}/questions/first").json()
print(f"  Question: {q['question_text']}")

# Submit answer
print("✓ Submitting answer...")
result = s.post(f"{BASE_URL}/answers/submit", 
    json={"question_id": q["question_id"], "answer_id": 1}).json()

print(f"✓ Got {len(result['relevant_theorems'])} relevant theorems")

# End session
s.post(f"{BASE_URL}/session/end", json={"feedback": 5, "save_to_db": True})
print("✓ Session ended successfully!")
```

Run it:
```bash
python test_api_quick.py
```

---

## Using the REST Client Extension (Optional)

For easy API testing without leaving VS Code:

### 1. Install REST Client Extension

1. Press `Ctrl+Shift+X`
2. Search for **"REST Client"**
3. Install **REST Client by Huachao Mao**

### 2. Create API Test File

Create a new file `api_tests.http` with this content:

```http
### Variables
@baseUrl = http://localhost:17654/api

### Health Check
GET {{baseUrl}}/health

### Start Session
# @name startSession
POST {{baseUrl}}/session/start
Content-Type: application/json

### Get First Question
GET {{baseUrl}}/questions/first

### Get Answer Options
GET {{baseUrl}}/answers/options

### Submit Answer
POST {{baseUrl}}/answers/submit
Content-Type: application/json

{
  "question_id": 1,
  "answer_id": 1
}

### Get Session Status
GET {{baseUrl}}/session/status

### End Session
POST {{baseUrl}}/session/end
Content-Type: application/json

{
  "feedback": 5,
  "save_to_db": true
}
```

### 3. Run Requests

- Click **"Send Request"** above each section
- Results appear in a new panel

---

## Keyboard Shortcuts

### Running & Debugging
- `F5` - Start debugging
- `Ctrl+F5` - Run without debugging
- `Shift+F5` - Stop debugging
- `Ctrl+Shift+F5` - Restart debugging

### Debugging
- `F9` - Toggle breakpoint
- `F10` - Step over
- `F11` - Step into
- `Shift+F11` - Step out
- `F5` - Continue

### Terminal
- `` Ctrl+` `` - Toggle terminal
- `` Ctrl+Shift+` `` - Create new terminal
- `Ctrl+C` - Stop running process

---

## Changing the Port

### Method 1: Edit launch.json

1. Open `.vscode/launch.json`
2. Find the `"env"` section
3. Change `"PORT": "17654"` to your desired port
4. Save and restart

### Method 2: Environment Variable (Temporary)

In the integrated terminal:
```bash
$env:PORT = "8080"
python api_server.py
```

### Method 3: Edit api_server.py (Permanent)

1. Open `api_server.py`
2. Find line: `port = int(os.environ.get('PORT', 17654))`
3. Change `17654` to your desired port
4. Save

---

## Viewing Logs

### In VS Code Terminal

All server output appears in the **integrated terminal** when you run the server.

### Filtering Logs

You can filter output by clicking the filter icon in the terminal toolbar or using PowerShell:

```powershell
python api_server.py 2>&1 | Select-String "ERROR"  # Show only errors
```

---

## Tips & Tricks

### 1. Split Terminal

- Run server in one terminal
- Test API in another terminal
- Right-click terminal tab → **Split Terminal**

### 2. Auto-Restart on Changes

Install `flask` with auto-reload (already in requirements.txt):
- Use **"Run API Server (Debug Mode)"** configuration
- Flask will auto-reload when you save changes

### 3. Quick Terminal Commands

Create tasks in `.vscode/tasks.json` for common commands (optional):

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start API Server",
            "type": "shell",
            "command": "python api_server.py",
            "problemMatcher": []
        }
    ]
}
```

### 4. Multi-root Workspace

If you have multiple projects:
- `File → Add Folder to Workspace`
- Save as workspace file
- Each folder can have its own launch configurations

---

## Troubleshooting in VS Code

### Server Won't Start

1. Check the **Problems** panel (`Ctrl+Shift+M`)
2. Check for syntax errors
3. Run test suite: Select **"Run Test Suite"** from debug dropdown

### Port Already in Use

```bash
# In PowerShell terminal
Get-NetTCPConnection -LocalPort 17654 | Select-Object OwningProcess
Stop-Process -Id <process_id>
```

Or change the port in `.vscode/launch.json`

### Python Extension Not Working

1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose the Python interpreter with packages installed

### Debugging Not Working

1. Ensure breakpoints are in executable code (not comments)
2. Check that you're running the **Debug Mode** configuration
3. Try "Run → Start Debugging" from menu

---

## Next Steps

1. ✅ Run **"Run Test Suite"** to verify everything works
2. 🚀 Run **"Run API Server"** to start the server
3. 🌐 Open browser to `http://localhost:17654/api/health`
4. 📚 Read `API_DOCUMENTATION.md` for endpoint details
5. 🔧 Try setting breakpoints and debugging

---

## Quick Reference Card

| Action | Shortcut |
|--------|----------|
| Open Debug Panel | `Ctrl+Shift+D` |
| Start Server | `F5` |
| Stop Server | `Shift+F5` |
| Open Terminal | `` Ctrl+` `` |
| Toggle Breakpoint | `F9` |
| Step Over | `F10` |
| Step Into | `F11` |
| Continue | `F5` |

---

## Files Created

- ✅ `.vscode/launch.json` - Debug configurations
- ✅ `VSCODE_GUIDE.md` - This guide

---

## Support

- Full API documentation: `API_DOCUMENTATION.md`
- Quick start guide: `QUICKSTART.md`
- Installation help: `INSTALL.md`

---

**Happy Coding! 🎉**

Your API server is now ready to run in VS Code on port 17654!
