import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from src.modeling.llm import load_llm
import bcrypt
import json

# Tải biến môi trường
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o"

# Đường dẫn lưu tài khoản người dùng
USER_DB = r'C:/Users/Admin/TEST/dapgt/dagpt/user/user_data.json'
if not os.path.exists(USER_DB):
    with open(USER_DB, 'w') as f:
        json.dump({}, f)

# Hàm tải user database
def load_users():
    with open(USER_DB, "r") as file:
        return json.load(file)

# Hàm lưu user database
def save_users(users):
    with open(USER_DB, "w") as file:
        json.dump(users, file)

# Hàm đăng nhập
def login(username, password):
    users = load_users()
    if username in users:
        hashed_pw = users[username].encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), hashed_pw)
    return False

# Hàm đăng ký
def register(username, password):
    users = load_users()
    if username in users:
        return False, "Tên đăng nhập đã tồn tại!"
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users[username] = hashed_pw.decode("utf-8")
    save_users(users)
    return True, "Đăng ký thành công!"

# Giao diện đăng nhập & đăng ký
def login_page():
    st.title("🔑 Đăng nhập / Đăng ký")
    menu = st.sidebar.selectbox("Chọn chức năng", ["Đăng nhập", "Đăng ký"])
    if menu == "Đăng nhập":
        st.subheader("Đăng nhập")
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            if login(username, password):
                st.success("Đăng nhập thành công!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.experimental_rerun()
            else:
                st.error("Tên đăng nhập hoặc mật khẩu không chính xác.")
    elif menu == "Đăng ký":
        st.subheader("Đăng ký tài khoản mới")
        new_username = st.text_input("Tên đăng nhập mới")
        new_password = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đăng ký"):
            success, message = register(new_username, new_password)
            if success:
                st.success(message)
            else:
                st.error(message)

# Giao diện chính sau khi đăng nhập
def main_app():
    st.sidebar.title("🔓 Menu")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.success("Đã đăng xuất.")
        st.experimental_rerun()
    st.title("🎉 Chào mừng, " + st.session_state["username"])
    
    # Kết nối PostgreSQL và chọn Database, Schema, Table
    st.subheader("🔗 Kết nối PostgreSQL và Chọn Database, Schema, Table")
    try:
        databases = get_databases()
        selected_db = st.selectbox("Chọn Database:", databases, key="selected_db")
    except Exception as e:
        st.error(f"Lỗi khi lấy danh sách database: {e}")
        selected_db = None

    if selected_db:
        try:
            schemas, engine = get_schemas(selected_db)
            selected_schema = st.selectbox("Chọn Schema:", schemas, key="selected_schema")
        except Exception as e:
            st.error(f"Lỗi khi lấy danh sách schema: {e}")
            selected_schema = None

        if selected_schema:
            try:
                tables, views = get_tables_and_views(engine, selected_schema)
                if tables or views:
                    selected_tables = st.multiselect("Chọn Table hoặc View:", tables + views, key="selected_tables")
                else:
                    st.warning("Không có bảng hoặc view nào trong schema này.")
                    selected_tables = []
            except Exception as e:
                st.error(f"Lỗi khi lấy danh sách bảng và view: {e}")
                selected_tables = []

            if selected_tables:
                chunk_size = st.number_input("Số dòng mỗi lần tải (chunk size):", min_value=5000, max_value=50000, value=10000, step=5000)
                if st.button("Tải dữ liệu", key="load_data"):
                    st.session_state.df = pd.DataFrame()
                    try:
                        for table in selected_tables:
                            for chunk in stream_data_from_table(engine, selected_schema, table, chunk_size):
                                st.session_state.df = pd.concat([st.session_state.df, chunk], ignore_index=True)
                                st.dataframe(chunk)
                        st.success(f"Đã tải dữ liệu từ {len(selected_tables)} bảng thành công.")
                    except Exception as e:
                        st.error(f"Lỗi khi tải dữ liệu: {e}")

                if st.session_state.df is not None and not st.session_state.df.empty:
                    llm = load_llm(MODEL_NAME, openai_api_key)
                    da_agent = create_pandas_dataframe_agent(
                        llm=llm,
                        df=st.session_state.df,
                        agent_type="tool-calling",
                        allow_dangerous_code=True,
                        verbose=True,
                        return_intermediate_steps=True
                    )
                    st.markdown("## Hỏi AI về dữ liệu:")
                    query = st.text_input("Nhập câu hỏi của bạn về dữ liệu:")
                    if st.button("Phân tích với AI", key="analyze_data"):
                        with st.spinner("Đang xử lý..."):
                            try:
                                response = da_agent(query)
                                st.write(response["output"])
                            except Exception as e:
                                st.error(f"Lỗi khi xử lý truy vấn: {e}")

# Kiểm tra trạng thái đăng nhập
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    login_page()
else:
    main_app()

if st.session_state.get('rerun', False):
    st.session_state['rerun'] = False
    st.experimental_rerun()

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
        result_tables = conn.execute(text(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema}';
        """))
        tables = [row[0] for row in result_tables.fetchall()]

        result_views = conn.execute(text(f"""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = '{schema}';
        """))
        views = [row[0] for row in result_views.fetchall()]
    return tables, views

def stream_data_from_table(engine, schema, table, chunk_size=10000):
    query = f"SELECT * FROM {schema}.{table}"
    chunks = pd.read_sql_query(query, engine, chunksize=chunk_size)
    for chunk in chunks:
        yield chunk