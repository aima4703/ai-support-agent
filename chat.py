"""
This is where the "AI decides what to do" part happens.

The flow, in plain words:
1. We send the user's message to Groq, along with a "menu" of tools
   it's allowed to use (right now, just lookup_order).
2. Groq reads the message and decides: does this need a tool, or can
   I just answer directly?
3. If it wants a tool, it tells us WHICH one and WITH WHAT arguments
   (e.g. "call lookup_order with order_id=4582"). We run that
   function ourselves — Groq never touches your database directly.
4. We send the tool's result back to Groq, and it writes a normal,
   friendly sentence using that information.
"""

import os
import json
from groq import Groq
from sqlalchemy.orm import Session

from tools import lookup_order, search_policy, TOOLS_SCHEMA

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-120b"  # same model family you used in PolicyBot

SYSTEM_PROMPT = (
    "You are a helpful customer support assistant for an online store. "
    "If the customer asks about an order, use the lookup_order tool to "
    "get real information before answering. If the customer asks about "
    "returns, refunds, or shipping rules, use the search_policy tool "
    "and answer ONLY based on what it returns. Never make up order "
    "details or policy rules. Keep answers short and friendly."
)


def chat_with_agent(user_message: str, db: Session) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # Step 1: ask Groq what it wants to do
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS_SCHEMA,
    )

    reply = response.choices[0].message

    # Step 2: did the AI ask to use a tool?
    if reply.tool_calls:
        # Add the AI's tool request to the conversation history
        messages.append(reply)

        for tool_call in reply.tool_calls:
            args = json.loads(tool_call.function.arguments)

            if tool_call.function.name == "lookup_order":
                result = lookup_order(order_id=args["order_id"], db=db)
            elif tool_call.function.name == "search_policy":
                result = search_policy(query=args["query"])
            else:
                result = {"error": "Unknown tool requested"}

            # Step 3: give the tool's result back to Groq
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        # Step 4: ask Groq to write the final, human-friendly answer
        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        return final_response.choices[0].message.content

    # No tool needed — the AI answered directly (e.g. "hello!")
    return reply.content
