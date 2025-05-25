# AIQA Backend V2

A FastAPI backend for orchestrating AI-powered agents, integrating with Supabase for document and template management, and supporting team-based context. The app is fully dockerizable and designed for extensibility.

---

## Project Overview

This backend serves as a router for multiple AI agents (e.g., User Story Creator, Test Case Creator, Automation Script Creator, etc.), handling user requests, file uploads, and dynamic context assembly. It fetches templates and documentation from Supabase, supports team-specific and global context, and can be run locally or in Docker.

---

## File & Directory Structure

- **main.py**  
  The FastAPI entrypoint. Handles all agent endpoints, request parsing, file uploads, context assembly, and routing to the MCP Server Router. Implements team-based logic and chunking for AI prompt limits.

- **utils.py**  
  Utility functions for environment variable management, prompt loading, chunking user messages, and sending requests to the MCP Server Router.

- **supabase_client.py**  
  All Supabase integration logic: fetches document types, templates, automation framework files, and supports team-based filtering for queries.

- **file_router.py**  
  Handles file upload and parsing logic for incoming requests.

- **prompts/**  
  Contains XML prompt files for each agent (e.g., user-story-creator.xml, test-case-creator.xml, anaylze_expert.xml, etc.).

- **supabase/**  
  Contains migration files and schema definitions for Supabase tables.

- **Dockerfile**  
  Docker build instructions for containerizing the app.

- **.dockerignore**  
  Specifies files and directories to exclude from the Docker build context.

- **requirements.txt**  
  Python dependencies for the backend.

---

## How To Customize

### Add a New Agent Endpoint

1. **Add the endpoint name** to the `ENDPOINTS` list in `main.py`.
2. **Create a prompt file** in `prompts/` (e.g., `prompts/my-new-agent.xml`).
3. **Update the agent_task_map** in `main.py` if the agent requires a custom task label.
4. **(Optional)**: Add any new Supabase logic to `supabase_client.py` if your agent needs custom document/template fetching.

### Remove an Agent Endpoint

1. **Remove the endpoint name** from the `ENDPOINTS` list in `main.py`.
2. **Delete the corresponding prompt file** from `prompts/`.
3. **Remove any custom logic** for the agent in `main.py` and `supabase_client.py`.

### Add/Remove Columns for Supabase Queries

1. **Update Supabase migrations** in `supabase/migrations/` to add/remove columns.
2. **Update query logic** in `supabase_client.py` to include/exclude the new columns in all relevant functions.
3. **If the column is used in context assembly**, update `main.py` to handle the new data.

### Modify Team-Based Logic

- All Supabase queries that fetch documentation/templates use the `team` column for filtering.  
- To change how team filtering works, update the relevant query construction in `supabase_client.py` and ensure `teamName` is passed from `main.py`.

### Add/Change Prompts

- Add new XML prompt files to `prompts/`.
- Update the `load_prompt` function in `utils.py` and the agent logic in `main.py` to use the new prompt.

### Dockerization & Environment Variables

- The app is dockerized via the `Dockerfile` and `.dockerignore`.
- Place your environment variables in a `.env` file (not included in the image by default).
- To build and run:
  ```
  docker build -t aiqa-backend .
  docker run --env-file .env -p 8000:8000 aiqa-backend
  ```

---

## Usage

- **Local Development**:  
  ```
  python3 -m venv venv
  source venv/bin/activate
  pip3 install -r requirements.txt
  uvicorn main:app --reload
  ```

- **Docker**:  
  See above.

- **Environment Variables**:  
  - Place all required variables (e.g., SUPABASE_URL, SUPABASE_ANON_KEY, CHUNKING_LIMIT, etc.) in a `.env` file.

---

## API Endpoints

- `POST /user-story-creator`
- `POST /acceptance-criteria-creator`
- `POST /test-case-creator`
- `POST /test-script-creator`
- `POST /test-data-creator`

Each endpoint accepts form data:
- `message`: The user message.
- `files`: (Optional) File uploads (single file only).
- `teamName`: (Optional) Team context.

---

## Example: Adding a New Supabase Column

1. Add the column to the relevant migration in `supabase/migrations/`.
2. Update all query functions in `supabase_client.py` that need to read/write the new column.
3. Update any context assembly logic in `main.py` if the new column is used in prompts.

---

## Example: Customizing Agent Logic

- To add a new agent, follow the steps in "Add a New Agent Endpoint".
- To change how context is assembled, modify the relevant section in `main.py`.
- To change how documents/templates are fetched, update `supabase_client.py`.

---
