from typing import NotRequired, Callable, Any
from typing import TypedDict
from langchain.agents.middleware import AgentState, AgentMiddleware, ModelRequest, ModelResponse, ExtendedModelResponse
from langchain_community.tools.sql_database.tool import (
    QuerySQLDatabaseTool,
    QuerySQLCheckerTool,
    ListSQLDatabaseTool, InfoSQLDatabaseTool,

)
from langchain.tools import tool
from langchain_core.messages import ToolMessage, SystemMessage
from langgraph.prebuilt import ToolRuntime
from langgraph.runtime import Runtime
from langgraph.types import Command
from data.state import WMState
from models.model_loader import get_google_llm, get_openai_fast_llm, get_groq_llm
from utils.sql_tools import WmsSqlTool

from dotenv import load_dotenv
load_dotenv()

class SQLAgentState(AgentState):
    list_tables: NotRequired[bool]
    schema_loaded: NotRequired[bool]
    query_checked: NotRequired[bool]
    table_context: NotRequired[bool]
    schema_context: NotRequired[bool]


sql_tools = WmsSqlTool(query_check_llm=get_groq_llm()).get_sql_tools()

_list_tables = next(t for t in sql_tools if isinstance(t, ListSQLDatabaseTool))
_list_info = next(t for t in sql_tools if isinstance(t, InfoSQLDatabaseTool))
_query_check = next(t for t in sql_tools if isinstance(t, QuerySQLCheckerTool))
_run_sql = next(t for t in sql_tools if isinstance(t, QuerySQLDatabaseTool))



@tool
def list_tables(runtime: ToolRuntime) -> Command:
    """List all tables in the database, CALL THIS FIRST"""

    tables = _list_tables.invoke("")

    return Command(
        update={
            "messages":[
                ToolMessage(
                    content=f"Available tables: {tables}",
                    tool_call_id= runtime.tool_call_id
                )
            ],
            "state":{
                "list_tables": True,
                "table_context": tables
            }
        }
    )

@tool
def get_schema(table_names: str, runtime: ToolRuntime) -> Command:
    """Get schema from the database"""

    schemas = _list_info.invoke({"table_names": table_names})

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=schemas,
                    tool_call_id= runtime.tool_call_id
                )
            ],
            "state": {
                "schema_loaded": True,
                "schema_context": schemas
            }
        }
    )

@tool
def check_query(query:str, runtime: ToolRuntime) -> Command:
    """Check if a query is valid
    Args: query (str)
    """

    result = _query_check.invoke({"query": query})

    return Command(
        update= {
            "messages": [
                ToolMessage(content=result, tool_call_id= runtime.tool_call_id),
            ],
            "state": {
                "query_checked": True,
            }
        }
    )

@tool
def run_query(query:str, runtime: ToolRuntime) -> Command:
    """Run a query on the database"""

    sql_runner = _run_sql.invoke({"query": query})

    return Command(
        update= {
            "messages": [
                ToolMessage(
                    content=sql_runner,
                    tool_call_id= runtime.tool_call_id
                )
            ],
            "state": {
                "query_checked": False,
            }
        }
    )



SKILLS = [
    {
        "name": "inventory",
        "description": "Schema and query guidance for on-hand inventory, case-level stock, SKU/location lookups, and inventory totals.",
        "content": """
# Inventory Lookup

## Tables

### wms1.inventory
- id (PRIMARY KEY)
- case_number (UNIQUE)
- sku
- unit_qty
- location
- wrkref
- dtl_num
- ins_dt

## Use Cases
- How much inventory do we have for a SKU?
- Where is a SKU stored?
- Which cases contain a SKU?
- What inventory is tied to a work reference or detail number?

## Business Rules
- unit_qty is the quantity stored in a case-level inventory record.
- Total on-hand inventory for a SKU = SUM(unit_qty) from wms1.inventory.
- Inventory can be grouped by sku, location, case_number, wrkref, or dtl_num.
- case_number is unique per inventory record.

## Example Queries

-- Total inventory for a SKU
SELECT
    sku,
    SUM(unit_qty) AS total_inventory
FROM wms1.inventory
WHERE sku = 'SKU004'
GROUP BY sku;

-- Inventory by location for a SKU
SELECT
    sku,
    location,
    SUM(unit_qty) AS total_units
FROM wms1.inventory
WHERE sku = 'SKU004'
GROUP BY sku, location
ORDER BY total_units DESC;

-- Case-level inventory for a SKU
SELECT
    case_number,
    sku,
    unit_qty,
    location,
    wrkref,
    dtl_num
FROM wms1.inventory
WHERE sku = 'SKU004'
ORDER BY ins_dt DESC;
""",
    },
    {
        "name": "outbound",
        "description": "Schema and query guidance for outbound pick work, order allocation, pending picks, and picked quantities.",
        "content": """
# Outbound Picking

## Tables

### wms1.pckwrk
- id (PRIMARY KEY)
- wrkref
- location
- sku
- dtl_num
- quantity
- pck_qty
- app_qty
- carton_number
- pck_dt
- status
- ins_dt
- order_number

## Use Cases
- What pick work exists for a SKU?
- Which orders have pending pick work?
- How much quantity is requested vs picked?
- Which work references or detail numbers are tied to a SKU?

## Business Rules
- quantity is the requested work quantity on the pick record.
- pck_qty is the picked quantity recorded on the pick work row.
- status indicates the pick work state.
- Pending outbound work can be checked with status = 'PENDING'.
- order_number, wrkref, and dtl_num are useful operational identifiers.

## Example Queries

-- Pending outbound work for a SKU
SELECT
    order_number,
    wrkref,
    dtl_num,
    sku,
    location,
    quantity,
    pck_qty,
    status
FROM wms1.pckwrk
WHERE sku = 'SKU004'
  AND status = 'PENDING'
ORDER BY ins_dt DESC;

-- Total pending requested quantity for a SKU
SELECT
    sku,
    SUM(quantity) AS total_requested_qty
FROM wms1.pckwrk
WHERE sku = 'SKU004'
  AND status = 'PENDING'
GROUP BY sku;

-- Requested vs picked quantity for a SKU
SELECT
    sku,
    SUM(quantity) AS total_requested_qty,
    SUM(COALESCE(pck_qty, 0)) AS total_picked_qty
FROM wms1.pckwrk
WHERE sku = 'SKU004'
GROUP BY sku;
""",
    },
    {
        "name": "receiving",
        "description": "Schema and query guidance for receipts, expected vs received quantities, receiving locations, and inbound status tracking.",
        "content": """
# Inbound Receiving

## Tables

### wms1.rcv_inventory
- rcv_id (PRIMARY KEY)
- rcv_inv
- warehouse_id
- sku
- supplier_number
- expected_qty
- received_qty
- received_date
- receiving_loc
- status
- created_at

## Use Cases
- What receipts exist for a SKU?
- How much was expected vs received?
- Which receiving location was used?
- Which receipts are pending, partial, received, or cancelled?

## Business Rules
- expected_qty is the planned receipt quantity.
- received_qty is the actual received quantity recorded.
- status is one of: PENDING, PARTIAL, RECEIVED, CANCELLED.
- Quantity variance can be checked as expected_qty - received_qty.

## Example Queries

-- Receipt history for a SKU
SELECT
    rcv_inv,
    warehouse_id,
    sku,
    supplier_number,
    expected_qty,
    received_qty,
    receiving_loc,
    status,
    received_date
FROM wms1.rcv_inventory
WHERE sku = 'SKU004'
ORDER BY created_at DESC;

-- Open inbound receipts
SELECT
    rcv_inv,
    sku,
    expected_qty,
    received_qty,
    status
FROM wms1.rcv_inventory
WHERE status IN ('PENDING', 'PARTIAL')
ORDER BY created_at DESC;

-- Receipt variance for a SKU
SELECT
    rcv_inv,
    sku,
    expected_qty,
    received_qty,
    (expected_qty - received_qty) AS variance_qty,
    status
FROM wms1.rcv_inventory
WHERE sku = 'SKU004'
ORDER BY created_at DESC;
""",
    },
]


@tool
def load_skills(skill_name: str, runtime: ToolRuntime) -> Command:
    """Load skills into database
    Args:
        skill_name: One of: inbound, outbound, inventory
        runtime: ToolRuntime[]
    """

    for skill in SKILLS:
        if skill[skill_name] == skill_name.lower().strip():
            content = (
                f"{skill_name.capitalize()} Skills "
                f"Description: {skill['description']}"
            )

            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=content,
                            tool_call_id= runtime.tool_call_id
                        )
                    ]
                }
            )
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"Skills not found",
                    tool_call_id= runtime.tool_call_id
                )
            ]
        }
    )


class SQLSkillsMiddleware(AgentMiddleware[SQLAgentState]):
    """Injects skill list + enforces tool ordering via state."""
    state_schema = SQLAgentState
    tools = [check_query, run_query]

    def __init__(self):
        skill_list = "\n".join(
            f"skills {skill} : description {skill.get("description")}"
            for skill in SKILLS
        )

        self.skill_list = skill_list


    def before_agent(
            self,
            state: WMState,
            runtime: Runtime,

    ) -> dict[str, Any] | None:
        # query = state['messages'][0]['content']

        # direct Python call, not agent tool call
        tables = _list_tables.invoke("")

        return {
            "list_tables": True,
            "table_context": tables,
        }

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:

        tables = request.state.get("table_context", "")

        addendum = (
            f"\n\n## Available Tables\n{tables}\n\n"
            f"## WMS Domains\n{self.skill_list}\n\n"
            "You already have the schema above. Do NOT ask the user for table or column names.\n"
            "SKU codes are stored in UPPERCASE. Always use UPPER() on user-provided SKU values.\n"
            "Write and run the SQL query directly.\n"
        )

        new_content = list(request.system_message.content_blocks) + [
            {"type":"text", "text": addendum}
        ]

        modified_request = request.override(
            system_message=SystemMessage(content=new_content),
        )

        return handler(modified_request)

