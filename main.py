import os
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional, List
import aiofiles
import shutil
import uuid

from file_router import handle_file_upload
from utils import load_prompt, get_env_bool, get_env_str, send_to_mcp_router

load_dotenv()

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

ENDPOINTS = [
  "user-story-creator",
  "acceptance-criteria-creator",
  "test-case-creator",
  "test-script-creator",
  "test-data-creator"
]

@app.post("/{agent_name}")
async def agent_handler(
  agent_name: str,
  request: Request,
  message: Optional[str] = Form(None),
  files: Optional[List[UploadFile]] = File(None),
  teamName: Optional[str] = Form(None)
):
  if agent_name not in ENDPOINTS:
    return JSONResponse({"error": "Invalid endpoint"}, status_code=404)

  # Debug: print incoming request details
  print("==== Incoming Request ====")
  print(f"Endpoint: /{agent_name}")
  print(f"Message: {message}")
  if files:
    print("Files:", [file.filename for file in files])
  else:
    print("Files: None")
  print(f"Team: {teamName}")
  print("=========================")

  # Save and process files
  parsed_file_data = ""
  if files:
    parsed_file_data = await handle_file_upload(files, request)

  # Load agent system prompt
  prompt = load_prompt(agent_name)

  # Compose user message
  user_message = message or ""
  if parsed_file_data:
    user_message += f"\n\nUse this as context:\n<context>\n{parsed_file_data}\n</context>"

  # Send to MCP Router
  try:
    mcp_response = await send_to_mcp_router(
      agent_name=agent_name,
      user_message=user_message,
      prompt=prompt
    )
    # Extract only the content key's value from the message key
    content_value = None
    if isinstance(mcp_response, dict):
      # Anthropic and non-Anthropic responses may differ, handle both
      # Try OpenAI-style: {"choices": [{"message": {"content": ...}}]}
      if "choices" in mcp_response and isinstance(mcp_response["choices"], list):
        first_choice = mcp_response["choices"][0] if mcp_response["choices"] else None
        if first_choice and "message" in first_choice and "content" in first_choice["message"]:
          content_value = first_choice["message"]["content"]
      # Try Anthropic-style: {"message": {"content": ...}}
      elif "message" in mcp_response and "content" in mcp_response["message"]:
        content_value = mcp_response["message"]["content"]
    if content_value is not None:
      return JSONResponse({"content": content_value})
    else:
      return JSONResponse({"error": "No content found in MCP Router response", "raw": mcp_response}, status_code=500)
  except Exception as e:
    return JSONResponse({"error": str(e)}, status_code=500)
