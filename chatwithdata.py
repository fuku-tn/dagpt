import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.title("🔗 Kết nối PostgreSQL & Phân Tích với GPT-4o")

st.subheader("Chọn Database")
response = requests.get(f"{API_URL}/databases")
if response.status_code == 200:
    databases = response.json()
    selected_db = st.selectbox("Chọn Database:", databases)
else:
    st.error("Lỗi khi lấy danh sách database!")
    selected_db = None

if selected_db:
    response = requests.get(f"{API_URL}/schemas?database={selected_db}")
    if response.status_code == 200:
        schemas = response.json()
        selected_schema = st.selectbox("Chọn Schema:", schemas)
    else:
        st.error("Lỗi khi lấy danh sách schema!")
        selected_schema = None

    if selected_schema:
        response = requests.get(f"{API_URL}/tables?database={selected_db}&schema={selected_schema}")
        if response.status_code == 200:
            tables = response.json()
            selected_table = st.selectbox("Chọn Table:", tables)
        else:
            st.error("Lỗi khi lấy danh sách bảng!")
            selected_table = None

        if selected_table:
            # 🆕 Lấy dữ liệu từ bảng đã chọn
            if st.button("Tải dữ liệu"):
                response = requests.get(f"{API_URL}/data?database={selected_db}&schema={selected_schema}&table={selected_table}")
                if response.status_code == 200:
                    data = response.json()
                    df = pd.DataFrame(data)  # Chuyển dữ liệu thành DataFrame
                    st.dataframe(df)  # Hiển thị bảng trong Streamlit
                else:
                    st.error("Lỗi khi tải dữ liệu!")

            # 🧠 Hỏi AI về dữ liệu
            st.markdown("## Hỏi AI về dữ liệu:")
            query = st.text_input("Nhập câu hỏi về dữ liệu:")
            if st.button("Phân tích với AI"):
                response = requests.post(f"{API_URL}/analyze", json={"query": query})
                if response.status_code == 200:
                    result = response.json()
                    st.write(result)
                else:
                    st.error("Lỗi khi phân tích dữ liệu!")
