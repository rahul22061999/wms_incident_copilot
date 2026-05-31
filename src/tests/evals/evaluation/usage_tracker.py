from typing import Any
from langchain_core.callbacks import AsyncCallbackHandler

COST_PER_1K: dict[str, tuple[float, float]] = {
    "gpt-5-nano":            (0.00005, 0.0004),
    "gpt-5-nano-2025-08-07": (0.00005, 0.0004),
    "gemini-2.5-flash-lite": (0.0001,  0.0004),
    "llama-3.1-8b-instant":  (0.00005, 0.00008),
    "gemma4:31b":            (0.0,     0.0),
    "gemma4:31b-cloud":      (0.0,     0.0),
}

class UsageTracker(AsyncCallbackHandler):
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.cost_by_model: dict[str, float] = {}

    def on_llm_end(self, response, **kwargs):
        input_tokens, output_tokens, model_name = 0, 0, ""

        if response.llm_output:
            usage = response.llm_output.get("token_usage") or response.llm_output.get("usage", {})
            model_name = response.llm_output.get("model_name", "")
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
        else:
            try:
                message = response.generations[0][0].message
                meta = getattr(message, "response_metadata", {}) or {}
                model_name = meta.get("model_name", "")
                usage = getattr(message, "usage_metadata", {}) or {}
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
            except (IndexError, AttributeError):
                pass

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        input_rate, output_rate = COST_PER_1K.get(model_name, (0.0, 0.0))
        cost = (input_tokens * input_rate + output_tokens * output_rate) / 1000
        self.total_cost += cost
        self.cost_by_model[model_name] = self.cost_by_model.get(model_name, 0.0) + cost
