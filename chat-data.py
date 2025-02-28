import streamlit as st
import pandas as pd 
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from src.modeling.logger.base import BaseLogger
from src.modeling.llm import load_llm
import os
import openai
from src.ulti import execute_plt_code
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Tải biến môi trường
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
logger = BaseLogger()
logger.info("### Tải thành công GPT ###")
MODEL_NAME = "gpt-4o-mini"

def process_query(da_agent, query):
    """Xử lý truy vấn từ người dùng."""
    try:
        response = da_agent(query)
        
        if response["intermediate_steps"] and "query" in response["intermediate_steps"][-1][0].tool_input:
            action = response["intermediate_steps"][-1][0].tool_input["query"]

            if "plt" in action:
                st.write(response["output"])
                figure = execute_plt_code(action, df=st.session_state.df)
                if figure:
                    st.pyplot(figure)
                st.write("**Code đã thực thi:**")
                st.code(action)
                to_display_string = response["output"] + "\n" + f"```python\n{action}\n```"
                st.session_state.history.append([query, to_display_string])  
            else:
                st.write(response["output"])
                st.session_state.history.append([query, response["output"]])
        else:
            st.write(response["output"])
            st.session_state.history.append([query, response["output"]])
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý truy vấn: {e}")
        logger.error(f"Lỗi xử lý truy vấn: {e}")    

def display_chat_history():
    """Hiển thị lịch sử trò chuyện."""
    st.markdown("Lịch sử chat:")
    for i, (q, r) in enumerate(st.session_state.history):
        st.markdown(f"**Truy vấn {i+1}:** {q}")
        st.markdown(f"**Phản hồi {i+1}:** {r}")
        st.markdown("---")

def get_table_names(engine):
    """Lấy danh sách các bảng trong cơ sở dữ liệu."""
    query = "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
    return pd.read_sql(query, engine)['table_name'].tolist()

def connect_to_database(db_connection_string):
    """Kết nối đến cơ sở dữ liệu PostgreSQL và trả về engine."""
    try:
        engine = create_engine(db_connection_string)
        return engine
    except SQLAlchemyError as e:
        st.error(f"Lỗi khi kết nối cơ sở dữ liệu: {e}")
        return None




def load_data_from_database(engine, table_name):
    
    try:
        # Tạo kết nối từ engine và thực hiện truy vấn SQL thủ công
        with engine.connect() as connection:
            result = connection.execute(f"SELECT * FROM {table_name}")
            # Chuyển đổi kết quả thành DataFrame
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        logger.info(f"Tải thành công {len(df)} dòng từ bảng '{table_name}'.")
        return df
    except SQLAlchemyError as e:
        st.error(f"Lỗi khi tải bảng '{table_name}': {e}")
        logger.error(f"Lỗi khi tải bảng '{table_name}': {e}")
        return pd.DataFrame()



def main():
    # Khởi tạo session_state cho df và history nếu chưa có
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if "history" not in st.session_state:
        st.session_state.history = []
    
    # Thiết lập giao diện Streamlit
    st.set_page_config(
        page_title="DA Tool",
        page_icon="📊",
        layout="centered"
    )
    st.header("Data Analyst Tool 📊")
    st.write("# Welcome to Data Analyst Tool #")
    
    # Tải mô hình ngôn ngữ
    llm = ChatOpenAI(model=MODEL_NAME)
    logger.info(f"### Tải thành công {MODEL_NAME} ! ###")

    st.sidebar.header("Nguồn dữ liệu")
    data_source = st.sidebar.radio("Chọn nguồn dữ liệu:", ("Cơ sở dữ liệu PostgreSQL", "Tải lên CSV"))
    
    if data_source == "Cơ sở dữ liệu PostgreSQL":
        # Lấy chuỗi kết nối cơ sở dữ liệu từ biến môi trường
        db_connection_string = os.getenv('DATABASE_URL')
        if not db_connection_string:
            st.sidebar.error("DATABASE_URL không được thiết lập trong biến môi trường.")
        else:
            # Kết nối tới cơ sở dữ liệu
            engine = connect_to_database(db_connection_string)
            if engine:
                st.sidebar.success("Kết nối đến cơ sở dữ liệu thành công.")
                table_names = get_table_names(engine)
                if table_names:
                    selected_table = st.sidebar.selectbox("Chọn Bảng để Tải Dữ Liệu:", table_names)
                    if st.sidebar.button("Tải Dữ Liệu Từ Bảng"):
                        df = load_data_from_database(engine, selected_table)
                        if not df.empty:
                            st.session_state.df = df
                            st.success(f"Đã tải dữ liệu từ bảng '{selected_table}' thành công.")
                            st.dataframe(st.session_state.df.head())
                            st.write(f"Kích thước DataFrame: {st.session_state.df.shape}")
                        else:
                            st.error(f"Không thể tải dữ liệu từ bảng '{selected_table}'.")
                else:
                    st.sidebar.error("Không tìm thấy bảng nào trong cơ sở dữ liệu.")
    elif data_source == "Tải lên CSV":
        upload_file = st.sidebar.file_uploader("Tải lên tệp CSV của bạn tại đây", type="csv")
        if upload_file is not None:
            try:
                df = pd.read_csv(upload_file)
                st.session_state.df = df
                st.success("Đã tải lên tệp CSV và dữ liệu được tải thành công.")
                st.dataframe(st.session_state.df.head())
                st.write(f"Kích thước DataFrame: {st.session_state.df.shape}")
            except Exception as e:
                st.sidebar.error(f"Lỗi khi đọc tệp CSV: {e}")
                logger.error(f"Lỗi tải lên CSV: {e}")
                st.session_state.df = pd.DataFrame()

    # Tạo data analyst agent để truy vấn dữ liệu
    da_agent = None
    if not st.session_state.df.empty:
        try:
            da_agent = create_pandas_dataframe_agent(
                llm=llm,
                df=st.session_state.df,
                agent_type="tool-calling",
                allow_dangerous_code=True,
                verbose=True,
                return_intermediate_steps=True
            )
            logger.info("### Tạo thành công data analyst agent ###")
        except Exception as e:
            st.error(f"Lỗi khi tạo tác nhân phân tích dữ liệu: {e}")
            logger.error(f"Lỗi khi tạo tác nhân phân tích dữ liệu: {e}")
    else:
        st.warning("Chưa tải dữ liệu. Vui lòng kết nối đến cơ sở dữ liệu hoặc tải file CSV lên.")

    # Nhập câu hỏi để truy vấn
    query = st.text_input("Nhập câu hỏi của bạn:")
    if st.button("Chạy truy vấn"):
        if da_agent is not None:
            if query.strip() == "":
                st.warning("Vui lòng nhập câu truy vấn hợp lệ.")
            else:
                with st.spinner("Đang xử lý ..."):
                    process_query(da_agent, query)
        else:
            st.error("Không thể thực hiện truy vấn. Tác nhân phân tích dữ liệu không khả dụng.")

    # Hiển thị lịch sử trò chuyện
    st.markdown("---")
    display_chat_history()

if __name__ == "__main__":
    main()
