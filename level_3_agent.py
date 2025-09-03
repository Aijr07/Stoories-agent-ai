from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.google import Gemini
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools

memory = Memory(
    model=Gemini(id="gemini-2.5-flash"),
    db=SqliteMemoryDb(table_name="user_memories", db_file="tmp/agent.db"),
    delete_memories=True,
    clear_memories=True,
)

agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[
    ReasoningTools(add_instructions=True),
    YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True),
    ],
    user_id="ava",
    instructions=[
    "Use tables to display data.",
    "Include sources in your response.",
    "Only include the report in your response. No other text.",
    ],
    memory=memory,
    enable_agentic_memory=True,
    markdown=True,
)

if __name__ == "__main__":
    # This will create a memory that "ava's" favorite stocks are NVIDIA and TSLA
    agent.print_response(
        "My favorite stocks are NVIDIA and TSLA",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )
    # This will use the memory to answer the question
    agent.print_response(
        "Can you compare my favorite stocks?",
        stream=True,
        show_full_reasoning=True,
        stream_intermediate_steps=True,
    )