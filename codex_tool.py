import os
import sys
import json
from pathlib import Path

# Try importing dependencies, or provide helpful guidance
try:
    from openai import OpenAI
    from dotenv import load_dotenv
except ImportError:
    print("\n[!] Missing required packages. Please install them by running:")
    print("    pip install openai python-dotenv\n")
    sys.exit(1)

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your_openai_api_key_here":
    print("\n[!] OPENAI_API_KEY is missing or not set in your .env file.")
    print("    Please open .env and add your valid OpenAI API key.\n")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# Define filesystem tools for the model
tools = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or overwrite an existing file with given content",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Name or relative path of the file"},
                    "content": {"type": "string", "description": "The full text content to write into the file"},
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the current workspace directory",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

def execute_tool(func_name, args):
    if func_name == "write_file":
        filename = args.get("filename")
        content = args.get("content", "")
        filepath = Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        print(f"  [+] Created/Updated: {filename}")
        return json.dumps({"status": "success", "file": filename})
    elif func_name == "list_files":
        files = [p.name for p in Path(".").iterdir()]
        return json.dumps({"files": files})
    return json.dumps({"error": f"Unknown function: {func_name}"})

def main():
    if len(sys.argv) < 2:
        prompt = input("What would you like Codex / OpenAI to create or do? > ").strip()
    else:
        prompt = " ".join(sys.argv[1:])

    if not prompt:
        print("No prompt provided. Exiting.")
        return

    print(f"\n[Codex Agent] Processing: '{prompt}'...")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AI assistant that creates and manages project files. "
                "When asked to create files or code, always use the write_file tool to write "
                "the files directly to disk."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            execute_tool(fn_name, fn_args)
        print("\n[Codex Agent] Done! Requested file(s) have been generated on disk.\n")
    else:
        print(f"\n[Codex Response]:\n{message.content}")

if __name__ == "__main__":
    main()
