from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.schemas.agent_schemas import AgentState
from app.services.agent import (
    agent_executor,
    agent_planner,
    planner_router,
    reviewer,
)
from app.services.tools import prepare_document

# Build the state graph
builder = StateGraph(state_schema=AgentState)

# Add nodes
builder.add_node("prepare_document", prepare_document)
builder.add_node("agent_planner", agent_planner)
builder.add_node("agent_executor", agent_executor)
builder.add_node("reviewer", reviewer)

# Add edges
builder.add_edge(START, "prepare_document")
builder.add_edge("prepare_document", "agent_planner")

# Conditional routing from planner
builder.add_conditional_edges(
    "agent_planner",
    planner_router,
    {"agent_executor": "agent_executor", "reviewer": "reviewer"},
)

builder.add_edge("agent_executor", "agent_planner")
builder.add_edge("reviewer", END)

checkpointer = InMemorySaver()

# Compile the graph
graph = builder.compile(checkpointer=checkpointer)
