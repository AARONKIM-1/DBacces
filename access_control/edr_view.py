import base64
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Database
import mysql.connector
import psycopg2

def get_mysql_connection(db):
    return mysql.connector.connect(
        host=db.host,
        user=db.user,
        password=db.password,
        database=db.name
    )

def get_postgresql_connection(db):
    return psycopg2.connect(
        host=db.host,
        user=db.user,
        password=db.get_password(),
        database=db.name
    )

def get_tables_and_relationships_mysql(connection):
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SHOW TABLES")
    tables = [row[f'Tables_in_{connection.database}'] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        columns = cursor.fetchall()
        schema[table] = [{"name": col["Field"], "type": col["Type"]} for col in columns]

    relationships = []
    cursor.execute("""
    SELECT
        table_name AS table1,
        column_name AS column1,
        referenced_table_name AS table2,
        referenced_column_name AS column2
    FROM
        information_schema.key_column_usage
    WHERE
        referenced_table_name IS NOT NULL
        AND table_schema = DATABASE();
    """)
    relationships = cursor.fetchall()
    
    return schema, relationships

def get_tables_and_relationships_postgresql(connection):
    cursor = connection.cursor()
    
    cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table}'
        """)
        columns = cursor.fetchall()
        schema[table] = [{"name": col[0], "type": col[1]} for col in columns]

    cursor.execute("""
    SELECT
        tc.table_name AS table1,
        kcu.column_name AS column1,
        ccu.table_name AS table2,
        ccu.column_name AS column2
    FROM
        information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
    """)
    relationships = cursor.fetchall()
    
    return schema, relationships

from graphviz import Digraph

from django.conf import settings
import os

# Generate Graphviz script and render it
from graphviz import Digraph

def generate_graphviz_script(tables, relationships):
    dot = Digraph(comment='ER Diagram', format='png')
    
    dot.graph_attr['rankdir'] = 'LR'  # Left to Right
    dot.graph_attr['size'] = '150,150'  # Size of the graph
    dot.node_attr['shape'] = 'record'
    dot.node_attr['fontsize'] = '16'
    dot.node_attr['width'] = '2'
    dot.node_attr['height'] = '1'

    # Add nodes for tables
    for table, columns in tables.items():
        label = f"{table}|{{"
        for column in columns:
            col_type = column.get('type', 'unknown')
            col_name = column.get('name', 'unknown')
            label += f"{col_name}: {col_type}\\l"
        label += "}}"
        dot.node(table, shape='record', label=label)
    
    # Add edges for relationships
    for rel in relationships:
        table1 = rel.get('table1')
        table2 = rel.get('table2')
        if table1 and table2:
            dot.edge(table1, table2, label=rel.get('relation', ''))

    return dot

@staff_member_required
def edr_view(request, db_id):
    db = get_object_or_404(Database, id=db_id)
    
    if db.db_type == 'mysql':
        connection = get_mysql_connection(db)
        tables, relationships = get_tables_and_relationships_mysql(connection)
    elif db.db_type == 'postgresql':
        connection = get_postgresql_connection(db)
        tables, relationships = get_tables_and_relationships_postgresql(connection)
    else:
        return render(request, 'access_control/edr_view.html', {
            'error': 'Unsupported database type'
        })

    dot = generate_graphviz_script(tables, relationships)
    file_path = os.path.join(settings.MEDIA_ROOT, 'edr_graph')
    dot.render(file_path)

    with open(f'{file_path}.png', 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    return render(request, 'access_control/edr_view.html', {
        'db': db,
        'image_data': image_data
    })
