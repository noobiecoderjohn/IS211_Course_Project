from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import sqlite3
import secrets

app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)

def initialize_database():
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT, author TEXT,
                 page_count INTEGER, average_rating REAL, thumbnail_url TEXT)''')
    conn.commit()
    conn.close()

initialize_database()

def fetch_book_details(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data:
            item = data['items'][0]['volumeInfo']
            title = item.get('title', 'Unknown')
            author = item.get('authors', ['Unknown'])[0]
            page_count = item.get('pageCount')
            average_rating = item.get('averageRating')
            return {'title': title, 'author': author, 'page_count': page_count,
                    'average_rating': average_rating}
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user_id'] = 1  
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('SELECT * FROM books WHERE user_id = ?', (session['user_id'],))
    books = c.fetchall()
    conn.close()
    return render_template('dashboard.html', books=books)

@app.route('/addbook', methods=['POST'])
def addbook():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    isbn = request.form['isbn']
    book_details = fetch_book_details(isbn)
    if book_details:
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('INSERT INTO books (user_id, title, author, page_count, average_rating) VALUES (?, ?, ?, ?, ?, ?)',
                  (session['user_id'], book_details['title'], book_details['author'], book_details['page_count'],
                   book_details['average_rating']))
        conn.commit()
        conn.close()
    else:
        flash('Could not find book with that ISBN.')

    return redirect(url_for('dashboard'))

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ? AND user_id = ?', (book_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

