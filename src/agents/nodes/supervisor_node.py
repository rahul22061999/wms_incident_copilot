from prompts.generate_supervisor_prompt import supervisor_prompt
from config import settings
from domain.states.supervisor.diagnose_graph_state import WMState
from domain.states.supervisor.supervisor_subagent_task_state import SupervisorToSubAgentDeligationItem
from models.model_loader import get_google_llm, get_openai_fast_llm
from dotenv import load_dotenv
from utils.supervisor.call_llm import invoke_llm
from utils.supervisor.command_builder import build_command
from utils.supervisor.supervisor_fallback import force_final_answer
from utils.supervisor.supervisor_previous_context import get_previous_task_findings

load_dotenv()



class SupervisorNode:
    def __init__(self):

        ##choose llm based on whats available
        self.llm = (
            get_google_llm()
            .with_structured_output(SupervisorToSubAgentDeligationItem)
            .with_fallbacks([
                get_openai_fast_llm()
                .with_structured_output(SupervisorToSubAgentDeligationItem)
            ])
        )

        ##set max loops for and llm to run over an issue
        self.max_loops = settings.SUPERVISOR_MAX_LOOP
        ##system prompt and chat prompt built in
        self.prompt = supervisor_prompt

    async def __call__(self, state: WMState):
        """Entry point called by LangGraph."""

        current_loop = state.loop_count
        task_description = state.description

        if current_loop >= settings.SUPERVISOR_MAX_LOOP:
            return force_final_answer(state, current_loop, self.max_loops)

         ## {"task_id": Subagentresponse}
        previous_task_findings = get_previous_task_findings(state)

        ##inject messages from the task to the prompt
        decision = await invoke_llm(
            task_description=task_description,
            previous_findings=previous_task_findings,
            prompt=self.prompt,
            llm=self.llm)

        #if llm is done then return previous findings
        if not decision or decision is None:
            return force_final_answer(state=state, current_loop=current_loop, max_loops=self.max_loops)

        return build_command(decision, current_loop)




