from runtime.session_store import SessionStore
import json


class WMSSessionRuntime:
    def __init__(self, graph):
        self.graph = graph
        self.store = SessionStore()


    async def run(self, session_id: str, ticket_number:str, description:str):
        ## load the old session messages

        try:
            saved_history = self.store.load(session_id)
        except (json.JSONDecodeError, Exception):
            return None

        result = await self.graph.ainvoke({
            "ticket_number": ticket_number,
            "description": description,
            "session_id": session_id,
        },
        config={"configurable": {"thread_id": session_id}})

        prev_message = saved_history.get("message_history", []) if saved_history else []

        new_messages = [
            {
                "type": type(msg).__name__,
                "content": msg.content if hasattr(msg, "content") else str(msg),
                "name": getattr(msg, "name", None)
            }

            for msg in result.get("messages", [])
        ]

        result["message_history"] = prev_message + new_messages
        result["run_count"] = (saved_history.get("run_count", 0) if saved_history else 0) + 1
        result["final_response"] = result["messages"][-1].content if result.get("messages") else ""
        self.store.save(session_id, result)
        print(f"Saved: {self.store._path(session_id)}")

        return result




