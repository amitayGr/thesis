# Installation and Setup Instructions

## Complete Setup Guide for Geometry Learning System API

This guide will help you set up and run both the Flask API server and the CLI interface.

---

## Prerequisites

✓ **Python 3.8 or higher**  
✓ **pip** (Python package installer)  
✓ **Internet connection** (for installing dependencies)

### Check Python Version

```bash
python --version
# Should show Python 3.8.x or higher
```

---

## Installation Steps

### Step 1: Navigate to Project Directory

```bash
cd c:\Users\lahavor\am\thesis\Geometry
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Collecting Flask==3.0.0
Collecting Flask-Cors==4.0.0
Collecting SQLAlchemy==2.0.23
Collecting pandas==2.1.3
...
Successfully installed Flask-3.0.0 Flask-Cors-4.0.0 SQLAlchemy-2.0.23 pandas-2.1.3
```

### Step 3: Verify Installation

```bash
python test_system.py
```

**Expected output:**
```
============================================================
Geometry Learning System - Test Suite
============================================================
Testing module imports...
✓ geometry_manager imported successfully
✓ session imported successfully
✓ session_db imported successfully

Testing GeometryManager...
✓ GeometryManager instantiated
✓ Database file exists: geometry_learning.db
✓ Got first question: X
✓ GeometryManager closed successfully

Testing Session...
✓ Session created with ID: ...
✓ Interaction added
✓ Feedback set
✓ Session converted to dict
✓ Session converted to JSON

Testing SessionDB...
✓ SessionDB instantiated
✓ Loaded X sessions from database

Testing api_server.py syntax...
✓ api_server.py syntax is valid

============================================================
Test Summary
============================================================
✓ PASS: Module Imports
✓ PASS: GeometryManager
✓ PASS: Session
✓ PASS: SessionDB
✓ PASS: API Server Syntax
============================================================
Results: 5/5 tests passed
============================================================

🎉 All tests passed!
```

If all tests pass, you're ready to go! ✓

---

## Running the System

### Option A: Run API Server (for Web/Mobile Apps)

#### 1. Start the Server

```bash
python api_server.py
```

**Expected output:**
```
============================================================
🚀 Geometry Learning API Server
============================================================
📡 Server starting on http://localhost:5000
🔧 Debug mode: False
📚 API Documentation: See API_DOCUMENTATION.md
============================================================
 * Serving Flask app 'api_server'
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

#### 2. Test the Server (in a new terminal)

```bash
# Windows PowerShell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET

# Or using curl (if installed)
curl http://localhost:5000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "active_sessions": 0
}
```

#### 3. Stop the Server

Press `CTRL+C` in the terminal where the server is running.

---

### Option B: Run CLI (Interactive Learning)

```bash
python geometry_manager.py
```

This will start the interactive learning session where you:
1. Answer geometry questions
2. See adaptive question selection
3. Receive relevant theorem suggestions
4. Provide feedback
5. Save your session

---

## Using the API

### Quick Test with PowerShell

```powershell
# Create a web session to maintain cookies
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Start a learning session
Invoke-RestMethod -Uri "http://localhost:5000/api/session/start" -Method POST -WebSession $session

# Get first question
$question = Invoke-RestMethod -Uri "http://localhost:5000/api/questions/first" -Method GET -WebSession $session
Write-Host "Question: $($question.question_text)"

# Get answer options
$answers = Invoke-RestMethod -Uri "http://localhost:5000/api/answers/options" -Method GET -WebSession $session
$answers.answers | Format-Table

# Submit answer (example with answer_id = 1)
$body = @{
    question_id = $question.question_id
    answer_id = 1
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:5000/api/answers/submit" -Method POST -Body $body -ContentType "application/json" -WebSession $session

# Display relevant theorems
Write-Host "`nRelevant theorems:"
$result.relevant_theorems | Format-Table theorem_id, theorem_text, combined_score
```

### Quick Test with Python

Create a file named `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:5000/api"
session = requests.Session()

# Start session
print("Starting session...")
response = session.post(f"{BASE_URL}/session/start")
print(response.json())

# Get first question
print("\nGetting first question...")
response = session.get(f"{BASE_URL}/questions/first")
question = response.json()
print(f"Question {question['question_id']}: {question['question_text']}")

# Get answer options
response = session.get(f"{BASE_URL}/answers/options")
answers = response.json()['answers']
print("\nAnswer options:")
for ans in answers:
    print(f"  {ans['id']}: {ans['text']}")

# Submit answer
print("\nSubmitting answer (כן)...")
response = session.post(
    f"{BASE_URL}/answers/submit",
    json={"question_id": question["question_id"], "answer_id": 1}
)
result = response.json()
print("Answer processed successfully!")

print("\nRelevant theorems:")
for theorem in result['relevant_theorems'][:3]:  # Show top 3
    print(f"  [{theorem['theorem_id']}] {theorem['theorem_text']}")
    print(f"      Score: {theorem['combined_score']:.3f}")

# End session
print("\nEnding session...")
response = session.post(
    f"{BASE_URL}/session/end",
    json={"feedback": 5, "save_to_db": True}
)
print(response.json()['message'])
```

Run it:
```bash
python test_api.py
```

---

## Configuration

### Environment Variables

You can customize the server using environment variables:

**Windows PowerShell:**
```powershell
$env:PORT = "8080"          # Change port (default: 5000)
$env:DEBUG = "True"         # Enable debug mode (default: False)
$env:SECRET_KEY = "my-key"  # Set session secret key
python api_server.py
```

**Linux/Mac:**
```bash
export PORT=8080
export DEBUG=True
export SECRET_KEY=my-key
python api_server.py
```

---

## Troubleshooting

### Problem: "Module not found" error

**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: "Database is locked" error

**Solution:**
- Make sure no other process is accessing the database
- Close any other instances of the CLI or API server
- The API server handles concurrent requests safely

### Problem: "Port already in use"

**Solution:**
```bash
# Use a different port
$env:PORT = "8080"
python api_server.py
```

### Problem: Session not persisting in API

**Solution:**
- Make sure you're using the same session object for all requests
- In JavaScript, use `credentials: 'include'`
- In Python, use `requests.Session()`
- Check that cookies are enabled

### Problem: Can't connect to API from browser

**Solution:**
- Make sure the server is running
- Try `http://localhost:5000/api/health` in your browser
- Check firewall settings
- CORS is enabled, so cross-origin requests should work

---

## Next Steps

### 1. Read the Documentation
- **API Reference**: Open `API_DOCUMENTATION.md` for complete endpoint documentation
- **Quick Start**: Open `QUICKSTART.md` for usage examples
- **Architecture**: Open `ARCHITECTURE.md` to understand the system design

### 2. Explore the Database
```bash
python view_tables.py
# View all database tables and their contents
```

### 3. Manage Sessions
```bash
python check_sessions.py
# View, create, clone, or delete saved sessions
```

### 4. Build Your Application
Use the API endpoints to create:
- Web applications
- Mobile apps
- Desktop applications
- Integration with other systems

### 5. CLI Learning
```bash
python geometry_manager.py
# Use the interactive learning interface
```

---

## File Structure Reference

```
Geometry/
├── api_server.py              # Flask API server
├── geometry_manager.py         # Core learning logic (CLI entry point)
├── session.py                  # Session data model
├── session_db.py               # Session database operations
├── requirements.txt            # Python dependencies
│
├── API_DOCUMENTATION.md        # Complete API reference
├── README.md                   # Project overview
├── QUICKSTART.md              # Quick start guide
├── INSTALL.md                 # This file
├── ARCHITECTURE.md            # System architecture
├── PROJECT_SUMMARY.md         # Implementation summary
│
├── test_system.py             # Test suite
├── view_tables.py             # Database viewer
├── check_sessions.py          # Session manager
│
└── Database Files
    ├── geometry_learning.db    # Main database
    └── sessions.db            # Sessions database
```

---

## Support

### Getting Help
1. Check documentation files (API_DOCUMENTATION.md, QUICKSTART.md, etc.)
2. Run test suite: `python test_system.py`
3. Check error messages for specific guidance

### Common Resources
- **Python requests docs**: https://docs.python-requests.org/
- **Flask documentation**: https://flask.palletsprojects.com/
- **REST API basics**: https://restfulapi.net/

---

## Success Checklist

Before deploying or using in production, verify:

- ✓ All tests pass (`python test_system.py`)
- ✓ API server starts without errors
- ✓ Can connect to API from client
- ✓ Sessions persist correctly
- ✓ Database files are accessible
- ✓ Documentation is available and clear

---

**Installation Guide Version**: 1.0  
**Last Updated**: November 6, 2025  
**Status**: Complete

Enjoy using the Geometry Learning System! 🎓📐
