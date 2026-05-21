"""
Seeds LangSmith evaluation datasets.

Run this script once (or after adding new examples) to create or update the
named datasets in your LangSmith workspace. get_or_create_dataset is idempotent
— running the script twice will not duplicate the dataset itself, but
create_examples will add duplicate rows if called again on an existing dataset.
Clear the dataset in the LangSmith UI before re-seeding if you need a clean slate.
"""

from langsmith import Client
from dotenv import load_dotenv
from langsmith.utils import LangSmithNotFoundError

load_dotenv()

client = Client()


def get_or_create_dataset(dataset_name: str, description: str):
    try:
        return client.read_dataset(dataset_name=dataset_name)
    except LangSmithNotFoundError:
        return client.create_dataset(
            dataset_name=dataset_name,
            description=description,
        )


# -----------------------------
# Router dataset
# -----------------------------

router_dataset = get_or_create_dataset(
    "wms-router-evals",
    "Router classification tests for WMS agent graph",
)

client.create_examples(
    inputs=[
        {"description": "Monitor SKU008 inventory every 30 seconds"},
        {"description": "What is the inbound status for PO-1042?"},
        {"description": "Stop monitoring INC0003"},
        {"description": "Show outbound shipments and check relevant SOPs"},
        {"description": "Why are orders not releasing from wave planning?"},
        {"description": "Check inbound receipts and relevant SOP for dock overload"},
        {"description": "Cancel the monitoring job for INC0003"},
        {"description": "Monitor pick failures for INC0005 every 60 seconds"},
        {"description": "Show me inventory levels AND check putaway SOP"},
        {"description": "Based on the inventory data, why is replenishment failing?"},
    ],
    outputs=[
        {"task": ["schedule"]},
        {"task": ["parallel"]},
        {"task": ["cancel_schedule"]},
        {"task": ["parallel"]},
        {"task": ["sequential"]},
        {"task": ["parallel"]},
        {"task": ["cancel_schedule"]},
        {"task": ["schedule"]},
        {"task": ["parallel"]},
        {"task": ["sequential"]},
    ],
    dataset_id=router_dataset.id,
)


# -----------------------------
# Graph dataset
# -----------------------------

graph_dataset = get_or_create_dataset(
    "wms-graph-evals",
    "Full graph end-to-end tests",
)

client.create_examples(
    inputs=[
        {
            "ticket_number": "INC0001",
            "description": "Monitor SKU008 every 30s",
            "user_id": "eval-user",
            "session_id": "eval-sess-1",
        },
        {
            "ticket_number": "INC0002",
            "description": "What is inbound status for PO-1042?",
            "user_id": "eval-user",
            "session_id": "eval-sess-2",
        },
        {
            "ticket_number": "INC0003",
            "description": "Why are orders aging and not releasing?",
            "user_id": "eval-user",
            "session_id": "eval-sess-3",
        },
        {
            "ticket_number": "INC0004",
            "description": "Stop monitoring INC0001",
            "user_id": "eval-user",
            "session_id": "eval-sess-4",
        },
    ],
    outputs=[
        {"expected_route": "schedule"},
        {"expected_route": "parallel"},
        {"expected_route": "sequential"},
        {"expected_route": "cancel_schedule"},
    ],
    dataset_id=graph_dataset.id,
)


# -----------------------------
# Parallel node dataset
# -----------------------------

parallel_dataset = get_or_create_dataset(
    "wms-parallel-node-evals",
    "Parallel execution node decomposition tests",
)

client.create_examples(
    inputs=[
        {"description": "What is the inbound receipt count and check putaway SOP?"},
        {"description": "Show inventory levels for SKU008"},
        {"description": "Get pick failures AND outbound shipment SOP"},
        {"description": "Why is replenishment failing based on inventory data?"},
    ],
    outputs=[
        {"expected_subtask_count": 2, "expected_tools": ["sql_lookup_tool", "sop_lookup"], "is_single_intent": False},
        {"expected_subtask_count": 1, "expected_tools": ["sql_lookup_tool"], "is_single_intent": True},
        {"expected_subtask_count": 2, "expected_tools": ["sql_lookup_tool", "sop_lookup"], "is_single_intent": False},
        {"expected_subtask_count": 1, "expected_tools": ["sql_lookup_tool"], "is_single_intent": True},
    ],
    dataset_id=parallel_dataset.id,
)


# -----------------------------
# Synthesizer fidelity dataset
# -----------------------------

fidelity_dataset = get_or_create_dataset(
    "wms-synthesizer-fidelity-evals",
    "Synthesizer hallucination and citation grounding tests",
)

client.create_examples(
    inputs=[
        {
            "parallel_results": [
                {"source": "sql_lookup_tool", "query": "pick failures", "status": "success",
                 "result": "SKU008 had 42 pick failures in the last 24h. Location WH-A-A13-BIN7 is flagged as blocked."},
                {"source": "sop_lookup", "query": "pick failure SOP", "status": "success",
                 "result": "SOP-PCK-003: When pick failures exceed 10 per shift, escalate to warehouse supervisor."},
            ],
            "sequential_results": [],
        },
        {
            "parallel_results": [],
            "sequential_results": [
                {"source": "sequential_agent", "query": "dock overload", "status": "success",
                 "result": "DOCK-A1 has 3 pending appointments and 0 available slots. DOCK-B2 has capacity."},
            ],
        },
    ],
    outputs=[
        {"description": "pick failure with SOP reference"},
        {"description": "dock overload with capacity data"},
    ],
    dataset_id=fidelity_dataset.id,
)

print("Datasets and examples created successfully.")
