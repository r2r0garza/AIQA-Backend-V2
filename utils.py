import os
import json
from dotenv import load_dotenv

load_dotenv()

def get_env_str(key: str, default: str = "") -> str:
  return os.getenv(key, default)

def get_env_bool(key: str, default: bool = False) -> bool:
  val = os.getenv(key)
  if val is None:
    return default
  return val.lower() in ("1", "true", "yes", "on")

def load_prompt(agent_name: str) -> str:
  # Map endpoint to prompt file
  prompt_map = {
    "user-story-creator": "user-story-creator.xml",
    "acceptance-criteria-creator": "acceptance-criteria-creator.xml",
    "test-case-creator": "test-case-creator.xml",
    "test-script-creator": "automation-test-script-creator.xml",
    "test-data-creator": "test-data-creator.xml"
  }
  filename = prompt_map.get(agent_name)
  if not filename:
    raise Exception(f"No prompt found for agent: {agent_name}")
  path = os.path.join("prompts", filename)
  with open(path, "r", encoding="utf-8") as f:
    return f.read()

async def send_to_mcp_router(agent_name: str, user_message: str, prompt: str):
  import aiohttp

  mcp_url = get_env_str("MCP_ROUTER_URL", "http://localhost:8000/ask")
  anthropic = get_env_bool("ANTHROPIC", default=False)

  # Compose payload
  if anthropic:
    history = [
      {
        "role": "user",
        "content": f"{prompt}.\n\n{user_message}"
      }
    ]
  else:
    history = [
      {
        "role": "system",
        "content": prompt
      },
      {
        "role": "user",
        "content": user_message
      }
    ]

  payload = {
    "identity": { "user_id": "demo" },
    "memory": { "history": history },
    "tools": [],
    "docs": [],
    "extra": {}
  }

  # Debug: print payload being sent to MCP Router
  # print("==== MCP Router Payload ====")
  # print(json.dumps(payload, indent=2, ensure_ascii=False))
  # print(f"POST to: {mcp_url}")
  # print("===========================")

  async with aiohttp.ClientSession() as session:
    async with session.post(mcp_url, json=payload) as resp:
      if resp.status == 200:
        return await resp.json()
      else:
        text = await resp.text()
        raise Exception(f"MCP Router error {resp.status}: {text}")
