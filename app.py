import streamlit as st
from database import get_databases, get_schemas, get_tables_and_views
from data_process import process_data_and_analyze
import pandas as pd
st.title("🔗 Kết nối PostgreSQL & Phân Tích với GPT-4o")

# mô hình để người dùng chọn
model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4o-mini"]
selected_model = st.selectbox("Chọn mô hình AI:", model_options, index=2) 

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
            selected_tables = st.multiselect("Chọn Table/View:", tables + views, key="selected_tables")
        except Exception as e:
            st.error(f"Lỗi khi lấy danh sách bảng: {e}")
            selected_tables = []
        
        if selected_tables:
            chunk_size = st.number_input("Chunk size:", min_value=1000, max_value=10000, value=5000, step=1000)
            if st.button("Tải dữ liệu"):
                with st.spinner("Đang xử lý..."):
                    try:
                        # Truyền selected_model vào process_data_and_analyze
                        result = process_data_and_analyze(
                            engine, 
                            selected_schema, 
                            selected_tables, 
                            chunk_size, 
                            model_name=selected_model  # Truyền mô hình được chọn
                        )
                        st.session_state.result = result
                        st.dataframe(pd.DataFrame(result["data"]))
                        st.success(f"Đã tải {len(result['data'])} dòng.")
                    except Exception as e:
                        st.error(f"Lỗi khi tải dữ liệu: {e}")
            
            if "result" in st.session_state:
                query = st.text_input("Hỏi về dữ liệu:")
                if st.button("Phân tích"):
                    with st.spinner("Đang phân tích..."):
                        try:
                            # Truyền selected_model vào khi phân tích
                            result = process_data_and_analyze(
                                engine, 
                                selected_schema, 
                                selected_tables, 
                                chunk_size, 
                                query=query, 
                                model_name=selected_model  # Truyền mô hình được chọn
                            )
                            st.write(result["analysis"])
                        except Exception as e:
                            st.error(f"Lỗi khi phân tích: {e}")