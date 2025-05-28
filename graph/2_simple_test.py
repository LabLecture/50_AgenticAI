#!/usr/bin/env python
# coding: utf-8

# In[1]:


# STATE 정의
from typing_extensions import TypedDict

class State(TypedDict): # TypedDict는 일종의 dictionary
    graph_state: str    # 상태(진행중, 다음 작업, 종료)
    goal : str          # 목표
    todo : list[str]    # 할 일 목록
    current_job : str   # 현재 작업
    total_time : int    # 총 소요시간(시간)
    time_spend : int    # 소요시간(시간)

# In[2]:


# NODE 정의
def node_1(state):
    print("---Node 1---")
    return {"graph_state": state['graph_state'] +" I am"}

def node_2(state):
    print("---Node 2---")
    return {"graph_state": state['graph_state'] +" happy!"}

def node_3(state):
    print("---Node 3---")
    return {"graph_state": state['graph_state'] +" sad!"}
    

# In[3]:


# EDGE 정의
import random
from typing import Literal

def decide_mood(state) -> Literal["node_2", "node_3"]:
    
    # Often, we will use state to decide on the next node to visit
    user_input = state['graph_state'] 
    
    # Here, let's just do a 50 / 50 split between nodes 2, 3
    if random.random() < 0.5:

        # 50% of the time, we return Node 2
        return "node_2"
    
    # 50% of the time, we return Node 3
    return "node_3"

# In[8]:


# GRAPH 정의
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END

# Build graph
builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# Add
graph = builder.compile()

# View
display(Image(graph.get_graph().draw_mermaid_png()))

# In[9]:


graph.invoke({"graph_state" : "Hi, this is Intel"})

# In[10]:


graph.invoke({"graph_state" : "Hi, this is Intel"})

# In[ ]:



