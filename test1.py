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
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)

# 2. State tipi
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_lang: str

# 3. Tool'lar
@tool
def add_numbers(a: float, b: float) -> float:
    """Toplama işlemi yapar"""
    return a + b

@tool
def search_web(query: str) -> str:
    """Web araması simülasyonu yapar"""
    return f"Fake result for: {query}"

# 4. Agent'lar (ReAct ve Default)
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

def default_agent(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(content="You are a friendly and helpful assistant. Respond to casual conversations, greetings, and general questions in a warm and engaging manner.")
    messages_with_prompt = [system_prompt] + state["messages"]
    response = llm.invoke(messages_with_prompt)
    return {"messages": state["messages"] + [response], "user_lang": state.get("user_lang", "en")}

# 5. Supervisor Agent
def supervisor_agent(state: AgentState) -> AgentState:
    decision_prompt = [
        HumanMessage(content="""
You are a supervisor agent. Decide which expert should handle the user message.
- If it's a math question, respond only with: math
- If it's an information/research query, respond only with: research
- For anything casual (greetings, emotions, undefined), respond only with: casual
Only say: math, research, or casual
""")
    ] + state["messages"][-1:]
    decision = llm.invoke(decision_prompt)
    return {"messages": state["messages"] + [decision], "user_lang": state.get("user_lang", "en")}

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

# 6. Dil Tespiti Node'u
def detect_language(state: AgentState) -> AgentState:
    msg = state["messages"][-1].content
    prompt = f"What is the language of the following text? Just say the ISO code (en, tr, etc):\n\n{msg}"
    lang_response = llm.invoke([HumanMessage(content=prompt)])
    lang_code = lang_response.content.strip().split()[0].lower()
    return {"messages": state["messages"], "user_lang": lang_code}

# 7. İngilizceye Çeviri Node'u
def translate_to_english(state: AgentState) -> AgentState:
    user_lang = state.get("user_lang", "en")
    msg = state["messages"][-1].content
    if user_lang == "en":
        return state
    prompt = f"Translate the following message to English. Only provide the translation, nothing else:\n\n{msg}"
    translation = llm.invoke([HumanMessage(content=prompt)])
    new_message = HumanMessage(content=translation.content)
    return {"messages": state["messages"][:-1] + [new_message], "user_lang": user_lang}

# 8. Kullanıcı Diline Geri Çeviri Node'u (END'den önce)
def translate_to_user_lang(state: AgentState) -> AgentState:
    user_lang = state.get("user_lang", "en")
    if user_lang == "en":
        return state
    ai_msg = state["messages"][-1].content
    prompt = f"Translate this to {user_lang}. Only translation:\n\n{ai_msg}"
    translation = llm.invoke([HumanMessage(content=prompt)])
    new_ai_msg = AIMessage(content=translation.content)
    return {"messages": state["messages"][:-1] + [new_ai_msg], "user_lang": user_lang}

# 9. Graph Kurulumu
graph = StateGraph(AgentState)
graph.add_node("detect_language", detect_language)
graph.add_node("translate_to_english", translate_to_english)
graph.add_node("supervisor", supervisor_agent)
graph.add_node("math_agent", math_agent_node)
graph.add_node("research_agent", research_agent_node)
graph.add_node("default_agent", default_agent)
graph.add_node("translate_to_user_lang", translate_to_user_lang)

graph.add_edge(START, "detect_language")
graph.add_edge("detect_language", "translate_to_english")
graph.add_edge("translate_to_english", "supervisor")
graph.add_conditional_edges(
    "supervisor",
    route,
    {
        "math_agent": "math_agent",
        "research_agent": "research_agent",
        "default_agent": "default_agent"
    }
)
graph.add_edge("math_agent", "translate_to_user_lang")
graph.add_edge("research_agent", "translate_to_user_lang")
graph.add_edge("default_agent", "translate_to_user_lang")
graph.add_edge("translate_to_user_lang", END)

# 10. Memory (MemorySaver)
memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# 11. Kullanıcı Arayüzü
while True:
    user_input = input("Kullanıcı: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    thread_id = "user-1"

    result = app.invoke(
        {"messages": [HumanMessage(content=user_input)], "user_lang": ""},
        config={"configurable": {"thread_id": thread_id}}
    )

    print("AI:", result["messages"][-1].content)
