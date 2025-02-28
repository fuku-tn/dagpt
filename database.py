import os
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_databases():
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/template1"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false;"))
        databases = [row[0] for row in result.fetchall()]
    return databases

def get_schemas(database):
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema');"))
        schemas = [row[0] for row in result.fetchall()]
    return schemas, engine

def get_tables_and_views(engine, schema):
    with engine.connect() as conn:
        result_tables = conn.execute(text(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}';"))
        tables = [row[0] for row in result_tables.fetchall()]
        result_views = conn.execute(text(f"SELECT table_name FROM information_schema.views WHERE table_schema = '{schema}';"))
        views = [row[0] for row in result_views.fetchall()]
    return tables, views

def stream_data_from_table(engine, schema, table, chunk_size=10000):
    query = f"SELECT * FROM {schema}.{table}"
    return pd.read_sql_query(query, engine, chunksize=chunk_size)