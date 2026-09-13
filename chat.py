"""
This is the LangGraph version of the agent — it replaces the manual
tool-calling loop from before (kept as chat_manual_backup.py) with an
actual GRAPH: a small state machine with nodes and edges.

Why this matters, in plain words:

The previous version worked, but the "keep calling tools until done"
logic was a hand-written while-loop. That's fine for one agent with
two tools, but it doesn't scale well — if you wanted multiple
specialist agents (an Order Agent, a Policy Agent, a Supervisor that
routes between them), you'd end up reinventing a lot of bookkeeping
by hand.

LangGraph gives you that bookkeeping for free, expressed as an
actual graph:

    START ──► [agent] ──► (does it want to use a tool?)
                 ▲               │
                 │          yes  │  no
                 │               ▼        ▼
                 └────────── [tools]     END

- The "agent" node calls the LLM and asks: "given the conversation
  so far, what should happen next?"
- If the LLM's answer includes a tool call, we go to the "tools"
  node, which actually runs the function, then loops back to "agent"
  so the LLM can see the result and decide what to do next.
- If the LLM's answer is just a normal reply (no tool call), we go
  to END and return that as the final answer.

This is the same overall behavior as before — the AI still decides
for itself whether it needs a tool — just expressed as an explicit,
inspectable graph instead of an implicit loop.
"""

import os
from sqlalchemy.orm import Session

from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from tools import lookup_order, search_policy

MODEL = "openai/gpt-oss-120b"  # same model you used before

SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for an online store. "
    "If the customer asks about an order, use the lookup_order tool to "
    "get real information before answering. If the customer asks about "
    "returns, refunds, or shipping rules, use the search_policy tool "
    "and answer ONLY based on what it returns. Never make up order "
    "details or policy rules. Keep answers short and friendly."
)


def _build_tools_for_this_request(db: Session):
    """
    Wraps our existing plain Python functions (from tools.py) as
    LangGraph-compatible tools.

    Why a function that builds tools per-request, instead of just
    defining them once at the top of the file? Because lookup_order
    needs a database SESSION, and each web request gets its own
    fresh session (see database.py's get_db). Building the tools
    fresh for each request is the simplest way to hand that
    request's session to the tool without using global variables —
    the trade-off is a little more setup work per request, which is
    a fine trade for a learning project like this one.
    """

    # IMPORTANT: we explicitly name each tool with @tool("exact_name")
    # instead of letting it default to the Python function's name.
    # Without this, the tool would be named "search_policy_tool" (the
    # function's name), but it turns out this particular model
    # sometimes generates a call to "search_policy" (no "_tool"
    # suffix) regardless of what we called it — Groq's API then
    # rejects the call because that exact name wasn't registered.
    # Naming it explicitly to match what the model actually generates
    # fixes this validation error.

    @tool("lookup_order")
    def lookup_order_tool(order_id: int) -> dict:
        """Look up an order's status, product, and delivery info by its order ID number."""
        return lookup_order(order_id=order_id, db=db)

    @tool("search_policy")
    def search_policy_tool(query: str) -> dict:
        """Search the store's return, refund, and shipping policy documents to answer questions about return windows, refund eligibility, or shipping costs and times."""
        return search_policy(query=query)

    return [lookup_order_tool, search_policy_tool]


def _build_graph(tools):
    """Builds and compiles the actual LangGraph graph described above."""

    llm = ChatGroq(model=MODEL, api_key=os.environ.get("GROQ_API_KEY"))
    llm_with_tools = llm.bind_tools(tools)

    def call_model(state: MessagesState):
        """The 'agent' node: ask the LLM what to do next."""
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: MessagesState):
        """Decides which edge to follow after the agent node runs."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")  # after using a tool, go back and let the AI respond

    return graph.compile()


def chat_with_agent(user_message: str, db: Session) -> str:
    tools = _build_tools_for_this_request(db)
    app = _build_graph(tools)

    result = app.invoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ]
        }
    )

    final_message = result["messages"][-1]
    return final_message.content
