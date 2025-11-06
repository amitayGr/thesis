# Geometry Learning System

An adaptive learning system for geometry that uses AI-driven question selection to help students learn geometric theorems efficiently.

## Features

- **Adaptive Learning Algorithm**: Questions are selected based on information gain and triangle type weights
- **Dynamic Weight Adjustment**: System adapts to student responses in real-time
- **Theorem Recommendation**: Suggests relevant theorems based on student's learning progress
- **Session Management**: Tracks and saves learning sessions for analysis
- **Dual Interface**: Both CLI and REST API available

## Project Structure

```
Geometry/
├── api_server.py                    # Flask REST API server
├── app.py                          # Legacy Flask app (minimal)
├── geometry_manager.py              # Core learning logic
├── session.py                       # Session data model
├── session_db.py                    # Session database handler
├── create.py                        # Database schema creation
├── insertData2.py                   # Data population scripts
├── dynamic_multiplier_db.py         # Dynamic weight calculations
├── theorems_score_db.py             # Theorem scoring system
├── view_tables.py                   # Database viewer utility
├── check_sessions.py                # Session management utility
├── clear_sessions.py                # Session cleanup utility
├── geometry_learning.db             # Main database
├── sessions.db                      # Sessions database
├── Questions-Theorems.csv           # Question-theorem mappings
├── requirements.txt                 # Python dependencies
├── API_DOCUMENTATION.md             # Complete API documentation
└── README.md                        # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd c:\Users\lahavor\am\thesis\Geometry
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify database files exist:**
   - `geometry_learning.db` - Main database with questions, theorems, and weights
   - `sessions.db` - Stores completed learning sessions

   If databases don't exist, you can create them using:
   ```bash
   python create.py
   ```

## Usage

### Option 1: REST API Server (Recommended for Web/Mobile Apps)

1. **Start the API server:**
   ```bash
   python api_server.py
   ```

   The server will start on `http://localhost:5000`

2. **Test the API:**
   ```bash
   # Check server health
   curl http://localhost:5000/api/health

   # Start a learning session
   curl -X POST http://localhost:5000/api/session/start -c cookies.txt

   # Get first question
   curl -X GET http://localhost:5000/api/questions/first -b cookies.txt
   ```

3. **Read the complete API documentation:**
   See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed endpoint documentation with examples.

### Option 2: Command-Line Interface (CLI)

Run the interactive CLI directly:

```bash
python geometry_manager.py
```

The CLI will:
1. Start a new learning session
2. Present questions adaptively based on your responses
3. Show relevant theorems after each answer
4. Allow you to provide feedback and save your session

### Environment Variables

Configure the API server using environment variables:

```bash
# Set custom port (default: 5000)
set PORT=8080

# Enable debug mode (default: False)
set DEBUG=True

# Set custom secret key for sessions
set SECRET_KEY=your-secret-key-here

# Run the server
python api_server.py
```

## API Quick Start

### Complete Learning Session Example (Python)

```python
import requests

BASE_URL = "http://localhost:5000/api"
session = requests.Session()

# 1. Start session
session.post(f"{BASE_URL}/session/start")

# 2. Get first question
response = session.get(f"{BASE_URL}/questions/first")
question = response.json()
print(f"Question: {question['question_text']}")

# 3. Submit answer
response = session.post(
    f"{BASE_URL}/answers/submit",
    json={"question_id": question["question_id"], "answer_id": 1}
)
result = response.json()
print(f"Relevant theorems: {result['relevant_theorems']}")

# 4. Get next question
response = session.get(f"{BASE_URL}/questions/next")
next_question = response.json()

# 5. End session with feedback
session.post(
    f"{BASE_URL}/session/end",
    json={
        "feedback": 5,  # Success
        "triangle_types": [2],
        "helpful_theorems": [1, 23],
        "save_to_db": True
    }
)
```

## Key Concepts

### Triangle Types
- **0**: כללי (General)
- **1**: שווה צלעות (Equilateral)
- **2**: שווה שוקיים (Isosceles)
- **3**: ישר זווית (Right-angled)

### Answer Options
- **0**: לא (No)
- **1**: כן (Yes)
- **2**: לא יודע (Don't know)
- **3**: כנראה (Probably)

### Feedback Options
- **4**: לא הצלחתי הפעם (Didn't succeed this time)
- **5**: הצלחתי תודה (Succeeded, thanks)
- **6**: התקדמתי אבל אנסה תרגיל חדש (Made progress but will try new exercise)
- **7**: חזרה לתרגיל (Return to exercise)

## Adaptive Learning Algorithm

The system uses a sophisticated algorithm that:

1. **Triangle Weight Management**: Maintains weights for each triangle type based on student responses
2. **Information Gain Calculation**: Selects questions that provide maximum information about student knowledge
3. **Theorem Relevance Scoring**: Combines:
   - Triangle type compatibility
   - Question-answer-theorem correlation
   - General theorem helpfulness
4. **Dynamic Multipliers**: Adjusts weights based on historical session data
5. **Prerequisite Enforcement**: Ensures questions are asked in logical order

## Database Schema

### Main Tables

- **Triangles**: Triangle type definitions
- **Theorems**: Geometric theorems with categories
- **Questions**: Learning questions with difficulty levels
- **TheoremTriangleMatrix**: Theorem-triangle relationships
- **TheoremQuestionMatrix**: Theorem-question mappings
- **DynamicAnswerMultipliers**: Adaptive weight multipliers
- **TheoremScores**: Question-answer-theorem correlation scores
- **TheoremGeneralHelpfulness**: Overall theorem utility scores
- **QuestionPrerequisites**: Question dependency relationships

### Session Tables

- **sessions**: Completed learning sessions with interactions and feedback

## Utilities

### View Database Contents
```bash
python view_tables.py
```

### Manage Sessions
```bash
python check_sessions.py
```

Options:
1. View all saved sessions
2. Create fake sessions for testing
3. Clone existing sessions
4. Delete sessions by ID

### Update Dynamic Weights
```bash
python dynamic_multiplier_db.py
```

Updates dynamic multipliers based on session history.

### Update Theorem Scores
```bash
python theorems_score_db.py
```

Recalculates theorem helpfulness scores.

## API Features

- **Thread-Safe**: Uses locks for concurrent database access
- **Session Management**: Flask sessions with secure cookies
- **CORS Enabled**: Cross-origin requests supported
- **Error Handling**: Consistent error responses
- **Pagination**: Support for large result sets
- **Statistics**: Aggregated analytics from session data

## Development

### Running in Debug Mode

```bash
set DEBUG=True
python api_server.py
```

### Testing Endpoints

Use the provided examples in [API_DOCUMENTATION.md](API_DOCUMENTATION.md) or tools like:
- **cURL**: Command-line HTTP client
- **Postman**: GUI-based API testing
- **Python requests**: Programmatic testing

### Adding New Features

1. **New Questions**: Add to `Questions` table and related mapping tables
2. **New Theorems**: Add to `Theorems` table and update relationships
3. **New Endpoints**: Add to `api_server.py` with proper error handling and documentation

## Performance Considerations

- **In-Memory Sessions**: Active sessions are stored in memory for performance
- **Database Connection Pooling**: Single connection per session
- **Thread Locking**: Ensures data consistency with concurrent requests
- **Optimized Queries**: Uses indices and efficient SQL queries

## Troubleshooting

### Database Locked Error
If you see "database is locked" errors:
- Ensure no other processes are accessing the database
- Check for long-running transactions
- Consider increasing the timeout in database connections

### Session Not Found
- Ensure cookies are being sent with requests
- Check session lifetime (24 hours by default)
- Verify server hasn't been restarted (clears in-memory sessions)

### Import Errors
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

## License

[Add your license information here]

## Contributors

[Add contributor information here]

## Contact

For questions or support, please [add contact information].

---

**Last Updated**: November 6, 2025  
**Version**: 1.0
