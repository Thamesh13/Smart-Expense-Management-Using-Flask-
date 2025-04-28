# APP for Flask
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os


app = Flask(__name__)
app.secret_key = 'supersecretkey'
 
DB_PATH='expenses.db'
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item TEXT,
                category TEXT,
                reason TEXT,
                amount REAL
            )
        """)

        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")

        conn.execute('''ALTER TABLE expenses ADD COLUMN date TEXT;''')
 
print('Users Table created successfully')
print("Expenses table created successfully")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        with sqlite3.connect(DB_PATH) as conn:
            try:
                conn.execute('INSERT INTO users (name, phone, email, password) VALUES (?, ?, ?, ?)',
                             (name, phone, email, password))
                flash('Registration successful! Please log in.')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Email already registered. Please use a different email.')

    return render_template('Register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect(DB_PATH) as conn: 
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

            if user and check_password_hash(user[4], password):
                session['user_id'] = user[0]
                session['username'] = user[1]  # Name
                flash('Login successful!')
                return redirect(url_for('welcome'))
            else:
                flash('Invalid credentials')
    return render_template('Login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', username=session['username'])


@app.route('/')
def home():
    return render_template('home.html')


def get_user_expense_table():
    user_id = session.get('user_id')
    return f'expenses_user_{user_id}'

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    table_name = get_user_expense_table()

    with sqlite3.connect(DB_PATH) as conn:
        # Create table if it doesn't exist
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item TEXT,
                category TEXT,
                reason TEXT,
                amount REAL
            )
        """)

        if request.method == 'POST':
            date = request.form['date']
            item = request.form['item']
            category = request.form['category']
            reason = request.form['reason']
            amount = float(request.form['amount'])

            conn.execute(f"""
                INSERT INTO {table_name} (date, item, category, reason, amount)
                VALUES (?, ?, ?, ?, ?)
            """, (date, item, category, reason, amount))

            return redirect(url_for('view_expenses'))

    return render_template('add_expenses.html')

@app.route('/view')
def view_expenses():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    table_name = get_user_expense_table()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item TEXT,
                category TEXT,
                reason TEXT,
                amount REAL
            )
        """)
        expenses = conn.execute(f"SELECT * FROM {table_name} ORDER BY date DESC").fetchall()

    return render_template('view_expenses.html', expenses=expenses)


@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    table_name = get_user_expense_table()

    with sqlite3.connect(DB_PATH) as conn:
        if request.method == 'POST':
            date = request.form['date']
            item = request.form['item']
            category = request.form['category']
            reason = request.form['reason']
            amount = float(request.form['amount'])

            conn.execute(f"""
                UPDATE {table_name}
                SET date = ?, item = ?, category = ?, reason = ?, amount = ?
                WHERE id = ?
            """, (date, item, category, reason, amount, expense_id))
            return redirect(url_for('view_expenses'))

        # GET request - Fetch old data for that user
        expense = conn.execute(f"SELECT * FROM {table_name} WHERE id = ?", (expense_id,)).fetchone()

    return render_template('edit_expenses.html', expense=expense)

@app.route('/delete/<int:expense_id>')
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    table_name = get_user_expense_table()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (expense_id,))

    return redirect(url_for('view_expenses'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
