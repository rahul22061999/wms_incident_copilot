from langgraph.cache.memory import InMemoryCache
from langgraph.graph import StateGraph
from domain.states.sql_subgraph_state.sql_graph_state import SQLGraphState
from src.agents.nodes.load_skills_node import sql_load_skills_node
from src.agents.nodes.generate_sql_node import generate_sql_node
from src.agents.nodes.check_sql_node import check_sql_node
from src.agents.nodes.run_sql_node import run_sql_node
from src.agents.nodes.sql_result_node import sql_result_node
from dotenv import load_dotenv
load_dotenv()


# def build_subgraph():
#     sql_subgraph = StateGraph(SQLGraphState)
#
#     sql_subgraph.add_node("load_skills_node", load_skills_node)
#     sql_subgraph.add_node("generate_sql_node", generate_sql_node)
#     sql_subgraph.add_node("check_sql_node", check_sql_node)
#     sql_subgraph.add_node("run_sql_node", run_sql_node)
#     sql_subgraph.add_node("sql_result_node", sql_result_node)
#
#     sql_subgraph.add_edge(START, "load_skills_node")
#     sql_subgraph.add_edge("sql_result_node", END)
#
#     return sql_subgraph
#
# sql_graph = build_subgraph().compile(cache=InMemoryCache())



def build_sql_subgraph():

    sql_graph_state = StateGraph(SQLGraphState)

    sql_graph_state.add_sequence([
        sql_load_skills_node,
        generate_sql_node,
        check_sql_node,
        run_sql_node,
        sql_result_node,
    ])

    return sql_graph_state

sql_graph = build_sql_subgraph().compile(cache=InMemoryCache())

