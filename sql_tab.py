import sqlite3
from typing import List, Optional
from collections import deque
import hashlib

class DB_manager:
    """Класс для работы с базой данных"""
    def __init__(self, db_name='chat.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Устанавливает соединение с базой данных"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        # Включаем поддержку внешних ключей
        self.cursor.execute("PRAGMA foreign_keys = ON")
    
    def _create_tables(self):
        """Создает необходимые таблицы"""
        # Таблица пользователей
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # Таблица для хранения сообщений
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER,
        message_text TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status INTEGER DEFAULT 0,
        reply_to_id INTEGER,
        chat_type BOOLEAN DEFAULT 0,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id),
        FOREIGN KEY (reply_to_id) REFERENCES messages(id)
        )
        ''')

        # Создание индексов
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_time 
            ON messages(group_id, timestamp DESC)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_sender 
            ON messages(sender_id, timestamp DESC)
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_receiver_status 
            ON messages(receiver_id, status, timestamp DESC)
        ''')
        
        self.conn.commit()

    
    def _hash_password(self, password: str) -> str:
        """Хэширует пароль"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str) -> Optional[int]:
        """Регистрирует нового пользователя"""
        try:
            password_hash = self._hash_password(password)
            self.cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Пользователь с таким имененм уже существует
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """Аутентифицирует пользователя"""
        password_hash = self._hash_password(password)
        self.cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        result = self.cursor.fetchone()
        
        if result:
            user_id = result[0]
            # Обновляем время последнего входа
            self.cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user_id,)
            )
            self.conn.commit()
            return user_id
        return None
    
    def get_username_by_id(self, user_id: int) -> Optional[str]:
        """Получает имя пользователя по ID"""
        self.cursor.execute(
            'SELECT username FROM users WHERE id = ?',
            (user_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_id_by_username(self, username: str) -> Optional[int]:
        """Получает имя пользователя по ID"""
        self.cursor.execute(
            'SELECT id FROM users WHERE username = ?',
            (username,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_all_users(self) -> List[tuple]:
        """Получает всех пользователей"""
        self.cursor.execute('SELECT id, username FROM users ORDER BY id')
        return self.cursor.fetchall()
    
    def user_exists(self, user_id: int) -> bool:
        """Проверяет существование пользователя"""
        self.cursor.execute('SELECT 1 FROM users WHERE id = ?', (user_id,))
        return self.cursor.fetchone() is not None
    

    
    def save_message(self, sender_id: int, receiver_id: int, text: str, 
                 group_id: int = None, reply_to_id: int = None, 
                 chat_type: int = 0, status: int = 0):
        """
        Сохраняет сообщение в базу данных
    
        Args:
            sender_id: ID отправителя
            receiver_id: ID получателя (для личных сообщений) или None для групповых
            text: Текст сообщения
            group_id: ID группы (если групповой чат) None для личных сообщений
            reply_to_id: ID сообщения, на которое отвечают (опционально)
            chat_type: тип чата (0 - личный, 1 - групповой)
            status: Статус сообщения (0 - отправлено, 1 - доставлено, 2 - прочитано)
        """
        
        if chat_type != 0 and receiver_id is None:
            receiver_id = None  # Явно указываем NULL для групповых сообщений
        
        self.cursor.execute(
            '''INSERT INTO messages 
            (sender_id, receiver_id, message_text, group_id, 
                reply_to_id, chat_type, status) 
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (sender_id, receiver_id, text, group_id, 
            reply_to_id, chat_type, status)
        )
        self.conn.commit()
        
        # Возвращаем ID созданного сообщения
        return self.cursor.lastrowid
    
    
    def close(self):
        """Закрывает соединение с базой данных"""
        if self.conn:
            self.conn.close()