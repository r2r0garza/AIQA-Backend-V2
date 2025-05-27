import os
import aiohttp
from fastapi import UploadFile, Request
from typing import List
from utils import get_env_bool, get_env_str

# Helper to determine file type
def get_file_type(filename: str) -> str:
  ext = filename.lower().split('.')[-1]
  if ext == "xlsx":
    return "xlsx"
  elif ext in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
    return "image"
  else:
    return "other"

async def handle_file_upload(
  files: List[UploadFile],
  request: Request,
  system_prompt: str = None
) -> str:
  """
  Receives a list of UploadFile, sends each to the correct backend endpoint,
  and returns the concatenated parsed text.
  """
  USE_CAPTIONS = get_env_bool("USE_CAPTIONS", default=False)
  backend_base = get_env_str("PARSER_SERVER_BASE_URL", "http://localhost:8001")
  results = []

  async with aiohttp.ClientSession() as session:
    for file in files:
      file_type = get_file_type(file.filename)
      if file_type == "xlsx":
        url = f"{backend_base}/xlsx-to-md"
        form = aiohttp.FormData()
        form.add_field("file", await file.read(), filename=file.filename, content_type=file.content_type)
      elif file_type == "image":
        url = f"{backend_base}/caption" if USE_CAPTIONS else f"{backend_base}/parse"
        form = aiohttp.FormData()
        if USE_CAPTIONS and "/caption" in url:
          form.add_field("image", await file.read(), filename=file.filename, content_type=file.content_type)
          if system_prompt is not None:
            form.add_field("system_prompt", system_prompt)
        else:
          form.add_field("file", await file.read(), filename=file.filename, content_type=file.content_type)
      else:
        url = f"{backend_base}/parse"
        form = aiohttp.FormData()
        form.add_field("file", await file.read(), filename=file.filename, content_type=file.content_type)

      async with session.post(url, data=form) as resp:
        if resp.status == 200:
          # Try to parse as JSON, else fallback to text
          try:
            data_json = await resp.json()
            # Try common content fields
            file_content = data_json.get("content") or data_json.get("text") or ""
            if not file_content:
              # If no known field, fallback to full JSON as string
              file_content = json.dumps(data_json, ensure_ascii=False)
            results.append(file_content)
          except Exception:
            # Not JSON, fallback to plain text
            data = await resp.text()
            results.append(data)
        else:
          results.append(f"[Error parsing {file.filename}: {resp.status}]")

  return "\n\n".join(results)
