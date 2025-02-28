from langchain_openai import ChatOpenAI

def load_llm(model_name,openai_api_key):
    # Load Large Language Model
    if model_name in ["gpt-3.5-turbo", "gpt-4","gpt-4o-mini"]:
        return ChatOpenAI(
            model=model_name,
            temperature=0.0,
            openai_api_key = openai_api_key,
            max_tokens=1000,
        )
    elif model_name == "gemini-pro":
        
        pass
    else:
        raise ValueError(
            "Unknown model. Please choose from ['gpt-3.5-turbo', 'gpt-4','gpt-4o-mini']"
        )
