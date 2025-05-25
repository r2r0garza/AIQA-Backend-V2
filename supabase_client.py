import os
from typing import List, Optional
from dotenv import load_dotenv
import asyncio

import aiohttp

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
  raise Exception("SUPABASE_URL and SUPABASE_ANON_KEY must be set in the .env file.")

SUPABASE_REST_URL = f"{SUPABASE_URL}/rest/v1"
SUPABASE_HEADERS = {
  "apikey": SUPABASE_ANON_KEY,
  "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
  "Content-Type": "application/json"
}

# Agent to template name mapping
AGENT_TEMPLATE_MAP = {
  "user-story-creator": "User Story Creator Template",
  "acceptance-criteria-creator": "Acceptance Criteria Creator Template",
  "test-case-creator": "Test Cases Generator Template",
  "test-script-creator": "Automation Script Generator Template",
  "test-data-creator": "Test Data Generator Template"
}

async def get_document_texts_by_type(document_type: str):
  """
  Fetch all document_texts from 'document' table where document_type matches (case-insensitive).
  Returns a list of document_text strings.
  """
  url = f"{SUPABASE_REST_URL}/document?document_type=ilike.{document_type}&select=document_text"
  #print(f"[Supabase Debug] Fetching document_texts for type: {document_type} from: {url}")
  async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=SUPABASE_HEADERS) as resp:
      #print(f"[Supabase Debug] Response status: {resp.status}")
      if resp.status == 200:
        data = await resp.json()
        #print(f"[Supabase Debug] Response data: {data}")
        return [row["document_text"] for row in data if "document_text" in row and row["document_text"]]
      else:
        text = await resp.text()
        #print(f"[Supabase Debug] Error response: {text}")
        return []

async def get_document_types() -> List[str]:
  """
  Fetch all rows from 'document_type', returning only the 'name' column.
  """
  url = f"{SUPABASE_REST_URL}/document_type?select=name"
  # print(f"[Supabase Debug] Fetching document types from: {url}")
  async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=SUPABASE_HEADERS) as resp:
      # print(f"[Supabase Debug] Response status: {resp.status}")
      if resp.status == 200:
        data = await resp.json()
        # print(f"[Supabase Debug] Response data: {data}")
        return [row["name"] for row in data if "name" in row]
      else:
        text = await resp.text()
        # print(f"[Supabase Debug] Error response: {text}")
        raise Exception(f"Supabase error {resp.status}: {text}")

async def debug_list_document_types():
  url = f"{SUPABASE_REST_URL}/document?select=document_type"
  # print(f"[Supabase Debug] Fetching all document_type values from: {url}")
  async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=SUPABASE_HEADERS) as resp:
      # print(f"[Supabase Debug] Response status: {resp.status}")
      if resp.status == 200:
        data = await resp.json()
        # print("[Supabase Debug] All document_type values in document table:")
        unique_types = set()
        for row in data:
          doc_type = row.get('document_type')
          # print(f"  - {doc_type!r}")
          if doc_type:
            unique_types.add(doc_type)
        unique_list = list(unique_types)
        # print(f"[Supabase Debug] Unique document_type values: {unique_list}")
        return unique_list
      else:
        text = await resp.text()
        # print(f"[Supabase Debug] Error response: {text}")
        return []

async def get_template_for_agent(agent_name: str) -> Optional[str]:
  """
  Given an agent_name, map to the correct template name, query 'document' table for a matching 'name',
  and return the 'document_text' if found.
  """
  template_name = AGENT_TEMPLATE_MAP.get(agent_name)
  #print(f"[Supabase Debug] Agent: {agent_name}, Template name: {template_name}")
  if not template_name:
    #print("[Supabase Debug] No template mapping found for agent.")
    return None
  # Query document table for the template using ILIKE for case-insensitive match
  url = f"{SUPABASE_REST_URL}/document?document_type=ilike.{template_name}&select=document_text"
  #print(f"[Supabase Debug] Fetching template from: {url}")
  async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=SUPABASE_HEADERS) as resp:
      #print(f"[Supabase Debug] Response status: {resp.status}")
      if resp.status == 200:
        data = await resp.json()
        #print(f"[Supabase Debug] Response data: {data}")
        if data and "document_text" in data[0]:
          #print(f"[Supabase Debug] Found template text.")
          return data[0]["document_text"]
        #print(f"[Supabase Debug] No template found in document table.")
        return None
      else:
        text = await resp.text()
        #print(f"[Supabase Debug] Error response: {text}")
        raise Exception(f"Supabase error {resp.status}: {text}")
