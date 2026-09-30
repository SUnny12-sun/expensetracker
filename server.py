# Flask REST API Server for SpendWise Expense Tracker
import os
import json
from flask import Flask, request, jsonify, send_from_directory, make_response
import database

app = Flask(__name__, static_folder='.', static_url_path='')

# Simple CORS support
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

def get_auth_user():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
        user = database.get_user_by_token(token)
        return user, token
    return None, None

# ----------------- STATIC ASSETS -----------------
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

# ----------------- AUTH APIS -----------------
@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    currency = data.get('currency', 'INR')

    if not email or not password or not name:
        return jsonify({'error': 'Email, password, and name are required.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    user_id, err = database.create_user(email, password, name, currency)
    if err:
        return jsonify({'error': err}), 400

    auth_data, err = database.authenticate_user(email, password)
    if err:
        return jsonify({'error': err}), 400

    return jsonify(auth_data), 201

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    auth_data, err = database.authenticate_user(email, password)
    if err:
        return jsonify({'error': err}), 401

    return jsonify(auth_data), 200

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return ('', 204)
    _, token = get_auth_user()
    if token:
        database.delete_session(token)
    return jsonify({'success': True}), 200

@app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
def get_me():
    if request.method == 'OPTIONS':
        return ('', 204)
    user, _ = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'user': user}), 200

@app.route('/api/auth/profile', methods=['PUT', 'OPTIONS'])
def update_profile():
    if request.method == 'OPTIONS':
        return ('', 204)
    user, _ = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    database.update_user_profile(user['id'], data.get('name'), data.get('currency'))
    updated_user = database.get_user_by_token(request.headers.get('Authorization', '')[7:].strip())
    return jsonify({'user': updated_user}), 200

# ----------------- TRANSACTION APIS -----------------
@app.route('/api/transactions', methods=['GET', 'POST', 'OPTIONS'])
def transactions():
    if request.method == 'OPTIONS':
        return ('', 204)
    user, _ = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        txs = database.get_user_transactions(user['id'])
        return jsonify({'transactions': txs}), 200

    elif request.method == 'POST':
        data = request.get_json() or {}
        if not data.get('amount') or not data.get('date') or not data.get('category'):
            return jsonify({'error': 'Amount, date, and category are required.'}), 400
        new_tx = database.add_user_transaction(user['id'], data)
        return jsonify({'transaction': new_tx}), 201

@app.route('/api/transactions/<tx_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def single_transaction(tx_id):
    if request.method == 'OPTIONS':
        return ('', 204)
    user, _ = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'PUT':
        data = request.get_json() or {}
        database.update_user_transaction(user['id'], tx_id, data)
        return jsonify({'success': True}), 200

    elif request.method == 'DELETE':
        database.delete_user_transaction(user['id'], tx_id)
        return jsonify({'success': True}), 200

@app.route('/api/transactions/seed', methods=['POST', 'OPTIONS'])
def seed_demo():
    if request.method == 'OPTIONS':
        return ('', 204)
    user, _ = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    database.seed_user_demo_transactions(user['id'], user.get('currency', 'INR'))
    txs = database.get_user_transactions(user['id'])
    return jsonify({'transactions': txs, 'message': '3+ months sample data seeded.'}), 200

# ----------------- BUDGET APIS -----------------
@app.route('/api/budgets', methods=['GET', 'POST', 'OPTIONS'])
def budgets():
    if request.method == 'OPTIONS':
        return ('', 204)
    user, _ = get_auth_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        b = database.get_user_budgets(user['id'])
        return jsonify({'budgets': b}), 200

    elif request.method == 'POST':
        data = request.get_json() or {}
        database.save_user_budgets(user['id'], data)
        return jsonify({'success': True}), 200

if __name__ == '__main__':
    database.init_db()
    port = int(os.environ.get('PORT', 5000))
    print(f"SpendWise Server running at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
