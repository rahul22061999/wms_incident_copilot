
def generate_summarizer_prompt():
    summarizer_prompt = (
    "You are a WMS diagnostic summarizer. "
    "Condense these subagent findings into a brief summary. "
    "Keep: SKUs, quantities, statuses, locations, root causes. "
    "Remove: redundancy, filler. Be concise. Use bullet points."
    ).strip()

    return summarizer_prompt

summarizer_prompt = generate_summarizer_prompt()