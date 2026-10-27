from pathlib import Path
from dotenv import load_dotenv
import os
import sys

load_dotenv(Path(__file__).with_name(".env"))

api_key = os.getenv("API_KEY")
sec_user_agent = os.getenv("SEC_USER_AGENT")

if not api_key or api_key == "paste-here":
      print("Error: API_KEY is missing or still a placeholder.", file=sys.stderr)
      sys.exit(1)

if not sec_user_agent or "[your full name]" in sec_user_agent:
      print("Error: SEC_USER_AGENT is missing or still a placeholder.", file=sys.stderr)
      sys.exit(1)

print(f"{api_key[:4]}...")
print(sec_user_agent)