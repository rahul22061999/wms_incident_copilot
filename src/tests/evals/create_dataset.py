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
    ],
    outputs=[
        {"task": ["schedule"]},
        {"task": ["parallel"]},
        {"task": ["cancel_schedule"]},
        {"task": ["parallel"]},
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
    ],
    outputs=[
        {"expected_route": "schedule"},
        {"expected_route": "parallel"},
    ],
    dataset_id=graph_dataset.id,
)

print("Datasets and examples created successfully.")