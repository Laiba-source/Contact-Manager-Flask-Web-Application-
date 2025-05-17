from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

DATABASE = 'contact_manager.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Create contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash("Please fill out all fields.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another one.')
            return redirect(url_for('register'))
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access your dashboard.')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts WHERE user_id = ?", (user_id,))
    contacts = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', contacts=contacts)
@app.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
    if 'user_id' not in session:
        flash('Please login to add contacts.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        user_id = session['user_id']

        if not name:
            flash('Name is required.')
            return redirect(url_for('add_contact'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contacts (user_id, name, phone, email) VALUES (?, ?, ?, ?)",
                       (user_id, name, phone, email))
        conn.commit()
        conn.close()

        flash('Contact added successfully.')
        return redirect(url_for('dashboard'))

    return render_template('add_contact.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))
@app.route('/edit_contact/<int:contact_id>', methods=['GET', 'POST'])
def edit_contact(contact_id):
    if 'user_id' not in session:
        flash('Login required.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts WHERE id = ? AND user_id = ?", (contact_id, session['user_id']))
    contact = cursor.fetchone()

    if not contact:
        flash('Contact not found.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']

        cursor.execute("UPDATE contacts SET name = ?, phone = ?, email = ? WHERE id = ? AND user_id = ?",
                       (name, phone, email, contact_id, session['user_id']))
        conn.commit()
        conn.close()

        flash('Contact updated successfully.')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit_contact.html', contact=contact)
@app.route('/delete_contact/<int:contact_id>')
def delete_contact(contact_id):
    if 'user_id' not in session:
        flash('Login required.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id = ? AND user_id = ?", (contact_id, session['user_id']))
    conn.commit()
    conn.close()

    flash('Contact deleted successfully.')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
