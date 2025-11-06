# Project Architecture - Geometry Learning System

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                          │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser  │  Mobile App  │  CLI Terminal  │  Python Script  │
└────────┬──────┴──────┬───────┴───────┬────────┴────────┬─────────┘
         │             │               │                 │
         │ HTTP/REST   │ HTTP/REST     │ Direct Call     │ Direct Call
         │             │               │                 │
┌────────▼─────────────▼───────────────┼─────────────────▼─────────┐
│                API SERVER             │                           │
│          (api_server.py)              │     CLI INTERFACE         │
│                                       │   (geometry_manager.py)   │
│  ┌─────────────────────────────┐     │                           │
│  │   Flask Application         │     │  ┌─────────────────────┐  │
│  │   - Routes (25+ endpoints)  │     │  │  Interactive Loop   │  │
│  │   - Session Management      │     │  │  - Question Display │  │
│  │   - CORS Support            │     │  │  - Answer Input     │  │
│  │   - Thread Safety           │     │  │  - Feedback         │  │
│  │   - Error Handling          │     │  └─────────────────────┘  │
│  └────────────┬────────────────┘     │                           │
└───────────────┼──────────────────────┴───────────────────────────┘
                │                              │
                │ Uses                         │ Uses
                │                              │
┌───────────────▼──────────────────────────────▼───────────────────┐
│                   CORE BUSINESS LOGIC                             │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐      │
│  │           GeometryManager (geometry_manager.py)        │      │
│  │                                                         │      │
│  │  • Adaptive Learning Algorithm                         │      │
│  │    - Triangle weight management                        │      │
│  │    - Information gain calculation                      │      │
│  │    - Question prerequisite enforcement                 │      │
│  │    - Theorem relevance scoring                         │      │
│  │                                                         │      │
│  │  • Question Selection                                  │      │
│  │    - First question (easy)                             │      │
│  │    - Next question (adaptive)                          │      │
│  │    - Prerequisite checking                             │      │
│  │                                                         │      │
│  │  • Answer Processing                                   │      │
│  │    - Triangle weight updates                           │      │
│  │    - Theorem weight updates                            │      │
│  │    - Dynamic multiplier application                    │      │
│  │                                                         │      │
│  │  • Theorem Retrieval                                   │      │
│  │    - Relevance calculation                             │      │
│  │    - Combined scoring (triangle + score + helpfulness) │      │
│  │    - Sorted by relevance                               │      │
│  └────────────┬───────────────────────────────────────────┘      │
│               │                                                   │
│               │ Uses                                              │
│               │                                                   │
│  ┌────────────▼─────────────┐  ┌──────────────────────────┐      │
│  │   Session (session.py)   │  │  SessionDB (session_db.py)│      │
│  │                          │  │                           │      │
│  │  • Interaction tracking  │  │  • Save sessions          │      │
│  │  • Feedback storage      │  │  • Load sessions          │      │
│  │  • Theorem tracking      │  │  • Query sessions         │      │
│  │  • Triangle type storage │  │  • Database connection    │      │
│  │  • JSON serialization    │  │                           │      │
│  └──────────────────────────┘  └───────────────────────────┘      │
│                                                                   │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                │ Reads/Writes
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                        DATA LAYER                                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │         geometry_learning.db (SQLite Database)           │    │
│  │                                                           │    │
│  │  Core Tables:                                            │    │
│  │  ├─ Triangles              (4 types)                     │    │
│  │  ├─ Theorems               (63 theorems)                 │    │
│  │  ├─ Questions              (28 questions)                │    │
│  │  ├─ inputDuring            (Answer options)              │    │
│  │  └─ inputFB                (Feedback options)            │    │
│  │                                                           │    │
│  │  Relationship Tables:                                    │    │
│  │  ├─ TheoremTriangleMatrix  (Theorem-Triangle links)      │    │
│  │  ├─ TheoremQuestionMatrix  (Theorem-Question links)      │    │
│  │  └─ QuestionPrerequisites  (Question dependencies)       │    │
│  │                                                           │    │
│  │  Adaptive Learning Tables:                               │    │
│  │  ├─ InitialAnswerMultipliers   (Baseline weights)        │    │
│  │  ├─ DynamicAnswerMultipliers   (Adaptive weights)        │    │
│  │  ├─ TheoremScores              (Q-A-T correlations)      │    │
│  │  └─ TheoremGeneralHelpfulness  (Overall helpfulness)     │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │            sessions.db (SQLite Database)                 │    │
│  │                                                           │    │
│  │  Tables:                                                 │    │
│  │  └─ sessions  (Completed learning sessions with data)    │    │
│  │               - Interactions (question-answer pairs)     │    │
│  │               - Feedback                                 │    │
│  │               - Triangle types                           │    │
│  │               - Helpful theorems                         │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────┐
│                    UTILITY SCRIPTS                                │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐              │
│  │  create.py           │  │  insertData2.py      │              │
│  │  Database schema     │  │  Populate database   │              │
│  │  creation            │  │  with initial data   │              │
│  └──────────────────────┘  └──────────────────────┘              │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐              │
│  │  view_tables.py      │  │  check_sessions.py   │              │
│  │  View DB contents    │  │  Manage sessions     │              │
│  │                      │  │  (view/create/clone) │              │
│  └──────────────────────┘  └──────────────────────┘              │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐              │
│  │  dynamic_multiplier  │  │  theorems_score_db   │              │
│  │  _db.py              │  │  .py                 │              │
│  │  Update dynamic      │  │  Update theorem      │              │
│  │  weights from        │  │  scores from         │              │
│  │  session data        │  │  session data        │              │
│  └──────────────────────┘  └──────────────────────┘              │
│                                                                   │
│  ┌──────────────────────┐                                         │
│  │  test_system.py      │                                         │
│  │  Automated test      │                                         │
│  │  suite               │                                         │
│  └──────────────────────┘                                         │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘


┌───────────────────────────────────────────────────────────────────┐
│                      DOCUMENTATION                                │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  • README.md              - Project overview & features           │
│  • API_DOCUMENTATION.md   - Complete API reference               │
│  • QUICKSTART.md          - Quick start guide                    │
│  • PROJECT_SUMMARY.md     - Implementation summary               │
│  • requirements.txt       - Python dependencies                  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Answer Submission

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Client submits answer                                     │
│    POST /api/answers/submit                                  │
│    {question_id: 7, answer_id: 1}                            │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. API Server validates request                              │
│    - Check active session                                    │
│    - Validate parameters                                     │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. GeometryManager.process_answer()                          │
│    ├─ Update triangle weights                                │
│    │  └─ Lookup multipliers from DynamicAnswerMultipliers    │
│    ├─ Update theorem weights                                 │
│    │  └─ Calculate from TheoremTriangleMatrix                │
│    └─ Add interaction to Session                             │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Get relevant theorems                                     │
│    GeometryManager.get_relevant_theorems()                   │
│    ├─ Filter by theorem weights                              │
│    ├─ Calculate triangle score                               │
│    ├─ Get theorem-specific score from TheoremScores          │
│    ├─ Get general helpfulness from TheoremGeneralHelpfulness │
│    └─ Combine & sort by weighted score                       │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Return response to client                                 │
│    {                                                          │
│      message: "Answer processed",                            │
│      updated_weights: {...},                                 │
│      relevant_theorems: [...]                                │
│    }                                                          │
└──────────────────────────────────────────────────────────────┘
```

## Key Architectural Principles

### 1. Separation of Concerns
- **API Layer**: HTTP handling, validation, serialization
- **Business Logic**: Learning algorithm, question selection
- **Data Layer**: Database operations, persistence

### 2. Thread Safety
- Database operations protected with locks
- Session state isolated per user
- No shared mutable state

### 3. Backward Compatibility
- API is an additional interface, not a replacement
- Core logic unchanged
- CLI fully functional

### 4. Extensibility
- Easy to add new endpoints
- Database schema supports expansion
- Modular component design

### 5. Performance
- In-memory session storage for speed
- Database indices for fast queries
- Minimal serialization overhead
