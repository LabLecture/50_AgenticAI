from langgraph.graph import StateGraph, START

from .types import State
from .nodes import (
    coordinator_node,
    planner_node,
    supervisor_node,
    user_class_node,
    class_progress_node,
    # research_node,
    # code_node,
    # browser_node,
    # reporter_node,
)


def build_graph():
    """Build and return the agent workflow graph."""
    builder = StateGraph(State)
    builder.add_edge(START, "coordinator")
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("planner", planner_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("user_class", user_class_node)
    builder.add_node("class_progress", class_progress_node)
    # builder.add_node("researcher", research_node)
    # builder.add_node("coder", code_node)
    # builder.add_node("browser", browser_node)
    # builder.add_node("reporter", reporter_node)
    return builder.compile()
