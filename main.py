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
from utils import load_prompt, get_env_bool, get_env_str, send_to_mcp_router, chunk_text_by_token_limit
from supabase_client import get_template_for_agent, debug_list_document_types, get_document_texts_by_type, get_automation_framework_files

load_dotenv()

app = FastAPI()

cors_urls = os.getenv("CORS_URLS", "*")
if cors_urls.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [url.strip() for url in cors_urls.split(",") if url.strip()]


# Allow CORS for local frontend dev
app.add_middleware(
  CORSMiddleware,
  allow_origins=allow_origins,
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
  # print("==== Incoming Request ====")
  # print(f"Endpoint: /{agent_name}")
  # print(f"Message: {message}")
  # if files:
  #   print("Files:", [file.filename for file in files])
  # else:
  #   print("Files: None")
  # print(f"Team: {teamName}")
  # print("=========================")

  # Save and process files
  parsed_file_data = ""
  if files:
    parsed_file_data = await handle_file_upload(files, request, message)

  # Load agent system prompt
  prompt = load_prompt(agent_name)

  # Compose user message
  user_message = message or ""
  if parsed_file_data:
    user_message += f"\n\nUse this as context:\n<context>\n{parsed_file_data}\n</context>"

  # Chunk user_message before sending to AI (using CHUNKING_LIMIT from .env)
  chunking_limit_str = get_env_str("CHUNKING_LIMIT", "3000")
  try:
    chunking_limit = int(chunking_limit_str)
  except Exception:
    chunking_limit = 2000
  user_message_chunks = chunk_text_by_token_limit(user_message, chunking_limit)
  # print("[Chunking Debug] User message chunks:", user_message_chunks)
  # For now, use only the first chunk for the AI request (can be extended to handle multiple)
  user_message = user_message_chunks[0] if user_message_chunks else user_message

  # Special workflow for automation script creation
  if agent_name == "test-script-creator":
    # Fetch all Automation Framework files
    automation_files = await get_automation_framework_files()
    additional_context_blocks = []
    for file in automation_files:
      url = file.get("document_url", "")
      doc_text = file.get("document_text", "")
      # Determine file name
      if "github.com" in url:
        name = url.split("/")[-1]
      else:
        name = url.split("_")[-1]
      additional_context_blocks.append(f"<additional_context>{name}\n{doc_text}</additional_context>")
    additional_context_str = "\n".join(additional_context_blocks)
    # print("[AI Debug] Automation Framework additional context blocks:", additional_context_str)
    # Fetch the Automation Script Generator Template
    template_text = await get_template_for_agent(agent_name)
    template_block = f"\n<template>\n{template_text}\n</template>" if template_text else ""
    # Build the final user prompt
    user_message += "\n" + additional_context_str + template_block
    # Chunk user_message before sending to AI (using CHUNKING_LIMIT from .env)
    chunking_limit_str = get_env_str("CHUNKING_LIMIT", "3000")
    try:
      chunking_limit = int(chunking_limit_str)
    except Exception:
      chunking_limit = 2000
    user_message_chunks = chunk_text_by_token_limit(user_message, chunking_limit)
    # print("[Chunking Debug] User message chunks:", user_message_chunks)
    user_message = user_message_chunks[0] if user_message_chunks else user_message
  else:
    # Supabase: get unique document_type values
    unique_document_types = await debug_list_document_types()

    # Compose AI user message for analyze_expert
    agent_task_map = {
      "user-story-creator": "User Story Creator",
      "acceptance-criteria-creator": "Acceptance Criteria Creator",
      "test-case-creator": "Manual Test Case Creator",
      "test-script-creator": "Automated Test Script Creator",
      "test-data-creator": "Test Data Creator"
    }
    analyze_task = agent_task_map.get(agent_name, agent_name)
    document_types_xml = "<document_types>" + ",".join(unique_document_types) + "</document_types>"
    document_text_xml = ""
    if parsed_file_data:
      document_text_xml = f"<document_text>{parsed_file_data}</document_text>"
    ai_user_message = f"<task>{analyze_task}</task>\n{document_types_xml}\n{document_text_xml}"

    # Load analyze_expert.xml system prompt
    with open("prompts/anaylze_expert.xml", "r", encoding="utf-8") as f:
      analyze_expert_prompt = f.read()

    # Send to MCP Router for document type analysis
    try:
      # Debug: show the JSON payload being sent to analyze_expert
      analyze_payload = {
        "agent_name": "analyze_expert",
        "user_message": ai_user_message,
        "prompt": analyze_expert_prompt
      }
      # ("[AI Debug] Payload sent to analyze_expert:", analyze_payload)

      ai_response = await send_to_mcp_router(
        agent_name="analyze_expert",
        user_message=ai_user_message,
        prompt=analyze_expert_prompt
      )
      # print("[AI Debug] analyze_expert response:", ai_response)
      # Debug: print document types returned by the agent
      if isinstance(ai_response, dict):
        # Try OpenAI-style: {"choices": [{"message": {"content": ...}}]}
        doc_types = None
        if "choices" in ai_response and isinstance(ai_response["choices"], list):
          first_choice = ai_response["choices"][0] if ai_response["choices"] else None
          if first_choice and "message" in first_choice and "content" in first_choice["message"]:
            doc_types = first_choice["message"]["content"]
        # Try Anthropic-style: {"message": {"content": ...}}
        elif "message" in ai_response and "content" in ai_response["message"]:
          doc_types = ai_response["message"]["content"]
        # print("[AI Debug] Document types returned by analyze_expert:", doc_types)
        # Filter out document types containing "template"
        if doc_types:
          # Clean up: remove first and last line, then split and filter
          if isinstance(doc_types, str):
            lines = [line.strip() for line in doc_types.splitlines() if line.strip()]
            # Remove first and last line if more than 2 lines
            if len(lines) > 2:
              lines = lines[1:-1]
            # Remove lines that are "```markdown" or "```"
            lines = [line for line in lines if line.lower() not in ("```markdown", "```")]
            # Remove text after ":" in each line, and leading "- "
            cleaned_lines = []
            for line in lines:
              if ":" in line:
                line = line.split(":", 1)[0]
              if line.startswith("- "):
                line = line[2:]
              cleaned_lines.append(line.strip())
            doc_types_cleaned = "\n".join(cleaned_lines)
            doc_type_list = [dt.strip() for dt in doc_types_cleaned.replace("\n", ",").split(",") if dt.strip()]
          elif isinstance(doc_types, list):
            lines = [str(line).strip() for line in doc_types if str(line).strip()]
            if len(lines) > 2:
              lines = lines[1:-1]
            doc_type_list = lines
          else:
            doc_type_list = []
          filtered_doc_types = [dt for dt in doc_type_list if "template" not in dt.lower()]
          # print("[AI Debug] Filtered document types (no 'template'):", filtered_doc_types)
          # Fetch document_texts for each filtered_doc_type and build additional_context
          additional_context_blocks = []
          for doc_type in filtered_doc_types:
            doc_texts = await get_document_texts_by_type(doc_type, team=teamName if teamName else None)
            for doc_text in doc_texts:
              additional_context_blocks.append(f"<additional_context>{doc_text}</additional_context>")
          additional_context_str = "\n".join(additional_context_blocks)
          # print("[AI Debug] Additional context blocks:", additional_context_str)
          # Append to user_message before sending to the AI
          user_message += "\n" + additional_context_str
    except Exception as e:
      print("[AI Debug] Error calling analyze_expert:", e)

    # Supabase: check for template for this agent
    template_text = await get_template_for_agent(agent_name)
    if template_text:
      user_message += f"\n<template>\n{template_text}\n</template>"

    # Chunk user_message before sending to AI (using CHUNKING_LIMIT from .env)
    chunking_limit_str = get_env_str("CHUNKING_LIMIT", "3000")
    try:
      chunking_limit = int(chunking_limit_str)
    except Exception:
      chunking_limit = 2000
    user_message_chunks = chunk_text_by_token_limit(user_message, chunking_limit)
    # print("[Chunking Debug] User message chunks:", user_message_chunks)
    user_message = user_message_chunks[0] if user_message_chunks else user_message

  # Supabase: check for template for this agent
  template_text = await get_template_for_agent(agent_name)
  if template_text:
    user_message += f"\n<template>\n{template_text}\n</template>"

  # Send to MCP Router
  try:
    # Debug: show the JSON payload being sent to the MCP Server Router
    mcp_payload = {
      "agent_name": agent_name,
      "user_message": user_message,
      "prompt": prompt
    }
    # print("[AI Debug] Payload sent to MCP Server Router:", mcp_payload)

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
          # print("[AI Debug] Response from MCP Server Router:", content_value)
      # Try Anthropic-style: {"message": {"content": ...}}
      elif "message" in mcp_response and "content" in mcp_response["message"]:
        content_value = mcp_response["message"]["content"]
    if content_value is not None:
      return JSONResponse({"content": content_value})
    else:
      return JSONResponse({"error": "No content found in MCP Router response", "raw": mcp_response}, status_code=500)
  except Exception as e:
    return JSONResponse({"error": str(e)}, status_code=500)
