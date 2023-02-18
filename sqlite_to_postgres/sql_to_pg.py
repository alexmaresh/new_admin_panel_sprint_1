import io
import os
import sqlite3
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection as psgr_connection
import logging
import data
from contextlib import contextmanager,closing

load_dotenv()

PACK_SIZE = 10

TABLES_TO_CLASSES = {
    'film_work': data.FilmWork,
    'genre': data.Genre,
    'person': data.Person,
    'genre_film_work': data.GenreFilmWork,
    'person_film_work': data.PersonFilmWork,
}

@contextmanager
def sqlite_connection(db_file):
    conn = sqlite3.connect(db_file)
    try:
        yield conn
    finally:
        conn.close()

class LoadDataSQLite:
    def __init__(self, connection, table_name, data_class):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.table_name = table_name
        self.data_class = data_class
        self.cursor.execute(f'SELECT * FROM {self.table_name}')

    def load_table(self):
        counter = 0
        while True:
            pack_rows = self.cursor.fetchmany(size=PACK_SIZE)
            if not pack_rows:
                break
            pack = []
            for row in pack_rows:
                data = self.data_class(*row)
                pack.append(data)
            yield pack
            counter += 1
        logging.info(f'Из таблицы {self.table_name} загружено {counter} пачек по {PACK_SIZE} записей')


class SavePostgres(LoadDataSQLite):

    def save_all_data(self, data):
        counter = 0

        for block in data:
            block_values = '\n'.join([obj.get_values() for obj in block])
            with io.StringIO(block_values) as f:
                self.cursor.copy_from(f, table=self.table_name, null='None', size=PACK_SIZE)
            counter += 1
        logging.info(f'В таблицу {self.table_name} загружено {counter} пачек по {PACK_SIZE} записей')


def transfer_from_sql_to_pg(sql_conn: sqlite3.Connection, psg_conn: psgr_connection):
    for table_name, data_class in TABLES_TO_CLASSES.items():
        try:
            sqlite_loader = LoadDataSQLite(sql_conn, table_name, data_class)
            data = sqlite_loader.load_table()
        except Exception as err:
            logging.error(f"Ошибка загрузки из SQLite:{err}")
            break
        try:
            postgres_saver = SavePostgres(psg_conn, table_name, data_class)
            postgres_saver.save_all_data(data)
        except Exception as err:
            logging.error(f"Ошибка сохранения в Postgres: {err}")
            break


if __name__ == '__main__':
    dsn = {
        'dbname': os.environ.get('DB_NAME'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'host': os.environ.get('DB_HOST', '127.0.0.1'),
        'port': os.environ.get('DB_PORT', 5432),
        'options': '-c search_path=public,content',
    }

with sqlite_connection('db.sqlite') as sqlite_conn, closing(psycopg2.connect(**dsn)) as pg_conn:
        transfer_from_sql_to_pg(sqlite_conn, pg_conn)

