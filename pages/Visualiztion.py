import streamlit as st
from pygwalker.api.streamlit import StreamlitRenderer


def main():
    st.set_page_config(
        page_title="Visualization",
        page_icon="VST",
        layout="wide"

    )
    if st.session_state.get('df') is not None:
        pyg_app = StreamlitRenderer(st.session_state.df)
        pyg_app.explorer()
    else:
        st.info("Hãy update data để có thể Visual")


    pass
if __name__ == "__main__":
    main()
    