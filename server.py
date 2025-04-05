"""
Серверна частина додатку для обміну книгами.
Реалізовано на Flask з MySQL базою даних.
"""

from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)

# Конфігурація для завантаження файлів
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Обмеження розміру файлів (16 МБ)

# Створення каталогу для завантажень, якщо його не існує
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Конфігурація бази даних
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1111',  # Змініть на свій пароль
    'database': 'book_ex1'
}

# Функція для перевірки дозволених розширень файлів
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Функція для створення бази даних
def create_database():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
            print(f"База даних {db_config['database']} успішно створена або вже існує")
            cursor.close()
    except Error as e:
        print(f"Помилка при створенні бази даних: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

# Функція для підключення до бази даних
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("З'єднання з MySQL успішно встановлено")
    except Error as e:
        print(f"Помилка при підключенні до MySQL: {e}")
    return connection

# Створення таблиць при першому запуску
def setup_database():
    # Спочатку створюємо базу даних, якщо вона не існує
    create_database()
    
    conn = create_connection()
    if conn is None:
        print("Не вдалося підключитися до бази даних")
        return
        
    cursor = conn.cursor()
    
    # Таблиця користувачів з розширеним профілем
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        full_name VARCHAR(200),
        phone_number VARCHAR(20),
        region VARCHAR(100),
        avatar_url VARCHAR(255),
        avatar_symbol VARCHAR(10), -- Новий рядок для зберігання символу
        rating FLOAT DEFAULT 0,
        rating_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблиця жанрів книг
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS genres (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    )
    ''')
    
    # Таблиця книг з розширеними властивостями
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        author VARCHAR(100) NOT NULL,
        description TEXT,
        genre_id INT,
        cover_url VARCHAR(255),
        owner_id INT NOT NULL,
        is_free BOOLEAN DEFAULT FALSE,
        status ENUM('доступна', 'видана', 'зарезервована') DEFAULT 'доступна',
        rating FLOAT DEFAULT 0,
        rating_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    )
    ''')
    
    # Таблиця обмінів
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exchanges (
        id INT AUTO_INCREMENT PRIMARY KEY,
        book_id INT NOT NULL,
        borrower_id INT NOT NULL,
        status ENUM('запит', 'прийнято', 'відхилено', 'повернуто') DEFAULT 'запит',
        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP NULL,
        FOREIGN KEY (book_id) REFERENCES books(id),
        FOREIGN KEY (borrower_id) REFERENCES users(id)
    )
    ''')
    
    # Таблиця списку бажаних книг
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wishlist (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        title VARCHAR(200) NOT NULL,
        author VARCHAR(100),
        genre_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (genre_id) REFERENCES genres(id)
    )
    ''')
    
    # Таблиця для відгуків про користувачів
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_reviews (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reviewer_id INT NOT NULL,
        user_id INT NOT NULL,
        rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reviewer_id) REFERENCES users(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Таблиця для відгуків про книги
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS book_reviews (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        book_id INT NOT NULL,
        rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    )
    ''')
    
    # Таблиця для повідомлень чату
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sender_id INT NOT NULL,
        receiver_id INT NOT NULL,
        content TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id)
    )
    ''')
    
    # Таблиця для системних повідомлень
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        content TEXT NOT NULL,
        type VARCHAR(50) NOT NULL,
        related_id INT,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Заповнення таблиці жанрів
    genres = [
        "Фантастика", "Фентезі", "Детектив", "Романтика", "Історичний роман",
        "Наукова література", "Біографія", "Пригоди", "Жахи", "Комікси",
        "Поезія", "Драма", "Дитяча література", "Психологія", "Бізнес",
        "Філософія", "Мистецтво", "Кулінарія", "Подорожі", "Саморозвиток"
    ]
    
    for genre in genres:
        try:
            cursor.execute("INSERT INTO genres (name) VALUES (%s)", (genre,))
        except:
            # Жанр вже може існувати - ігноруємо помилку
            pass
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Структуру бази даних успішно створено або оновлено")

# Ініціалізація бази даних
setup_database()

# Маршрути API

# Реєстрація користувача
@app.route('/api/users', methods=['POST'])
def register_user():
    data = request.form if request.form else request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    phone_number = data.get('phone_number')
    region = data.get('region')
    avatar_symbol = data.get('avatar_symbol', '👤')  # Використовуємо стандартний символ, якщо не передано
    
    if not all([username, email, password]):
        return jsonify({"status": "помилка", "повідомлення": "Всі обов'язкові поля повинні бути заповнені"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """INSERT INTO users 
               (username, email, password, full_name, phone_number, region, avatar_symbol) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (username, email, password, full_name, phone_number, region, avatar_symbol)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return jsonify({"status": "успіх", "id": user_id}), 201
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Оновлення профілю користувача
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.form if request.form else request.get_json()
    full_name = data.get('full_name')
    phone_number = data.get('phone_number')
    region = data.get('region')
    avatar_symbol = data.get('avatar_symbol')
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевіряємо, чи існує користувач
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"status": "помилка", "повідомлення": "Користувача не знайдено"}), 404
        
        # Оновлюємо профіль з символом аватарки
        if avatar_symbol:
            cursor.execute(
                """UPDATE users 
                   SET full_name = %s, phone_number = %s, region = %s, avatar_symbol = %s
                   WHERE id = %s""",
                (full_name, phone_number, region, avatar_symbol, user_id)
            )
        else:
            cursor.execute(
                """UPDATE users 
                   SET full_name = %s, phone_number = %s, region = %s
                   WHERE id = %s""",
                (full_name, phone_number, region, user_id)
            )
        conn.commit()
        
        return jsonify({"status": "успіх"}), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання профілю користувача
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, username, email, full_name, phone_number, region, 
                   avatar_url, rating, rating_count, created_at 
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if user:
            # Отримання відгуків про користувача
            cursor.execute("""
                SELECT ur.*, u.username, u.avatar_url 
                FROM user_reviews ur 
                JOIN users u ON ur.reviewer_id = u.id 
                WHERE ur.user_id = %s 
                ORDER BY ur.created_at DESC
            """, (user_id,))
            reviews = cursor.fetchall()
            
            # Отримання книг користувача
            cursor.execute("""
                SELECT COUNT(*) as total_books 
                FROM books 
                WHERE owner_id = %s
            """, (user_id,))
            books_count = cursor.fetchone()
            
            user['відгуки'] = reviews
            user['кількість_книг'] = books_count['total_books']
            
            return jsonify({"status": "успіх", "користувач": user}), 200
        else:
            return jsonify({"status": "помилка", "повідомлення": "Користувача не знайдено"}), 404
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Авторизація користувача
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """SELECT id, username, email, full_name, phone_number, region, avatar_url, avatar_symbol 
               FROM users WHERE email = %s AND password = %s""",
            (email, password)
        )
        user = cursor.fetchone()
        
        if user:
            # Остальной код функции остается без изменений...
            return jsonify({"status": "успіх", "користувач": user}), 200
        else:
            return jsonify({"status": "помилка", "повідомлення": "Невірний email або пароль"}), 401
    finally:
        cursor.close()
        conn.close()

# Додавання нової книги
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.form if request.form else request.get_json()
    title = data.get('title')
    author = data.get('author')
    description = data.get('description')
    owner_id = data.get('owner_id')
    genre_id = data.get('genre_id')
    is_free = data.get('is_free', False)
    
    if not all([title, author, owner_id]):
        return jsonify({"status": "помилка", "повідомлення": "Назва, автор та ID власника обов'язкові"}), 400
    
    cover_url = None
    # Обробка завантаження обкладинки
    if 'cover' in request.files:
        cover = request.files['cover']
        if cover and allowed_file(cover.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{cover.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cover.save(filepath)
            cover_url = f"/static/uploads/{filename}"
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Початок транзакції
        conn.start_transaction()
        
        # Додавання книги
        cursor.execute(
            """INSERT INTO books 
               (title, author, description, genre_id, cover_url, owner_id, is_free) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (title, author, description, genre_id, cover_url, owner_id, is_free)
        )
        book_id = cursor.lastrowid
        
        # Отримання даних про власника
        cursor.execute(
            "SELECT username FROM users WHERE id = %s", 
            (owner_id,)
        )
        owner_result = cursor.fetchone()
        owner_name = owner_result[0] if owner_result else "Невідомий користувач"
        
        # Пошук користувачів, які мають цю книгу в списку бажаного
        cursor.execute("""
            SELECT w.user_id, u.email, u.username 
            FROM wishlist w 
            JOIN users u ON w.user_id = u.id 
            WHERE (LOWER(w.title) LIKE %s OR LOWER(w.author) LIKE %s)
            AND w.user_id != %s
        """, (f"%{title.lower()}%", f"%{author.lower()}%", owner_id))
        
        wishlist_matches = cursor.fetchall()
        notification_count = 0
        
        # Створення сповіщень для користувачів, які мають цю книгу в списку бажаного
        for match in wishlist_matches:
            user_id, email, username = match
            
            # Текст сповіщення
            notification_text = f"Нова книга '{title}' від {author} додана користувачем {owner_name}. Ця книга відповідає вашому списку бажаного!"
            
            # Створення сповіщення
            cursor.execute(
                """INSERT INTO notifications 
                   (user_id, content, type, related_id) 
                   VALUES (%s, %s, %s, %s)""",
                (user_id, notification_text, 'wishlist_match', book_id)
            )
            notification_count += 1
        
        conn.commit()
        
        return jsonify({
            "status": "успіх", 
            "id": book_id,
            "сповіщення_відправлено": notification_count,
            "повідомлення": f"Книгу успішно додано! {notification_count} користувачів отримали сповіщення."
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Оновлення інформації про книгу
@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.form if request.form else request.get_json()
    title = data.get('title')
    author = data.get('author')
    description = data.get('description')
    genre_id = data.get('genre_id')
    is_free = data.get('is_free')
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка існування книги
        cursor.execute("SELECT cover_url, owner_id FROM books WHERE id = %s", (book_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"status": "помилка", "повідомлення": "Книгу не знайдено"}), 404
            
        current_cover, owner_id = result
        
        cover_url = current_cover
        # Обробка завантаження нової обкладинки
        if 'cover' in request.files:
            cover = request.files['cover']
            if cover and allowed_file(cover.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{cover.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                cover.save(filepath)
                cover_url = f"/static/uploads/{filename}"
                
                # Видалення старої обкладинки, якщо вона існує
                if current_cover and os.path.exists(os.path.join('static', current_cover.lstrip('/'))):
                    os.remove(os.path.join('static', current_cover.lstrip('/')))
        
        # Побудова SQL запиту для оновлення
        update_fields = []
        params = []
        
        if title:
            update_fields.append("title = %s")
            params.append(title)
        if author:
            update_fields.append("author = %s")
            params.append(author)
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
        if genre_id:
            update_fields.append("genre_id = %s")
            params.append(genre_id)
        if is_free is not None:
            update_fields.append("is_free = %s")
            params.append(is_free)
        if cover_url is not None:
            update_fields.append("cover_url = %s")
            params.append(cover_url)
        
        if update_fields:
            params.append(book_id)
            query = f"UPDATE books SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, params)
            conn.commit()
            
            # Якщо змінилися основні дані книги, перевіряємо списки бажаного
            if title or author:
                # Отримання оновлених даних про книгу
                cursor.execute("SELECT title, author FROM books WHERE id = %s", (book_id,))
                updated_book = cursor.fetchone()
                updated_title, updated_author = updated_book
                
                # Отримання даних про власника
                cursor.execute("SELECT username FROM users WHERE id = %s", (owner_id,))
                owner_result = cursor.fetchone()
                owner_name = owner_result[0] if owner_result else "Невідомий користувач"
                
                # Пошук користувачів, які мають цю книгу в списку бажаного
                cursor.execute("""
                    SELECT w.user_id, u.username
                    FROM wishlist w 
                    JOIN users u ON w.user_id = u.id 
                    WHERE (LOWER(w.title) LIKE %s OR LOWER(w.author) LIKE %s)
                    AND w.user_id != %s
                """, (f"%{updated_title.lower()}%", f"%{updated_author.lower()}%", owner_id))
                
                wishlist_matches = cursor.fetchall()
                notification_count = 0
                
                # Створення сповіщень для користувачів
                for match in wishlist_matches:
                    user_id, username = match
                    
                    # Текст сповіщення
                    notification_text = f"Книга '{updated_title}' від {updated_author} була оновлена користувачем {owner_name}. Ця книга відповідає вашому списку бажаного!"
                    
                    # Створення сповіщення
                    cursor.execute(
                        """INSERT INTO notifications 
                           (user_id, content, type, related_id) 
                           VALUES (%s, %s, %s, %s)""",
                        (user_id, notification_text, 'wishlist_update', book_id)
                    )
                    notification_count += 1
                
                conn.commit()
                return jsonify({
                    "status": "успіх",
                    "сповіщення_відправлено": notification_count,
                    "повідомлення": "Інформацію про книгу успішно оновлено"
                }), 200
            else:
                return jsonify({"status": "успіх", "повідомлення": "Інформацію про книгу успішно оновлено"}), 200
        else:
            return jsonify({"status": "помилка", "повідомлення": "Не вказано поля для оновлення"}), 400
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Видалення книги
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"status": "помилка", "повідомлення": "Необхідно вказати ID користувача"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка прав доступу
        cursor.execute("SELECT owner_id, cover_url FROM books WHERE id = %s", (book_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"status": "помилка", "повідомлення": "Книгу не знайдено"}), 404
            
        owner_id, cover_url = result
        
        if int(owner_id) != int(user_id):
            return jsonify({"status": "помилка", "повідомлення": "У вас немає прав для видалення цієї книги"}), 403
        
        # Початок транзакції
        conn.start_transaction()
        
        # Видалення всіх пов'язаних записів
        cursor.execute("DELETE FROM book_reviews WHERE book_id = %s", (book_id,))
        cursor.execute("DELETE FROM exchanges WHERE book_id = %s", (book_id,))
        cursor.execute("DELETE FROM notifications WHERE related_id = %s AND type LIKE 'book_%'", (book_id,))
        
        # Видалення самої книги
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        
        # Видалення файлу обкладинки, якщо він існує
        if cover_url and os.path.exists(os.path.join('static', cover_url.lstrip('/'))):
            os.remove(os.path.join('static', cover_url.lstrip('/')))
        
        conn.commit()
        return jsonify({"status": "успіх", "повідомлення": "Книгу успішно видалено"}), 200
    except Error as e:
        conn.rollback()
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання списку всіх книг з фільтрацією
@app.route('/api/books', methods=['GET'])
def get_books():
    # Параметри фільтрації
    title = request.args.get('title', '')
    author = request.args.get('author', '')
    genre_id = request.args.get('genre_id')
    region = request.args.get('region', '')
    owner_id = request.args.get('owner_id')
    owner_id_not = request.args.get('owner_id_not')
    is_free = request.args.get('is_free')
    status = request.args.get('status', '')
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Базовий SQL запит
        query = """
        SELECT b.*, u.username as owner_name, u.region as owner_region, 
               u.avatar_url as owner_avatar, g.name as genre_name 
        FROM books b 
        JOIN users u ON b.owner_id = u.id
        LEFT JOIN genres g ON b.genre_id = g.id
        WHERE 1=1
        """
        params = []
        
        # Додавання умов фільтрації
        if title:
            query += " AND LOWER(b.title) LIKE %s"
            params.append(f"%{title.lower()}%")
        if author:
            query += " AND LOWER(b.author) LIKE %s"
            params.append(f"%{author.lower()}%")
        if genre_id:
            query += " AND b.genre_id = %s"
            params.append(genre_id)
        if region:
            query += " AND LOWER(u.region) LIKE %s"
            params.append(f"%{region.lower()}%")
        if owner_id:
            query += " AND b.owner_id = %s"
            params.append(owner_id)
        if owner_id_not:
            query += " AND b.owner_id != %s"
            params.append(owner_id_not)
        if is_free is not None:
            is_free_bool = is_free.lower() in ('true', '1', 't')
            query += " AND b.is_free = %s"
            params.append(is_free_bool)
        if status:
            query += " AND b.status = %s"
            params.append(status)
        
        # Сортування
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'DESC')
        
        allowed_sort_fields = ['title', 'author', 'created_at', 'rating']
        allowed_sort_orders = ['ASC', 'DESC']
        
        if sort_by not in allowed_sort_fields:
            sort_by = 'created_at'
        if sort_order not in allowed_sort_orders:
            sort_order = 'DESC'
        
        # Отримання загальної кількості книг для пагінації
        count_query = """
        SELECT COUNT(*) as total 
        FROM books b 
        JOIN users u ON b.owner_id = u.id
        LEFT JOIN genres g ON b.genre_id = g.id
        WHERE 1=1
        """
        
        # Додаємо ті ж умови фільтрації до запиту підрахунку
        count_params = params.copy()  # Копіюємо параметри
        
        if title:
            count_query += " AND LOWER(b.title) LIKE %s"
        if author:
            count_query += " AND LOWER(b.author) LIKE %s"
        if genre_id:
            count_query += " AND b.genre_id = %s"
        if region:
            count_query += " AND LOWER(u.region) LIKE %s"
        if owner_id:
            count_query += " AND b.owner_id = %s"
        if owner_id_not:
            count_query += " AND b.owner_id != %s"
        if is_free is not None:
            count_query += " AND b.is_free = %s"
        if status:
            count_query += " AND b.status = %s"
        
        cursor.execute(count_query, count_params)
        result = cursor.fetchone()
        total = 0
        if result:
            total = result['total']
        
        # Сортування та пагінація основного запиту
        query += f" ORDER BY b.{sort_by} {sort_order}"
        
        # Пагінація
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        
        # Додавання лімітів для пагінації
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Виконання запиту
        cursor.execute(query, params)
        books = cursor.fetchall()
        
        return jsonify({
            "status": "успіх", 
            "книги": books,
            "загальна_кількість": total,
            "сторінка": page,
            "на_сторінці": per_page,
            "загальна_кількість_сторінок": (total + per_page - 1) // per_page if total > 0 else 1
        }), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання даних про конкретну книгу
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
        SELECT b.*, u.username as owner_name, u.region as owner_region, u.id as owner_id,
               u.avatar_url as owner_avatar, g.name as genre_name 
        FROM books b 
        JOIN users u ON b.owner_id = u.id
        LEFT JOIN genres g ON b.genre_id = g.id
        WHERE b.id = %s
        ''', (book_id,))
        book = cursor.fetchone()
        
        if book:
            # Отримання відгуків про книгу
            cursor.execute('''
            SELECT br.*, u.username, u.avatar_url 
            FROM book_reviews br 
            JOIN users u ON br.user_id = u.id 
            WHERE br.book_id = %s 
            ORDER BY br.created_at DESC
            ''', (book_id,))
            reviews = cursor.fetchall()
            
            book['відгуки'] = reviews
            
            return jsonify({"status": "успіх", "книга": book}), 200
        else:
            return jsonify({"status": "помилка", "повідомлення": "Книгу не знайдено"}), 404
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Додавання відгуку про книгу
@app.route('/api/books/<int:book_id>/reviews', methods=['POST'])
def add_book_review(book_id):
    data = request.get_json()
    user_id = data.get('user_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not all([user_id, rating]):
        return jsonify({"status": "помилка", "повідомлення": "ID користувача та оцінка обов'язкові"}), 400
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"status": "помилка", "повідомлення": "Оцінка повинна бути від 1 до 5"}), 400
    except:
        return jsonify({"status": "помилка", "повідомлення": "Оцінка повинна бути цілим числом"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка, чи існує книга
        cursor.execute("SELECT id, owner_id, title FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        
        if not book:
            return jsonify({"status": "помилка", "повідомлення": "Книгу не знайдено"}), 404
        
        book_owner_id = book[1]
        book_title = book[2]
        
        # Перевірка, чи користувач не є власником книги
        if int(user_id) == int(book_owner_id):
            return jsonify({"status": "помилка", "повідомлення": "Ви не можете оцінити власну книгу"}), 400
        
        # Перевірка, чи користувач вже залишав відгук
        cursor.execute(
            "SELECT id FROM book_reviews WHERE book_id = %s AND user_id = %s", 
            (book_id, user_id)
        )
        
        existing_review = cursor.fetchone()
        
        # Початок транзакції
        conn.start_transaction()
        
        if existing_review:
            # Оновлення існуючого відгуку
            review_id = existing_review[0]
            cursor.execute(
                "UPDATE book_reviews SET rating = %s, comment = %s WHERE id = %s",
                (rating, comment, review_id)
            )
        else:
            # Створення нового відгуку
            cursor.execute(
                "INSERT INTO book_reviews (user_id, book_id, rating, comment) VALUES (%s, %s, %s, %s)",
                (user_id, book_id, rating, comment)
            )
            review_id = cursor.lastrowid
        
        # Оновлення середньої оцінки книги
        cursor.execute(
            """
            UPDATE books 
            SET rating = (SELECT AVG(rating) FROM book_reviews WHERE book_id = %s),
                rating_count = (SELECT COUNT(*) FROM book_reviews WHERE book_id = %s)
            WHERE id = %s
            """,
            (book_id, book_id, book_id)
        )
        
        # Отримання імені користувача, який залишив відгук
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        reviewer_name = cursor.fetchone()[0]
        
        # Створення сповіщення для власника книги
        notification_text = f"Користувач {reviewer_name} залишив відгук на вашу книгу '{book_title}' з оцінкою {rating}/5."
        
        cursor.execute(
            "INSERT INTO notifications (user_id, content, type, related_id) VALUES (%s, %s, %s, %s)",
            (book_owner_id, notification_text, 'book_review', book_id)
        )
        
        conn.commit()
        
        return jsonify({
            "status": "успіх",
            "повідомлення": "Відгук успішно додано",
            "id": review_id
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Додавання відгуку про користувача
@app.route('/api/users/<int:user_id>/reviews', methods=['POST'])
def add_user_review(user_id):
    data = request.get_json()
    reviewer_id = data.get('reviewer_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not all([reviewer_id, rating]):
        return jsonify({"status": "помилка", "повідомлення": "ID рецензента та оцінка обов'язкові"}), 400
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"status": "помилка", "повідомлення": "Оцінка повинна бути від 1 до 5"}), 400
    except:
        return jsonify({"status": "помилка", "повідомлення": "Оцінка повинна бути цілим числом"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка, чи існує користувач
        cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"status": "помилка", "повідомлення": "Користувача не знайдено"}), 404
        
        user_name = user[1]
        
        # Перевірка, чи користувач не оцінює себе
        if int(reviewer_id) == int(user_id):
            return jsonify({"status": "помилка", "повідомлення": "Ви не можете оцінити самого себе"}), 400
        
        # Перевірка, чи існував обмін між користувачами
        cursor.execute("""
            SELECT COUNT(*) FROM exchanges 
            WHERE (
                (borrower_id = %s AND book_id IN (SELECT id FROM books WHERE owner_id = %s))
                OR 
                (borrower_id = %s AND book_id IN (SELECT id FROM books WHERE owner_id = %s))
            )
            AND status IN ('прийнято', 'повернуто')
        """, (reviewer_id, user_id, user_id, reviewer_id))
        
        exchange_count = cursor.fetchone()[0]
        
        if exchange_count == 0:
            return jsonify({
                "status": "помилка", 
                "повідомлення": "Ви можете оцінити користувача тільки після успішного обміну книгами"
            }), 400
        
        # Перевірка, чи користувач вже залишав відгук
        cursor.execute(
            "SELECT id FROM user_reviews WHERE user_id = %s AND reviewer_id = %s", 
            (user_id, reviewer_id)
        )
        
        existing_review = cursor.fetchone()
        
        # Початок транзакції
        conn.start_transaction()
        
        if existing_review:
            # Оновлення існуючого відгуку
            review_id = existing_review[0]
            cursor.execute(
                "UPDATE user_reviews SET rating = %s, comment = %s WHERE id = %s",
                (rating, comment, review_id)
            )
        else:
            # Створення нового відгуку
            cursor.execute(
                "INSERT INTO user_reviews (reviewer_id, user_id, rating, comment) VALUES (%s, %s, %s, %s)",
                (reviewer_id, user_id, rating, comment)
            )
            review_id = cursor.lastrowid
        
        # Оновлення середньої оцінки користувача
        cursor.execute(
            """
            UPDATE users 
            SET rating = (SELECT AVG(rating) FROM user_reviews WHERE user_id = %s),
                rating_count = (SELECT COUNT(*) FROM user_reviews WHERE user_id = %s)
            WHERE id = %s
            """,
            (user_id, user_id, user_id)
        )
        
        # Отримання імені рецензента
        cursor.execute("SELECT username FROM users WHERE id = %s", (reviewer_id,))
        reviewer_name = cursor.fetchone()[0]
        
        # Створення сповіщення для користувача
        notification_text = f"Користувач {reviewer_name} залишив вам відгук з оцінкою {rating}/5."
        
        cursor.execute(
            "INSERT INTO notifications (user_id, content, type, related_id) VALUES (%s, %s, %s, %s)",
            (user_id, notification_text, 'user_review', reviewer_id)
        )
        
        conn.commit()
        
        return jsonify({
            "status": "успіх",
            "повідомлення": "Відгук успішно додано",
            "id": review_id
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання списку жанрів
@app.route('/api/genres', methods=['GET'])
def get_genres():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM genres ORDER BY name")
        genres = cursor.fetchall()
        return jsonify({"status": "успіх", "жанри": genres}), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Додавання книги в список бажаного
@app.route('/api/wishlist', methods=['POST'])
def add_to_wishlist():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    author = data.get('author')
    genre_id = data.get('genre_id')
    
    if not all([user_id, title]):
        return jsonify({"status": "помилка", "повідомлення": "ID користувача та назва книги обов'язкові"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка наявності такої книги у списку бажаного
        cursor.execute(
            "SELECT id FROM wishlist WHERE user_id = %s AND LOWER(title) = LOWER(%s) AND (author IS NULL OR LOWER(author) = LOWER(%s))",
            (user_id, title, author or "")
        )
        
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                "status": "помилка", 
                "повідомлення": "Ця книга вже є у вашому списку бажаного"
            }), 400
        
        # Додавання в список бажаного
        cursor.execute(
            "INSERT INTO wishlist (user_id, title, author, genre_id) VALUES (%s, %s, %s, %s)",
            (user_id, title, author, genre_id)
        )
        conn.commit()
        wishlist_id = cursor.lastrowid
        
        # Перевірка, чи є вже така книга в каталозі
        cursor.execute("""
            SELECT b.id, b.title, b.author, u.username, u.id as owner_id, b.status
            FROM books b 
            JOIN users u ON b.owner_id = u.id 
            WHERE b.status = 'доступна' AND 
                  (LOWER(b.title) LIKE %s) AND
                  (u.id != %s)
        """, (f"%{title.lower()}%", user_id))
        
        matching_books = cursor.fetchall()
        
        # Створення сповіщень про наявні книги
        notifications = []
        for book in matching_books:
            book_id, book_title, book_author, owner_name, owner_id, status = book
            
            notification_text = f"Знайдено книгу '{book_title}' від {book_author}, яка відповідає вашому списку бажаного! Власник: {owner_name}"
            
            cursor.execute(
                "INSERT INTO notifications (user_id, content, type, related_id) VALUES (%s, %s, %s, %s)",
                (user_id, notification_text, 'wishlist_match', book_id)
            )
            
            notifications.append({
                "книга_id": book_id,
                "назва": book_title,
                "автор": book_author,
                "власник": owner_name
            })
        
        conn.commit()
        
        return jsonify({
            "status": "успіх", 
            "id": wishlist_id,
            "знайдені_книги": notifications,
            "повідомлення": f"Книгу додано до списку бажаного. Знайдено {len(notifications)} відповідних книг."
        }), 201
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання списку бажаних книг користувача
@app.route('/api/wishlist/<int:user_id>', methods=['GET'])
def get_wishlist(user_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
        SELECT w.*, g.name as genre_name 
        FROM wishlist w 
        LEFT JOIN genres g ON w.genre_id = g.id 
        WHERE w.user_id = %s
        ORDER BY w.created_at DESC
        ''', (user_id,))
        wishlist = cursor.fetchall()
        
        # Для кожної книги в списку бажаного знаходимо доступні варіанти
        for item in wishlist:
            cursor.execute("""
                SELECT b.id, b.title, b.author, u.username as owner_name, u.id as owner_id, 
                       b.cover_url, b.is_free, b.status
                FROM books b 
                JOIN users u ON b.owner_id = u.id 
                WHERE b.status = 'доступна' AND 
                      (LOWER(b.title) LIKE %s OR LOWER(b.author) LIKE %s) AND
                      u.id != %s
                LIMIT 5
            """, (f"%{item['title'].lower()}%", f"%{item.get('author', '').lower()}%", user_id))
            
            item['доступні_варіанти'] = cursor.fetchall()
        
        return jsonify({"status": "успіх", "список_бажаного": wishlist}), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Видалення книги зі списку бажаного
@app.route('/api/wishlist/<int:wishlist_id>', methods=['DELETE'])
def delete_from_wishlist(wishlist_id):
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"status": "помилка", "повідомлення": "Необхідно вказати ID користувача"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка прав доступу
        cursor.execute("SELECT user_id FROM wishlist WHERE id = %s", (wishlist_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"status": "помилка", "повідомлення": "Запис не знайдено"}), 404
            
        if int(result[0]) != int(user_id):
            return jsonify({"status": "помилка", "повідомлення": "У вас немає прав для видалення цього запису"}), 403
        
        cursor.execute("DELETE FROM wishlist WHERE id = %s", (wishlist_id,))
        conn.commit()
        
        return jsonify({"status": "успіх", "повідомлення": "Запис успішно видалено зі списку бажаного"}), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Запит на обмін
@app.route('/api/exchanges', methods=['POST'])
def request_exchange():
    data = request.get_json()
    book_id = data.get('book_id')
    borrower_id = data.get('borrower_id')
    message = data.get('message', '')
    
    if not all([book_id, borrower_id]):
        return jsonify({"status": "помилка", "повідомлення": "ID книги та ID позичальника обов'язкові"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Початок транзакції
        conn.start_transaction()
        
        # Перевірка, чи книга доступна
        cursor.execute("SELECT status, owner_id, title, author FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        
        if not book:
            return jsonify({"status": "помилка", "повідомлення": "Книгу не знайдено"}), 404
        
        status, owner_id, title, author = book
        
        if status != 'доступна':
            return jsonify({"status": "помилка", "повідомлення": "Книга недоступна для обміну"}), 400
        
        if int(owner_id) == int(borrower_id):
            return jsonify({"status": "помилка", "повідомлення": "Ви не можете позичити власну книгу"}), 400
        
        # Отримання даних про власника і позичальника
        cursor.execute("SELECT username FROM users WHERE id = %s", (owner_id,))
        owner_name = cursor.fetchone()[0]
        
        cursor.execute("SELECT username FROM users WHERE id = %s", (borrower_id,))
        borrower_name = cursor.fetchone()[0]
        
        # Створення запиту на обмін
        cursor.execute(
            "INSERT INTO exchanges (book_id, borrower_id) VALUES (%s, %s)",
            (book_id, borrower_id)
        )
        
        # Оновлення статусу книги
        cursor.execute(
            "UPDATE books SET status = 'зарезервована' WHERE id = %s",
            (book_id,)
        )
        
        exchange_id = cursor.lastrowid
        
        # Якщо є повідомлення, створюємо запис чату
        if message:
            cursor.execute(
                "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
                (borrower_id, owner_id, message)
            )
        
        # Створення сповіщення для власника
        notification_text = f"Користувач {borrower_name} запитує вашу книгу '{title}' автора {author}."
        
        cursor.execute(
            "INSERT INTO notifications (user_id, content, type, related_id) VALUES (%s, %s, %s, %s)",
            (owner_id, notification_text, 'exchange_request', exchange_id)
        )
        
        conn.commit()
        
        return jsonify({
            "status": "успіх",
            "id": exchange_id,
            "повідомлення": "Запит на обмін успішно створено"
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання запитів на обмін для власника
@app.route('/api/exchanges/owner/<int:owner_id>', methods=['GET'])
def get_owner_exchanges(owner_id):
    status_filter = request.args.get('status')
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = '''
        SELECT e.*, b.title, b.author, b.cover_url, b.genre_id, 
               u.username as borrower_name, u.avatar_url as borrower_avatar,
               g.name as genre_name 
        FROM exchanges e 
        JOIN books b ON e.book_id = b.id 
        JOIN users u ON e.borrower_id = u.id 
        LEFT JOIN genres g ON b.genre_id = g.id
        WHERE b.owner_id = %s
        '''
        
        params = [owner_id]
        
        if status_filter:
            query += " AND e.status = %s"
            params.append(status_filter)
        
        query += " ORDER BY e.start_date DESC"
        
        cursor.execute(query, params)
        exchanges = cursor.fetchall()
        
        # Отримання кількості непрочитаних повідомлень для кожного обміну
        for exchange in exchanges:
            cursor.execute("""
                SELECT COUNT(*) as unread_count 
                FROM messages 
                WHERE receiver_id = %s AND sender_id = %s AND is_read = FALSE
            """, (owner_id, exchange['borrower_id']))
            
            unread = cursor.fetchone()
            exchange['непрочитані_повідомлення'] = unread['unread_count']
        
        return jsonify({"status": "успіх", "обміни": exchanges}), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання запитів на обмін для позичальника
@app.route('/api/exchanges/borrower/<int:borrower_id>', methods=['GET'])
def get_borrower_exchanges(borrower_id):
    status_filter = request.args.get('status')
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = '''
        SELECT e.*, b.title, b.author, b.cover_url, b.genre_id, 
               u.username as owner_name, u.id as owner_id, u.avatar_url as owner_avatar,
               g.name as genre_name 
        FROM exchanges e 
        JOIN books b ON e.book_id = b.id 
        JOIN users u ON b.owner_id = u.id 
        LEFT JOIN genres g ON b.genre_id = g.id
        WHERE e.borrower_id = %s
        '''
        
        params = [borrower_id]
        
        if status_filter:
            query += " AND e.status = %s"
            params.append(status_filter)
        
        query += " ORDER BY e.start_date DESC"
        
        cursor.execute(query, params)
        exchanges = cursor.fetchall()
        
        # Отримання кількості непрочитаних повідомлень для кожного обміну
        for exchange in exchanges:
            cursor.execute("""
                SELECT COUNT(*) as unread_count 
                FROM messages 
                WHERE receiver_id = %s AND sender_id = %s AND is_read = FALSE
            """, (borrower_id, exchange['owner_id']))
            
            unread = cursor.fetchone()
            exchange['непрочитані_повідомлення'] = unread['unread_count']
        
        return jsonify({"status": "успіх", "обміни": exchanges}), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Оновлення статусу обміну
@app.route('/api/exchanges/<int:exchange_id>', methods=['PUT'])
def update_exchange_status(exchange_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['прийнято', 'відхилено', 'повернуто']:
        return jsonify({"status": "помилка", "повідомлення": "Невірний статус"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Початок транзакції
        conn.start_transaction()
        
        # Отримання інформації про обмін
        cursor.execute("""
            SELECT e.book_id, e.borrower_id, e.status, 
                   b.title, b.owner_id,
                   u1.username as borrower_name, 
                   u2.username as owner_name
            FROM exchanges e
            JOIN books b ON e.book_id = b.id
            JOIN users u1 ON e.borrower_id = u1.id
            JOIN users u2 ON b.owner_id = u2.id
            WHERE e.id = %s
        """, (exchange_id,))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"status": "помилка", "повідомлення": "Обмін не знайдено"}), 404
        
        book_id, borrower_id, current_status, book_title, owner_id, borrower_name, owner_name = result
        
        # Перевірка, чи можна змінити статус
        if current_status == 'відхилено' and new_status != 'запит':
            return jsonify({"status": "помилка", "повідомлення": "Неможливо змінити статус відхиленого запиту"}), 400
        
        if current_status == 'повернуто':
            return jsonify({"status": "помилка", "повідомлення": "Неможливо змінити статус поверненої книги"}), 400
        
        # Оновлення статусу обміну
        if new_status == 'повернуто':
            cursor.execute(
                "UPDATE exchanges SET status = %s, end_date = CURRENT_TIMESTAMP WHERE id = %s",
                (new_status, exchange_id)
            )
        else:
            cursor.execute(
                "UPDATE exchanges SET status = %s WHERE id = %s",
                (new_status, exchange_id)
            )
        
        # Оновлення статусу книги
        book_status = 'доступна'
        if new_status == 'прийнято':
            book_status = 'видана'
        
        cursor.execute(
            "UPDATE books SET status = %s WHERE id = %s",
            (book_status, book_id)
        )
        
        # Створення сповіщення
        notification_text = ""
        notification_user_id = None
        
        if new_status == 'прийнято':
            notification_text = f"Ваш запит на книгу '{book_title}' було прийнято користувачем {owner_name}."
            notification_user_id = borrower_id
        elif new_status == 'відхилено':
            notification_text = f"Ваш запит на книгу '{book_title}' було відхилено користувачем {owner_name}."
            notification_user_id = borrower_id
        elif new_status == 'повернуто':
            notification_text = f"Книгу '{book_title}' було повернуто користувачем {borrower_name}."
            notification_user_id = owner_id
        
        if notification_text and notification_user_id:
            cursor.execute(
                "INSERT INTO notifications (user_id, content, type, related_id) VALUES (%s, %s, %s, %s)",
                (notification_user_id, notification_text, 'exchange_update', exchange_id)
            )
        
        conn.commit()
        
        return jsonify({
            "status": "успіх",
            "повідомлення": f"Статус обміну успішно оновлено на '{new_status}'"
        }), 200
    except Error as e:
        conn.rollback()
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання чату між користувачами
@app.route('/api/chat/<int:user1_id>/<int:user2_id>', methods=['GET'])
def get_chat(user1_id, user2_id):
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Отримання повідомлень
        cursor.execute("""
            SELECT m.*, 
                   u_sender.username as sender_name, 
                   u_sender.avatar_symbol as sender_avatar_symbol
            FROM messages m
            JOIN users u_sender ON m.sender_id = u_sender.id
            WHERE (m.sender_id = %s AND m.receiver_id = %s)
               OR (m.sender_id = %s AND m.receiver_id = %s)
            ORDER BY m.created_at ASC
        """, (user1_id, user2_id, user2_id, user1_id))
        
        messages = cursor.fetchall()
        
      
        
        # Позначаємо повідомлення як прочитані
        cursor.execute("""
            UPDATE messages
            SET is_read = TRUE
            WHERE sender_id = %s AND receiver_id = %s AND is_read = FALSE
        """, (user2_id, user1_id))
        
        conn.commit()
        
        # Отримання інформації про другого користувача
        cursor.execute("""
            SELECT id, username, avatar_url
            FROM users
            WHERE id = %s
        """, (user2_id,))
        
        user_info = cursor.fetchone()
        
        return jsonify({
            "status": "успіх",
            "повідомлення": messages,
            "співрозмовник": user_info
        }), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Надсилання повідомлення
@app.route('/api/chat/send', methods=['POST'])
def send_message():
    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not all([sender_id, receiver_id, content]):
        return jsonify({"status": "помилка", "повідомлення": "Всі поля обов'язкові"}), 400
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Перевірка, чи існують користувачі
        cursor.execute("SELECT id, username FROM users WHERE id IN (%s, %s)", (sender_id, receiver_id))
        users = cursor.fetchall()
        
        if len(users) < 2:
            return jsonify({"status": "помилка", "повідомлення": "Одного з користувачів не існує"}), 404
        
        # Відправлення повідомлення
        cursor.execute(
            "INSERT INTO messages (sender_id, receiver_id, content) VALUES (%s, %s, %s)",
            (sender_id, receiver_id, content)
        )
        
        conn.commit()
        message_id = cursor.lastrowid
        
        # Отримання інформації про відправника
        cursor.execute("SELECT username FROM users WHERE id = %s", (sender_id,))
        sender_name = cursor.fetchone()[0]
        
        # Створення даних про повідомлення для відповіді
        cursor.execute("""
            SELECT m.*, 
                   u.username as sender_name, 
                   u.avatar_url as sender_avatar
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.id = %s
        """, (message_id,))
        
        message_data = cursor.fetchone()
        
        return jsonify({
            "status": "успіх",
            "повідомлення": "Повідомлення успішно надіслано",
            "дані_повідомлення": {
                "id": message_id,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": content,
                "is_read": False,
                "created_at": message_data[5].strftime("%Y-%m-%d %H:%M:%S"),
                "sender_name": message_data[6],
                "sender_avatar": message_data[7]
            }
        }), 201
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання сповіщень
@app.route('/api/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    mark_read = request.args.get('mark_read', 'false').lower() == 'true'
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Отримання сповіщень
        cursor.execute("""
            SELECT *
            FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        
        notifications = cursor.fetchall()
        
        # Позначення сповіщень як прочитаних, якщо потрібно
        if mark_read:
            cursor.execute("""
                UPDATE notifications
                SET is_read = TRUE
                WHERE user_id = %s AND is_read = FALSE
            """, (user_id,))
            
            conn.commit()
        
        return jsonify({
            "status": "успіх",
            "сповіщення": notifications
        }), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Пошук користувачів
@app.route('/api/users/search', methods=['GET'])
def search_users():
    query = request.args.get('q', '')
    region = request.args.get('region', '')
    
    if not query and not region:
        return jsonify({"status": "помилка", "повідомлення": "Необхідно вказати параметр пошуку"}), 400
    
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Формування запиту
        sql_query = """
            SELECT id, username, full_name, region, avatar_url, rating
            FROM users
            WHERE 1=1
        """
        params = []
        
        if query:
            sql_query += " AND (LOWER(username) LIKE %s OR LOWER(full_name) LIKE %s)"
            params.extend([f"%{query.lower()}%", f"%{query.lower()}%"])
        
        if region:
            sql_query += " AND LOWER(region) LIKE %s"
            params.append(f"%{region.lower()}%")
        
        sql_query += " ORDER BY username LIMIT 20"
        
        cursor.execute(sql_query, params)
        users = cursor.fetchall()
        
        # Отримання додаткової інформації для кожного користувача
        for user in users:
            # Кількість книг
            cursor.execute("SELECT COUNT(*) as book_count FROM books WHERE owner_id = %s", (user['id'],))
            book_count = cursor.fetchone()
            user['кількість_книг'] = book_count['book_count']
            
            # Кількість відгуків
            cursor.execute("SELECT COUNT(*) as review_count FROM user_reviews WHERE user_id = %s", (user['id'],))
            review_count = cursor.fetchone()
            user['кількість_відгуків'] = review_count['review_count']
        
        return jsonify({
            "status": "успіх",
            "користувачі": users
        }), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# Отримання статистики
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Загальна кількість користувачів
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        user_count = cursor.fetchone()['user_count']
        
        # Загальна кількість книг
        cursor.execute("SELECT COUNT(*) as book_count FROM books")
        book_count = cursor.fetchone()['book_count']
        
        # Кількість доступних книг
        cursor.execute("SELECT COUNT(*) as available_count FROM books WHERE status = 'доступна'")
        available_count = cursor.fetchone()['available_count']
        
        # Кількість обмінів
        cursor.execute("SELECT COUNT(*) as exchange_count FROM exchanges")
        exchange_count = cursor.fetchone()['exchange_count']
        
        # Успішні обміни
        cursor.execute("SELECT COUNT(*) as successful_count FROM exchanges WHERE status = 'повернуто'")
        successful_count = cursor.fetchone()['successful_count']
        
        # Активні обміни
        cursor.execute("SELECT COUNT(*) as active_count FROM exchanges WHERE status = 'прийнято'")
        active_count = cursor.fetchone()['active_count']
        
        # Популярні жанри
        cursor.execute("""
            SELECT g.name, COUNT(*) as count
            FROM books b
            JOIN genres g ON b.genre_id = g.id
            GROUP BY g.name
            ORDER BY count DESC
            LIMIT 5
        """)
        popular_genres = cursor.fetchall()
        
        # Найновіші книги
        cursor.execute("""
            SELECT b.id, b.title, b.author, u.username as owner_name, b.created_at
            FROM books b
            JOIN users u ON b.owner_id = u.id
            ORDER BY b.created_at DESC
            LIMIT 5
        """)
        newest_books = cursor.fetchall()
        
        # Найактивніші користувачі (за кількістю книг)
        cursor.execute("""
            SELECT u.id, u.username, u.avatar_url, COUNT(*) as book_count
            FROM books b
            JOIN users u ON b.owner_id = u.id
            GROUP BY u.id, u.username, u.avatar_url
            ORDER BY book_count DESC
            LIMIT 5
        """)
        most_active_users = cursor.fetchall()
        
        return jsonify({
            "status": "успіх",
            "статистика": {
                "користувачів": user_count,
                "книг_всього": book_count,
                "книг_доступно": available_count,
                "обмінів_всього": exchange_count,
                "обмінів_успішних": successful_count,
                "обмінів_активних": active_count,
                "популярні_жанри": popular_genres,
                "нові_книги": newest_books,
                "активні_користувачі": most_active_users
            }
        }), 200
    except Error as e:
        return jsonify({"status": "помилка", "повідомлення": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)