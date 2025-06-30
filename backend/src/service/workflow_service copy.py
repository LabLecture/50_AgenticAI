import logging
import json

from src.config import TEAM_MEMBERS
from src.graph import build_graph
from langchain_community.adapters.openai import convert_message_to_dict
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default level is INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def enable_debug_logging():
    """Enable debug level logging for more detailed execution information."""
    logging.getLogger("src").setLevel(logging.DEBUG)


logger = logging.getLogger(__name__)

# Create the graph
graph = build_graph()

# Cache for coordinator messages
coordinator_cache = []
MAX_CACHE_SIZE = 2

def safe_serialize(obj):
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except TypeError as e:
        print("Serialization failed:", e)
        return "{}"  # 또는 적절한 fallback


async def run_agent_workflow(
    user_input_messages: list,
    debug: bool = False,
    deep_thinking_mode: bool = False,
    search_before_planning: bool = False,
    return_final_only: bool = False,  # ✅ 추가
):
    """Run the agent workflow with the given user input.

    Args:
        user_input_messages: The user request messages
        debug: If True, enables debug level logging

    Returns:
        The final state after the workflow completes
    """
    if not user_input_messages:
        raise ValueError("Input could not be empty")

    if debug:
        enable_debug_logging()

    logger.info(f"Starting workflow with user input: {user_input_messages}")

    workflow_id = str(uuid.uuid4())

    # streaming_llm_agents = [*TEAM_MEMBERS, "planner", "coordinator"]
    streaming_llm_agents = [tuple(TEAM_MEMBERS), "planner", "coordinator"]

    # Reset coordinator cache at the start of each workflow
    global coordinator_cache
    coordinator_cache = []
    global is_handoff_case
    is_handoff_case = False

    # TODO: extract message content from object, specifically for on_chat_model_stream
    async for event in graph.astream_events(
        {
            # Constants
            "TEAM_MEMBERS": TEAM_MEMBERS,
            # Runtime Variables
            "messages": user_input_messages,
            "deep_thinking_mode": deep_thinking_mode,
            "search_before_planning": search_before_planning,
        },
        version="v2",
    ):
        kind = event.get("event")
        data = event.get("data")
        name = event.get("name")
        metadata = event.get("metadata")
        node = (
            ""
            if (metadata.get("checkpoint_ns") is None)
            else metadata.get("checkpoint_ns").split(":")[0]
        )
        langgraph_step = (
            ""
            if (metadata.get("langgraph_step") is None)
            else str(metadata["langgraph_step"])
        )
        run_id = "" if (event.get("run_id") is None) else str(event["run_id"])

        # 스트리밍 때문에 단어 제어가 어려움. 스트리밍 기능 제거필요. 5/15 내일 해보자.
        if 'handoff_to_planner' in safe_serialize(data) and node == "coordinator" and kind=="on_chat_model_start":
            is_handoff_case = True
            logger.debug(f"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@====> node ={node}, kind={kind}, data={data}")

        if kind == "on_chain_start" and name in streaming_llm_agents:
            if name == "planner":
                yield {
                    "event": "start_of_workflow",
                    "data": {"workflow_id": workflow_id, "input": user_input_messages},
                }
            ydata = {
                "event": "start_of_agent",
                "data": {
                    "agent_name": name,
                    "agent_id": f"{workflow_id}_{name}_{langgraph_step}",
                },
            }
        elif kind == "on_chain_end" and name in streaming_llm_agents:
            ydata = {
                "event": "end_of_agent",
                "data": {
                    "agent_name": name,
                    "agent_id": f"{workflow_id}_{name}_{langgraph_step}",
                },
            }
        elif kind == "on_chat_model_start" and node in streaming_llm_agents:
            ydata = {
                "event": "start_of_llm",
                "data": {"agent_name": node},
            }
            logger.debug(f"@@@@@@@@@on_chat_model_start@@@on_chat_model_start@@@@@@@@@@@@@@@@@@====> ydata ={ydata}")

        elif kind == "on_chat_model_end" and node in streaming_llm_agents:
            ydata = {
                "event": "end_of_llm",
                "data": {"agent_name": node},
            }
        elif kind == "on_chat_model_stream" and node in streaming_llm_agents:
            content = data["chunk"].content

            if node == "planner":
                continue  # 👈 planner 응답은 SSE로 출력하지 않음

            # elif node == "coordinator":  # ---> 이렇게만 하면 확실히 handoff_to_planner 출력안함.   
            elif node == "coordinator" and 'handoff_to_planner' in content:
                is_handoff_case = True
                continue  # 👈 coordinator 응답은 SSE로 출력하지 않음
            
            if content is None or content == "":
                if not data["chunk"].additional_kwargs.get("reasoning_content"):
                    # Skip empty messages
                    continue
                ydata = {
                    "event": "message",
                    "data": {
                        "message_id": data["chunk"].id,
                        "delta": {
                            "reasoning_content": (
                                data["chunk"].additional_kwargs["reasoning_content"]
                            )
                        },
                    },
                }
            else:
                # Check if the message is from the coordinator
                if node == "coordinator":
                    if len(coordinator_cache) < MAX_CACHE_SIZE:
                        coordinator_cache.append(content)
                        cached_content = "".join(coordinator_cache)
                        # if cached_content.startswith("handoff"):
                        if 'handoff_to_planner' in cached_content:
                            is_handoff_case = True
                            logger.debug(f"------------------------------------> is_handoff_case node={node}, kind={kind}")
                            continue
                        if len(coordinator_cache) < MAX_CACHE_SIZE:
                            continue
                        # Send the cached message
                        ydata = {
                            "event": "message",
                            "data": {
                                "message_id": data["chunk"].id,
                                "delta": {"content": cached_content},
                            },
                        }
                    elif not is_handoff_case:
                        # For other agents, send the message directly
                        ydata = {
                            "event": "message",
                            "data": {
                                "message_id": data["chunk"].id,
                                "delta": {"content": content},
                            },
                        }
                else:
                    # For other agents, send the message directly
                    ydata = {
                        "event": "message",
                        "data": {
                            "message_id": data["chunk"].id,
                            "delta": {"content": content},
                        },
                    }
        elif kind == "on_tool_start" and node in TEAM_MEMBERS:
            ydata = {
                "event": "tool_call",
                "data": {
                    "tool_call_id": f"{workflow_id}_{node}_{name}_{run_id}",
                    "tool_name": name,
                    "tool_input": data.get("input"),
                },
            }
        elif kind == "on_tool_end" and node in TEAM_MEMBERS:
            ydata = {
                "event": "tool_call_result",
                "data": {
                    "tool_call_id": f"{workflow_id}_{node}_{name}_{run_id}",
                    "tool_name": name,
                    "tool_result": data["output"].content if data.get("output") else "",
                },
            }
        else:
            continue

        yield ydata               # 이거 주석하니 json데이타는 안나옴. but 정상적인 답변도 안나옴.
        

    last_state = data.get("output", {})  # 마지막 상태 보존

    if is_handoff_case:
        print("혹시 이거 때문에...? ")
        yield {
            "event": "end_of_workflow",
            "data": {
                "workflow_id": workflow_id,
                "messages": [
                    convert_message_to_dict(msg)
                    for msg in last_state.get("messages", [])
                ],
            },
        }
    else:
        # 👉 planner가 full_plan으로 정보 부족 메시지를 생성했을 경우 사용자에게 전달
        full_plan = last_state.get("full_plan")
        if full_plan:
            try:
                parsed_plan = json.loads(full_plan)
                if "정보 요청" in parsed_plan.get("title", ""):
                    yield {
                        "event": "message",
                        "data": {
                            "message_id": str(uuid.uuid4()),
                            "delta": {
                                "content": # parsed_plan.get("title") + "\n\n" +
                                           parsed_plan.get("steps", [{}])[0].get("description", "")
                            },
                        },
                    }
            except Exception as e:
                logger.warning(f"Failed to parse full_plan JSON: {e}")
        
        # 마지막 end 이벤트는 그대로    이건 주석해도 차이가 없는데.. 왜? 
        # yield {
        #     "event": "end_of_workflow",
        #     "data": {
        #         "workflow_id": workflow_id,
        #         "messages": [
        #             convert_message_to_dict(msg)
        #             for msg in last_state.get("messages", [])
        #         ],
        #     },
        # }

