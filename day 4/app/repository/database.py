import sqlite3
from pathlib import Path


# Find the project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Database folder
DATABASE_DIR = BASE_DIR / "database"

# Database file
DB_PATH = DATABASE_DIR / "academic.db"


def get_connection():
    """Create a connection to the SQLite database."""

    # Make sure database folder exists
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)

    # Return rows as dictionaries
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create all required database tables."""

    connection = get_connection()
    cursor = connection.cursor()

    # Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            credits INTEGER NOT NULL,
            prerequisite TEXT,
            description TEXT
        )
    """)

    # Resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            title TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            url TEXT
        )
    """)

    connection.commit()
    connection.close()

    print(f"Database initialized at:")
    print(DB_PATH)


def get_course(course_name: str):
    """Find a course by name."""

    # Make sure tables exist
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            code,
            name,
            credits,
            prerequisite,
            description
        FROM courses
        WHERE LOWER(name) = LOWER(?)
    """, (course_name,))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def search_resources(topic: str):
    """Find learning resources for a topic."""

    # Make sure tables exist
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            topic,
            title,
            resource_type,
            url
        FROM resources
        WHERE LOWER(topic) LIKE LOWER(?)
    """, (f"%{topic}%",))

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]