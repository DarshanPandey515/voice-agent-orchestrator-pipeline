import asyncio
from dotenv import load_dotenv
import subprocess
import shlex

class BashTool:    
    @staticmethod
    async def execute_command(command: str) -> str:
        try:
            args = shlex.split(command)
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                return f"Success:\n{result.stdout}"
            else:
                return f"Error (exit code {result.returncode}):\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"
