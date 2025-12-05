import os 
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


os.environ["AZURE_OPENAI_API_KEY"] = "xxxx"
model = AzureChatOpenAI(
    azure_endpoint="xxxxx",
    azure_deployment="gpt-4o",
    openai_api_version="2024-08-01-preview",
    temperature = 0.0,
)

def generate_shell_command(natural_language_query):
    if not model:
        return "Error: LLM model is not initialized."
    current_os = os.name 
    current_dir = os.getcwd()
    prompt = ChatPromptTemplate.from_messages([
        ("system","""You are a Command line translate engine.
         Target OS:{os_name}
         Current Directory:{dir_path}
         Rules:
        1. Output ONLY the raw shell command. No markdown, no explanations, no quotes.
        2. If the user asks to do something dangerous, generate the command anyway (user will verify).
        3. Do not say "Here is the command". Just the command string."""),
        ("user", "{query}")
    ])
    chain = prompt | model | StrOutputParser()
    try:
        response = chain.invoke({
            "os_name": "Shell" if current_os == 'nt' else "Unix/Linux",
            "dir_path": current_dir,
            "query": natural_language_query
        })
        return response.strip()
    except Exception as e:
        return f"Error generating command: {e}"
# Example usage:
print(generate_shell_command("create a file "))

# Doctor mode
def analyze_error(last_command,error_message):
    if not model:
        return "Error: LLM model is not initialized."
    prompt = ChatPromptTemplate.from_messages([
         ("system", "You are a Shell Debugger. The user ran a command that failed. Explain why it failed and provide the corrected command."),
        ("user", "Command: {cmd}\nError Output: {err}\n\nProvide the fix.")
    ])
    chain =  prompt | model | StrOutputParser()
    return chain.invoke({
        "cmd":last_command,
        "err":error_message
    })
# Example usage:
print(analyze_error("ls -z","ls: invalid option -- 'z'"))

# Agent Mode
def generate_multi_step_plan(natural_language_query):
    if not model: return []

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an Autonomous Shell Agent.
        The user has a complex request. Generate a list of shell commands to execute it.
        Rules:
        1. Return ONLY the commands, one per line.
        2. No markdown, no numbering.
        3. Example:
           mkdir my_project
           cd my_project
           touch main.py"""),
        ("user", "{query}")
    ])
    chain = prompt | model | StrOutputParser()
    response = chain.invoke({"query": natural_language_query})
    return [cmd.strip() for cmd in response.split('\n') if cmd.strip()]
# Example usage:
print(generate_multi_step_plan("Set up a new Python project with a virtual environment and a main.py file."))

# Chat with File 
def chat_with_file(filename,question):
    if not model:
        return "Error: LLM model is not initialized."
    with open(filename, 'r') as f:
        content = f.read()

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Code Assistant. Answer the question based on the file content provided."),
        ("user", "File Content:\n{content}\n\nQuestion: {q}")
    ])
    chain = prompt | model | StrOutputParser()
    return chain.invoke({"content":content,"q":question})
# Example usage:
print(chat_with_file("example.py","What does this file do?"))

