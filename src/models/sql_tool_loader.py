from models.model_loader import get_groq_llm
from utils.sql_tools import WmsSqlTool

_sql_tools = None
def get_sql_tools_loader():
    global _sql_tools
    if _sql_tools is None:
        _sql_tools = WmsSqlTool(query_check_llm=get_groq_llm()).get_sql_tools()
    return _sql_tools