"""
Flask API Server for Geometry Learning System

This server exposes all the functionality of the geometry learning system
through RESTful API endpoints. It maintains session state using Flask sessions
and provides thread-safe operations for concurrent requests.
"""

from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS
from flask_caching import Cache
from flask_compress import Compress
from geometry_manager import GeometryManager
from session_db import SessionDB
from session import Session
import sqlite3
import json
import uuid
import os
from threading import Lock
from functools import wraps
from datetime import timedelta
from queue import Queue, Empty
import time
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'geometry-learning-secret-key-2024')
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configure caching for static data
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes cache by default
cache = Cache(app)

# Enable response compression (gzip)
app.config['COMPRESS_MIMETYPES'] = ['application/json', 'text/html', 'text/plain']
app.config['COMPRESS_LEVEL'] = 6  # Compression level (1-9, 6 is balanced)
app.config['COMPRESS_MIN_SIZE'] = 500  # Only compress responses > 500 bytes
compress = Compress(app)

# Enable CORS for cross-origin requests
CORS(app, supports_credentials=True)

# ============================================================================
# Connection Pool for Database Performance
# ============================================================================

class ConnectionPool:
    """
    Thread-safe connection pool for SQLite databases.
    Reduces overhead of creating connections per request.
    """
    def __init__(self, db_path, pool_size=10):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = Lock()
        self.total_connections = 0
        
        # Pre-create connections
        for _ in range(pool_size):
            self.pool.put(self._create_connection())
    
    def _create_connection(self):
        """Create a new database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self.total_connections += 1
        return conn
    
    def get_connection(self, timeout=5):
        """Get a connection from the pool."""
        try:
            return self.pool.get(timeout=timeout)
        except Empty:
            # If pool is exhausted, create a new temporary connection
            app.logger.warning(f"Connection pool exhausted, creating temporary connection")
            return self._create_connection()
    
    def return_connection(self, conn):
        """Return a connection to the pool."""
        try:
            self.pool.put_nowait(conn)
        except:
            # Pool is full, close this connection
            conn.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break

# Initialize connection pools
geometry_pool = ConnectionPool('geometry_learning.db', pool_size=10)
sessions_pool = ConnectionPool('sessions.db', pool_size=5)

# Thread locks for database operations
db_lock = Lock()
session_lock = Lock()

# In-memory storage for session state data (keyed by session_id)
# We store state separately and create fresh GeometryManager instances per request
session_states = {}


# ============================================================================
# Helper Functions & Decorators
# ============================================================================

def get_or_create_session_id():
    """Get existing session ID or create a new one."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True
    return session['session_id']


def get_geometry_manager():
    """
    Get a GeometryManager instance for the current session.
    Uses connection pool for better performance.
    Restores session state from in-memory storage.
    """
    session_id = get_or_create_session_id()
    
    # Get connection from pool
    conn = geometry_pool.get_connection()
    
    # Create a new GeometryManager instance with pooled connection
    gm = GeometryManager()
    gm.conn.close()  # Close the default connection
    gm.conn = conn  # Use pooled connection
    
    with session_lock:
        # Restore state if exists
        if session_id in session_states:
            state_data = session_states[session_id]
            gm.state = state_data['state']
            gm.session = state_data['session_obj']
            gm._pending_question = state_data.get('pending_question')
            gm._resume_requested = state_data.get('resume_requested', False)
    
    return gm


def save_geometry_manager_state(gm):
    """
    Save the GeometryManager state to in-memory storage.
    Returns connection to pool instead of closing.
    Called after operations that modify state.
    """
    session_id = get_or_create_session_id()
    
    with session_lock:
        session_states[session_id] = {
            'state': gm.state,
            'session_obj': gm.session,
            'pending_question': gm._pending_question,
            'resume_requested': gm._resume_requested
        }
    
    # Return connection to pool
    try:
        geometry_pool.return_connection(gm.conn)
    except:
        pass


def require_active_session(f):
    """Decorator to ensure there's an active learning session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = session.get('session_id')
        if not session_id or session_id not in session_states:
            return jsonify({
                "error": "No active session found",
                "message": "Please start a new session first"
            }), 400
        return f(*args, **kwargs)
    return decorated_function


def handle_errors(f):
    """Decorator for consistent error handling."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    return decorated_function


def measure_performance(f):
    """Decorator to measure endpoint performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log slow requests (> 100ms)
        if elapsed > 100:
            app.logger.warning(f"{f.__name__} took {elapsed:.2f}ms")
        
        # Add performance header
        if isinstance(result, tuple):
            response, status_code = result[0], result[1]
            if hasattr(response, 'headers'):
                response.headers['X-Response-Time'] = f"{elapsed:.2f}ms"
            return result
        return result
    
    return decorated_function


def add_cache_headers(response_data, max_age=300):
    """
    Add HTTP caching headers (ETag, Cache-Control) to responses.
    Enables browser caching and conditional requests (If-None-Match).
    
    Args:
        response_data: Dict or JSON data to return
        max_age: Cache duration in seconds (default 5 minutes)
    
    Returns:
        Flask response with caching headers
    """
    # Generate ETag from response content
    content = json.dumps(response_data, sort_keys=True)
    etag = hashlib.md5(content.encode('utf-8')).hexdigest()
    
    # Check if client has cached version
    client_etag = request.headers.get('If-None-Match')
    if client_etag == etag:
        # Client has current version, return 304 Not Modified
        response = make_response('', 304)
        response.headers['ETag'] = etag
        return response
    
    # Return full response with caching headers
    response = make_response(jsonify(response_data), 200)
    response.headers['ETag'] = etag
    response.headers['Cache-Control'] = f'public, max-age={max_age}'
    return response


# ============================================================================
# Session Management Endpoints
# ============================================================================

@app.route('/api/session/start', methods=['POST'])
@handle_errors
def start_session():
    """
    Start a new learning session.
    
    Returns:
        session_id: Unique identifier for the session
        message: Confirmation message
    """
    session_id = get_or_create_session_id()
    
    # Clean up any existing state for this session
    with session_lock:
        if session_id in session_states:
            del session_states[session_id]
        
        # Create new initial state
        gm = GeometryManager()
        session_states[session_id] = {
            'state': gm.state,
            'session_obj': gm.session,
            'pending_question': None,
            'resume_requested': False
        }
        gm.close()  # Close the temporary connection
    
    return jsonify({
        "session_id": session_id,
        "message": "New learning session started successfully"
    }), 200


@app.route('/api/session/status', methods=['GET'])
@handle_errors
def session_status():
    """
    Get the current session status and state.
    
    Returns:
        session_id: Current session identifier
        active: Whether session is active
        state: Current learning state (if active)
    """
    session_id = session.get('session_id')
    
    if not session_id or session_id not in session_states:
        return jsonify({
            "active": False,
            "message": "No active session"
        }), 200
    
    # Get state from storage
    with session_lock:
        state_data = session_states[session_id]
    
    return jsonify({
        "session_id": session_id,
        "active": True,
        "state": {
            "triangle_weights": state_data['state']['triangle_weights'],
            "questions_count": state_data['state']['questions_count'],
            "asked_questions": state_data['state']['asked_questions']
        }
    }), 200


@app.route('/api/session/end', methods=['POST'])
@require_active_session
@handle_errors
def end_session():
    """
    End the current learning session.
    Optionally provide feedback and save the session to database.
    
    Request body:
        feedback: Feedback ID (4-7, optional)
        triangle_types: List of triangle type IDs that were relevant (optional)
        helpful_theorems: List of theorem IDs that were helpful (optional)
        save_to_db: Whether to save session to database (default: true)
    
    Returns:
        message: Confirmation message
        session_data: Saved session data (if saved)
    """
    session_id = session['session_id']
    
    # Get the session state
    with session_lock:
        state_data = session_states[session_id]
        session_obj = state_data['session_obj']
    
    data = request.get_json() or {}
    
    # Get optional feedback data
    feedback = data.get('feedback')
    triangle_types = data.get('triangle_types', [])
    helpful_theorems = data.get('helpful_theorems', [])
    save_to_db = data.get('save_to_db', True)
    
    # Validate feedback if provided
    if feedback is not None:
        if feedback not in [4, 5, 6, 7]:
            return jsonify({
                "error": "Invalid feedback value",
                "message": "Feedback must be 4, 5, 6, or 7"
            }), 400
        session_obj.set_feedback(feedback)
    
    # Set triangle types if provided
    if triangle_types:
        valid_types = [t for t in triangle_types if t in [0, 1, 2, 3]]
        if valid_types:
            session_obj.set_triangle_type(valid_types)
    
    # Set helpful theorems if provided
    if helpful_theorems:
        valid_theorems = [t for t in helpful_theorems if 1 <= t <= 63]
        if valid_theorems:
            session_obj.set_helpful_theorems(valid_theorems)
    
    # Save to database if requested
    session_data = None
    if save_to_db:
        with db_lock:
            session_db = SessionDB()
            session_db.save_session(session_obj)
        session_data = session_obj.to_dict()
    
    # Clean up
    with session_lock:
        del session_states[session_id]
    
    session.clear()
    
    return jsonify({
        "message": "Session ended successfully",
        "session_data": session_data
    }), 200


@app.route('/api/session/reset', methods=['POST'])
@require_active_session
@handle_errors
def reset_session():
    """
    Reset the current session state without ending it.
    
    Returns:
        message: Confirmation message
        new_state: The reset state
    """
    session_id = session['session_id']
    
    # Create a fresh manager to get initialized state
    gm = GeometryManager()
    
    # Reset the state in storage
    with session_lock:
        session_states[session_id] = {
            'state': gm.state,
            'session_obj': Session(),
            'pending_question': None,
            'resume_requested': False
        }
        new_state = gm.state
    
    gm.close()
    
    return jsonify({
        "message": "Session state reset successfully",
        "new_state": {
            "triangle_weights": new_state['triangle_weights'],
            "questions_count": new_state['questions_count'],
            "asked_questions": new_state['asked_questions']
        }
    }), 200


# ============================================================================
# Optimized Batch Endpoints (Performance)
# ============================================================================

@app.route('/api/bootstrap', methods=['POST'])
@handle_errors
@measure_performance
def bootstrap_initial_data():
    """
    Bootstrap endpoint that returns all initial data needed for the UI in a single request.
    This dramatically reduces the number of round-trips needed to initialize the page.
    
    Request body (optional):
        auto_start_session: Start a new session automatically (default: true)
        include_theorems: Include full theorems list (default: true)
        include_feedback_options: Include feedback options (default: true)
        include_triangles: Include triangle types (default: true)
    
    Returns:
        session: Session information (if started)
        first_question: First question data (if session started)
        answer_options: Available answer options
        theorems: List of all theorems (if requested)
        feedback_options: Available feedback options (if requested)
        triangles: Triangle types (if requested)
        
    Performance: Replaces 4-6 separate API calls with 1 call
    """
    data = request.get_json() or {}
    auto_start = data.get('auto_start_session', True)
    include_theorems = data.get('include_theorems', True)
    include_feedback = data.get('include_feedback_options', True)
    include_triangles = data.get('include_triangles', True)
    
    result = {}
    
    # Start session and get first question if requested
    if auto_start:
        session_id = get_or_create_session_id()
        
        # Clean up any existing state
        with session_lock:
            if session_id in session_states:
                del session_states[session_id]
            
            # Create new session with GeometryManager
            gm = GeometryManager()
            
            # Get first question
            question_data = gm.get_first_question()
            
            # Save state
            session_states[session_id] = {
                'state': gm.state,
                'session_obj': gm.session,
                'pending_question': question_data,
                'resume_requested': False
            }
            
            geometry_pool.return_connection(gm.conn)
        
        result['session'] = {
            'session_id': session_id,
            'started': True
        }
        
        if 'error' not in question_data:
            result['first_question'] = question_data
            
            # Get answer options for this question
            conn = geometry_pool.get_connection()
            with db_lock:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT answer_id, answer_text, correct 
                    FROM Answers 
                    WHERE question_id = ?
                """, (question_data['question_id'],))
                answers = cursor.fetchall()
            geometry_pool.return_connection(conn)
            
            result['answer_options'] = {
                'question_id': question_data['question_id'],
                'answers': [{
                    'answer_id': ans['answer_id'],
                    'answer_text': ans['answer_text'],
                    'correct': bool(ans['correct'])
                } for ans in answers]
            }
    
    # Get theorems if requested (from cache)
    if include_theorems:
        conn = geometry_pool.get_connection()
        with db_lock:
            cursor = conn.cursor()
            cursor.execute("SELECT theorem_id, theorem_text, category, active FROM Theorems WHERE active = 1")
            rows = cursor.fetchall()
        geometry_pool.return_connection(conn)
        
        result['theorems'] = [{
            'theorem_id': row['theorem_id'],
            'theorem_text': row['theorem_text'],
            'category': row['category'],
            'active': bool(row['active'])
        } for row in rows]
    
    # Get feedback options if requested (from cache)
    if include_feedback:
        conn = geometry_pool.get_connection()
        with db_lock:
            cursor = conn.cursor()
            cursor.execute("SELECT fbID, fb FROM inputFB")
            rows = cursor.fetchall()
        geometry_pool.return_connection(conn)
        
        result['feedback_options'] = [{
            'id': row['fbID'],
            'text': row['fb']
        } for row in rows]
    
    # Get triangle types if requested (from cache)
    if include_triangles:
        conn = geometry_pool.get_connection()
        with db_lock:
            cursor = conn.cursor()
            cursor.execute("SELECT triangle_id, triangle_type, active FROM Triangles")
            rows = cursor.fetchall()
        geometry_pool.return_connection(conn)
        
        result['triangles'] = [{
            'triangle_id': row['triangle_id'],
            'triangle_type': row['triangle_type'],
            'active': bool(row['active'])
        } for row in rows]
    
    return jsonify(result), 200


# ============================================================================
# Question & Answer Flow Endpoints
# ============================================================================

@app.route('/api/questions/first', methods=['GET'])
@require_active_session
@handle_errors
def get_first_question():
    """
    Get the first question for a new session (easy difficulty).
    
    Returns:
        question_id: Question identifier
        question_text: The question text
        difficulty_level: Always 1 (easy)
    """
    gm = get_geometry_manager()
    
    question = gm.get_first_question()
    
    if "error" in question:
        gm.close()
        return jsonify(question), 404
    
    # Store as pending question
    gm._store_pending_question(question)
    
    # Save state
    save_geometry_manager_state(gm)
    
    return jsonify(question), 200


@app.route('/api/questions/next', methods=['GET'])
@require_active_session
@handle_errors
def get_next_question():
    """
    Get the next question based on current learning state.
    Uses adaptive algorithm considering triangle weights and information gain.
    
    Returns:
        question_id: Question identifier
        question_text: The question text
        info: Information about selection algorithm
    """
    gm = get_geometry_manager()
    
    # Check if we should resume a pending question
    if gm._resume_requested and gm._pending_question:
        question = gm._pending_question
        gm._resume_requested = False
    else:
        question = gm.get_next_question()
        if "error" not in question:
            gm._store_pending_question(question)
    
    if "error" in question:
        gm.close()
        return jsonify(question), 404
    
    # Save state
    save_geometry_manager_state(gm)
    
    return jsonify(question), 200


@app.route('/api/questions/<int:question_id>', methods=['GET'])
@handle_errors
def get_question_details(question_id):
    """
    Get details about a specific question.
    
    Path parameters:
        question_id: Question identifier
    
    Returns:
        question_id: Question identifier
        question_text: The question text
        difficulty_level: Question difficulty (1-3)
        active: Whether question is active
    """
    gm = GeometryManager()
    
    with db_lock:
        cursor = gm.conn.cursor()
        cursor.execute("""
            SELECT question_id, question_text, difficulty_level, active
            FROM Questions
            WHERE question_id = ?
        """, (question_id,))
        row = cursor.fetchone()
    
    gm.close()
    
    if not row:
        return jsonify({"error": "Question not found"}), 404
    
    return jsonify({
        "question_id": row["question_id"],
        "question_text": row["question_text"],
        "difficulty_level": row["difficulty_level"],
        "active": bool(row["active"])
    }), 200


@app.route('/api/answers/options', methods=['GET'])
@handle_errors
def get_answer_options():
    """
    Get available answer options.
    
    Returns:
        answers: List of answer options with ID and text
    """
    gm = GeometryManager()
    
    with db_lock:
        cursor = gm.conn.cursor()
        cursor.execute("SELECT ansID, ans FROM inputDuring")
        rows = cursor.fetchall()
    
    answers = [{"id": row["ansID"], "text": row["ans"]} for row in rows]
    
    gm.close()
    
    return jsonify({"answers": answers}), 200


@app.route('/api/answers/submit', methods=['POST'])
@require_active_session
@handle_errors
@measure_performance
def submit_answer():
    """
    Submit an answer to the current question.
    Updates triangle and theorem weights based on the answer.
    
    Request body:
        question_id: Question identifier
        answer_id: Answer identifier (0-3)
        include_next_question: Return next question in response (default: true)
        include_answer_options: Return answer options for next question (default: true)
    
    Returns:
        message: Confirmation message
        updated_weights: New triangle weights
        relevant_theorems: Theorems relevant to this answer
        next_question: Next question data (if requested and available)
        answer_options: Answer options for next question (if requested)
        
    Performance: Combines answer submission + next question fetch in one call
    """
    gm = get_geometry_manager()
    data = request.get_json()
    
    if not data:
        geometry_pool.return_connection(gm.conn)
        return jsonify({"error": "Request body is required"}), 400
    
    question_id = data.get('question_id')
    answer_id = data.get('answer_id')
    include_next = data.get('include_next_question', True)
    include_answers = data.get('include_answer_options', True)
    
    if question_id is None or answer_id is None:
        geometry_pool.return_connection(gm.conn)
        return jsonify({
            "error": "Missing required fields",
            "message": "Both question_id and answer_id are required"
        }), 400
    
    # Validate answer_id
    if answer_id not in [0, 1, 2, 3]:
        geometry_pool.return_connection(gm.conn)
        return jsonify({
            "error": "Invalid answer_id",
            "message": "answer_id must be between 0 and 3"
        }), 400
    
    # Process the answer
    gm.process_answer(question_id, answer_id)
    
    # Get relevant theorems
    relevant_theorems = gm.get_relevant_theorems(question_id, answer_id)
    
    result = {
        "message": "Answer processed successfully",
        "updated_weights": gm.state['triangle_weights'],
        "relevant_theorems": relevant_theorems
    }
    
    # Get next question if requested (performance optimization)
    if include_next:
        try:
            next_question = gm.get_next_question()
            if 'error' not in next_question:
                result['next_question'] = next_question
                
                # Get answer options for next question if requested
                if include_answers and 'question_id' in next_question:
                    cursor = gm.conn.cursor()
                    cursor.execute("""
                        SELECT answer_id, answer_text, correct 
                        FROM Answers 
                        WHERE question_id = ?
                    """, (next_question['question_id'],))
                    answers = cursor.fetchall()
                    
                    result['answer_options'] = {
                        'question_id': next_question['question_id'],
                        'answers': [{
                            'answer_id': ans['answer_id'],
                            'answer_text': ans['answer_text'],
                            'correct': bool(ans['correct'])
                        } for ans in answers]
                    }
            else:
                result['next_question'] = None
                result['session_complete'] = True
        except Exception as e:
            app.logger.warning(f"Could not fetch next question: {e}")
            result['next_question'] = None
    
    # Save state
    save_geometry_manager_state(gm)
    
    return jsonify(result), 200


# ============================================================================
# Theorem Endpoints
# ============================================================================

@app.route('/api/theorems', methods=['GET'])
@handle_errors
@measure_performance
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes based on query params
def get_all_theorems():
    """
    Get all theorems in the system.
    
    Query parameters:
        active_only: Return only active theorems (default: true)
        category: Filter by triangle category (0-3, optional)
    
    Returns:
        theorems: List of theorems with details
    """
    conn = geometry_pool.get_connection()
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    category = request.args.get('category', type=int)
    
    with db_lock:
        cursor = conn.cursor()
        
        query = "SELECT theorem_id, theorem_text, category, active FROM Theorems"
        conditions = []
        params = []
        
        if active_only:
            conditions.append("active = 1")
        
        if category is not None:
            conditions.append("category = ?")
            params.append(category)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    theorems = [{
        "theorem_id": row["theorem_id"],
        "theorem_text": row["theorem_text"],
        "category": row["category"],
        "active": bool(row["active"])
    } for row in rows]
    
    geometry_pool.return_connection(conn)
    
    # Return with HTTP caching headers (ETag, Cache-Control)
    return add_cache_headers({"theorems": theorems}, max_age=300)


@app.route('/api/theorems/<int:theorem_id>', methods=['GET'])
@handle_errors
def get_theorem_details(theorem_id):
    """
    Get detailed information about a specific theorem.
    
    Path parameters:
        theorem_id: Theorem identifier
    
    Returns:
        theorem_id: Theorem identifier
        theorem_text: The theorem text
        category: Triangle category
        active: Whether theorem is active
        general_helpfulness: Overall helpfulness score
    """
    gm = GeometryManager()
    
    with db_lock:
        cursor = gm.conn.cursor()
        
        # Get theorem basic info
        cursor.execute("""
            SELECT theorem_id, theorem_text, category, active
            FROM Theorems
            WHERE theorem_id = ?
        """, (theorem_id,))
        row = cursor.fetchone()
        
        if not row:
            gm.close()
            return jsonify({"error": "Theorem not found"}), 404
        
        # Get general helpfulness
        cursor.execute("""
            SELECT general_helpfulness
            FROM TheoremGeneralHelpfulness
            WHERE theorem_id = ?
        """, (theorem_id,))
        helpfulness_row = cursor.fetchone()
    
    result = {
        "theorem_id": row["theorem_id"],
        "theorem_text": row["theorem_text"],
        "category": row["category"],
        "active": bool(row["active"]),
        "general_helpfulness": helpfulness_row["general_helpfulness"] if helpfulness_row else 0
    }
    
    gm.close()
    
    return jsonify(result), 200


@app.route('/api/theorems/relevant', methods=['POST'])
@require_active_session
@handle_errors
def get_relevant_theorems():
    """
    Get theorems relevant to a specific question and answer combination.
    
    Request body:
        question_id: Question identifier
        answer_id: Answer identifier
        base_threshold: Minimum threshold for theorem weights (optional, default: 0.01)
    
    Returns:
        theorems: List of relevant theorems sorted by relevance score
    """
    gm = get_geometry_manager()
    data = request.get_json()
    
    if not data:
        gm.close()
        return jsonify({"error": "Request body is required"}), 400
    
    question_id = data.get('question_id')
    answer_id = data.get('answer_id')
    base_threshold = data.get('base_threshold', 0.01)
    
    if question_id is None or answer_id is None:
        gm.close()
        return jsonify({
            "error": "Missing required fields",
            "message": "Both question_id and answer_id are required"
        }), 400
    
    theorems = gm.get_relevant_theorems(question_id, answer_id, base_threshold)
    
    gm.close()
    
    return jsonify({"theorems": theorems}), 200


# ============================================================================
# Session History & Statistics Endpoints
# ============================================================================

@app.route('/api/sessions/history', methods=['GET'])
@handle_errors
def get_session_history():
    """
    Get all saved sessions from the database.
    
    Query parameters:
        limit: Maximum number of sessions to return (optional)
        offset: Number of sessions to skip (optional, for pagination)
    
    Returns:
        sessions: List of saved session data
        total: Total number of sessions
    """
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    with db_lock:
        session_db = SessionDB()
        all_sessions = session_db.load_all_sessions()
    
    total = len(all_sessions)
    
    # Apply pagination
    if limit:
        sessions = all_sessions[offset:offset + limit]
    else:
        sessions = all_sessions[offset:]
    
    return jsonify({
        "sessions": sessions,
        "total": total,
        "returned": len(sessions)
    }), 200


@app.route('/api/sessions/current', methods=['GET'])
@require_active_session
@handle_errors
def get_current_session_data():
    """
    Get the current session's interaction data.
    
    Returns:
        session_id: Current session identifier
        interactions: List of question-answer pairs
        feedback: Feedback value (if set)
        triangle_type: Triangle types (if set)
        helpful_theorems: Helpful theorem IDs (if set)
    """
    session_id = session['session_id']
    
    # Get session object from storage
    with session_lock:
        session_obj = session_states[session_id]['session_obj']
    
    return jsonify(session_obj.to_dict()), 200


@app.route('/api/sessions/statistics', methods=['GET'])
@handle_errors
def get_session_statistics():
    """
    Get aggregated statistics from all saved sessions.
    
    Returns:
        total_sessions: Total number of saved sessions
        feedback_distribution: Count of each feedback type
        average_interactions: Average number of interactions per session
        most_helpful_theorems: Top helpful theorems across all sessions
    """
    with db_lock:
        session_db = SessionDB()
        all_sessions = session_db.load_all_sessions()
    
    if not all_sessions:
        return jsonify({
            "total_sessions": 0,
            "message": "No sessions found"
        }), 200
    
    # Calculate statistics
    feedback_dist = {4: 0, 5: 0, 6: 0, 7: 0}
    total_interactions = 0
    theorem_counts = {}
    
    for sess in all_sessions:
        # Feedback distribution
        fb = sess.get('feedback')
        if fb in feedback_dist:
            feedback_dist[fb] += 1
        
        # Interactions
        total_interactions += len(sess.get('interactions', []))
        
        # Helpful theorems
        for tid in sess.get('helpful_theorems', []):
            theorem_counts[tid] = theorem_counts.get(tid, 0) + 1
    
    # Sort theorems by count
    top_theorems = sorted(theorem_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return jsonify({
        "total_sessions": len(all_sessions),
        "feedback_distribution": feedback_dist,
        "average_interactions": total_interactions / len(all_sessions) if all_sessions else 0,
        "most_helpful_theorems": [{"theorem_id": tid, "count": count} for tid, count in top_theorems]
    }), 200


@app.route('/api/admin/dashboard', methods=['GET'])
@handle_errors
@measure_performance
def get_admin_dashboard():
    """
    Get comprehensive admin dashboard data in a single request.
    Combines session statistics, theorems, and system health.
    
    Returns:
        statistics: Session statistics
        theorems: All theorems with details
        system_health: Current system status
        active_sessions: Number of active sessions
        
    Performance: Replaces 3-4 separate API calls with 1 call
    """
    result = {}
    
    # Get session statistics
    with db_lock:
        session_db = SessionDB()
        all_sessions = session_db.load_all_sessions()
    
    if all_sessions:
        feedback_dist = {4: 0, 5: 0, 6: 0, 7: 0}
        total_interactions = 0
        theorem_counts = {}
        
        for sess in all_sessions:
            fb = sess.get('feedback')
            if fb in feedback_dist:
                feedback_dist[fb] += 1
            total_interactions += len(sess.get('interactions', []))
            for tid in sess.get('helpful_theorems', []):
                theorem_counts[tid] = theorem_counts.get(tid, 0) + 1
        
        top_theorems = sorted(theorem_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        result['statistics'] = {
            "total_sessions": len(all_sessions),
            "feedback_distribution": feedback_dist,
            "average_interactions": total_interactions / len(all_sessions),
            "most_helpful_theorems": [{"theorem_id": tid, "count": count} for tid, count in top_theorems]
        }
    else:
        result['statistics'] = {"total_sessions": 0, "message": "No sessions found"}
    
    # Get all theorems
    conn = geometry_pool.get_connection()
    with db_lock:
        cursor = conn.cursor()
        cursor.execute("SELECT theorem_id, theorem_text, category, active FROM Theorems WHERE active = 1")
        rows = cursor.fetchall()
    
    result['theorems'] = [{
        "theorem_id": row["theorem_id"],
        "theorem_text": row["theorem_text"],
        "category": row["category"],
        "active": bool(row["active"])
    } for row in rows]
    
    geometry_pool.return_connection(conn)
    
    # System health info
    result['system_health'] = {
        "status": "healthy",
        "active_sessions": len(session_states),
        "connection_pool_size": geometry_pool.pool_size,
        "total_connections": geometry_pool.total_connections
    }
    
    return jsonify(result), 200


# ============================================================================
# Feedback Endpoints
# ============================================================================

@app.route('/api/feedback/options', methods=['GET'])
@handle_errors
@measure_performance
@cache.cached(timeout=600)  # Cache for 10 minutes - rarely changes
def get_feedback_options():
    """
    Get available feedback options.
    
    Returns:
        feedback_options: List of feedback options with ID and text
    """
    conn = geometry_pool.get_connection()
    
    with db_lock:
        cursor = conn.cursor()
        cursor.execute("SELECT fbID, fb FROM inputFB")
        rows = cursor.fetchall()
    
    feedback_options = [{"id": row["fbID"], "text": row["fb"]} for row in rows]
    
    geometry_pool.return_connection(conn)
    
    # Return with HTTP caching headers (static data, cache longer)
    return add_cache_headers({"feedback_options": feedback_options}, max_age=600)


@app.route('/api/feedback/submit', methods=['POST'])
@require_active_session
@handle_errors
def submit_feedback():
    """
    Submit feedback for the current session (without ending it).
    
    Request body:
        feedback: Feedback ID (4-7)
        triangle_types: List of relevant triangle type IDs (optional)
        helpful_theorems: List of helpful theorem IDs (optional)
    
    Returns:
        message: Confirmation message
    """
    session_id = session['session_id']
    
    # Get session data from storage
    with session_lock:
        state_data = session_states[session_id]
        session_obj = state_data['session_obj']
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    feedback = data.get('feedback')
    
    if feedback is None:
        return jsonify({"error": "feedback is required"}), 400
    
    if feedback not in [4, 5, 6, 7]:
        return jsonify({
            "error": "Invalid feedback value",
            "message": "Feedback must be 4, 5, 6, or 7"
        }), 400
    
    session_obj.set_feedback(feedback)
    
    # Handle return to exercise (feedback 7)
    if feedback == 7:
        with session_lock:
            session_states[session_id]['resume_requested'] = True
        return jsonify({
            "message": "Feedback recorded. Will resume current question.",
            "action": "resume"
        }), 200
    
    # Optional: Set triangle types and helpful theorems
    triangle_types = data.get('triangle_types', [])
    if triangle_types:
        valid_types = [t for t in triangle_types if t in [0, 1, 2, 3]]
        if valid_types:
            session_obj.set_triangle_type(valid_types)
    
    helpful_theorems = data.get('helpful_theorems', [])
    if helpful_theorems:
        valid_theorems = [t for t in helpful_theorems if 1 <= t <= 63]
        if valid_theorems:
            session_obj.set_helpful_theorems(valid_theorems)
    
    return jsonify({"message": "Feedback recorded successfully"}), 200


# ============================================================================
# Database Utility Endpoints
# ============================================================================

@app.route('/api/db/tables', methods=['GET'])
@handle_errors
def get_database_tables():
    """
    Get list of all tables in the geometry database.
    
    Returns:
        tables: List of table names
    """
    gm = GeometryManager()
    
    with db_lock:
        cursor = gm.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = cursor.fetchall()
    
    tables = [row[0] for row in rows]
    
    gm.close()
    
    return jsonify({"tables": tables}), 200


@app.route('/api/db/triangles', methods=['GET'])
@handle_errors
@measure_performance
@cache.cached(timeout=600)  # Cache for 10 minutes - rarely changes
def get_triangle_types():
    """
    Get all triangle types.
    
    Returns:
        triangles: List of triangle types with IDs
    """
    conn = geometry_pool.get_connection()
    
    with db_lock:
        cursor = conn.cursor()
        cursor.execute("SELECT triangle_id, triangle_type, active FROM Triangles")
        rows = cursor.fetchall()
    
    triangles = [{
        "triangle_id": row["triangle_id"],
        "triangle_type": row["triangle_type"],
        "active": bool(row["active"])
    } for row in rows]
    
    geometry_pool.return_connection(conn)
    
    # Return with HTTP caching headers (static data, cache longer)
    return add_cache_headers({"triangles": triangles}, max_age=600)


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        status: Server status
        active_sessions: Number of active learning sessions
    """
    return jsonify({
        "status": "healthy",
        "active_sessions": len(session_states)
    }), 200


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 17654))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("=" * 60)
    print("🚀 Geometry Learning API Server")
    print("=" * 60)
    print(f"📡 Server starting on http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    print("📚 API Documentation: See API_DOCUMENTATION.md")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True  # Enable threading for concurrent requests
    )
