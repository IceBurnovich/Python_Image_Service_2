import os
from contextlib import closing

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "images_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5533"),
}


def get_images_count(query=""):
    with closing(psycopg2.connect(**DB_CONFIG)) as connection:
        with connection:
            with connection.cursor() as cursor:
                if query:
                    cursor.execute(
                        "SELECT COUNT(*) FROM images WHERE original_name ILIKE %s",
                        (f"%{query}%",),
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM images")
                return cursor.fetchone()[0]


def save_image(filename, original_name, size, file_type):
    with closing(psycopg2.connect(**DB_CONFIG)) as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO images (filename, original_name, size, file_type)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (filename, original_name, size, file_type),
                )


def get_images(page=1, per_page=10, query=""):
    offset = (page - 1) * per_page
    sql = """
        SELECT
            id,
            filename,
            original_name,
            size,
            upload_time,
            file_type,
            ROUND(size / 1024.0, 1) AS size_kb
        FROM images
    """
    params = []
    if query:
        sql += " WHERE original_name ILIKE %s"
        params.append(f"%{query}%")
    sql += " ORDER BY upload_time DESC, id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    with closing(psycopg2.connect(**DB_CONFIG)) as connection:
        with connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, tuple(params))
                return cursor.fetchall()


def get_image_by_id(image_id):
    with closing(psycopg2.connect(**DB_CONFIG)) as connection:
        with connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, filename FROM images WHERE id = %s",
                    (image_id,),
                )
                return cursor.fetchone()


def delete_image(image_id):
    with closing(psycopg2.connect(**DB_CONFIG)) as connection:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM images WHERE id = %s", (image_id,))
                return cursor.rowcount
