from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.models.google import Gemini
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow import Workflow


class CacheWorkflow(Workflow):
    # Agen default memakai Gemini
    agent = Agent(model=Gemini(id="gemini-2.5-flash"))

    # Jika ingin pakai varian experimental:
    # agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))

    def run(self, message: str) -> Iterator[RunResponse]:
        logger.info(f"Checking cache for '{message}'")
        # Cek cache di session_state workflow
        if self.session_state.get(message):
            logger.info(f"Cache hit for '{message}'")
            yield RunResponse(run_id=self.run_id, content=self.session_state.get(message))
            return

        logger.info(f"Cache miss for '{message}'")
        # Jalankan agen dan stream respons
        yield from self.agent.run(message, stream=True)

        # Simpan hasil ke cache setelah ada respons
        self.session_state[message] = self.agent.run_response.content


if __name__ == "__main__":
    workflow = CacheWorkflow()
    # Eksekusi pertama: miss (panggil API)
    response: Iterator[RunResponse] = workflow.run(message="Tell me a joke.")
    pprint_run_response(response, markdown=True, show_time=True)
    # Eksekusi kedua: hit (ambil dari cache, instan)
    response = workflow.run(message="Tell me a joke.")
    pprint_run_response(response, markdown=True, show_time=True)
