from django.shortcuts import render, get_object_or_404
from django.db import connections
from .models import Database

def get_database_objects(db_name):
    connection = connections[db_name]
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = [row[0] for row in cursor.fetchall()]
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", [db_name])
        procedures = [row[1] for row in cursor.fetchall()]
        cursor.execute("SHOW FUNCTION STATUS WHERE Db = %s", [db_name])
        functions = [row[1] for row in cursor.fetchall()]
        cursor.execute("SHOW TRIGGERS")
        triggers = [row[0] for row in cursor.fetchall()]
    return {
        'tables': tables,
        'views': views,
        'procedures': procedures,
        'functions': functions,
        'triggers': triggers,
    }

def object_explorer(request, db_id):
    db = get_object_or_404(Database, id=db_id)
    objects = get_database_objects(db.name)
    return render(request, 'access_control/object_explorer.html', {'objects': objects, 'db_name': db.name, 'db_id': db.id})
def view_table_data(request, db_id, table_name):
    db = get_object_or_404(Database, id=db_id)
    connection = connections[db.name]
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
    return render(request, 'access_control/view_table_data.html', {'columns': columns, 'rows': rows, 'table_name': table_name})
