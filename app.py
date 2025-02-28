import streamlit as st
from database import get_databases, get_schemas, get_tables_and_views
from data_process import process_data_and_analyze
import pandas as pd
st.title("🔗 Kết nối PostgreSQL, Chọn Database, Schema & Phân Tích với GPT-4o")

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
            selected_tables = st.multiselect("Chọn Table hoặc View:", tables + views, key="selected_tables")
        except Exception as e:
            st.error(f"Lỗi khi lấy danh sách bảng và view: {e}")
            selected_tables = []
        
        if selected_tables:
            chunk_size = st.number_input("Số dòng mỗi lần tải (chunk size):", min_value=5000, max_value=50000, value=10000, step=5000)
            
            if "result" not in st.session_state:
                st.session_state.result = None
            
            if st.button("Tải và Phân tích", key="load_data"):
                with st.spinner("Đang xử lý..."):
                    try:
                        st.session_state.result = process_data_and_analyze(engine, selected_schema, selected_tables, chunk_size)
                        st.dataframe(pd.DataFrame(st.session_state.result["data"]))
                        st.success(f"Đã tải dữ liệu từ {len(selected_tables)} bảng thành công ({len(st.session_state.result['data'])} dòng).")
                    except Exception as e:
                        st.error(f"Lỗi khi tải dữ liệu: {e}")
            
            if st.session_state.result:
                query = st.text_input("Nhập câu hỏi của bạn về dữ liệu:")
                if st.button("Phân tích với AI", key="analyze_data"):
                    with st.spinner("Đang xử lý..."):
                        try:
                            result = process_data_and_analyze(engine, selected_schema, selected_tables, chunk_size, query)
                            st.write(result["analysis"])
                        except Exception as e:
                            st.error(f"Lỗi khi xử lý truy vấn: {e}")