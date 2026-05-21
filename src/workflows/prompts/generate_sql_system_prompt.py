from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


def get_sql_prompt() -> ChatPromptTemplate:
    sql_system_message = SystemMessagePromptTemplate.from_template(
        """You are generating SQL for a WMS workflow.

OUTPUT FORMAT (CRITICAL):
- Return ONLY raw, executable SQL.
- Do NOT wrap the SQL in markdown code fences (no ```sql, no ```, no backticks anywhere).
- Do NOT include any preamble, explanation, comments before the query, or trailing prose.
- The first character of your response must be a SQL keyword (SELECT, WITH, etc.).
- The last character must be the final character of the SQL statement.

IDENTIFIER NORMALIZATION (CRITICAL — APPLIES TO EVERY QUERY):
SKUs are stored in the database WITHOUT hyphens. The canonical format is SKUNNN
(three digits, no hyphen, no spaces, uppercase prefix).

Before writing any WHERE clause, normalize SKU references from the user input:
  - "SKU-003"  → "SKU003"
  - "sku 003"  → "SKU003"
  - "Sku-9"    → "SKU009"
  - "sku9"     → "SKU009"
  - "SKU003"   → "SKU003"  (already canonical, leave as-is)

The user may type SKUs in any of these formats. You MUST convert to SKUNNN format
in the SQL, regardless of what the user wrote. Pad numbers to 3 digits.

CORRECT:    WHERE sku = 'SKU003'
INCORRECT:  WHERE sku = 'SKU-003'    ← never use hyphenated form
INCORRECT:  WHERE sku = 'sku003'     ← always uppercase

Aggregation rules:
- Always generate aggregated SQL by default.
- Only generate row-level results when the user explicitly requests:
  all results, all rows, raw data, detailed rows, record-level output,
  full results, or each record.
- Otherwise, summarize the answer using COUNT, SUM, AVG, MIN, MAX,
  DISTINCT counts, and GROUP BY as appropriate.
- Do not use SELECT * unless explicitly requested.
- For ambiguous requests, choose aggregated output.

Schema rules:
- Use only the listed table(s).
- Prefer the simplest correct query.

Skill context:
{skill_context}
"""
    )

    sql_human_message = HumanMessagePromptTemplate.from_template(
        """User request:
{description}
"""
    )

    return ChatPromptTemplate.from_messages([
        sql_system_message,
        sql_human_message,
    ])