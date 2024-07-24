from django.db import connections, OperationalError
from django.conf import settings
from .models import Database

def load_databases():
    DATABASES = {}
    for db in Database.objects.all():
        db.update_database_settings()
    return DATABASES


def check_database_connections(databases):
    for db_name in databases.keys():
        try:
            with connections[db_name].cursor() as cursor:
                cursor.execute("SELECT 1")
            Database.objects.filter(name=db_name).update(status='Connected')
        except OperationalError as e:
            print(f"Connection to {db_name} failed: {e}")
            Database.objects.filter(name=db_name).update(status='Disconnected')


# utils.py
from django.db import connections

def get_database_objects(connection_name):
    connection = connections[connection_name]
    cursor = connection.cursor()

    cursor.execute("SHOW FULL TABLES")
    tables = cursor.fetchall()

    cursor.execute("SHOW PROCEDURE STATUS WHERE Db = DATABASE()")
    procedures = cursor.fetchall()

    cursor.execute("SHOW FUNCTION STATUS WHERE Db = DATABASE()")
    functions = cursor.fetchall()

    cursor.execute("SHOW TRIGGERS")
    triggers = cursor.fetchall()

    objects = {
        'tables': tables,
        'procedures': procedures,
        'functions': functions,
        'triggers': triggers,
    }

    return objects
