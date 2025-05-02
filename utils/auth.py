import mysql.connector
import hashlib

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ashu@2003",
    "database": "ai_project"
}

def connect_db(with_database=True):
    """Connects to MySQL, optionally without a database."""
    config = DB_CONFIG.copy()
    if not with_database:
        config.pop("database")  # Connect without selecting a DB
    return mysql.connector.connect(**config)

def initialize_db():
    """Creates the database and necessary tables if they don’t exist."""
    db = connect_db(with_database=False)
    cursor = db.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS ai_project")
    cursor.execute("USE ai_project")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            surname VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            address TEXT NOT NULL,
            dob DATE NOT NULL,
            occupation VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            summary TEXT,  -- ✅ NEW: Store summary in database
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        )
    """)

    db.commit()
    db.close()



def register_user(username, password, name, surname, email, address, occupation):
    """Registers a user with hashed password and additional fields."""
    db = connect_db()
    cursor = db.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, name, surname, email, address, occupation) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, hashed_password, name, surname, email, address, occupation))
        
        db.commit()
        return True
    except mysql.connector.IntegrityError:
        return False
    finally:
        db.close()

def authenticate_user(username, password):
    """Authenticates a user."""
    db = connect_db()
    cursor = db.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    
    db.close()
    return result is not None and result[0] == hashed_password

# Initialize database on first run
if __name__ == "__main__":
    initialize_db()