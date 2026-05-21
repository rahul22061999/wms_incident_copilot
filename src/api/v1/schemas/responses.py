from pydantic import BaseModel, ConfigDict

from domain.states.synthesizer_node_state import SynthesizerNodeReturnState


class TicketDiagnosisResponse(BaseModel):
    ticket_number: str
    session_id: str
    user_id: str
    result: SynthesizerNodeReturnState

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticket_number": "WMS-1234",
                "session_id": "sess-abc123",
                "user_id": "rahul",
                "result": {
                    "summarized_issue": "Low inventory on bin A-12 caused pick failure.",
                    "confidence": 0.87,
                    "citations": [{"source_type": "sql", "reference": "inventory.qty_on_hand"}],
                },
            }
        }
    )
