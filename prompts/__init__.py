import os

PROMPT_DIR = os.path.dirname(__file__)

def load_prompt(prompt_filename: str) -> str:
  """
  Loads a prompt file from the prompts directory.
  Raises FileNotFoundError if the file does not exist.
  """
  prompt_path = os.path.join(PROMPT_DIR, prompt_filename)
  with open(prompt_path, "r", encoding="utf-8") as f:
    return f.read()
