import logging
import asyncio

from agent_framework import ChatAgent, GroupChatBuilder, GroupChatStateSnapshot, WorkflowOutputEvent
from agent_framework.openai import OpenAIChatClient

logging.basicConfig(level=logging.INFO)

import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIChatClient

load_dotenv()
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")



def select_next_speaker(state: GroupChatStateSnapshot) -> str | None:

    participants = state["participants"]             
    history = state["history"]
    round_idx = state["round_index"]

    # Construct the effective cycle from the preferred order,
    # keeping only roles that are actually present.
    preferred = ["Researcher", "Writer", "Editor"]
    order = [p for p in preferred if p in participants]

    # Finish after 6 turns (researcher -> writer -> editor -> researcher -> writer)
    if round_idx >= 6:
        return None

    # First turn: start with the first available in the preferred order
    if not history:
        return order[0]

    last = history[-1].speaker

    # If last speaker is not recognized (e.g., system/user), restart from the first
    try:
        i = order.index(last)
        return order[(i + 1) % len(order)]
    except ValueError:
        return order[0]


async def main() -> None:

    chat_client=AzureOpenAIChatClient(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment,
    )

    writer = chat_client.create_agent(
    name="Writer",
    instructions="""
    You are a creative writer crafting engaging content.

    Role:
    1. Generate original, compelling narratives.
    2. Apply storytelling techniques for engagement.
    3. Incorporate feedback from editor/researcher.
    4. Revise to address issues while preserving core message.

    Feedback:
    - Accept constructive criticism, Explain creative choices when needed, Keep responses concise, imaginative, and engaging.""",
    )

    editor = chat_client.create_agent(
        name="Editor",
        instructions="""
        You are an editor focused on clarity and quality.

        Role:
        1. Ensure clarity, coherence, and flow.
        2. Fix grammar, structure, and style.
        3. Suggest improvements for readability and impact.

        Feedback:
        - Be specific and constructive, Address sentence-level and structural issues, Respect writer's voice while improving content.
        Keep responses concise and clear.""",
    )


    researcher = chat_client.create_agent(
        name="Researcher",
        instructions="""
        You provide accurate, relevant research.

        Role:
        1. Gather credible, up-to-date info.
        2. Summarize findings clearly.
        3. Highlight key insights and fill gaps.
        4. Ensure factual accuracy and alignment with goals.

        Responses:
        - Base on verifiable facts, Use bullet points or short paragraphs, Suggest sources when useful.
        Keep responses concise, relevant, and actionable.""",
    )

    workflow = (
    GroupChatBuilder()
    .select_speakers(select_next_speaker, display_name="Orchestrator")
    .participants([researcher, writer, editor])  # Uses agent.name for participant names
    .build()
    )

    task = "What are the key benefits of using async/await in Python?"

    print("\nStarting Group Chat with Simple Speaker Selector...\n")
    print(f"TASK: {task}\n")
    print("=" * 80)

    async for event in workflow.run_stream(task):
        if isinstance(event, WorkflowOutputEvent):
            print("WE ARE IN")
            final_message = event.data
            author = getattr(final_message, "author_name", "Unknown")
            text = getattr(final_message, "text", str(final_message))
            print(f"\n[{author}]\n{text}\n")
            print("-" * 80)

    print("\nWorkflow completed.")


if __name__ == "__main__":
    asyncio.run(main())