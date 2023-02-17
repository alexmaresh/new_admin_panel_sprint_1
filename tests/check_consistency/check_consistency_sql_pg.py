import unittest
import sqlite3
import psycopg2
import os

db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sqlite_to_postgres', 'db.sqlite')
tables_for_test = ['genre', 'film_work', 'person', 'genre_film_work', 'person_film_work']


class TestCompareSQLitePostgresTables(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            # Get database connection parameters for SQLite database
            cls.sqlite_conn = sqlite3.connect(db_path)

            # Create a connection to PostgreSQL database
            cls.postgres_conn = psycopg2.connect(
                dbname='movies_database',
                user='app',
                password='123qwe',
                host='127.0.0.1',
                port='5432'
            )

        except Exception as e:
            raise e

    def compare_tables_quontity(self, table_name):
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute('''SELECT count(*) FROM %s''' % (table_name))
        sqlite_result = sqlite_cursor.fetchall()

        postgres_cursor = self.postgres_conn.cursor()
        postgres_cursor.execute('''SELECT count(*) FROM content.%s''' % (table_name))
        postgres_result = postgres_cursor.fetchall()
        self.assertEqual(sqlite_result, postgres_result)

    def compare_tables_content(self, table_name):
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute(f'''PRAGMA table_info({table_name});''')
        sqlite_result = len(sqlite_cursor.fetchall())

        postgres_cursor = self.postgres_conn.cursor()
        postgres_cursor.execute(f'''SELECT count(*) FROM information_schema.columns WHERE table_name = {table_name}''')
        postgres_result = postgres_cursor.fetchall()
        self.assertEqual(sqlite_result, postgres_result)

    def test_compare_tables(self):
        for table in tables_for_test:
            self.compare_tables_quontity(table)
            self.compare_tables_content(table)

    @classmethod
    def tearDownClass(cls):
        # Close the database connections
        cls.sqlite_conn.close()
        cls.postgres_conn.close()


if __name__ == "__main__":
    unittest.main()
