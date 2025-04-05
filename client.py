"""
Клієнтська частина додатку для обміну книгами.
Реалізовано на Streamlit зі стильним оформленням.
"""

import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import time

# Адреса сервера
SERVER_URL = "http://localhost:5000/api"

# Кольорова гама 
COLORS = {
    "primary": "#5D9CEC",      # Яскраво-синій
    "primary_light": "#8BB8F1", # Світло-синій
    "secondary": "#48CFAD",    # М'ятний
    "text": "#333333",         # Темно-сірий
    "text_light": "#656D78",   # Сірий
    "success": "#48CFAD",      # Зелений
    "warning": "#FFCE54",      # Жовтий
    "error": "#ED5565",        # Червоний
    "background": "#F5F7FA",   # Світло-сірий
    "surface": "#FFFFFF",      # Білий
}

# Налаштування стилю сторінки
def set_page_style():
    # CSS для оформлення
    st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLORS["background"]};
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: {COLORS["text"]};
        font-weight: 600;
    }}
    
    h1 {{
        font-size: 2.2rem;
        margin-bottom: 1.5rem;
        color: {COLORS["primary"]};
    }}
    
    h2 {{
        font-size: 1.8rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        color: {COLORS["primary"]};
    }}
    
    h3 {{
        font-size: 1.5rem;
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
        color: {COLORS["text"]};
    }}
    
    .book-card {{
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}
    
    .user-card {{
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .book-status-available {{
        color: {COLORS["success"]};
        font-weight: bold;
    }}
    
    .book-status-reserved {{
        color: {COLORS["warning"]};
        font-weight: bold;
    }}
    
    .book-status-borrowed {{
        color: {COLORS["primary"]};
        font-weight: bold;
    }}
    
    .exchange-status-pending {{
        color: {COLORS["warning"]};
        font-weight: bold;
    }}
    
    .exchange-status-accepted {{
        color: {COLORS["success"]};
        font-weight: bold;
    }}
    
    .exchange-status-rejected {{
        color: {COLORS["error"]};
        font-weight: bold;
    }}
    
    .exchange-status-returned {{
        color: {COLORS["primary"]};
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# Налаштування сторінки
st.set_page_config(
    page_title="Книгообмін",
    page_icon="📚",
    layout="wide"
)

# Застосування стилів
set_page_style()

# Ініціалізація стану сесії
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Доступні книги"
if 'book_filter' not in st.session_state:
    st.session_state.book_filter = {}
if 'show_book_details' not in st.session_state:
    st.session_state.show_book_details = None
if 'show_user_profile' not in st.session_state:
    st.session_state.show_user_profile = None
if 'chat_user_id' not in st.session_state:
    st.session_state.chat_user_id = None

if 'search_params' not in st.session_state:
    st.session_state.search_params = {}

# Функції для взаємодії з API

def api_request(method, endpoint, data=None, params=None):
    url = f"{SERVER_URL}/{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url, params=params)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_message = f"Помилка з'єднання з сервером: {e}"
        st.error(error_message)
        return {"status": "помилка", "повідомлення": error_message}
    except json.JSONDecodeError:
        error_message = "Помилка отримання даних з сервера"
        st.error(error_message)
        return {"status": "помилка", "повідомлення": error_message}

def register_user(data):
    # Додаємо емодзі-аватарку
    import random
    avatars = ["👨", "👩", "🧑", "👦", "👧", "👨‍🦰", "👩‍🦰", "👨‍🦱", "👩‍🦱", "👨‍🦲", 
               "👩‍🦲", "👨‍🦳", "👩‍🦳", "🧔", "🧑‍🦰", "🧑‍🦱", "🧑‍🦲", "🧑‍🦳"]
    
    # Додаємо випадковий емодзі як аватарку
    data["avatar_symbol"] = random.choice(avatars)
    
    response = requests.post(
        f"{SERVER_URL}/users",
        json=data
    )
    return response.json()



def login_user(email, password):
    response = requests.post(
        f"{SERVER_URL}/login",
        json={"email": email, "password": password}
    )
    return response.json()

def get_user_profile(user_id):
    response = requests.get(f"{SERVER_URL}/users/{user_id}")
    return response.json()

def update_user_profile(user_id, data):
    response = requests.put(
        f"{SERVER_URL}/users/{user_id}",
        json=data
    )
    return response.json()

def get_books(params=None):
    url = f"{SERVER_URL}/books"
    if params:
        url += "?" + "&".join([f"{k}={v}" for k, v in params.items() if v])
    try:
        response = requests.get(url)
        response.raise_for_status()  # Перевіряємо статус відповіді
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Помилка з'єднання з сервером: {e}")
        return {"status": "помилка", "повідомлення": f"Помилка з'єднання з сервером: {e}", "книги": []}
    except json.JSONDecodeError:
        st.error("Помилка отримання даних з сервера")
        return {"status": "помилка", "повідомлення": "Помилка отримання даних з сервера", "книги": []}

def get_book(book_id):
    response = requests.get(f"{SERVER_URL}/books/{book_id}")
    return response.json()

def add_book(data):
    response = requests.post(
        f"{SERVER_URL}/books",
        json=data
    )
    return response.json()

def update_book(book_id, data):
    response = requests.put(
        f"{SERVER_URL}/books/{book_id}",
        json=data
    )
    return response.json()

def delete_book(book_id, user_id):
    response = requests.delete(f"{SERVER_URL}/books/{book_id}?user_id={user_id}")
    return response.json()

def request_exchange(book_id, borrower_id, message=None):
    data = {
        "book_id": book_id,
        "borrower_id": borrower_id
    }
    if message:
        data["message"] = message
    
    response = requests.post(
        f"{SERVER_URL}/exchanges",
        json=data
    )
    return response.json()

def get_owner_exchanges(owner_id, status=None):
    url = f"{SERVER_URL}/exchanges/owner/{owner_id}"
    if status:
        url += f"?status={status}"
    response = requests.get(url)
    return response.json()

def get_borrower_exchanges(borrower_id, status=None):
    url = f"{SERVER_URL}/exchanges/borrower/{borrower_id}"
    if status:
        url += f"?status={status}"
    response = requests.get(url)
    return response.json()

def update_exchange_status(exchange_id, status):
    response = requests.put(
        f"{SERVER_URL}/exchanges/{exchange_id}",
        json={"status": status}
    )
    return response.json()

def get_genres():
    response = requests.get(f"{SERVER_URL}/genres")
    return response.json()

def add_to_wishlist(data):
    response = requests.post(
        f"{SERVER_URL}/wishlist",
        json=data
    )
    return response.json()

def get_wishlist(user_id):
    response = requests.get(f"{SERVER_URL}/wishlist/{user_id}")
    return response.json()

def delete_from_wishlist(wishlist_id, user_id):
    response = requests.delete(f"{SERVER_URL}/wishlist/{wishlist_id}?user_id={user_id}")
    return response.json()

def add_book_review(book_id, user_id, rating, comment):
    response = requests.post(
        f"{SERVER_URL}/books/{book_id}/reviews",
        json={"user_id": user_id, "rating": rating, "comment": comment}
    )
    return response.json()

def add_user_review(user_id, reviewer_id, rating, comment):
    response = requests.post(
        f"{SERVER_URL}/users/{user_id}/reviews",
        json={"reviewer_id": reviewer_id, "rating": rating, "comment": comment}
    )
    return response.json()

def get_chat_messages(user1_id, user2_id):
    response = requests.get(f"{SERVER_URL}/chat/{user1_id}/{user2_id}")
    return response.json()

def send_message(sender_id, receiver_id, content):
    response = requests.post(
        f"{SERVER_URL}/chat/send",
        json={"sender_id": sender_id, "receiver_id": receiver_id, "content": content}
    )
    return response.json()

def get_notifications(user_id, mark_read=False):
    response = requests.get(f"{SERVER_URL}/notifications/{user_id}?mark_read={str(mark_read).lower()}")
    return response.json()

def search_users(query=None, region=None):
    url = f"{SERVER_URL}/users/search"
    params = []
    if query:
        params.append(f"q={query}")
    if region:
        params.append(f"region={region}")
    
    if params:
        url += "?" + "&".join(params)
    
    response = requests.get(url)
    return response.json()

def get_statistics():
    response = requests.get(f"{SERVER_URL}/statistics")
    return response.json()

# Функція для форматування дати
def format_date(date_str):
    if not date_str:
        return ""
    try:
        date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
        return date_obj.strftime("%d.%m.%Y %H:%M")
    except:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return date_obj.strftime("%d.%m.%Y %H:%M")
        except:
            return date_str

# Відображення рейтингу зірочками
def display_rating(rating):
    stars = "★" * int(rating)
    stars += "☆" * (5 - int(rating))
    return f"{stars} ({rating}/5)"

# Функції для сторінок додатку

def show_login_page():
    st.title("📚 Книгообмін")
    st.subheader("Платформа для обміну книгами українською мовою")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Вхід", "Реєстрація"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Вхід до системи")
                email = st.text_input("Електронна пошта")
                password = st.text_input("Пароль", type="password")
                submit = st.form_submit_button("Увійти")
                
                if submit:
                    if email and password:
                        with st.spinner("Авторизація..."):
                            result = login_user(email, password)
                            if result.get("status") == "успіх":
                                st.session_state.user = result.get("користувач")
                                st.session_state.page = 'main'
                                st.rerun()
                            else:
                                st.error(result.get("повідомлення", "Помилка авторизації"))
                    else:
                        st.error("Всі поля повинні бути заповнені")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("Створення облікового запису")
                username = st.text_input("Ім'я користувача")
                email = st.text_input("Електронна пошта", key="reg_email")
                password = st.text_input("Пароль", type="password", key="reg_password")
                password_confirm = st.text_input("Підтвердження пароля", type="password")
                full_name = st.text_input("Повне ім'я (необов'язково)")
                
                col1, col2 = st.columns(2)
                with col1:
                    phone_number = st.text_input("Номер телефону (необов'язково)")
                with col2:
                    region = st.text_input("Регіон (необов'язково)")
                
                submit = st.form_submit_button("Зареєструватися")
                
                if submit:
                    if username and email and password and password_confirm:
                        if password != password_confirm:
                            st.error("Паролі не співпадають")
                        else:
                            with st.spinner("Реєстрація..."):
                                result = register_user({
                                    "username": username,
                                    "email": email,
                                    "password": password,
                                    "full_name": full_name,
                                    "phone_number": phone_number,
                                    "region": region
                                })
                                
                                if result.get("status") == "успіх":
                                    st.success("Реєстрація успішна. Тепер ви можете увійти.")
                                else:
                                    st.error(result.get("повідомлення", "Помилка реєстрації"))
                    else:
                        st.error("Ім'я користувача, електронна пошта та пароль обов'язкові")
    
    # Інформація про платформу
    st.markdown("---")
    st.subheader("Що таке \"Книгообмін\"?")
    st.write("Платформа \"Книгообмін\" допомагає читачам ділитися книгами та знаходити нові цікаві видання.")
    
    st.write("**Можливості платформи:**")
    st.write("• Додавання власних книг в каталог")
    st.write("• Обмін книгами з іншими користувачами")
    st.write("• Ведення списку бажаних книг")
    st.write("• Спілкування через внутрішній чат")
    st.write("• Оцінки та відгуки про книги та користувачів")

def show_main_page():
    # Перевірка авторизації
    if not st.session_state.user:
        st.session_state.page = 'login'
        st.rerun()
        return
    
    # Бічна панель з меню
    with st.sidebar:
        st.title("📚 Книгообмін")
        st.write(f"Вітаємо, **{st.session_state.user['username']}**!")
        
        # Меню
        st.subheader("Меню")
        menu_options = [
            "Доступні книги", 
            "Мої книги", 
            "Обміни", 
            "Список бажаного", 
            "Повідомлення", 
            "Мій профіль",
            "Пошук користувачів",
            "Статистика"
        ]
        
        # Замінюємо радіокнопки окремими кнопками
        for option in menu_options:
            if st.button(option, key=f"menu_{option}", use_container_width=True):
                st.session_state.active_tab = option
                st.session_state.show_book_details = None
                st.session_state.show_user_profile = None
                st.rerun()
        
        if st.button("Вихід", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = 'login'
            st.rerun()
    
    # Головний контент
    if st.session_state.show_book_details:
        show_book_details(st.session_state.show_book_details)
    elif st.session_state.show_user_profile:
        show_user_profile(st.session_state.show_user_profile)
    elif st.session_state.active_tab == "Доступні книги":
        show_available_books()
    elif st.session_state.active_tab == "Мої книги":
        show_my_books()
    elif st.session_state.active_tab == "Обміни":
        show_exchanges()
    elif st.session_state.active_tab == "Список бажаного":
        show_wishlist()
    elif st.session_state.active_tab == "Повідомлення":
        show_messages()
    elif st.session_state.active_tab == "Мій профіль":
        show_my_profile()
    elif st.session_state.active_tab == "Пошук користувачів":
        show_user_search()
    elif st.session_state.active_tab == "Статистика":
        show_statistics_page()

def reset_details():
    st.session_state.show_book_details = None
    st.session_state.show_user_profile = None
    if 'edit_book' in st.session_state:
        del st.session_state.edit_book

def show_available_books():
    st.title("📖 Доступні книги")
    
    # Фільтри пошуку
    with st.expander("🔍 Фільтри пошуку", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            title = st.text_input("Назва книги", st.session_state.book_filter.get('title', ''))
        
        with col2:
            author = st.text_input("Автор", st.session_state.book_filter.get('author', ''))
        
        with col3:
            # Отримання списку жанрів
            genres_result = get_genres()
            if genres_result.get("status") == "успіх":
                genres = genres_result.get("жанри", [])
                genre_options = ["Всі жанри"] + [g["name"] for g in genres]
                genre_id_map = {g["name"]: g["id"] for g in genres}
                
                current_genre = "Всі жанри"
                if 'genre_id' in st.session_state.book_filter:
                    for g in genres:
                        if g["id"] == st.session_state.book_filter['genre_id']:
                            current_genre = g["name"]
                            break
                
                selected_genre = st.selectbox("Жанр", genre_options, index=genre_options.index(current_genre))
            else:
                selected_genre = "Всі жанри"
                genre_id_map = {}
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            region = st.text_input("Регіон власника", st.session_state.book_filter.get('region', ''))
        
        with col2:
            is_free_options = ["Всі книги", "Безкоштовно", "Обмін"]
            is_free_index = 0
            if 'is_free' in st.session_state.book_filter:
                is_free_index = 1 if st.session_state.book_filter['is_free'] == 'true' else 2
            
            is_free = st.selectbox("Тип", is_free_options, index=is_free_index)
        
        with col3:
            sort_options = {
                "created_at_DESC": "Спочатку новіші",
                "created_at_ASC": "Спочатку старіші",
                "title_ASC": "Назва (А-Я)",
                "title_DESC": "Назва (Я-А)",
                "rating_DESC": "Рейтинг (спадання)",
                "rating_ASC": "Рейтинг (зростання)"
            }
            
            default_sort = st.session_state.book_filter.get('sort_by', 'created_at') + '_' + st.session_state.book_filter.get('sort_order', 'DESC')
            if default_sort not in sort_options:
                default_sort = "created_at_DESC"
            
            sort_option = st.selectbox(
                "Сортування",
                options=list(sort_options.keys()),
                format_func=lambda x: sort_options[x],
                index=list(sort_options.keys()).index(default_sort)
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Застосувати фільтри", use_container_width=True):
                # Оновлення фільтрів
                st.session_state.book_filter = {
                    'title': title,
                    'author': author,
                    'region': region,
                    'sort_by': sort_option.split('_')[0],
                    'sort_order': sort_option.split('_')[1]
                }
                
                # Додавання жанру
                if selected_genre != "Всі жанри":
                    st.session_state.book_filter['genre_id'] = genre_id_map.get(selected_genre)
                elif 'genre_id' in st.session_state.book_filter:
                    del st.session_state.book_filter['genre_id']
                
                # Додавання типу (безкоштовно/обмін)
                if is_free == "Безкоштовно":
                    st.session_state.book_filter['is_free'] = 'true'
                elif is_free == "Обмін":
                    st.session_state.book_filter['is_free'] = 'false'
                elif 'is_free' in st.session_state.book_filter:
                    del st.session_state.book_filter['is_free']
                
                st.rerun()
        
        with col2:
            if st.button("Скинути фільтри", use_container_width=True):
                st.session_state.book_filter = {}
                st.rerun()
    
    # Отримання списку книг з фільтрами
    filter_params = {**st.session_state.book_filter, 'status': 'доступна'}
    
    # Не показуємо власні книги
    if st.session_state.user:
        filter_params['owner_id_not'] = st.session_state.user["id"]
    
    books_result = get_books(filter_params)
    
    if books_result.get("status") == "успіх":
        books = books_result.get("книги", [])
        total_books = books_result.get("загальна_кількість", 0)
        
        # Відображення кількості знайдених книг
        st.write(f"Знайдено книг: {total_books}")
        
        if not books:
            st.info("Немає доступних книг, які відповідають вашим критеріям пошуку.")
            return
        
        # Відображення книг сіткою
        cols = st.columns(3)
        
        for i, book in enumerate(books):
            with cols[i % 3]:
                with st.container():
                    st.markdown(f"""
                    <div class="book-card">
                        <h3>{book['title']}</h3>
                        <p><em>{book['author']}</em></p>
                        <p>Жанр: {book.get('genre_name', 'Не вказано')}</p>
                        <p>Власник: {book.get('owner_name', 'Невідомо')}</p>
                        <p>Тип: {"Безкоштовно" if book.get('is_free') else "Обмін"}</p>
                        <p>{display_rating(book.get('rating', 0))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Деталі", key=f"book_{book['id']}"):
                        st.session_state.show_book_details = book['id']
                        st.rerun()

def show_book_details(book_id):
    # Отримання даних про книгу
    result = get_book(book_id)
    
    if result.get("status") != "успіх":
        st.error(result.get("повідомлення", "Не вдалося отримати дані про книгу"))
        st.button("← Назад", on_click=reset_details)
        return
    
    book = result.get("книга")
    
    # Верхня панель з навігацією
    col1, col2 = st.columns([1, 6])
    with col1:
        st.button("← Назад", on_click=reset_details)
    with col2:
        st.title(book['title'])
    
    # Основний вміст
    col1, col2 = st.columns([1, 2])
    
    with col1:
        cover_url = book.get("cover_url") or "https://via.placeholder.com/300x450?text=Немає+обкладинки"
        st.image(cover_url, width=300)
        
        st.subheader("Власник книги")
        st.markdown(f"""
        <div class="user-card">
            <strong>{book.get('owner_name')}</strong><br>
            Регіон: {book.get('owner_region', 'Не вказано')}
        </div>
        """, unsafe_allow_html=True)
        
        # Кнопки дій
        if book["status"] == "доступна" and book["owner_id"] != st.session_state.user["id"]:
            st.subheader("Дії")
            
            if st.button("Запитати обмін", type="primary", use_container_width=True):
                with st.form(key="exchange_request_form"):
                    st.subheader("Запит на обмін")
                    message = st.text_area("Повідомлення власнику (необов'язково)", 
                                          placeholder="Напишіть повідомлення власнику книги")
                    submit = st.form_submit_button("Надіслати запит", use_container_width=True)
                    
                    if submit:
                        with st.spinner("Надсилання запиту..."):
                            result = request_exchange(book["id"], st.session_state.user["id"], message)
                            if result.get("status") == "успіх":
                                st.success("Запит на обмін успішно надіслано!")
                                time.sleep(2)
                                reset_details()
                                st.rerun()
                            else:
                                st.error(result.get("повідомлення", "Помилка при створенні запиту"))
            
            # Додати в список бажаного
            if st.button("Додати в список бажаного", use_container_width=True):
                with st.spinner("Додавання в список бажаного..."):
                    result = add_to_wishlist({
                        "user_id": st.session_state.user["id"],
                        "title": book["title"],
                        "author": book["author"],
                        "genre_id": book["genre_id"]
                    })
                    
                    if result.get("status") == "успіх":
                        st.success("Книгу додано до списку бажаного!")
                    else:
                        st.error(result.get("повідомлення", "Помилка при додаванні в список бажаного"))
            
            # Написати власнику
            if st.button("Написати власнику", use_container_width=True):
                st.session_state.chat_user_id = book["owner_id"]
                st.session_state.active_tab = "Повідомлення"
                st.session_state.show_book_details = None
                st.rerun()
        
        elif book["owner_id"] == st.session_state.user["id"]:
            st.subheader("Керування книгою")
            
            if book["status"] == "доступна":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Редагувати", use_container_width=True):
                        st.session_state.edit_book = book
                        st.rerun()
                with col2:
                    if st.button("Видалити", use_container_width=True):
                        confirm_delete = st.checkbox("Підтвердити видалення")
                        if confirm_delete:
                            with st.spinner("Видалення книги..."):
                                result = delete_book(book["id"], st.session_state.user["id"])
                                if result.get("status") == "успіх":
                                    st.success("Книгу успішно видалено!")
                                    time.sleep(2)
                                    reset_details()
                                    st.rerun()
                                else:
                                    st.error(result.get("повідомлення", "Помилка при видаленні книги"))
            else:
                status_text = ""
                if book["status"] == "зарезервована":
                    status_text = '<span class="book-status-reserved">Зарезервована</span>'
                elif book["status"] == "видана":
                    status_text = '<span class="book-status-borrowed">Видана</span>'
                
                st.markdown(f"Статус: {status_text}", unsafe_allow_html=True)
    
    with col2:
        # Інформація про книгу
        st.subheader("Інформація про книгу")
        
        book_type = "Безкоштовно" if book.get("is_free") else "Обмін"
        
        status_text = ""
        if book["status"] == "доступна":
            status_text = '<span class="book-status-available">Доступна</span>'
        elif book["status"] == "зарезервована":
            status_text = '<span class="book-status-reserved">Зарезервована</span>'
        elif book["status"] == "видана":
            status_text = '<span class="book-status-borrowed">Видана</span>'
        
        st.markdown(f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <p><strong>Автор:</strong> {book["author"]}</p>
            <p><strong>Жанр:</strong> {book.get("genre_name") or "Не вказано"}</p>
            <p><strong>Тип:</strong> {book_type}</p>
            <p><strong>Статус:</strong> {status_text}</p>
            <p><strong>Рейтинг:</strong> {display_rating(book.get("rating") or 0)}</p>
            <p><strong>Додано:</strong> {format_date(book.get("created_at"))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if "description" in book and book["description"]:
            st.subheader("Опис")
            st.write(book["description"])
        
        # Відгуки про книгу
        st.subheader("Відгуки")
        
        reviews = book.get("відгуки", [])
        
        # Форма для додавання нового відгуку
        if book["owner_id"] != st.session_state.user["id"]:
            with st.expander("Додати відгук", expanded=False):
                with st.form(key="add_review_form"):
                    rating = st.slider("Оцінка", min_value=1, max_value=5, value=5)
                    comment = st.text_area("Коментар", placeholder="Напишіть свій відгук про книгу")
                    submit = st.form_submit_button("Додати відгук", use_container_width=True)
                    
                    if submit:
                        with st.spinner("Додавання відгуку..."):
                            result = add_book_review(book["id"], st.session_state.user["id"], rating, comment)
                            if result.get("status") == "успіх":
                                st.success("Відгук успішно додано!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(result.get("повідомлення", "Помилка при додаванні відгуку"))
        
        if reviews:
            for review in reviews:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <p><strong>{review.get('username')}</strong> • {format_date(review.get('created_at'))}</p>
                    <p>{display_rating(review.get('rating') or 0)}</p>
                    <p>{review.get('comment') or "Без коментаря"}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("У цієї книги ще немає відгуків.")

def show_my_books():
    st.title("📚 Мої книги")
    
    # Додавання нової книги
    with st.expander("📝 Додати нову книгу", expanded=False):
        with st.form(key="add_book_form"):
            st.subheader("Додавання нової книги")
            
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Назва книги", key="add_title")
            with col2:
                author = st.text_input("Автор", key="add_author")
            
            # Отримання списку жанрів
            genres_result = get_genres()
            if genres_result.get("status") == "успіх":
                genres = genres_result.get("жанри", [])
                genre_options = ["Не вказано"] + [g["name"] for g in genres]
                genre_id_map = {g["name"]: g["id"] for g in genres}
                
                selected_genre = st.selectbox("Жанр", genre_options, index=0, key="add_genre")
            else:
                selected_genre = "Не вказано"
                genre_id_map = {}
            
            is_free = st.checkbox("Безкоштовно (не вимагає обміну)", key="add_is_free")
            
            description = st.text_area("Опис книги", key="add_description")
            
            submit = st.form_submit_button("Додати книгу", use_container_width=True)
            
            if submit:
                if title and author:
                    with st.spinner("Додавання книги..."):
                        # Підготовка даних
                        book_data = {
                            "title": title,
                            "author": author,
                            "description": description,
                            "owner_id": st.session_state.user["id"],
                            "is_free": is_free
                        }
                        
                        if selected_genre != "Не вказано":
                            book_data["genre_id"] = genre_id_map.get(selected_genre)
                        
                        # Додавання книги
                        result = add_book(book_data)
                        
                        if result.get("status") == "успіх":
                            st.success(f"Книгу успішно додано! {result.get('повідомлення', '')}")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(result.get("повідомлення", "Помилка при додаванні книги"))
                else:
                    st.error("Назва та автор обов'язкові")
    
    # Відображення моїх книг
    if 'edit_book' in st.session_state:
        # Режим редагування книги
        with st.form(key="edit_book_form"):
            book = st.session_state.edit_book
            st.subheader(f"Редагування книги: {book['title']}")
            
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Назва книги", value=book.get("title", ""), key="edit_title")
            with col2:
                author = st.text_input("Автор", value=book.get("author", ""), key="edit_author")
            
            # Отримання списку жанрів
            genres_result = get_genres()
            if genres_result.get("status") == "успіх":
                genres = genres_result.get("жанри", [])
                genre_options = ["Не вказано"] + [g["name"] for g in genres]
                genre_id_map = {g["name"]: g["id"] for g in genres}
                
                current_genre_index = 0
                if book.get("genre_id"):
                    current_genre = next((g["name"] for g in genres if g["id"] == book["genre_id"]), "Не вказано")
                    if current_genre in genre_options:
                        current_genre_index = genre_options.index(current_genre)
                
                selected_genre = st.selectbox("Жанр", genre_options, index=current_genre_index, key="edit_genre")
            else:
                selected_genre = "Не вказано"
                genre_id_map = {}
            
            is_free = st.checkbox("Безкоштовно (не вимагає обміну)", value=book.get("is_free", False), key="edit_is_free")
            
            description = st.text_area("Опис книги", value=book.get("description", ""), key="edit_description")
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Зберегти зміни", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Скасувати", use_container_width=True)
            
            if submit:
                if title and author:
                    with st.spinner("Оновлення книги..."):
                        # Підготовка даних
                        book_data = {
                            "title": title,
                            "author": author,
                            "description": description,
                            "is_free": is_free
                        }
                        
                        if selected_genre != "Не вказано":
                            book_data["genre_id"] = genre_id_map.get(selected_genre)
                        
                        # Оновлення книги
                        result = update_book(book["id"], book_data)
                        
                        if result.get("status") == "успіх":
                            st.success("Книгу успішно оновлено!")
                            del st.session_state.edit_book
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(result.get("повідомлення", "Помилка при оновленні книги"))
                else:
                    st.error("Назва та автор обов'язкові")
            
            if cancel:
                del st.session_state.edit_book
                st.rerun()
    else:
        # Отримання моїх книг
        books_result = get_books({"owner_id": st.session_state.user["id"]})
        
        if books_result.get("status") == "успіх":
            books = books_result.get("книги", [])
            
            if not books:
                st.info("У вас поки що немає доданих книг.")
                return
            
            # Статистика
            total_books = len(books)
            available_count = len([book for book in books if book["status"] == "доступна"])
            reserved_count = len([book for book in books if book["status"] == "зарезервована"])
            lent_count = len([book for book in books if book["status"] == "видана"])
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Всього книг", total_books)
            col2.metric("Доступні", available_count)
            col3.metric("Зарезервовані", reserved_count)
            col4.metric("Видані", lent_count)
            
            # Групування за статусом
            available_books = [book for book in books if book["status"] == "доступна"]
            reserved_books = [book for book in books if book["status"] == "зарезервована"]
            lent_books = [book for book in books if book["status"] == "видана"]
    
            # Закладки для разных групп книг
            tabs = st.tabs(["Всі книги", "Доступні", "Зарезервовані", "Видані"])
    
            with tabs[0]:
                show_book_list(books, prefix="all")
    
            with tabs[1]:
                if available_books:
                    show_book_list(available_books, prefix="available")
                else:
                    st.info("У вас немає доступних книг.")
    
            with tabs[2]:
                if reserved_books:
                    show_book_list(reserved_books, prefix="reserved")
                else:
                    st.info("У вас немає зарезервованих книг.")
    
            with tabs[3]:
                if lent_books:
                    show_book_list(lent_books, prefix="lent")
                else:
                    st.info("У вас немає виданих книг.")
        else:
            st.error(books_result.get("повідомлення", "Не вдалося отримати список книг"))

def show_book_list(books, prefix="mybook"):
    # Відображення книг сіткою
    cols = st.columns(3)
    
    for i, book in enumerate(books):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="book-card">
                <h3>{book['title']}</h3>
                <p><em>{book['author']}</em></p>
                <p><strong>Жанр:</strong> {book.get('genre_name', 'Не вказано')}</p>
                <p><strong>Тип:</strong> {"Безкоштовно" if book.get('is_free') else "Обмін"}</p>
                <p><strong>Статус:</strong> <span class="book-status-{book['status'].lower()}">{book['status'].capitalize()}</span></p>
                <p>{display_rating(book.get('rating', 0))}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Деталі", key=f"{prefix}_{book['id']}_{i}"):
                st.session_state.show_book_details = book['id']
                st.rerun()

def show_exchanges():
    st.title("🔄 Обміни")
    
    # Закладки для різних типів обмінів
    tabs = st.tabs(["Запити на мої книги", "Мої запити на книги"])
    
    # Обробка запитів від інших користувачів
    with tabs[0]:
        # Отримання запитів на обмін для власника
        result = get_owner_exchanges(st.session_state.user["id"])
        
        if result.get("status") == "успіх":
            exchanges = result.get("обміни", [])
            
            if not exchanges:
                st.info("У вас немає запитів на обмін.")
            else:
                # Групування за статусом
                pending_requests = [ex for ex in exchanges if ex["status"] == "запит"]
                accepted_requests = [ex for ex in exchanges if ex["status"] == "прийнято"]
                rejected_requests = [ex for ex in exchanges if ex["status"] == "відхилено"]
                returned_requests = [ex for ex in exchanges if ex["status"] == "повернуто"]
                
                # Статистика
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Очікують", len(pending_requests))
                col2.metric("Активні", len(accepted_requests))
                col3.metric("Відхилені", len(rejected_requests))
                col4.metric("Повернуті", len(returned_requests))
                
                # Закладки для різних статусів
                status_tabs = st.tabs(["Очікують", "Активні", "Відхилені", "Повернуті"])
                
                with status_tabs[0]:
                    if pending_requests:
                        for ex in pending_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Позичальник:</strong> {ex['borrower_name']}</p>
                                <p><strong>Дата запиту:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-pending">Очікує підтвердження</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("Прийняти", key=f"accept_{ex['id']}"):
                                    with st.spinner("Обробка запиту..."):
                                        result = update_exchange_status(ex['id'], "прийнято")
                                        if result.get("status") == "успіх":
                                            st.success("Запит прийнято!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(result.get("повідомлення", "Помилка при оновленні запиту"))
                            with col2:
                                if st.button("Відхилити", key=f"reject_{ex['id']}"):
                                    with st.spinner("Обробка запиту..."):
                                        result = update_exchange_status(ex['id'], "відхилено")
                                        if result.get("status") == "успіх":
                                            st.success("Запит відхилено.")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(result.get("повідомлення", "Помилка при оновленні запиту"))
                            with col3:
                                if st.button("Написати", key=f"message_o_{ex['borrower_id']}"):
                                    st.session_state.chat_user_id = ex['borrower_id']
                                    st.session_state.active_tab = "Повідомлення"
                                    st.rerun()
                    else:
                        st.info("У вас немає запитів, які очікують підтвердження.")
                
                with status_tabs[1]:
                    if accepted_requests:
                        for ex in accepted_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Позичальник:</strong> {ex['borrower_name']}</p>
                                <p><strong>Дата видачі:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-accepted">Видано</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Написати позичальнику", key=f"message_a_{ex['borrower_id']}"):
                                st.session_state.chat_user_id = ex['borrower_id']
                                st.session_state.active_tab = "Повідомлення"
                                st.rerun()
                    else:
                        st.info("У вас немає активних обмінів.")
                
                with status_tabs[2]:
                    if rejected_requests:
                        for ex in rejected_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Позичальник:</strong> {ex['borrower_name']}</p>
                                <p><strong>Дата запиту:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-rejected">Відхилено</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("У вас немає відхилених запитів.")
                
                with status_tabs[3]:
                    if returned_requests:
                        for ex in returned_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Позичальник:</strong> {ex['borrower_name']}</p>
                                <p><strong>Дата запиту:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Дата повернення:</strong> {format_date(ex['end_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-returned">Повернуто</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Оцінити користувача", key=f"review_u_{ex['borrower_id']}"):
                                with st.form(key=f"review_user_form_{ex['borrower_id']}"):
                                    st.subheader(f"Оцінка користувача {ex['borrower_name']}")
                                    rating = st.slider("Оцінка", min_value=1, max_value=5, value=5)
                                    comment = st.text_area("Коментар", placeholder="Напишіть свій відгук про користувача")
                                    submit = st.form_submit_button("Додати відгук", use_container_width=True)
                                    
                                    if submit:
                                        with st.spinner("Додавання відгуку..."):
                                            result = add_user_review(
                                                ex['borrower_id'], 
                                                st.session_state.user["id"], 
                                                rating, 
                                                comment
                                            )
                                            
                                            if result.get("status") == "успіх":
                                                st.success("Відгук успішно додано!")
                                                time.sleep(2)
                                                st.rerun()
                                            else:
                                                st.error(result.get("повідомлення", "Помилка при додаванні відгуку"))
                    else:
                        st.info("У вас немає повернутих книг.")
        else:
            st.error(result.get("повідомлення", "Не вдалося отримати список запитів"))
    
    # Обробка моїх запитів на книги інших користувачів
    with tabs[1]:
        # Отримання запитів на обмін для позичальника
        result = get_borrower_exchanges(st.session_state.user["id"])
        
        if result.get("status") == "успіх":
            exchanges = result.get("обміни", [])
            
            if not exchanges:
                st.info("У вас немає запитів на обмін.")
            else:
                # Групування за статусом
                pending_requests = [ex for ex in exchanges if ex["status"] == "запит"]
                accepted_requests = [ex for ex in exchanges if ex["status"] == "прийнято"]
                rejected_requests = [ex for ex in exchanges if ex["status"] == "відхилено"]
                returned_requests = [ex for ex in exchanges if ex["status"] == "повернуто"]
                
                # Статистика
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("В очікуванні", len(pending_requests))
                col2.metric("Отримані", len(accepted_requests))
                col3.metric("Відхилені", len(rejected_requests))
                col4.metric("Повернуті", len(returned_requests))
                
                # Закладки для різних статусів
                status_tabs = st.tabs(["В очікуванні", "Отримані", "Відхилені", "Повернуті"])
                
                with status_tabs[0]:
                    if pending_requests:
                        for ex in pending_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Власник:</strong> {ex['owner_name']}</p>
                                <p><strong>Дата запиту:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-pending">Очікує підтвердження</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Скасувати запит", key=f"cancel_{ex['id']}"):
                                    with st.spinner("Обробка запиту..."):
                                        result = update_exchange_status(ex['id'], "відхилено")
                                        if result.get("status") == "успіх":
                                            st.success("Запит скасовано.")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(result.get("повідомлення", "Помилка при оновленні запиту"))
                            with col2:
                                if st.button("Написати власнику", key=f"message_b_{ex['owner_id']}"):
                                    st.session_state.chat_user_id = ex['owner_id']
                                    st.session_state.active_tab = "Повідомлення"
                                    st.rerun()
                    else:
                        st.info("У вас немає запитів, які очікують підтвердження.")
                
                with status_tabs[1]:
                    if accepted_requests:
                        for ex in accepted_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Власник:</strong> {ex['owner_name']}</p>
                                <p><strong>Дата видачі:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-accepted">Отримано</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Повернути книгу", key=f"return_{ex['id']}"):
                                    with st.spinner("Обробка запиту..."):
                                        result = update_exchange_status(ex['id'], "повернуто")
                                        if result.get("status") == "успіх":
                                            st.success("Книгу позначено як повернуту!")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(result.get("повідомлення", "Помилка при оновленні запиту"))
                            with col2:
                                if st.button("Написати власнику", key=f"message_c_{ex['owner_id']}"):
                                    st.session_state.chat_user_id = ex['owner_id']
                                    st.session_state.active_tab = "Повідомлення"
                                    st.rerun()
                    else:
                        st.info("У вас немає отриманих книг.")
                
                with status_tabs[2]:
                    if rejected_requests:
                        for ex in rejected_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Власник:</strong> {ex['owner_name']}</p>
                                <p><strong>Дата запиту:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-rejected">Відхилено</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("У вас немає відхилених запитів.")
                
                with status_tabs[3]:
                    if returned_requests:
                        for ex in returned_requests:
                            st.markdown(f"""
                            <div class="book-card">
                                <h3>{ex['title']}</h3>
                                <p><em>{ex['author']}</em></p>
                                <p><strong>Власник:</strong> {ex['owner_name']}</p>
                                <p><strong>Дата запиту:</strong> {format_date(ex['start_date'])}</p>
                                <p><strong>Дата повернення:</strong> {format_date(ex['end_date'])}</p>
                                <p><strong>Статус:</strong> <span class="exchange-status-returned">Повернуто</span></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Оцінити користувача", key=f"review_o_{ex['owner_id']}"):
                                    with st.form(key=f"review_owner_form_{ex['owner_id']}"):
                                        st.subheader(f"Оцінка користувача {ex['owner_name']}")
                                        rating = st.slider("Оцінка", min_value=1, max_value=5, value=5)
                                        comment = st.text_area("Коментар", placeholder="Напишіть свій відгук про користувача")
                                        submit = st.form_submit_button("Додати відгук", use_container_width=True)
                                        
                                        if submit:
                                            with st.spinner("Додавання відгуку..."):
                                                result = add_user_review(
                                                    ex['owner_id'], 
                                                    st.session_state.user["id"], 
                                                    rating, 
                                                    comment
                                                )
                                                
                                                if result.get("status") == "успіх":
                                                    st.success("Відгук успішно додано!")
                                                    time.sleep(2)
                                                    st.rerun()
                                                else:
                                                    st.error(result.get("повідомлення", "Помилка при додаванні відгуку"))
                            with col2:
                                if st.button("Оцінити книгу", key=f"review_b_{ex['book_id']}"):
                                    with st.form(key=f"review_book_form_{ex['book_id']}"):
                                        st.subheader(f"Оцінка книги '{ex['title']}'")
                                        rating = st.slider("Оцінка", min_value=1, max_value=5, value=5)
                                        comment = st.text_area("Коментар", placeholder="Напишіть свій відгук про книгу")
                                        submit = st.form_submit_button("Додати відгук", use_container_width=True)
                                        
                                        if submit:
                                            with st.spinner("Додавання відгуку..."):
                                                result = add_book_review(
                                                    ex['book_id'], 
                                                    st.session_state.user["id"], 
                                                    rating, 
                                                    comment
                                                )
                                                
                                                if result.get("status") == "успіх":
                                                    st.success("Відгук успішно додано!")
                                                    time.sleep(2)
                                                    st.rerun()
                                                else:
                                                    st.error(result.get("повідомлення", "Помилка при додаванні відгуку"))
                    else:
                        st.info("У вас немає повернутих книг.")
        else:
            st.error(result.get("повідомлення", "Не вдалося отримати список запитів"))

def show_wishlist():
    st.title("📋 Список бажаного")
    
    # Додавання книги в список бажаного
    with st.expander("📝 Додати книгу в список бажаного", expanded=False):
        with st.form(key="add_wishlist_form"):
            st.subheader("Додавання книги в список бажаного")
            
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Назва книги", key="wish_title")
            with col2:
                author = st.text_input("Автор (необов'язково)", key="wish_author")
            
            # Отримання списку жанрів
            genres_result = get_genres()
            if genres_result.get("status") == "успіх":
                genres = genres_result.get("жанри", [])
                genre_options = ["Не вказано"] + [g["name"] for g in genres]
                genre_id_map = {g["name"]: g["id"] for g in genres}
                
                selected_genre = st.selectbox("Жанр (необов'язково)", genre_options, index=0, key="wish_genre")
            else:
                selected_genre = "Не вказано"
                genre_id_map = {}
            
            submit = st.form_submit_button("Додати в список бажаного", use_container_width=True)
            
            if submit:
                if title:
                    with st.spinner("Додавання в список бажаного..."):
                        # Підготовка даних
                        wishlist_data = {
                            "user_id": st.session_state.user["id"],
                            "title": title,
                            "author": author
                        }
                        
                        if selected_genre != "Не вказано":
                            wishlist_data["genre_id"] = genre_id_map.get(selected_genre)
                        
                        # Додавання в список бажаного
                        result = add_to_wishlist(wishlist_data)
                        
                        if result.get("status") == "успіх":
                            if result.get("знайдені_книги"):
                                st.success(f"Додано в список бажаного! Знайдено {len(result.get('знайдені_книги'))} відповідних книг.")
                            else:
                                st.success("Додано в список бажаного!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(result.get("повідомлення", "Помилка при додаванні в список бажаного"))
                else:
                    st.error("Назва книги обов'язкова")
    
    # Отримання списку бажаного
    result = get_wishlist(st.session_state.user["id"])
    
    if result.get("status") == "успіх":
        wishlist = result.get("список_бажаного", [])
        
        if not wishlist:
            st.info("Ваш список бажаного порожній.")
            return
        
        st.write(f"У вашому списку бажаного {len(wishlist)} книг")
        
        for item in wishlist:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div class="book-card">
                    <h3>{item['title']}</h3>
                    <p><em>{item.get('author') or 'Автор не вказаний'}</em></p>
                    <p><strong>Жанр:</strong> {item.get('genre_name') or 'Не вказано'}</p>
                    <p><strong>Додано:</strong> {format_date(item.get('created_at'))}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Видалити", key=f"delete_wish_{item['id']}"):
                    with st.spinner("Видалення зі списку бажаного..."):
                        result = delete_from_wishlist(item['id'], st.session_state.user["id"])
                        if result.get("status") == "успіх":
                            st.success("Видалено зі списку бажаного!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(result.get("повідомлення", "Помилка при видаленні зі списку бажаного"))
            
            if "доступні_варіанти" in item and item["доступні_варіанти"]:
                st.write(f"Знайдено {len(item['доступні_варіанти'])} книг, які відповідають запиту:")
                
                for variant in item["доступні_варіанти"]:
                    st.markdown(f"""
                    <div class="book-card" style="margin-left: 30px;">
                        <h4>{variant['title']}</h4>
                        <p><em>{variant['author']}</em></p>
                        <p><strong>Власник:</strong> {variant['owner_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Переглянути", key=f"view_variant_{variant['id']}"):
                        st.session_state.show_book_details = variant['id']
                        st.rerun()
    else:
        st.error(result.get("повідомлення", "Не вдалося отримати список бажаного"))

def show_messages():
    st.title("💬 Повідомлення")
    
    # Отримання активних обмінів для визначення співрозмовників
    owner_exchanges = get_owner_exchanges(st.session_state.user["id"])
    borrower_exchanges = get_borrower_exchanges(st.session_state.user["id"])
    
    contacts = []
    
    if owner_exchanges.get("status") == "успіх":
        for exchange in owner_exchanges.get("обміни", []):
            if exchange.get("status") in ["запит", "прийнято"]:
                contacts.append({
                    "id": exchange["borrower_id"],
                    "username": exchange["borrower_name"],
                    "unread_messages": exchange.get("непрочитані_повідомлення", 0)
                })
    
    if borrower_exchanges.get("status") == "успіх":
        for exchange in borrower_exchanges.get("обміни", []):
            if exchange.get("status") in ["запит", "прийнято"]:
                contacts.append({
                    "id": exchange["owner_id"],
                    "username": exchange["owner_name"],
                    "unread_messages": exchange.get("непрочитані_повідомлення", 0)
                })
    
    # Видалення дублікатів контактів
    unique_contacts = []
    seen_ids = set()
    for contact in contacts:
        if contact["id"] not in seen_ids:
            seen_ids.add(contact["id"])
            unique_contacts.append(contact)
    
    contacts = unique_contacts
    
    # Якщо немає активного співрозмовника, вибираємо першого зі списку
    if not st.session_state.chat_user_id and contacts:
        st.session_state.chat_user_id = contacts[0]["id"]
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Контакти")
        
        if not contacts:
            st.info("У вас немає активних контактів.")
            return
        
        for contact in contacts:
            style = ""
            if contact["id"] == st.session_state.chat_user_id:
                style = "background-color: #f0f0f0;"
            
            st.markdown(f"""
            <div class="user-card" style="{style}">
                <strong>{contact.get('username')}</strong>
                {f"<span style='color: red; margin-left: 10px;'>({contact['unread_messages']} непрочитаних)</span>" if contact.get("unread_messages", 0) > 0 else ""}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Вибрати", key=f"select_contact_{contact['id']}"):
                st.session_state.chat_user_id = contact["id"]
                st.rerun()
    
    with col2:
        if st.session_state.chat_user_id:
            # Отримання повідомлень
            chat_result = get_chat_messages(st.session_state.user["id"], st.session_state.chat_user_id)
            
            if chat_result.get("status") == "успіх":
                messages = chat_result.get("повідомлення", [])
                chat_user = chat_result.get("співрозмовник", {})
                
                st.subheader(f"Чат з {chat_user.get('username')}")
                
                # Відображення повідомлень
                message_container = st.container()
                
                with message_container:
                    if not messages:
                        st.info("У вас ще немає повідомлень з цим користувачем.")
                    else:
                        for message in messages:
                            is_user = message["sender_id"] == st.session_state.user["id"]
                            align = "flex-end" if is_user else "flex-start"
                            bg_color = COLORS["primary_light"] if is_user else "#f0f0f0"
    
                            # Використовуємо символ аватарки
                            avatar_symbol = message.get("sender_avatar_symbol", "👤")
    
                            st.markdown(f"""
                            <div style="display: flex; justify-content: {align}; margin-bottom: 10px;">
                                <div style="display: flex; align-items: center;">
                                    <div style="font-size: 24px; margin-right: 10px;">
                                        {avatar_symbol}
                                    </div>
                                    <div style="background-color: {bg_color}; padding: 10px; border-radius: 10px; max-width: 80%;">
                                        <p style="margin: 0;">{message.get('content')}</p>
                                        <p style="margin: 0; font-size: 0.7rem; text-align: right; color: #777;">
                                            {format_date(message.get('created_at'))}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Форма для надсилання повідомлення
                with st.form(key=f"send_message_form"):
                    message = st.text_area("Повідомлення", key="message_text", placeholder="Напишіть повідомлення...")
                    
                    submit = st.form_submit_button("Надіслати")
                    
                    if submit and message:
                        with st.spinner("Надсилання повідомлення..."):
                            result = send_message(
                                st.session_state.user["id"], 
                                st.session_state.chat_user_id, 
                                message
                            )
                            
                            if result.get("status") == "успіх":
                                st.rerun()
                            else:
                                st.error(result.get("повідомлення", "Помилка при надсиланні повідомлення"))
            else:
                st.error(chat_result.get("повідомлення", "Не вдалося отримати повідомлення"))
        else:
            st.info("Виберіть контакт зі списку зліва, щоб розпочати спілкування.")

def show_my_profile():
    st.title("👤 Мій профіль")
    
    # Отримання даних профілю
    result = get_user_profile(st.session_state.user["id"])
    
    if result.get("status") == "успіх":
        user = result.get("користувач")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Використовуємо символ аватарки або стандартний символ
            avatar_symbol = user.get("avatar_symbol", "👤")
            
            # Відображаємо символ у великому розмірі
            st.markdown(f"""
            <div style="font-size: 100px; text-align: center; margin-bottom: 20px;">
                {avatar_symbol}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="user-card" style="display: block; text-align: center;">
                <h3>{user.get('username')}</h3>
                <p>{display_rating(user.get("rating") or 0)}</p>
                <p>{user.get("rating_count") or 0} відгуків</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Додаткова інформація
            st.markdown(f"""
            <div class="book-card">
                <h3>Статистика</h3>
                <p><strong>Книг у бібліотеці:</strong> {user.get("кількість_книг") or 0}</p>
                <p><strong>Дата реєстрації:</strong> {format_date(user.get("created_at"))}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Особисті дані
            with st.expander("✏️ Редагувати профіль", expanded=False):
                with st.form(key="edit_profile_form"):
                    st.subheader("Редагування профілю")
                    
                    # Додаємо вибір емодзі-аватарки
                    avatars = ["👨", "👩", "🧑", "👦", "👧", "👨‍🦰", "👩‍🦰", "👨‍🦱", "👩‍🦱", "👨‍🦲", 
                              "👩‍🦲", "👨‍🦳", "👩‍🦳", "🧔", "🧑‍🦰", "🧑‍🦱", "🧑‍🦲", "🧑‍🦳"]
                    
                    current_avatar = user.get("avatar_symbol", "👤")
                    selected_avatar = st.selectbox(
                        "Аватарка", 
                        options=avatars,
                        index=avatars.index(current_avatar) if current_avatar in avatars else 0
                    )
                    
                    full_name = st.text_input("Повне ім'я", value=user.get("full_name", ""))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        phone_number = st.text_input("Номер телефону", value=user.get("phone_number", ""))
                    with col2:
                        region = st.text_input("Регіон", value=user.get("region", ""))
                    
                    submit = st.form_submit_button("Зберегти зміни", use_container_width=True)
                    
                    if submit:
                        with st.spinner("Оновлення профілю..."):
                            # Підготовка даних
                            profile_data = {
                                "full_name": full_name,
                                "phone_number": phone_number,
                                "region": region,
                                "avatar_symbol": selected_avatar
                            }
                            
                            # Оновлення профілю
                            result = update_user_profile(st.session_state.user["id"], profile_data)
                            
                            if result.get("status") == "успіх":
                                st.success("Профіль успішно оновлено!")
                                # Оновлення даних користувача в сесії
                                st.session_state.user["full_name"] = full_name
                                st.session_state.user["phone_number"] = phone_number
                                st.session_state.user["region"] = region
                                st.session_state.user["avatar_symbol"] = selected_avatar
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(result.get("повідомлення", "Помилка при оновленні профілю"))
            
            # Відгуки про користувача
            st.subheader("Відгуки про мене")
            
            reviews = user.get("відгуки", [])
            
            if reviews:
                for review in reviews:
                    st.markdown(f"""
                    <div class="book-card">
                        <p><strong>{review.get('username')}</strong> • {format_date(review.get('created_at'))}</p>
                        <p>{display_rating(review.get('rating') or 0)}</p>
                        <p>{review.get('comment') or "Без коментаря"}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("У вас ще немає відгуків від інших користувачів.")
    else:
        st.error(result.get("повідомлення", "Не вдалося отримати дані профілю"))

def show_user_profile(user_id):
    # Отримання даних профілю
    result = get_user_profile(user_id)
    
    if result.get("status") != "успіх":
        st.error(result.get("повідомлення", "Не вдалося отримати дані профілю"))
        st.button("← Назад", on_click=reset_details)
        return
    
    user = result.get("користувач")
    
    # Верхня панель з навігацією
    col1, col2 = st.columns([1, 6])
    with col1:
        st.button("← Назад", on_click=reset_details)
    with col2:
        st.title(f"Профіль користувача {user['username']}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        avatar_url = user.get("avatar_url") or "https://via.placeholder.com/200"
        st.image(avatar_url, width=200)
        
        st.markdown(f"""
        <div class="user-card" style="display: block; text-align: center;">
            <h3>{user.get('username')}</h3>
            <p>{display_rating(user.get("rating") or 0)}</p>
            <p>{user.get("rating_count") or 0} відгуків</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Додаткова інформація
        st.markdown(f"""
        <div class="book-card">
            <h3>Інформація</h3>
            <p><strong>Регіон:</strong> {user.get("region") or "Не вказано"}</p>
            <p><strong>Книг у бібліотеці:</strong> {user.get("кількість_книг") or 0}</p>
            <p><strong>На платформі з:</strong> {format_date(user.get("created_at"))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Кнопки дій
        st.subheader("Дії")
        
        if st.button("Написати повідомлення", use_container_width=True):
            st.session_state.chat_user_id = user["id"]
            st.session_state.active_tab = "Повідомлення"
            st.session_state.show_user_profile = None
            st.rerun()
        
        # Пошук книг користувача
        if st.button("Переглянути книги", use_container_width=True):
            st.session_state.book_filter = {"owner_id": user["id"]}
            st.session_state.active_tab = "Доступні книги"
            st.session_state.show_user_profile = None
            st.rerun()
    
    with col2:
        # Відгуки про користувача
        st.subheader("Відгуки про користувача")
        
        reviews = user.get("відгуки", [])
        
        # Додавання відгуку
        can_review = False
        
        # Отримання обмінів з користувачем для перевірки можливості додати відгук
        owner_exchanges = get_owner_exchanges(st.session_state.user["id"])
        borrower_exchanges = get_borrower_exchanges(st.session_state.user["id"])
        
        if owner_exchanges.get("status") == "успіх":
            for exchange in owner_exchanges.get("обміни", []):
                if exchange.get("borrower_id") == user["id"] and exchange.get("status") == "повернуто":
                    can_review = True
                    break
        
        if not can_review and borrower_exchanges.get("status") == "успіх":
            for exchange in borrower_exchanges.get("обміни", []):
                if exchange.get("owner_id") == user["id"] and exchange.get("status") == "повернуто":
                    can_review = True
                    break
        
        if can_review:
            with st.expander("Додати відгук", expanded=False):
                with st.form(key=f"add_user_review_form"):
                    rating = st.slider("Оцінка", min_value=1, max_value=5, value=5)
                    comment = st.text_area("Коментар", placeholder="Напишіть свій відгук про користувача")
                    submit = st.form_submit_button("Додати відгук", use_container_width=True)
                    
                    if submit:
                        with st.spinner("Додавання відгуку..."):
                            result = add_user_review(
                                user["id"], 
                                st.session_state.user["id"], 
                                rating, 
                                comment
                            )
                            
                            if result.get("status") == "успіх":
                                st.success("Відгук успішно додано!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(result.get("повідомлення", "Помилка при додаванні відгуку"))
        
        if reviews:
            for review in reviews:
                st.markdown(f"""
                <div class="book-card">
                    <p><strong>{review.get('username')}</strong> • {format_date(review.get('created_at'))}</p>
                    <p>{display_rating(review.get('rating') or 0)}</p>
                    <p>{review.get('comment') or "Без коментаря"}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("У користувача ще немає відгуків.")
        
        # Отримання книг користувача
        books_result = get_books({"owner_id": user["id"], "status": "доступна"})
        
        if books_result.get("status") == "успіх":
            books = books_result.get("книги", [])
            
            if books:
                st.subheader("Доступні книги користувача")
                
                for book in books[:5]:  # Показуємо тільки останні 5 книг
                    st.markdown(f"""
                    <div class="book-card">
                        <h3>{book['title']}</h3>
                        <p><em>{book['author']}</em></p>
                        <p><strong>Жанр:</strong> {book.get('genre_name') or 'Не вказано'}</p>
                        <p><strong>Тип:</strong> {"Безкоштовно" if book.get("is_free") else "Обмін"}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Деталі", key=f"user_book_{book['id']}"):
                        st.session_state.show_book_details = book['id']
                        st.session_state.show_user_profile = None
                        st.rerun()
                
                if len(books) > 5:
                    if st.button("Показати всі книги користувача", use_container_width=True):
                        st.session_state.book_filter = {"owner_id": user["id"]}
                        st.session_state.active_tab = "Доступні книги"
                        st.session_state.show_user_profile = None
                        st.rerun()
            else:
                st.info("У користувача немає доступних книг.")
        else:
            st.error(books_result.get("повідомлення", "Не вдалося отримати список книг користувача"))

def show_user_search():
    st.title("🔍 Пошук користувачів")
    
    # Форма пошуку
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        query = st.text_input("Ім'я або повне ім'я", st.session_state.search_params.get('query', ''))
    
    with col2:
        region = st.text_input("Регіон", st.session_state.search_params.get('region', ''))
    
    with col3:
        st.write(" ")  # Проміжок для вирівнювання
        search_button = st.button("Пошук", use_container_width=True)
    
    if search_button:
        if not query and not region:
            st.warning("Вкажіть хоча б один параметр пошуку.")
        else:
            st.session_state.search_params = {'query': query, 'region': region}
            st.rerun()
    
    # Результати пошуку
    if 'search_params' in st.session_state and (st.session_state.search_params.get('query') or st.session_state.search_params.get('region')):
        with st.spinner("Пошук користувачів..."):
            result = search_users(
                st.session_state.search_params.get('query'), 
                st.session_state.search_params.get('region')
            )
            
            if result.get("status") == "успіх":
                users = result.get("користувачі", [])
                
                if users:
                    st.subheader(f"Знайдено {len(users)} користувачів")
                    
                    # Відображення результатів
                    cols = st.columns(3)
                    
                    for i, user in enumerate(users):
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div class="user-card" style="display: block;">
                                <h3>{user.get('username')}</h3>
                                <p>{user.get('full_name') or 'Ім\'я не вказано'}</p>
                                <p><strong>Регіон:</strong> {user.get('region') or 'Не вказано'}</p>
                                <p>{display_rating(user.get('rating') or 0)}</p>
                                <p>📚 {user.get('кількість_книг') or 0} книг • ⭐ {user.get('кількість_відгуків') or 0} відгуків</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("Перейти до профілю", key=f"user_profile_{user['id']}"):
                                st.session_state.show_user_profile = user["id"]
                                st.rerun()
                else:
                    st.info("За вашим запитом не знайдено користувачів.")
            else:
                st.error(result.get("повідомлення", "Помилка при пошуку користувачів"))

def show_statistics_page():
    st.title("📊 Статистика платформи")
    
    with st.spinner("Завантаження статистики..."):
        result = get_statistics()
        
        if result.get("status") == "успіх":
            stats = result.get("статистика", {})
            
            # Основні цифри
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Користувачів", stats.get("користувачів", 0))
            
            with col2:
                st.metric("Всього книг", stats.get("книг_всього", 0))
            
            with col3:
                st.metric("Доступних книг", stats.get("книг_доступно", 0))
            
            with col4:
                st.metric("Успішних обмінів", stats.get("обмінів_успішних", 0))
            
            st.markdown("---")
            
            # Обміни
            st.subheader("Статистика обмінів")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="book-card" style="text-align: center;">
                    <h3>Всього обмінів</h3>
                    <p style="font-size: 2rem; font-weight: 600;">{stats.get("обмінів_всього", 0)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="book-card" style="text-align: center;">
                    <h3>Активних обмінів</h3>
                    <p style="font-size: 2rem; font-weight: 600;">{stats.get("обмінів_активних", 0)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Обчислення відсотка успішних обмінів
                total_exchanges = stats.get("обмінів_всього", 0)
                successful_exchanges = stats.get("обмінів_успішних", 0)
                success_rate = 0
                
                if total_exchanges > 0:
                    success_rate = round((successful_exchanges / total_exchanges) * 100)
                
                st.markdown(f"""
                <div class="book-card" style="text-align: center;">
                    <h3>Успішність обмінів</h3>
                    <p style="font-size: 2rem; font-weight: 600;">{success_rate}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Популярні жанри і нові книги
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Популярні жанри")
                
                popular_genres = stats.get("популярні_жанри", [])
                
                if popular_genres:
                    for genre in popular_genres:
                        st.markdown(f"""
                        <div class="book-card">
                            <div style="display: flex; justify-content: space-between;">
                                <p>{genre.get('name')}</p>
                                <p><strong>{genre.get('count')} книг</strong></p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Немає даних про популярні жанри.")
            
            with col2:
                st.subheader("Нові книги")
                
                newest_books = stats.get("нові_книги", [])
                
                if newest_books:
                    for book in newest_books:
                        st.markdown(f"""
                        <div class="book-card">
                            <h4>{book.get('title')}</h4>
                            <p>{book.get('author')}</p>
                            <p><small>Додано: {format_date(book.get('created_at'))}</small></p>
                            <p><small>Власник: {book.get('owner_name')}</small></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Деталі", key=f"stats_book_{book['id']}"):
                            st.session_state.show_book_details = book["id"]
                            st.rerun()
                else:
                    st.info("Немає даних про нові книги.")
            
            st.markdown("---")
            
            # Найактивніші користувачі
            st.subheader("Найактивніші користувачі")
            
            active_users = stats.get("активні_користувачі", [])
            
            if active_users:
                cols = st.columns(5)
                
                for i, user in enumerate(active_users):
                    with cols[i % 5]:
                        st.markdown(f"""
                        <div class="user-card" style="display: block; text-align: center;">
                            <h4>{user.get('username')}</h4>
                            <p>{user.get('book_count')} книг</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Профіль", key=f"stats_user_{user['id']}"):
                            st.session_state.show_user_profile = user["id"]
                            st.rerun()
            else:
                st.info("Немає даних про активних користувачів.")
        else:
            st.error(result.get("повідомлення", "Не вдалося отримати статистику"))

# Головна функція для запуску додатку
def main():
    # Направлення на відповідну сторінку
    if st.session_state.page == 'login':
        show_login_page()
    elif st.session_state.page == 'main':
        show_main_page()

if __name__ == "__main__":
    main()