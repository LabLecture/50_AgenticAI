import logging
import json
import re

from copy import deepcopy
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from langgraph.graph import END

# from src.agents import research_agent, coder_agent, browser_agent
from src.agents import user_class_agent, class_progress_agent, link_provider_agent
from src.agents.llm import get_llm_by_type
from src.config import TEAM_MEMBERS
from src.config.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
from src.tools.search import tavily_tool
from .types import State, Router

logger = logging.getLogger(__name__)

RESPONSE_FORMAT = "Response from {}:\n\n<response>\n{}\n</response>\n\n*Please execute the next step.*"


def user_class_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the user_class_agent_that performs user_class tasks."""
    logger.info(f"user_class_agent_starting task  state: {state}")
    result = user_class_agent.invoke(state)
    logger.info("user_class_agent_completed task")
    logger.debug(f"user_class_agent_response: {result}")

    # Get the last AI message
    last_message = None
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            last_message = msg
            break
    
    if not last_message:
        last_message = AIMessage(content="죄송합니다. 응답을 생성하는데 실패했습니다.")
    
    return Command(
        update={
            "messages": [last_message]
        },
        goto="__end__"  
    )


def class_progress_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the class_progress agent that performs class_progress tasks."""
    logger.info("class_progress agent starting task")
    result = class_progress_agent.invoke(state)
    logger.info("class_progress agent completed task")
    # logger.debug(f"class_progress agent response: {result['messages'][-1].content}")
    logger.debug(f"class_progress agent response: {result}")
    # Get the last AI message
    last_message = None
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            last_message = msg
            break
    
    if not last_message:
        last_message = AIMessage(content="죄송합니다. 응답을 생성하는데 실패했습니다.")
    
    return Command(
        update={
            "messages": [last_message]
        },
        goto="__end__"  
    )

def link_provider_node(state: State) -> Command[Literal["supervisor"]]:
    """Node for the link_provider agent that performs link_provider tasks."""
    logger.info("link_provider agent starting task")
    result = link_provider_agent.invoke(state)
    logger.info("link_provider agent completed task")
    # logger.debug(f"link_provider agent response: {result['messages'][-1].content}")
    logger.debug(f"link_provider agent response: {result}")
    # Get the last AI message
    last_message = None
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            last_message = msg
            break
    
    if not last_message:
        last_message = AIMessage(content="죄송합니다. 응답을 생성하는데 실패했습니다.")
    
    return Command(
        update={
            "messages": [last_message]
        },
        goto="__end__"  
    )

def supervisor_node(state: State) -> Command[Literal[*TEAM_MEMBERS, "__end__"]]:
    """Supervisor node that decides which agent should act next."""
    logger.info("Supervisor_evaluating_next_action ------------------------------------------>")
    messages = apply_prompt_template("supervisor", state)
    response = (
        get_llm_by_type(AGENT_LLM_MAP["supervisor"])
        .with_structured_output(Router, method="json_mode")
        .invoke(messages)
    )
    goto = response["next"]
    logger.debug(f"Current_state_messages: {state['messages']}")
    logger.debug(f"Supervisor_response: {response}")

    # 🔍 수동 검증: Planner 계획에서 정보 누락으로 인해 중단된 경우 처리
    try:
        plan = json.loads(state.get("full_plan", "{}"))
        if (
            plan.get("title", "").startswith("수업 정보 조회 실패")
            or plan.get("title", "").startswith("수업 진도 확인 실패")
        ):
            logger.info("필수 정보 누락으로 흐름을 종료합니다.")
            return Command(goto="__end__", update={"next": "__end__"})
    except Exception as e:
        logger.warning(f"full_plan JSON parse error: {e}")

    if goto == "FINISH":
        goto = "__end__"
        logger.info("Workflow completed")
    else:
        logger.info(f"Supervisor delegating to: {goto}")

    return Command(goto=goto, update={"next": goto})

def safe_serialize(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except TypeError as e:
        print("Serialization failed:", e)
        return "{}"  # 또는 적절한 fallback

def planner_node(state: State) -> Command[Literal["supervisor", "__end__"]]:
    """Planner node that generate the full plan."""
    logger.info("Planner_generating_full_plan_------------------------------------------>>>>> ")
    messages = apply_prompt_template("planner", state)
    # whether to enable deep thinking mode
    llm = get_llm_by_type("supervisor")
    # llm = get_llm_by_type("basic")

    if state.get("deep_thinking_mode"):
        # llm = get_llm_by_type("reasoning")
        llm = get_llm_by_type("supervisor")
    if state.get("search_before_planning"):
        searched_content = tavily_tool.invoke({"query": state["messages"][-1].content})
        messages = deepcopy(messages)
        messages[
            -1
        ].content += f"\n\n# Relative Search Results\n\n{json.dumps([{'titile': elem['title'], 'content': elem['content']} for elem in searched_content], ensure_ascii=False)}"
    
    response = llm.invoke(messages)
    full_response = response.content.strip()

    logger.debug(f"Current state messages: {state['messages']}")
    logger.debug(f"Planner response: {full_response}")

    if full_response.startswith("```json"):
        full_response = full_response.removeprefix("```json")

    if full_response.endswith("```"):
        full_response = full_response.removesuffix("```")

    goto = "supervisor"
    try:
        json_response = json.loads(full_response)
    except json.JSONDecodeError:
        logger.warning("Planner response is not a valid JSON")
        goto = "__end__"

    if "정보 요청" in json_response.get("title", ""):
        final_response = json_response.get("steps", [{}])[0].get("description", "")
        final_message = [AIMessage(content=final_response, name="planner")]
    else:
        final_message = [HumanMessage(content=full_response, name="planner")]

    return Command(
        update={"messages": final_message,"full_plan": full_response},
        goto=goto,
    )


def coordinator_node(state: State) -> Command[Literal["planner", "__end__"]]:
    """Coordinator node that communicate with customers."""
    logger.info(f"Coordinator talking. ------------------------------------------>>>> state : {state}")
    messages = apply_prompt_template("coordinator", state)
    response = get_llm_by_type(AGENT_LLM_MAP["coordinator"]).invoke(messages)
    logger.debug(f"Current state messages: {state['messages']}")
    logger.debug(f"coordinator response: {response}")

    goto = "__end__"
    if "handoff_to_planner" in response.content:
        goto = "planner"

    # 메시지 update 추가
    if goto == "__end__":
        return Command(
            goto=goto,
            update={
                "messages": state["messages"] + [response]
            }
        )
    else:
        return Command(
            goto=goto,
        )



