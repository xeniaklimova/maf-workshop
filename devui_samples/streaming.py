# BROKEN - Infinite loop issue
import asyncio
import logging

from agent_framework import AgentRunUpdateEvent, ChatAgent, GroupChatBuilder, WorkflowOutputEvent
from agent_framework.openai import OpenAIChatClient, OpenAIResponsesClient

logging.basicConfig(level=logging.INFO)


import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIChatClient

load_dotenv()
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")



async def main() -> None:

    chat_client=AzureOpenAIChatClient(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment,
    )

    researcher = chat_client.create_agent(
        name="Researcher",
        description="Collects relevant background information.",
        instructions="Gather concise facts that help a teammate answer the question.",
    )

    writer = chat_client.create_agent(
        name="Writer",
        description="Synthesizes a polished answer using the gathered notes.",
        instructions="Compose clear and structured answers using any notes provided.",
    )

    workflow = (
        GroupChatBuilder()
        .set_prompt_based_manager(chat_client=AzureOpenAIChatClient(), display_name="Coordinator")
        .participants(researcher=researcher, writer=writer)
        .build()
    )

    task = "Outline the core considerations for planning a community hackathon, and finish with a concise action plan."

    print("\nStarting Group Chat Workflow...\n")
    print(f"TASK: {task}\n")

    final_response = None
    last_executor_id: str | None = None
    async for event in workflow.run_stream(task):
        if isinstance(event, AgentRunUpdateEvent):
            # Handle the streaming agent update as it's produced
            eid = event.executor_id
            if eid != last_executor_id:
                if last_executor_id is not None:
                    print()
                print(f"{eid}:", end=" ", flush=True)
                last_executor_id = eid
            print(event.data, end="", flush=True)
        elif isinstance(event, WorkflowOutputEvent):
            final_response = getattr(event.data, "text", str(event.data))

    if final_response:
        print("=" * 60)
        print("FINAL RESPONSE")
        print("=" * 60)
        print(final_response)
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())