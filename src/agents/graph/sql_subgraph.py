from langgraph.cache.memory import InMemoryCache
from langgraph.graph import StateGraph,START
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from src.agents.nodes.sql_load_skills_node import sql_load_skills_node
from src.agents.nodes.sql_generate_query_node import sql_generate_query_node
from src.agents.nodes.check_sql_node import check_sql_node
from src.agents.nodes.sql_run_sql_node import sql_run_sql_node
from dotenv import load_dotenv
load_dotenv()




def build_sql_subgraph():

    sql_graph_state = StateGraph(SQLGraphState)

    sql_graph_state.add_sequence([
        sql_load_skills_node,
        sql_generate_query_node,
        check_sql_node,
        sql_run_sql_node
    ])

    sql_graph_state.add_edge(START, "sql_load_skills_node")

    return sql_graph_state

sql_graph = build_sql_subgraph().compile(cache=InMemoryCache())

