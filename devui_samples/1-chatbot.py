import asyncio
import os
from dotenv import load_dotenv
from agent_framework import (
    ChatAgent,
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from agent_framework import Executor, WorkflowBuilder, WorkflowContext,handler
from typing_extensions import Never
from agent_framework.devui import serve

from agent_framework.azure import AzureOpenAIChatClient

load_dotenv()
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

client = AzureOpenAIChatClient(
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment,
    )

# you're just a generator, we get a chat response from you:
class HandleInput(Executor):

    agent: ChatAgent

    def __init__(self, chat_client: AzureOpenAIChatClient, id: str = "chat_agent"):
        # Create a domain specific agent using your configured AzureOpenAIChatClient.
        self.agent = chat_client.create_agent(
            instructions=(
                "You are a helpful and concise assistant which answers user questions."
            ),
        )
        # Associate this agent with the executor node. The base Executor stores it on self.agent.
        super().__init__(id=id)

    @handler
    async def handle(self, message: str, ctx: WorkflowContext[str]) -> None:

        response = await self.agent.run(message)
        print(f"(Agent): {response}")
        print(type(response))
  
        await ctx.send_message(str(response))


class GetQuestion(Executor):
    @handler
    async def get_question(self, ques: str, ctx: WorkflowContext[str]) -> None:
        """ Get the user's question to pass over to the chat """

        print("What is your question?")
        ques = input("Q: ")

        if ques == "exit":
            await ctx.yield_output("Good bye!")
            return

        await ctx.send_message(ques)


prompter = HandleInput(client)
responder = GetQuestion(id="userQuestion")


workflow = (
    WorkflowBuilder()
    .add_edge(responder, prompter)
    .add_edge(prompter, responder)
    .set_start_executor(responder)
    .build()
)

# serve(entities=[workflow], auto_open=True)


async def main() -> None:

    events = await workflow.run("Hello")
    print(events.get_outputs())



if __name__ == "__main__":
    print("Initializing Workflow as Agent Sample...")
    asyncio.run(main())
    