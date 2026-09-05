# llm_agent.py
from pydantic_ai.agent import Agent
from pydantic_ai import RunContext
from voice_agent.tools import BashTool, ReadFileTool, GetTreeTool
from voice_agent.config import llm_config
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are a helpful, natural-sounding voice assistant. Keep responses:
- Concise and conversational (1-3 sentences)
- Spoken-style: no markdown, lists, or labels
- Direct and clear

When a tool returns file paths, code, or command output, summarize it in
plain spoken language instead of reading it verbatim — don't recite file
paths, symbols, or raw command output character-by-character.

Available tools: bash (read-only commands only), read a file, list the
project tree.
"""


class LLMAgent:

    def __init__(self):
        self.agent = Agent(
            model=llm_config.model,
            system_prompt=SYSTEM_PROMPT,
        )
        self.register_tools()
        self.conversation_history = []

    def register_tools(self):
        @self.agent.tool
        async def bash_tool(ctx: RunContext, command: str) -> str:
            """Run a read-only shell command (e.g. ls, cat, grep, git status) and return its output."""
            return await BashTool.execute_command(command)

        @self.agent.tool
        async def readfile_tool(ctx: RunContext, path: str) -> str:
            """Read the contents of a text file at the given path."""
            return await ReadFileTool.readfile(path)

        @self.agent.tool
        async def get_tree_tool(ctx: RunContext) -> str:
            """List the files in the current project directory."""
            return await GetTreeTool.get_tree()

    async def generate_response(self, user_text: str) -> str:
        context = self.conversation_history[-10:]
        response = await self.agent.run(user_text, message_history=context)

        self.conversation_history.extend(response.all_messages())
        self.conversation_history = self.conversation_history[-10:]
        return response.output