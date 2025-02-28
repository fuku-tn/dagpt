import streamlit as st
import pandas as pd
from hdfs import InsecureClient
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
import os
import openai
from src.modeling.logger.base import BaseLogger
from src.ulti import execute_plt_code

# Thiết lập cấu hình trang phải là lệnh đầu tiên
st.set_page_config(
    page_title="DA Tool",
    page_icon="📊",
    layout="centered"
)

# Tải biến môi trường
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
logger = BaseLogger()
logger.info("### Tải thành công GPT ###")
MODEL_NAME = "gpt-4o-mini"

# Địa chỉ IP của máy ảo Ubuntu và cổng dịch vụ HDFS
HDFS_HOST = os.getenv('HDFS_HOST', '192.168.0.104')  # Địa chỉ IP của máy ảo Ubuntu
HDFS_PORT = os.getenv('HDFS_PORT', '50070')  # Cổng WebHDFS
HDFS_USER = os.getenv('HDFS_USER', 'hadoop')
HDFS_URL = f'http://{HDFS_HOST}:{HDFS_PORT}'

# Khởi tạo kết nối HDFS
try:
    hdfs_client = InsecureClient(HDFS_URL, user=HDFS_USER)
    st.sidebar.success("Kết nối đến HDFS thành công!")
except Exception as e:
    st.sidebar.error(f"Không thể kết nối đến HDFS: {e}")

# Hàm để tải dữ liệu từ HDFS
@st.cache_data
def load_data_from_hdfs(file_path):
    try:
        st.write(f"Đang tải dữ liệu từ: {file_path}")  # Thông báo trạng thái
        with hdfs_client.read(file_path, encoding='utf-8') as reader:
            df = pd.read_csv(reader)
        logger.info(f"Tải thành công {len(df)} dòng từ '{file_path}'.")
        return df
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu từ HDFS: {e}")
        logger.error(f"Lỗi khi tải dữ liệu từ HDFS: {e}")
        return pd.DataFrame()

# Hàm hiển thị các mục trong HDFS và chỉ liệt kê thư mục
@st.cache_data
def list_hdfs_directory(path):
    try:
        items = hdfs_client.list(path, status=True)
        if not items:
            st.warning(f"Không tìm thấy mục nào trong đường dẫn '{path}'.")
        directories = [item[0] for item in items if item[1]['type'] == 'DIRECTORY']
        files = [item[0] for item in items if item[1]['type'] == 'FILE']
        return directories, files
    except Exception as e:
        st.error(f"Lỗi khi liệt kê đường dẫn '{path}': {e}")
        return [], []

# Hàm xử lý truy vấn từ người dùng
def process_query(da_agent, query):
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

# Hiển thị lịch sử trò chuyện
def display_chat_history():
    st.markdown("Lịch sử chat:")
    if not st.session_state.history:
        st.write("Chưa có lịch sử trò chuyện.")
    for i, (q, r) in enumerate(st.session_state.history):
        st.markdown(f"**Truy vấn {i+1}:** {q}")
        st.markdown(f"**Phản hồi {i+1}:** {r}")
        st.markdown("---")

def main():
    # Khởi tạo session_state cho df và history nếu chưa có
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame()
    if "history" not in st.session_state:
        st.session_state.history = []

    st.header("Data Analyst Tool 📊")
    st.write("# Welcome to Data Analyst Tool #")

    # Tải mô hình ngôn ngữ
    llm = ChatOpenAI(model=MODEL_NAME)
    logger.info(f"### Tải thành công {MODEL_NAME} ! ###")

    st.sidebar.header("Nguồn dữ liệu")
    data_source = st.sidebar.radio("Chọn nguồn dữ liệu:", ("Data Lake trên HDFS",))

    if data_source == "Data Lake trên HDFS":
        base_path = '/datalake'
        directories, _ = list_hdfs_directory(base_path)
        if directories:
            current_level = st.sidebar.selectbox("Chọn thư mục:", [base_path] + directories)
            st.write(f"Đã chọn thư mục: {current_level}")  # Thông báo trạng thái

            if current_level != base_path:
                sub_directories, files = list_hdfs_directory(f'{base_path}/{current_level}')
                sub_level = st.sidebar.selectbox("Chọn thư mục con:", [current_level] + sub_directories)
                
                if sub_level != current_level:
                    sub_sub_directories, sub_files = list_hdfs_directory(f'{base_path}/{current_level}/{sub_level}')
                    if sub_sub_directories:
                        sub_sub_level = st.sidebar.selectbox("Chọn thư mục con tiếp theo:", [sub_level] + sub_sub_directories)
                        if sub_sub_level != sub_level:
                            _, final_files = list_hdfs_directory(f'{base_path}/{current_level}/{sub_level}/{sub_sub_level}')
                            file_path = st.sidebar.selectbox("Chọn tệp từ Data Lake:", final_files)
                    else:
                        file_path = st.sidebar.selectbox("Chọn tệp từ Data Lake:", sub_files)
                else:
                    file_path = st.sidebar.selectbox("Chọn tệp từ Data Lake:", files)

                if file_path:
                    st.write(f"Đã chọn tệp: {file_path}")  # Thông báo trạng thái
                    if st.sidebar.button("Tải Dữ Liệu"):
                        if sub_level != current_level:
                            full_path = f'{base_path}/{current_level}/{sub_level}/{file_path}'
                        else:
                            full_path = f'{base_path}/{current_level}/{file_path}'
                        st.write(f"Đang tải tệp từ: {full_path}")  # Thông báo trạng thái
                        df = load_data_from_hdfs(full_path)
                        if not df.empty:
                            st.session_state.df = df
                            st.success(f"Đã tải dữ liệu từ '{file_path}' thành công.")
                            st.dataframe(st.session_state.df.head())
                            st.write(f"Kích thước DataFrame: {st.session_state.df.shape}")
                        else:
                            st.error(f"Không thể tải dữ liệu từ '{file_path}'.")
        else:
            st.warning("Không tìm thấy thư mục nào để hiển thị.")

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
        st.warning("Chưa tải dữ liệu. Vui lòng kết nối đến Data Lake và tải dữ liệu.")

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

