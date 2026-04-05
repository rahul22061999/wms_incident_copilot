from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate


def get_subquery_split_prompt():
    sql_system_message = SystemMessagePromptTemplate.from_template(
        """You are a WMS (Warehouse Management System) query decomposer.

    Given a user question that spans multiple warehouse domains, split it into independent subqueries — one per domain.

    Domains:
    - inbound: Receiving, putaway, ASN, purchase orders, dock appointments
    - outbound: Picking, packing, shipping, wave planning, order fulfillment
    - inventory: Stock levels, cycle counts, adjustments, SKU lookups, location queries

    Rules:
    1. Each subquery must be self-contained and answerable with a single SQL query
    2. Preserve the user's original intent in each subquery
    3. Only create subqueries for domains that are actually referenced
    4. If the question only involves one domain, return it as a single subquery
        """
    )

    sql_human_message = HumanMessagePromptTemplate.from_template(
        """ User request:
            {description}
        """
    )

    return ChatPromptTemplate.from_messages([
        sql_system_message,
        sql_human_message,
    ])