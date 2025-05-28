#!/usr/bin/env python
# coding: utf-8

# In[1]:


# https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/#create-agent-supervisor

from dotenv import load_dotenv

from typing import Annotated

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

load_dotenv()

tavily_tool = TavilySearchResults(max_results=5)

# This executes code locally, which can be unsafe
repl = PythonREPL()

@tool
def python_repl_tool(
    code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code and do math. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return result_str

################################ Create Agent Supervisor

from typing import Literal
from typing_extensions import TypedDict

from langchain_ollama import ChatOllama

from langgraph.graph import MessagesState, END
from langgraph.types import Command


members = ["researcher", "coder"]
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    f" following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]
    # next: Literal["researcher", "coder", "FINISH"]

# llm = ChatAnthropic(model="claude-3-5-sonnet-latest")
# llm = ChatOllama(model="mistral-small:latest", temperature=0, base_url = "http://192.168.1.203:11434")
llm = ChatOllama(model="qwq:latest", temperature=0, base_url = "http://192.168.1.203:11434")


class State(MessagesState):
    next: str


def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto, update={"next": goto})


################################ Construct Graph

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent   

research_prompt = "You are a researcher. DO NOT do any math."
research_agent = create_react_agent(
# research_agent = create_structured_chat_agent(
    llm, tools=[tavily_tool], prompt=research_prompt
)
# research_executor = AgentExecutor(agent=research_agent, tools=[tavily_tool])

def research_node(state: State) -> Command[Literal["supervisor"]]:
    # last_message = next((m for m in reversed(state["messages"]) if m["role"] == "user"), None)
    result = research_agent.invoke(state)
    # result = research_agent.invoke({"input": last_message["content"]})
    # result = research_executor.invoke({"input": last_message["content"]})
    # output = result.get("output", "No research results found.")
    return Command(
        update={
            "messages": [HumanMessage(content=result["messages"][-1].content, name="researcher")]
            # "messages": state["messages"] + [{"role": "assistant", "content": output, "name": "researcher"}]
        },
        goto="supervisor",
    )

# NOTE: THIS PERFORMS ARBITRARY CODE EXECUTION, WHICH CAN BE UNSAFE WHEN NOT SANDBOXED
code_agent = create_react_agent(llm, tools=[python_repl_tool])
# code_agent = create_react_agent(llm, tools=[python_repl_tool], prompt=original_prompt)
# code_agent = create_structured_chat_agent(llm, [python_repl_tool], "You are a Python coder.")
# code_executor = AgentExecutor(agent=code_agent, tools=[python_repl_tool])

def code_node(state: State) -> Command[Literal["supervisor"]]:
    # last_message = next((m for m in reversed(state["messages"]) if m["role"] == "user"), None)
    result = code_agent.invoke(state)
    # result = code_agent.invoke({"input": last_message["content"]})
    # last_message = next((m for m in reversed(state["messages"]) if m["role"] == "user"), None)
    # result = code_executor.invoke({"input": last_message["content"]})
    # output = result.get("output", "No code results")
    return Command(
        update={
            "messages": [HumanMessage(content=result["messages"][-1].content, name="coder")]
            # "messages": state["messages"] + [{"role": "assistant", "content": output, "name": "coder"}]
        },
        goto="supervisor",
    )

builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", research_node)
builder.add_node("coder", code_node)
graph = builder.compile()

# In[2]:


from IPython.display import display, Image
try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except:
    print("Unable to display graph visualization")

# In[4]:


# user_message = {"role": "user", "content": "What's the square root of 42?"}
# for s in graph.stream({"messages": [user_message]}, subgraphs=True):
#     print(s)
#     print("----")

for s in graph.stream(
    {
        "messages": [
            (
                "user",
                "Find the latest GDP of New York and California, then calculate the average",
            )
        ]
    },
    subgraphs=True,
):
    print(s)
    print("----")    

# In[ ]:



