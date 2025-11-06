# Quick Start Guide - Geometry Learning System

## Installation & Setup (2 minutes)

### Step 1: Install Dependencies
```bash
cd c:\Users\lahavor\am\thesis\Geometry
pip install -r requirements.txt
```

### Step 2: Verify Installation
```bash
python test_system.py
```

You should see "🎉 All tests passed!"

---

## Using the API Server

### Start the Server
```bash
python api_server.py
```

Server runs on: **http://localhost:5000**

### Test the Server
```bash
# In a new terminal/PowerShell window
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status": "healthy", "active_sessions": 0}
```

---

## Quick API Test (PowerShell)

```powershell
# Start a session
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-RestMethod -Uri "http://localhost:5000/api/session/start" -Method POST -WebSession $session

# Get first question
$question = Invoke-RestMethod -Uri "http://localhost:5000/api/questions/first" -Method GET -WebSession $session
Write-Host "Question: $($question.question_text)"

# Get answer options
$answers = Invoke-RestMethod -Uri "http://localhost:5000/api/answers/options" -Method GET -WebSession $session
$answers.answers | Format-Table

# Submit answer (example: answer_id = 1)
$body = @{
    question_id = $question.question_id
    answer_id = 1
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:5000/api/answers/submit" -Method POST -Body $body -ContentType "application/json" -WebSession $session
Write-Host "Relevant theorems:"
$result.relevant_theorems | Format-Table theorem_id, theorem_text, combined_score
```

---

## Using the CLI (Original Interface)

### Interactive Mode
```bash
python geometry_manager.py
```

This launches the interactive learning session with:
- Adaptive question selection
- Real-time theorem suggestions
- Feedback collection
- Session saving

---

## API Endpoints Overview

### Session Management
- `POST /api/session/start` - Start new session
- `GET /api/session/status` - Check session status
- `POST /api/session/end` - End and save session
- `POST /api/session/reset` - Reset session state

### Questions & Answers
- `GET /api/questions/first` - Get first question
- `GET /api/questions/next` - Get next adaptive question
- `GET /api/questions/{id}` - Get question details
- `GET /api/answers/options` - Get answer options
- `POST /api/answers/submit` - Submit answer

### Theorems
- `GET /api/theorems` - Get all theorems
- `GET /api/theorems/{id}` - Get theorem details
- `POST /api/theorems/relevant` - Get relevant theorems

### Session History
- `GET /api/sessions/history` - Get all saved sessions
- `GET /api/sessions/current` - Get current session data
- `GET /api/sessions/statistics` - Get aggregated stats

### Utilities
- `GET /api/health` - Health check
- `GET /api/db/tables` - List database tables
- `GET /api/db/triangles` - Get triangle types
- `GET /api/feedback/options` - Get feedback options
- `POST /api/feedback/submit` - Submit feedback

---

## Python Example (Complete Flow)

```python
import requests

BASE_URL = "http://localhost:5000/api"
s = requests.Session()

# Start session
s.post(f"{BASE_URL}/session/start")
print("Session started")

# Get first question
q = s.get(f"{BASE_URL}/questions/first").json()
print(f"Q: {q['question_text']}")

# Submit answer
result = s.post(f"{BASE_URL}/answers/submit", json={
    "question_id": q["question_id"],
    "answer_id": 1  # כן
}).json()

# Show relevant theorems
for theorem in result["relevant_theorems"]:
    print(f"- {theorem['theorem_text']}")

# Get next question
q2 = s.get(f"{BASE_URL}/questions/next").json()
print(f"Next Q: {q2['question_text']}")

# End session
s.post(f"{BASE_URL}/session/end", json={
    "feedback": 5,  # הצלחתי תודה
    "save_to_db": True
})
print("Session ended")
```

---

## JavaScript Example (Fetch)

```javascript
const BASE_URL = 'http://localhost:5000/api';

async function demo() {
  // Start session
  await fetch(`${BASE_URL}/session/start`, {
    method: 'POST',
    credentials: 'include'
  });

  // Get question
  const q = await fetch(`${BASE_URL}/questions/first`, {
    credentials: 'include'
  }).then(r => r.json());
  
  console.log('Question:', q.question_text);

  // Submit answer
  const result = await fetch(`${BASE_URL}/answers/submit`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    credentials: 'include',
    body: JSON.stringify({
      question_id: q.question_id,
      answer_id: 1
    })
  }).then(r => r.json());

  console.log('Theorems:', result.relevant_theorems);

  // End session
  await fetch(`${BASE_URL}/session/end`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    credentials: 'include',
    body: JSON.stringify({feedback: 5, save_to_db: true})
  });
}

demo();
```

---

## Configuration

### Environment Variables

```bash
# Windows (PowerShell)
$env:PORT = "8080"
$env:DEBUG = "True"
$env:SECRET_KEY = "your-secret-key"
python api_server.py

# Linux/Mac
export PORT=8080
export DEBUG=True
export SECRET_KEY=your-secret-key
python api_server.py
```

### Default Values
- **PORT**: 5000
- **DEBUG**: False
- **SECRET_KEY**: Auto-generated (changes on restart)

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### "Database is locked"
- Close other connections to the database
- Only one CLI session at a time
- API server handles concurrent requests safely

### Session not persisting
- Make sure cookies are enabled
- Use `credentials: 'include'` in JavaScript
- Use `requests.Session()` in Python

---

## Next Steps

1. **Read full documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Explore utilities**: `view_tables.py`, `check_sessions.py`
3. **Build your app**: Use API endpoints to create web/mobile interface

---

**Need Help?**
- Full API docs: `API_DOCUMENTATION.md`
- Project overview: `README.md`
- Run tests: `python test_system.py`
