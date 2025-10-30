from flask import Flask, session, jsonify
from geometry_manager import GeometryManager

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # נדרש כדי לאחסן מידע ב-session

@app.route('/start')
def start_session():
    manager = GeometryManager()
    manager.reset_session()
    return jsonify({"message": "Session initialized!"})

if __name__ == '__main__':
    app.run(debug=True)
