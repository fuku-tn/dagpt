import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
import os
from dotenv import load_dotenv
from database import stream_data_from_table
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini"

def process_data_and_analyze(engine, schema, tables, chunk_size=10000, query=None):
    df = pd.DataFrame()
    for table in tables:
        for chunk in stream_data_from_table(engine, schema, table, chunk_size):
            df = pd.concat([df, chunk], ignore_index=True)
    
    if query and not df.empty:
        llm = ChatOpenAI(model=MODEL_NAME, openai_api_key=openai_api_key)
        da_agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            agent_type="tool-calling",
            allow_dangerous_code=True,
            verbose=True,
            return_intermediate_steps=True
        )
        response = da_agent(query)
        return {"data": df.to_dict(), "analysis": response["output"]}
    return {"data": df.to_dict(), "analysis": None}