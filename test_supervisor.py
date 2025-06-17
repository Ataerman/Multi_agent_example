from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List, Union
from config import openai_api_key
# 1. LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0,openai_api_key=openai_api_key)

# 2. State tipi
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# 3. Tool'lar (sadece math ve research için)
@tool
def add_numbers(a: float, b: float) -> float:
    """Toplama işlemi yapar"""
    return a + b

@tool
def search_web(query: str) -> str:
    """Web araması simülasyonu yapar"""
    return f"Fake result for: {query}"

# 4. Math ve Research Agent'ları (ReAct agent)
math_agent_node = create_react_agent(
    model=llm,
    tools=[add_numbers],
    messages_modifier="You are a math expert. Use your tools to solve mathematical problems step by step. Always show your calculations clearly."
)

research_agent_node = create_react_agent(
    model=llm,
    tools=[search_web],
    messages_modifier="You are a research expert. Use your tools to search for information and provide comprehensive, well-researched answers. Always cite your sources when possible."
)

# 5. Default Agent (sadece LLM ile yazılmış, tools yok)
def default_agent(state: AgentState) -> AgentState:
    """Gündelik, casual mesajlara sadece LLM ile yanıt verir"""
    # Özel prompt ile sistem mesajı ekliyoruz
    system_prompt = SystemMessage(content="You are a friendly and helpful assistant. Respond to casual conversations, greetings, and general questions in a warm and engaging manner.")
    messages_with_prompt = [system_prompt] + state["messages"]
    response = llm.invoke(messages_with_prompt)
    return {"messages": state["messages"] + [response]}

# 6. Supervisor Agent
def supervisor_agent(state: AgentState) -> AgentState:
    decision_prompt = [
        HumanMessage(content="""
You are a supervisor agent. Decide which expert should handle the user message.
- If it's a math question, respond only with: math
- If it's an information/research query, respond only with: research
- For anything casual (greetings, emotions, undefined), respond only with: casual
Only say: math, research, or casual
""")
    ]
    decision = llm.invoke(decision_prompt)
    return {"messages": state["messages"] + [decision]}

# 7. Yönlendirme
def route(state: AgentState) -> str:
    last_message = state["messages"][-1].content.lower()
    if "math" in last_message:
        return "math_agent"
    elif "research" in last_message:
        return "research_agent"
    elif "casual" in last_message:
        return "default_agent"
    else:
        return "default_agent"

# 8. Graph kur
graph = StateGraph(AgentState)

graph.add_node("supervisor", supervisor_agent)
graph.add_node("math_agent", math_agent_node)
graph.add_node("research_agent", research_agent_node)
graph.add_node("default_agent", default_agent)  

graph.add_edge(START, "supervisor")

graph.add_conditional_edges(
    "supervisor",
    route,
    {
        "math_agent": "math_agent",
        "research_agent": "research_agent",
        "default_agent": "default_agent"
    }
)

graph.add_edge("math_agent", END)
graph.add_edge("research_agent", END)
graph.add_edge("default_agent", END)

# 9. Memory (MemorySaver)
memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# 10. Kullanıcı Arayüzü
while True:
    user_input = input("Kullanıcı: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    thread_id = "user-1"

    result = app.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    print("AI:", result["messages"][-1].content)


