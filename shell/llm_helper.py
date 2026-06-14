import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _call_gemini(system_prompt: str, user_prompt: str, temperature: float = 0.0, model: str | None = None):
    model = model or DEFAULT_GEMINI_MODEL
    content = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"
    resp = client.models.generate_content(
        model=model,
        contents=content,
    )
    return getattr(resp, "text", str(resp))

def generate_shell_command(natural_language_query: str):
    system = (
        "You are a Command line translate engine.\n"
        "Rules:\n"
        "1. Output ONLY the raw powershell command. No markdown, no explanations, no quotes.\n"
        "2. If the user asks to do something dangerous, generate the command anyway (user will verify).\n"
        "3. Do not say 'Here is the command'. Just the command string."
    )
    current_os = os.name
    current_dir = os.getcwd()
    user = (
        f"Target OS: {'Shell' if current_os == 'nt' else 'Unix/Linux'}\n"
        f"Current Directory: {current_dir}\n"
        f"Request: {natural_language_query}"
    )
    try:
        response = _call_gemini(system, user, temperature=0.0)
        return response.strip()
    except Exception as e:
        return f"Error generating command: {e}"

# Doctor mode
def analyze_error(last_command: str, error_message: str):
    system = "You are a Shell Debugger. The user ran a command that failed. Explain why it failed and provide the corrected command."
    user = f"Command: {last_command}\nError Output: {error_message}\n\nProvide the fix."
    try:
        return _call_gemini(system, user, temperature=0.0).strip()
    except Exception as e:
        return f"Error generating analysis: {e}"

# Agent Mode
def generate_multi_step_plan(natural_language_query: str):
    system = (
        "You are an Autonomous Shell Agent.\n"
        "The user has a complex request. Generate a list of shell commands to execute it.\n"
        "Rules:\n"
        "1. Return ONLY the commands, one per line.\n"
        "2. No markdown, no numbering.\n"
        "3. Example:\n"
        "   mkdir my_project\n"
        "   cd my_project\n"
        "   touch main.py"
    )
    user = natural_language_query
    try:
        response = _call_gemini(system, user, temperature=0.0)
        return [cmd.strip() for cmd in response.split('\n') if cmd.strip()]
    except Exception:
        return []

# Chat with File
def chat_with_file(filename: str, question: str):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"

    system = "You are a Code Assistant. Answer the question based on the file content provided."
    user = f"File Content:\n{content}\n\nQuestion: {question}"
    try:
        return _call_gemini(system, user, temperature=0.0).strip()
    except Exception as e:
        return f"Error generating answer: {e}"


if __name__ == "__main__":
    # Quick smoke tests for the Gemini-backed helpers.
    print(generate_shell_command("create a file"))
    print(analyze_error("ls -z", "ls: invalid option -- 'z'"))
    print(generate_multi_step_plan(
        "Generate a Python script that scrapes the top 10 GitHub repositories "
        "for machine learning and save them in a CSV file."
    ))
    print(chat_with_file("commands.py", "Can you describe the command history saving logic?"))