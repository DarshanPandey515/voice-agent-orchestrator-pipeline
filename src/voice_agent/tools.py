# tools.py
import asyncio
import shlex
from pathlib import Path

MAX_CONTENT = 1500          
COMMAND_TIMEOUT = 10         
TREE_MAX_ENTRIES = 200



ALLOWED_COMMANDS = {
    "ls", "pwd", "cat", "head", "tail", "grep", "find",
    "git", "wc", "echo", "date", "whoami", "df", "du",
}


def truncate(text: str, limit: int = MAX_CONTENT) -> str:
    if len(text) > limit:
        return text[:limit] + f"... [truncated {len(text) - limit} more characters]"
    return text


class BashTool:
    """Runs a small allowlist of read-only shell commands, safely and asynchronously."""

    @staticmethod
    async def execute_command(command: str) -> str:
        if not command or not command.strip():
            return "No command given."

        try:
            args = shlex.split(command)
        except ValueError as e:
            return f"Couldn't parse that command: {e}"

        if not args:
            return "No command given."

        base_cmd = args[0]
        if base_cmd not in ALLOWED_COMMANDS:
            return (
                f"'{base_cmd}' isn't allowed. I can only run read-only commands "
                f"like: {', '.join(sorted(ALLOWED_COMMANDS))}."
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=COMMAND_TIMEOUT
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return f"Command timed out after {COMMAND_TIMEOUT} seconds."

            if proc.returncode == 0:
                return truncate(stdout.decode(errors="replace").strip() or "(no output)")
            else:
                return f"Command failed: {truncate(stderr.decode(errors='replace').strip())}"

        except FileNotFoundError:
            return f"Command not found: {base_cmd}"
        except Exception as e:
            return f"Error executing command: {e}"


class ReadFileTool:
    """Reads a text file from disk and returns a short, voice-friendly excerpt."""

    @staticmethod
    async def readfile(path: str) -> str:
        if not path:
            return "No file path provided."

        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        if not p.is_file():
            return f"{path} is not a file."

        try:
            content = await asyncio.to_thread(p.read_text, errors="replace")
        except Exception as e:
            return f"Error reading file: {e}"

        return truncate(content)


class GetTreeTool:
    """Lists project files (capped in size) so the model can describe the structure briefly."""

    IGNORE = {".git", "__pycache__", "env", "venv", ".venv", "node_modules"}

    @staticmethod
    async def get_tree(root: str = ".") -> str:
        def _walk():
            lines = []
            for path in Path(root).rglob("*"):
                if any(part in GetTreeTool.IGNORE for part in path.parts):
                    continue
                lines.append(str(path))
                if len(lines) >= TREE_MAX_ENTRIES:
                    lines.append(f"... [truncated, more than {TREE_MAX_ENTRIES} entries]")
                    break
            return "\n".join(lines) if lines else "(empty directory)"

        return await asyncio.to_thread(_walk)


class WriteFileTool:
    """Writes content to a file, creating parent directories as needed."""

    @staticmethod
    async def write_file(path: str, content: str) -> dict:
        def _write():
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return p

        try:
            p = await asyncio.to_thread(_write)
            return {"success": True, "path": str(p), "content_preview": content[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}


class EditFileTool:
    """Replaces the first occurrence of old_text with new_text in a file."""

    @staticmethod
    async def edit_file(path: str, old_text: str, new_text: str) -> dict:
        def _edit():
            p = Path(path)
            content = p.read_text()
            if old_text not in content:
                return {"success": False, "error": "text not found"}
            p.write_text(content.replace(old_text, new_text, 1))
            return {"success": True, "path": str(p)}

        try:
            return await asyncio.to_thread(_edit)
        except Exception as e:
            return {"success": False, "error": str(e)}