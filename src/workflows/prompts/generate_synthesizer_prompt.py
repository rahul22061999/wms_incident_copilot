from langchain_core.prompts import ChatPromptTemplate


def build_synthesizer_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", """\
                You are a synthesizer agent. Your job is to merge information from the source content into one faithful diagnosis.
                
                Rules:
                - Use only facts present in the source content.
                - Preserve every concrete identifier and number exactly as written.
                - Do not paraphrase identifiers such as SKU, ASN, order ID, ticket number, table.column, node name, or job_id.
                - If the source content is insufficient, say that in summarized_issue.
                - If there is conflicting information, mention the conflict in summarized_issue.
                - confidence must be a number between 0.0 and 1.0.
                - citations must contain only evidence references that appear in the input content.
                - Each citation.source_type must be one of: sql, sop, node, job, other.
                - Each citation.reference must be a non-empty exact reference from the input.
                
                Return ONLY valid JSON matching this exact shape:
                {{
                  "summarized_issue": "string",
                  "confidence": 0.0,
                  "citations": [
                    {{
                      "source_type": "sql",
                      "reference": "string"
                    }}
                  ]
                }}
                
                Do not return markdown.
                Do not use code fences.
                Do not include text before or after the JSON.
                """
        ),
        ("human", "Synthesize the following content:\n\n{content}"),
    ])


synthesizer_prompt = build_synthesizer_prompt()