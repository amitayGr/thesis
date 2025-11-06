# Geometry Learning System - API Documentation

## Overview

This document provides comprehensive documentation for the Geometry Learning System REST API. The API exposes all functionality of the geometry learning system through RESTful endpoints, enabling both web and mobile applications to integrate with the adaptive learning platform.

**Base URL:** `http://localhost:5000/api`

**API Version:** 1.0

---

## Table of Contents

1. [Authentication & Sessions](#authentication--sessions)
2. [Session Management](#session-management)
3. [Question & Answer Flow](#question--answer-flow)
4. [Theorems](#theorems)
5. [Session History & Statistics](#session-history--statistics)
6. [Feedback](#feedback)
7. [Database Utilities](#database-utilities)
8. [Error Handling](#error-handling)
9. [Examples](#examples)

---

## Authentication & Sessions

The API uses **Flask sessions** with secure cookies for session management. Each user session maintains its own learning state, including triangle weights, theorem weights, and question history.

### Session Flow

1. **Start Session:** Call `POST /api/session/start` to initialize a new learning session
2. **Session Cookie:** The server sets a session cookie that must be included in subsequent requests
3. **Maintain Session:** All API calls will use this session until it's explicitly ended
4. **End Session:** Call `POST /api/session/end` to terminate and optionally save the session

### Session Cookie

- **Name:** `session`
- **HttpOnly:** Yes
- **SameSite:** Lax
- **Lifetime:** 24 hours

---

## Session Management

### Start New Session

**Endpoint:** `POST /api/session/start`

**Description:** Initializes a new learning session with fresh state.

**Request:**
```http
POST /api/session/start
Content-Type: application/json
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "New learning session started successfully"
}
```

**Status Codes:**
- `200 OK` - Session created successfully
- `500 Internal Server Error` - Server error

---

### Get Session Status

**Endpoint:** `GET /api/session/status`

**Description:** Retrieves the current session status and learning state.

**Request:**
```http
GET /api/session/status
```

**Response (Active Session):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "active": true,
  "state": {
    "triangle_weights": {
      "0": 0.25,
      "1": 0.25,
      "2": 0.25,
      "3": 0.25
    },
    "questions_count": 5,
    "asked_questions": [1, 3, 7, 12, 15]
  }
}
```

**Response (No Active Session):**
```json
{
  "active": false,
  "message": "No active session"
}
```

**Status Codes:**
- `200 OK` - Status retrieved successfully

---

### End Session

**Endpoint:** `POST /api/session/end`

**Description:** Ends the current learning session, optionally saving feedback and session data to the database.

**Request:**
```http
POST /api/session/end
Content-Type: application/json

{
  "feedback": 5,
  "triangle_types": [2, 3],
  "helpful_theorems": [5, 12, 23],
  "save_to_db": true
}
```

**Request Body Parameters:**
- `feedback` (integer, optional): Feedback ID (4-7)
  - `4`: "לא הצלחתי הפעם" (Didn't succeed this time)
  - `5`: "הצלחתי תודה" (Succeeded, thanks)
  - `6`: "התקדמתי אבל אנסה תרגיל חדש" (Made progress but will try new exercise)
  - `7`: "חזרה לתרגיל" (Return to exercise)
- `triangle_types` (array, optional): List of relevant triangle type IDs (0-3)
- `helpful_theorems` (array, optional): List of helpful theorem IDs (1-63)
- `save_to_db` (boolean, optional, default: true): Whether to save session to database

**Response:**
```json
{
  "message": "Session ended successfully",
  "session_data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "interactions": [
      {"question_id": 1, "answer_id": 1},
      {"question_id": 3, "answer_id": 0}
    ],
    "feedback": 5,
    "triangle_type": [2, 3],
    "helpful_theorems": [5, 12, 23]
  }
}
```

**Status Codes:**
- `200 OK` - Session ended successfully
- `400 Bad Request` - Invalid feedback or no active session
- `500 Internal Server Error` - Server error

---

### Reset Session

**Endpoint:** `POST /api/session/reset`

**Description:** Resets the current session state without ending the session.

**Request:**
```http
POST /api/session/reset
```

**Response:**
```json
{
  "message": "Session state reset successfully",
  "new_state": {
    "triangle_weights": {
      "0": 0.25,
      "1": 0.25,
      "2": 0.25,
      "3": 0.25
    },
    "questions_count": 0,
    "asked_questions": []
  }
}
```

**Status Codes:**
- `200 OK` - Session reset successfully
- `400 Bad Request` - No active session
- `500 Internal Server Error` - Server error

---

## Question & Answer Flow

### Get First Question

**Endpoint:** `GET /api/questions/first`

**Description:** Retrieves the first question for a new session. Always returns an easy question (difficulty level 1).

**Request:**
```http
GET /api/questions/first
```

**Response:**
```json
{
  "question_id": 1,
  "question_text": "האם סכום הזוויות במשולש שווה ל-180 מעלות?"
}
```

**Status Codes:**
- `200 OK` - Question retrieved successfully
- `400 Bad Request` - No active session
- `404 Not Found` - No easy questions available
- `500 Internal Server Error` - Server error

---

### Get Next Question

**Endpoint:** `GET /api/questions/next`

**Description:** Retrieves the next question based on the current learning state. Uses an adaptive algorithm that considers triangle weights, information gain, and question prerequisites.

**Request:**
```http
GET /api/questions/next
```

**Response:**
```json
{
  "question_id": 7,
  "question_text": "האם במשולש שווה שוקיים הזוויות הבסיסיות שוות?",
  "info": "שאלה נבחרה לפי חישוב משולב של רלוונטיות, רווח מידע ותנאי קדימות"
}
```

**Status Codes:**
- `200 OK` - Question retrieved successfully
- `400 Bad Request` - No active session
- `404 Not Found` - No suitable questions found
- `500 Internal Server Error` - Server error

---

### Get Question Details

**Endpoint:** `GET /api/questions/{question_id}`

**Description:** Retrieves detailed information about a specific question.

**Request:**
```http
GET /api/questions/7
```

**Response:**
```json
{
  "question_id": 7,
  "question_text": "האם במשולש שווה שוקיים הזוויות הבסיסיות שוות?",
  "difficulty_level": 2,
  "active": true
}
```

**Status Codes:**
- `200 OK` - Question found
- `404 Not Found` - Question not found
- `500 Internal Server Error` - Server error

---

### Get Answer Options

**Endpoint:** `GET /api/answers/options`

**Description:** Retrieves all available answer options for questions.

**Request:**
```http
GET /api/answers/options
```

**Response:**
```json
{
  "answers": [
    {"id": 0, "text": "לא"},
    {"id": 1, "text": "כן"},
    {"id": 2, "text": "לא יודע"},
    {"id": 3, "text": "כנראה"}
  ]
}
```

**Status Codes:**
- `200 OK` - Options retrieved successfully
- `500 Internal Server Error` - Server error

---

### Submit Answer

**Endpoint:** `POST /api/answers/submit`

**Description:** Submits an answer to the current question. Updates triangle and theorem weights based on the answer, and returns relevant theorems.

**Request:**
```http
POST /api/answers/submit
Content-Type: application/json

{
  "question_id": 7,
  "answer_id": 1
}
```

**Request Body Parameters:**
- `question_id` (integer, required): ID of the question being answered
- `answer_id` (integer, required): ID of the selected answer (0-3)

**Response:**
```json
{
  "message": "Answer processed successfully",
  "updated_weights": {
    "0": 0.15,
    "1": 0.10,
    "2": 0.55,
    "3": 0.20
  },
  "relevant_theorems": [
    {
      "theorem_id": 23,
      "theorem_text": "במשולש שווה שוקיים הזוויות הבסיסיות שוות",
      "weight": 0.45,
      "category": 2,
      "combined_score": 0.82
    },
    {
      "theorem_id": 24,
      "theorem_text": "במשולש שווה שוקיים הצלע השלישית נקראת בסיס",
      "weight": 0.38,
      "category": 2,
      "combined_score": 0.67
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Answer processed successfully
- `400 Bad Request` - Invalid parameters or no active session
- `500 Internal Server Error` - Server error

---

## Theorems

### Get All Theorems

**Endpoint:** `GET /api/theorems`

**Description:** Retrieves all theorems in the system with optional filtering.

**Request:**
```http
GET /api/theorems?active_only=true&category=2
```

**Query Parameters:**
- `active_only` (boolean, optional, default: true): Return only active theorems
- `category` (integer, optional): Filter by triangle category (0-3)
  - `0`: כללי (General)
  - `1`: שווה צלעות (Equilateral)
  - `2`: שווה שוקיים (Isosceles)
  - `3`: ישר זווית (Right-angled)

**Response:**
```json
{
  "theorems": [
    {
      "theorem_id": 23,
      "theorem_text": "במשולש שווה שוקיים הזוויות הבסיסיות שוות",
      "category": 2,
      "active": true
    },
    {
      "theorem_id": 24,
      "theorem_text": "במשולש שווה שוקיים הצלע השלישית נקראת בסיס",
      "category": 2,
      "active": true
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Theorems retrieved successfully
- `500 Internal Server Error` - Server error

---

### Get Theorem Details

**Endpoint:** `GET /api/theorems/{theorem_id}`

**Description:** Retrieves detailed information about a specific theorem.

**Request:**
```http
GET /api/theorems/23
```

**Response:**
```json
{
  "theorem_id": 23,
  "theorem_text": "במשולש שווה שוקיים הזוויות הבסיסיות שוות",
  "category": 2,
  "active": true,
  "general_helpfulness": 0.65
}
```

**Status Codes:**
- `200 OK` - Theorem found
- `404 Not Found` - Theorem not found
- `500 Internal Server Error` - Server error

---

### Get Relevant Theorems

**Endpoint:** `POST /api/theorems/relevant`

**Description:** Retrieves theorems relevant to a specific question and answer combination, sorted by relevance score.

**Request:**
```http
POST /api/theorems/relevant
Content-Type: application/json

{
  "question_id": 7,
  "answer_id": 1,
  "base_threshold": 0.01
}
```

**Request Body Parameters:**
- `question_id` (integer, required): Question ID
- `answer_id` (integer, required): Answer ID
- `base_threshold` (float, optional, default: 0.01): Minimum threshold for theorem weights

**Response:**
```json
{
  "theorems": [
    {
      "theorem_id": 23,
      "theorem_text": "במשולש שווה שוקיים הזוויות הבסיסיות שוות",
      "weight": 0.45,
      "category": 2,
      "combined_score": 0.82
    },
    {
      "theorem_id": 24,
      "theorem_text": "במשולש שווה שוקיים הצלע השלישית נקראת בסיס",
      "weight": 0.38,
      "category": 2,
      "combined_score": 0.67
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Theorems retrieved successfully
- `400 Bad Request` - Invalid parameters or no active session
- `500 Internal Server Error` - Server error

---

## Session History & Statistics

### Get Session History

**Endpoint:** `GET /api/sessions/history`

**Description:** Retrieves all saved sessions from the database with optional pagination.

**Request:**
```http
GET /api/sessions/history?limit=10&offset=0
```

**Query Parameters:**
- `limit` (integer, optional): Maximum number of sessions to return
- `offset` (integer, optional, default: 0): Number of sessions to skip (for pagination)

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "interactions": [
        {"question_id": 1, "answer_id": 1},
        {"question_id": 3, "answer_id": 0}
      ],
      "feedback": 5,
      "triangle_type": [2, 3],
      "helpful_theorems": [5, 12, 23]
    }
  ],
  "total": 45,
  "returned": 10
}
```

**Status Codes:**
- `200 OK` - Sessions retrieved successfully
- `500 Internal Server Error` - Server error

---

### Get Current Session Data

**Endpoint:** `GET /api/sessions/current`

**Description:** Retrieves the current session's interaction data.

**Request:**
```http
GET /api/sessions/current
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "interactions": [
    {"question_id": 1, "answer_id": 1},
    {"question_id": 3, "answer_id": 0}
  ],
  "feedback": null,
  "triangle_type": null,
  "helpful_theorems": []
}
```

**Status Codes:**
- `200 OK` - Session data retrieved successfully
- `400 Bad Request` - No active session
- `500 Internal Server Error` - Server error

---

### Get Session Statistics

**Endpoint:** `GET /api/sessions/statistics`

**Description:** Retrieves aggregated statistics from all saved sessions.

**Request:**
```http
GET /api/sessions/statistics
```

**Response:**
```json
{
  "total_sessions": 45,
  "feedback_distribution": {
    "4": 5,
    "5": 28,
    "6": 10,
    "7": 2
  },
  "average_interactions": 6.8,
  "most_helpful_theorems": [
    {"theorem_id": 23, "count": 35},
    {"theorem_id": 5, "count": 32},
    {"theorem_id": 12, "count": 28}
  ]
}
```

**Status Codes:**
- `200 OK` - Statistics retrieved successfully
- `500 Internal Server Error` - Server error

---

## Feedback

### Get Feedback Options

**Endpoint:** `GET /api/feedback/options`

**Description:** Retrieves all available feedback options.

**Request:**
```http
GET /api/feedback/options
```

**Response:**
```json
{
  "feedback_options": [
    {"id": 4, "text": "לא הצלחתי הפעם"},
    {"id": 5, "text": "הצלחתי תודה"},
    {"id": 6, "text": "התקדמתי אבל אנסה תרגיל חדש"},
    {"id": 7, "text": "חזרה לתרגיל"}
  ]
}
```

**Status Codes:**
- `200 OK` - Options retrieved successfully
- `500 Internal Server Error` - Server error

---

### Submit Feedback

**Endpoint:** `POST /api/feedback/submit`

**Description:** Submits feedback for the current session without ending it.

**Request:**
```http
POST /api/feedback/submit
Content-Type: application/json

{
  "feedback": 5,
  "triangle_types": [2, 3],
  "helpful_theorems": [5, 12, 23]
}
```

**Request Body Parameters:**
- `feedback` (integer, required): Feedback ID (4-7)
- `triangle_types` (array, optional): List of relevant triangle type IDs (0-3)
- `helpful_theorems` (array, optional): List of helpful theorem IDs (1-63)

**Response (Regular Feedback):**
```json
{
  "message": "Feedback recorded successfully"
}
```

**Response (Return to Exercise - Feedback 7):**
```json
{
  "message": "Feedback recorded. Will resume current question.",
  "action": "resume"
}
```

**Status Codes:**
- `200 OK` - Feedback recorded successfully
- `400 Bad Request` - Invalid feedback or no active session
- `500 Internal Server Error` - Server error

---

## Database Utilities

### Get Database Tables

**Endpoint:** `GET /api/db/tables`

**Description:** Retrieves a list of all tables in the geometry database.

**Request:**
```http
GET /api/db/tables
```

**Response:**
```json
{
  "tables": [
    "Triangles",
    "Theorems",
    "Questions",
    "TheoremTriangleMatrix",
    "TheoremQuestionMatrix",
    "InitialAnswerMultipliers",
    "inputDuring",
    "inputFB",
    "QuestionPrerequisites",
    "DynamicAnswerMultipliers",
    "TheoremScores",
    "TheoremGeneralHelpfulness"
  ]
}
```

**Status Codes:**
- `200 OK` - Tables retrieved successfully
- `500 Internal Server Error` - Server error

---

### Get Triangle Types

**Endpoint:** `GET /api/db/triangles`

**Description:** Retrieves all triangle types in the system.

**Request:**
```http
GET /api/db/triangles
```

**Response:**
```json
{
  "triangles": [
    {"triangle_id": 0, "triangle_type": "משולש כללי", "active": true},
    {"triangle_id": 1, "triangle_type": "משולש שווה צלעות", "active": true},
    {"triangle_id": 2, "triangle_type": "משולש שווה שוקיים", "active": true},
    {"triangle_id": 3, "triangle_type": "משולש ישר זווית", "active": true}
  ]
}
```

**Status Codes:**
- `200 OK` - Triangle types retrieved successfully
- `500 Internal Server Error` - Server error

---

### Health Check

**Endpoint:** `GET /api/health`

**Description:** Health check endpoint to verify server status.

**Request:**
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 3
}
```

**Status Codes:**
- `200 OK` - Server is healthy

---

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses.

### Error Response Format

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

### Common Status Codes

- `200 OK` - Request succeeded
- `400 Bad Request` - Invalid request parameters or missing required fields
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Examples

**Missing Required Fields:**
```json
{
  "error": "Missing required fields",
  "message": "Both question_id and answer_id are required"
}
```

**No Active Session:**
```json
{
  "error": "No active session found",
  "message": "Please start a new session first"
}
```

**Invalid Parameters:**
```json
{
  "error": "Invalid feedback value",
  "message": "Feedback must be 4, 5, 6, or 7"
}
```

---

## Examples

### Complete Learning Session Flow

This example demonstrates a complete learning session from start to finish.

#### 1. Start a New Session

```bash
curl -X POST http://localhost:5000/api/session/start \
  -H "Content-Type: application/json" \
  -c cookies.txt
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "New learning session started successfully"
}
```

#### 2. Get Answer Options

```bash
curl -X GET http://localhost:5000/api/answers/options \
  -b cookies.txt
```

**Response:**
```json
{
  "answers": [
    {"id": 0, "text": "לא"},
    {"id": 1, "text": "כן"},
    {"id": 2, "text": "לא יודע"},
    {"id": 3, "text": "כנראה"}
  ]
}
```

#### 3. Get First Question

```bash
curl -X GET http://localhost:5000/api/questions/first \
  -b cookies.txt
```

**Response:**
```json
{
  "question_id": 1,
  "question_text": "האם סכום הזוויות במשולש שווה ל-180 מעלות?"
}
```

#### 4. Submit Answer

```bash
curl -X POST http://localhost:5000/api/answers/submit \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question_id": 1,
    "answer_id": 1
  }'
```

**Response:**
```json
{
  "message": "Answer processed successfully",
  "updated_weights": {
    "0": 0.30,
    "1": 0.25,
    "2": 0.25,
    "3": 0.20
  },
  "relevant_theorems": [
    {
      "theorem_id": 1,
      "theorem_text": "סכום הזוויות של משולש הוא 180°",
      "weight": 0.75,
      "category": 0,
      "combined_score": 0.88
    }
  ]
}
```

#### 5. Get Next Question

```bash
curl -X GET http://localhost:5000/api/questions/next \
  -b cookies.txt
```

**Response:**
```json
{
  "question_id": 7,
  "question_text": "האם במשולש שווה שוקיים הזוויות הבסיסיות שוות?",
  "info": "שאלה נבחרה לפי חישוב משולב של רלוונטיות, רווח מידע ותנאי קדימות"
}
```

#### 6. Submit Another Answer

```bash
curl -X POST http://localhost:5000/api/answers/submit \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question_id": 7,
    "answer_id": 1
  }'
```

#### 7. Check Session Status

```bash
curl -X GET http://localhost:5000/api/session/status \
  -b cookies.txt
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "active": true,
  "state": {
    "triangle_weights": {
      "0": 0.15,
      "1": 0.10,
      "2": 0.55,
      "3": 0.20
    },
    "questions_count": 2,
    "asked_questions": [1, 7]
  }
}
```

#### 8. End Session with Feedback

```bash
curl -X POST http://localhost:5000/api/session/end \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "feedback": 5,
    "triangle_types": [2],
    "helpful_theorems": [1, 23],
    "save_to_db": true
  }'
```

**Response:**
```json
{
  "message": "Session ended successfully",
  "session_data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "interactions": [
      {"question_id": 1, "answer_id": 1},
      {"question_id": 7, "answer_id": 1}
    ],
    "feedback": 5,
    "triangle_type": [2],
    "helpful_theorems": [1, 23]
  }
}
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Create a session to persist cookies
session = requests.Session()

# 1. Start a new learning session
response = session.post(f"{BASE_URL}/session/start")
print("Session started:", response.json())

# 2. Get answer options
response = session.get(f"{BASE_URL}/answers/options")
answers = response.json()["answers"]
print("Answer options:", answers)

# 3. Get first question
response = session.get(f"{BASE_URL}/questions/first")
question = response.json()
print("First question:", question)

# 4. Submit answer
response = session.post(
    f"{BASE_URL}/answers/submit",
    json={
        "question_id": question["question_id"],
        "answer_id": 1  # כן
    }
)
result = response.json()
print("Answer processed:", result)
print("Relevant theorems:", result["relevant_theorems"])

# 5. Get next question
response = session.get(f"{BASE_URL}/questions/next")
next_question = response.json()
print("Next question:", next_question)

# 6. Submit another answer
response = session.post(
    f"{BASE_URL}/answers/submit",
    json={
        "question_id": next_question["question_id"],
        "answer_id": 1
    }
)
print("Second answer processed:", response.json())

# 7. End session with feedback
response = session.post(
    f"{BASE_URL}/session/end",
    json={
        "feedback": 5,
        "triangle_types": [2],
        "helpful_theorems": [1, 23],
        "save_to_db": True
    }
)
print("Session ended:", response.json())
```

### JavaScript Example (Fetch API)

```javascript
const BASE_URL = 'http://localhost:5000/api';

async function runLearningSession() {
  // 1. Start session
  let response = await fetch(`${BASE_URL}/session/start`, {
    method: 'POST',
    credentials: 'include'  // Important for cookies
  });
  console.log('Session started:', await response.json());

  // 2. Get first question
  response = await fetch(`${BASE_URL}/questions/first`, {
    credentials: 'include'
  });
  const question = await response.json();
  console.log('First question:', question);

  // 3. Submit answer
  response = await fetch(`${BASE_URL}/answers/submit`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    credentials: 'include',
    body: JSON.stringify({
      question_id: question.question_id,
      answer_id: 1
    })
  });
  const result = await response.json();
  console.log('Answer result:', result);

  // 4. Get next question
  response = await fetch(`${BASE_URL}/questions/next`, {
    credentials: 'include'
  });
  const nextQuestion = await response.json();
  console.log('Next question:', nextQuestion);

  // 5. End session
  response = await fetch(`${BASE_URL}/session/end`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    credentials: 'include',
    body: JSON.stringify({
      feedback: 5,
      triangle_types: [2],
      helpful_theorems: [1, 23],
      save_to_db: true
    })
  });
  console.log('Session ended:', await response.json());
}

runLearningSession();
```

---

## Running the Server

### Starting the Server

```bash
python api_server.py
```

**Server will start on:** `http://localhost:5000`

### Environment Variables

- `PORT` (default: 5000): Server port
- `DEBUG` (default: False): Enable debug mode
- `SECRET_KEY` (default: auto-generated): Flask secret key for sessions

### Example with Custom Configuration

```bash
export PORT=8080
export DEBUG=True
export SECRET_KEY=your-secret-key
python api_server.py
```

---

## Notes

1. **Session Persistence:** Sessions are stored in memory. Restarting the server will clear all active sessions.
2. **Thread Safety:** The API uses threading locks to ensure thread-safe database operations.
3. **Concurrent Requests:** The server supports multiple concurrent requests through Flask's threaded mode.
4. **CLI Compatibility:** The original CLI functionality remains intact in `geometry_manager.py` and can be used independently.
5. **Database Files:** 
   - `geometry_learning.db`: Main database with questions, theorems, and weights
   - `sessions.db`: Stores completed learning sessions

---

## Support

For issues or questions about the API, please refer to the main project documentation or contact the development team.

**API Version:** 1.0  
**Last Updated:** November 6, 2025
