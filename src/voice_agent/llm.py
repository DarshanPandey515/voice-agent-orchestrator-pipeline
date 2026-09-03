from pydantic_ai.agent import Agent
from pydantic_ai import RunContext
from voice_agent.tools import BashTool
from voice_agent.config import llm_config
from dotenv import load_dotenv 

load_dotenv()

SYSTEM_PROMPT = """
You are a helpful, natural-sounding voice assistant. Keep responses:
- Concise and conversational (1-3 sentences)
- Spoken-style: no markdown, lists, or labels
- Direct and clear

Available tools: bash (read-only commands)
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
            return await BashTool.execute_command(command)
        
        
    async def generate_response(self, user_text: str) -> str:
        context = self.conversation_history[-10:]
        response = await self.agent.run(user_text, message_history=context)

        self.conversation_history.extend(response.all_messages())
        self.conversation_history = self.conversation_history[-10:]
        return response.output