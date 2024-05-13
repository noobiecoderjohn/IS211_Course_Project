from flask import Flask, render_template, request, redirect, url_for
import requests
import sqlite3

app = Flask(__name__, template_folder='templates')

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
            thumbnail_url = item['imageLinks']['thumbnail'] if 'imageLinks' in item else None
            return {'title': title, 'author': author, 'page_count': page_count,
                    'average_rating': average_rating, 'thumbnail_url': thumbnail_url}
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():

    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('SELECT * FROM books')
    books = c.fetchall()
    conn.close()
    return render_template('dashboard.html', books=books)

@app.route('/add_book', methods=['POST'])
def add_book():
    isbn = request.form['isbn']
    book_details = fetch_book_details(isbn)
    if book_details:
        conn = sqlite3.connect('books.db')
        c = conn.cursor()
        c.execute('INSERT INTO books (title, author, page_count, average_rating, thumbnail_url) VALUES (?, ?, ?, ?, ?)',
                  (book_details['title'], book_details['author'], book_details['page_count'],
                   book_details['average_rating'], book_details['thumbnail_url']))
        conn.commit()
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    conn = sqlite3.connect('books.db')
    c = conn.cursor()
    c.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
