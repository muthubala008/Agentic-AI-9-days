from app.repository.database import (
    get_connection,
    initialize_database
)


def seed_courses():

    courses = [
        (
            "CS101",
            "Programming Fundamentals",
            4,
            "None",
            "Introduction to programming, variables, loops, functions and basic problem solving."
        ),
        (
            "CS201",
            "Data Structures",
            4,
            "Programming Fundamentals",
            "Arrays, linked lists, stacks, queues, trees, graphs and algorithms."
        ),
        (
            "CS301",
            "Database Management",
            3,
            "Data Structures",
            "Relational databases, SQL, normalization and database design."
        ),
        (
            "AI301",
            "Machine Learning",
            4,
            "Python, Statistics",
            "Introduction to supervised learning, unsupervised learning and model evaluation."
        ),
        (
            "AI302",
            "Artificial Intelligence",
            4,
            "Data Structures",
            "Search, knowledge representation, reasoning and intelligent systems."
        )
    ]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.executemany("""
        INSERT OR IGNORE INTO courses
        (code, name, credits, prerequisite, description)
        VALUES (?, ?, ?, ?, ?)
    """, courses)

    connection.commit()
    connection.close()

    print("Courses inserted successfully.")


def seed_resources():

    resources = [
        (
            "Python",
            "Python Official Documentation",
            "Documentation",
            "https://docs.python.org/3/"
        ),
        (
            "Python",
            "Python Tutorial",
            "Tutorial",
            "https://docs.python.org/3/tutorial/"
        ),
        (
            "Python",
            "Python Programming Course",
            "Course",
            "https://www.python.org/about/gettingstarted/"
        ),
        (
            "SQL",
            "SQL Tutorial",
            "Tutorial",
            "https://www.w3schools.com/sql/"
        ),
        (
            "NumPy",
            "NumPy Documentation",
            "Documentation",
            "https://numpy.org/doc/"
        ),
        (
            "Pandas",
            "Pandas Documentation",
            "Documentation",
            "https://pandas.pydata.org/docs/"
        ),
        (
            "Data Structures",
            "Data Structures Study Guide",
            "Study Guide",
            "https://www.geeksforgeeks.org/data-structures/"
        )
    ]

    connection = get_connection()
    cursor = connection.cursor()

    cursor.executemany("""
        INSERT INTO resources
        (topic, title, resource_type, url)
        VALUES (?, ?, ?, ?)
    """, resources)

    connection.commit()
    connection.close()

    print("Resources inserted successfully.")


def main():

    print("Starting database setup...")

    initialize_database()

    seed_courses()

    seed_resources()

    print()
    print("====================================")
    print("DATABASE SETUP COMPLETED")
    print("====================================")


if __name__ == "__main__":
    main()