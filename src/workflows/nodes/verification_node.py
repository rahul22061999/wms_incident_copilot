from domain.states.supervisor.diagnose_graph_state import WMState
from domain.states.supervisor.supervisor_evidence_states import VerificationResult
from models.model_loader import get_google_llm, get_openai_fast_llm
from prompts.verification_result_prompt import get_verification_node_prompt


def verification_node(state: WMState):
    evidence = state.evidence_records or []
    evidence_str = "\n".join(f"- {e.model_dump_json()}" for e in evidence) or "(none)"

    llm = (
        get_google_llm()
        .with_structured_output(VerificationResult)
        .with_fallbacks([
            get_openai_fast_llm().with_structured_output(VerificationResult)
        ])
    )

    chain = get_verification_node_prompt() | llm

    result = chain.invoke({
        "question": state.description,
        "result": state.result,
        "evidence": evidence_str,
        "evidence_count": len(evidence)
    })

    return {"verification_result": result}