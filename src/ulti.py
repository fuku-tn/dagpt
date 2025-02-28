import matplotlib.pyplot as plt
import pandas as pd 
import streamlit as st

def execute_plt_code(code: str, df: pd.DataFrame):
    try:
        # Định nghĩa biến cục bộ chứa DataFrame và plt
        local_variable = {"plt": plt, "df": df}
        
        # Compile và thực thi code với biến toàn cục và cục bộ đã xác định
        compile_code = compile(code, "<string>", "exec")
        exec(compile_code, globals(), local_variable)

        # Trả về biểu đồ hiện tại
        return plt.gcf()
    except Exception as e:
        st.error(f"Lỗi khi thực thi mã plt: {e}")
        return None

    
