# SQLite Database Manager for SpendWise
import sqlite3
import hashlib
import os
import json
import secrets
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'spendwise.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            currency TEXT DEFAULT 'INR',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            frequency TEXT DEFAULT 'one_time',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            user_id TEXT PRIMARY KEY,
            monthly_total REAL NOT NULL,
            weekly_total REAL NOT NULL,
            category_budgets_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return hashed, salt

def verify_password(password, salt, hashed):
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed

# User Operations
def create_user(email, password, name, currency='INR'):
    conn = get_db_connection()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    
    # Check if exists
    cursor.execute('SELECT id FROM users WHERE email = ?', (email_clean,))
    if cursor.fetchone():
        conn.close()
        return None, 'Email is already registered.'

    user_id = 'usr_' + secrets.token_hex(8)
    password_hash, salt = hash_password(password)

    cursor.execute('''
        INSERT INTO users (id, email, name, password_hash, salt, currency)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, email_clean, name.strip(), password_hash, salt, currency))

    # Initialize default budget for user (adjusted for currency defaults)
    default_cat_budgets = {
        'food': 12000 if currency == 'INR' else 450,
        'groceries': 10000 if currency == 'INR' else 400,
        'transportation': 6000 if currency == 'INR' else 250,
        'housing': 25000 if currency == 'INR' else 1200,
        'utilities': 5000 if currency == 'INR' else 200,
        'entertainment': 4000 if currency == 'INR' else 200,
        'subscriptions': 2000 if currency == 'INR' else 80,
        'shopping': 8000 if currency == 'INR' else 300,
        'healthcare': 4000 if currency == 'INR' else 150,
        'miscellaneous': 4000 if currency == 'INR' else 150
    }
    monthly_tot = sum(default_cat_budgets.values())
    weekly_tot = round(monthly_tot / 4)

    cursor.execute('''
        INSERT INTO budgets (user_id, monthly_total, weekly_total, category_budgets_json)
        VALUES (?, ?, ?, ?)
    ''', (user_id, monthly_tot, weekly_tot, json.dumps(default_cat_budgets)))

    conn.commit()
    conn.close()

    # Seed 3+ months rich sample data for new user
    seed_user_demo_transactions(user_id, currency)

    return user_id, None

def authenticate_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    email_clean = email.strip().lower()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email_clean,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return None, 'Invalid email or password.'

    if not verify_password(password, user['salt'], user['password_hash']):
        conn.close()
        return None, 'Invalid email or password.'

    # Create session token valid for 30 days
    token = 'tok_' + secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=30)

    cursor.execute('''
        INSERT INTO sessions (token, user_id, expires_at)
        VALUES (?, ?, ?)
    ''', (token, user['id'], expires_at.isoformat()))

    conn.commit()
    conn.close()

    return {
        'token': token,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'currency': user['currency']
        }
    }, None

def get_user_by_token(token):
    if not token:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.id, users.email, users.name, users.currency, sessions.expires_at
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.token = ?
    ''', (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    
    expires_at = datetime.fromisoformat(row['expires_at'])
    if datetime.now() > expires_at:
        return None

    return {
        'id': row['id'],
        'email': row['email'],
        'name': row['name'],
        'currency': row['currency']
    }

def update_user_profile(user_id, name=None, currency=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if name and currency:
        cursor.execute('UPDATE users SET name = ?, currency = ? WHERE id = ?', (name, currency, user_id))
    elif name:
        cursor.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
    elif currency:
        cursor.execute('UPDATE users SET currency = ? WHERE id = ?', (currency, user_id))
    conn.commit()
    conn.close()

def delete_session(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
    conn.commit()
    conn.close()

# Transaction Operations
def get_user_transactions(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, date, amount, category, payment_method as paymentMethod, frequency, notes, created_at as createdAt
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_user_transaction(user_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    tx_id = 'tx_' + str(int(datetime.now().timestamp() * 1000)) + '_' + secrets.token_hex(4)
    created_at = datetime.now().isoformat()

    cursor.execute('''
        INSERT INTO transactions (id, user_id, date, amount, category, payment_method, frequency, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tx_id,
        user_id,
        data['date'],
        float(data['amount']),
        data['category'],
        data.get('paymentMethod', 'credit_card'),
        data.get('frequency', 'one_time'),
        data.get('notes', ''),
        created_at
    ))
    conn.commit()
    conn.close()
    return {
        'id': tx_id,
        'user_id': user_id,
        'date': data['date'],
        'amount': float(data['amount']),
        'category': data['category'],
        'paymentMethod': data.get('paymentMethod', 'credit_card'),
        'frequency': data.get('frequency', 'one_time'),
        'notes': data.get('notes', ''),
        'createdAt': created_at
    }

def update_user_transaction(user_id, tx_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions
        SET date = ?, amount = ?, category = ?, payment_method = ?, frequency = ?, notes = ?
        WHERE id = ? AND user_id = ?
    ''', (
        data['date'],
        float(data['amount']),
        data['category'],
        data.get('paymentMethod', 'credit_card'),
        data.get('frequency', 'one_time'),
        data.get('notes', ''),
        tx_id,
        user_id
    ))
    conn.commit()
    conn.close()
    return True

def delete_user_transaction(user_id, tx_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ? AND user_id = ?', (tx_id, user_id))
    conn.commit()
    conn.close()
    return True

# Budget Operations
def get_user_budgets(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT monthly_total, weekly_total, category_budgets_json FROM budgets WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'monthlyTotal': row['monthly_total'],
            'weeklyTotal': row['weekly_total'],
            'categoryBudgets': json.loads(row['category_budgets_json'])
        }
    return {
        'monthlyTotal': 50000,
        'weeklyTotal': 12500,
        'categoryBudgets': {}
    }

def save_user_budgets(user_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cat_json = json.dumps(data.get('categoryBudgets', {}))
    cursor.execute('''
        INSERT INTO budgets (user_id, monthly_total, weekly_total, category_budgets_json, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            monthly_total = excluded.monthly_total,
            weekly_total = excluded.weekly_total,
            category_budgets_json = excluded.category_budgets_json,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, float(data['monthlyTotal']), float(data['weeklyTotal']), cat_json))
    conn.commit()
    conn.close()
    return True

# Seed 3+ Months Demo Data
def seed_user_demo_transactions(user_id, currency='INR'):
    import random
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Delete existing transactions for user if re-seeding
    cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    
    today = datetime.now()
    multiplier = 75 if currency == 'INR' else 1

    recurring = [
        (1, 1200 * multiplier, 'housing', 'Monthly Apartment Rent / EMI', 'upi_transfer', 'monthly'),
        (3, 85 * multiplier, 'utilities', 'Electricity & Gas Bill', 'debit_card', 'monthly'),
        (5, 55 * multiplier, 'utilities', 'High-speed Fiber Broadband', 'credit_card', 'monthly'),
        (8, 15 * multiplier, 'subscriptions', 'Netflix Premium 4K', 'credit_card', 'monthly'),
        (10, 10 * multiplier, 'subscriptions', 'Spotify Premium Duo', 'credit_card', 'monthly'),
        (12, 25 * multiplier, 'subscriptions', 'Fitness Gym Pass', 'debit_card', 'monthly'),
        (20, 45 * multiplier, 'healthcare', 'Monthly Vitamins & Pharmacy', 'credit_card', 'monthly')
    ]

    activities = [
        ('food', ['Artisan Coffee & Snacks', 'Family Weekend Dinner', 'Food Delivery Order', 'Brunch with Colleagues', 'Gourmet Bistro Takeout', 'Café Cold Brew'], 8 * multiplier, 65 * multiplier, ['upi_transfer', 'credit_card', 'cash']),
        ('groceries', ['Weekly Supermarket Haul', 'Fresh Organic Fruits & Veggies', 'Dairy, Bread & Pantry Staples', 'Wholesale Market Restock'], 35 * multiplier, 140 * multiplier, ['debit_card', 'upi_transfer']),
        ('transportation', ['Petrol / Fuel Refill', 'City Metro Transit Card', 'Cab / Ride Share', 'Parking Toll Fee', 'Car Service & Maintenance'], 15 * multiplier, 55 * multiplier, ['upi_transfer', 'credit_card']),
        ('shopping', ['Casual Apparel & Footwear', 'Online Electronics Order', 'Home Utility & Decor', 'Stationery & Books'], 20 * multiplier, 120 * multiplier, ['credit_card', 'debit_card']),
        ('entertainment', ['Movie IMAX Tickets', 'Gaming Store Purchase', 'Weekend Concert Passes', 'Board Games & Sports Lounge'], 15 * multiplier, 70 * multiplier, ['credit_card', 'upi_transfer']),
        ('miscellaneous', ['Courier & Shipping', 'Dry Cleaning & Laundry', 'Hardware Supplies'], 10 * multiplier, 45 * multiplier, ['cash', 'upi_transfer'])
    ]

    # Generate for 4 months (120 days)
    for m_offset in range(3, -1, -1):
        # Calculate target month
        year = today.year
        month = today.month - m_offset
        while month <= 0:
            month += 12
            year -= 1
        
        # Max day
        if month in [1, 3, 5, 7, 8, 10, 12]:
            days_in_m = 31
        elif month in [4, 6, 9, 11]:
            days_in_m = 30
        else:
            days_in_m = 29 if year % 4 == 0 else 28
        
        is_cur = (m_offset == 0)
        max_d = today.day if is_cur else days_in_m

        # Add fixed
        for day, amt, cat, notes, method, freq in recurring:
            if day <= max_d:
                d_str = f"{year:04d}-{month:02d}-{day:02d}"
                tx_id = f"seed_{m_offset}_{day}_{secrets.token_hex(4)}"
                cursor.execute('''
                    INSERT INTO transactions (id, user_id, date, amount, category, payment_method, frequency, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tx_id, user_id, d_str, amt, cat, method, freq, notes, f"{d_str}T10:00:00"))

        # Add variable
        for day in range(1, max_d + 1):
            date_obj = datetime(year, month, day)
            is_wknd = date_obj.weekday() in [4, 5, 6]
            count = 2 if (is_wknd and random.random() > 0.4) else (1 if random.random() > 0.55 else 0)

            for _ in range(count):
                cat, notes_list, min_a, max_a, methods = random.choice(activities)
                note = random.choice(notes_list)
                amt = round(random.uniform(min_a, max_a), 2)
                method = random.choice(methods)
                d_str = f"{year:04d}-{month:02d}-{day:02d}"
                tx_id = f"seed_var_{m_offset}_{day}_{secrets.token_hex(4)}"
                cursor.execute('''
                    INSERT INTO transactions (id, user_id, date, amount, category, payment_method, frequency, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (tx_id, user_id, d_str, amt, cat, method, 'one_time', note, f"{d_str}T14:30:00"))

    conn.commit()
    conn.close()

# Initialize on import
init_db()
