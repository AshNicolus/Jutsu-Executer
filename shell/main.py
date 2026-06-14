import os
import sys
import readline

from completer import setup_readline, BUILTINS
import parser
import commands as cmds

# The LLM helper is optional: if google-genai or the API key are missing,
# the shell still works as a plain shell and the AI commands report that
# they are unavailable.
try:
    import llm_helper
except Exception as e:  # pragma: no cover - import-time environment issue
    llm_helper = None
    _llm_import_error = e

setup_readline(readline)


def handle_ask(cmd_tokens):
    if llm_helper is None:
        print("ask: LLM helper unavailable (is GEMINI_API_KEY set?)")
        return
    if len(cmd_tokens) < 3:
        print("ask: usage: ask <file> <question>")
        return
    filename = cmd_tokens[1]
    question = " ".join(cmd_tokens[2:])
    print(llm_helper.chat_with_file(filename, question))


def handle_agent(cmd_tokens):
    if llm_helper is None:
        print("agent: LLM helper unavailable (is GEMINI_API_KEY set?)")
        return
    goal = " ".join(cmd_tokens[1:]).strip()
    if not goal:
        print("agent: usage: agent <goal>")
        return
    plan = llm_helper.generate_multi_step_plan(goal)
    if not plan:
        print("agent: could not generate a plan")
        return
    print("Planned commands:")
    for step in plan:
        print(f"  {step}")
    try:
        confirm = input("Execute this plan? [y/N] ").strip().lower()
    except EOFError:
        print()
        return
    if confirm not in ("y", "yes"):
        return
    for step in plan:
        print(f"$ {step}")
        run_line(step)


def handle_doctor(cmd_tokens):
    if llm_helper is None:
        print("doctor: LLM helper unavailable (is GEMINI_API_KEY set?)")
        return
    if len(cmd_tokens) < 2:
        print("doctor: usage: doctor <command>")
        return
    target = cmd_tokens[1:]
    returncode, error_output = cmds.run_capturing(target)
    if returncode == 0:
        print("doctor: command succeeded, nothing to diagnose")
        return
    print("--- diagnosis ---")
    print(llm_helper.analyze_error(" ".join(target), error_output or ""))


def run_line(stripped_line):
    tokens = parser.shell_tokenize(stripped_line)
    if not tokens:
        return

    cmd_tokens, stdout_file, stderr_file, append_stdout, append_stderr = parser.split_redirection(tokens)
    if not cmd_tokens:
        return

    if '|' in cmd_tokens:
        cmds.run_pipeline(cmd_tokens)
        return

    command = cmd_tokens[0]

    if stdout_file is not None or stderr_file is not None:
        cmds.run_with_redirection(cmd_tokens, stdout_file, stderr_file,
                                  append_stdout, append_stderr, set(BUILTINS))
        return

    if command == "echo":
        cmds.execute_echo(cmd_tokens)
    elif command == "exit":
        cmds.save_history()  # Save history on 'exit' command
        sys.exit(0)
    elif command == "type":
        cmds.handle_type(cmd_tokens, set(BUILTINS))
    elif command == "pwd":
        print(os.getcwd())
    elif command == "cd":
        cmds.handle_cd(cmd_tokens)
    elif command == "history":
        cmds.execute_history(cmd_tokens)
    elif command == "ask":
        handle_ask(cmd_tokens)
    elif command == "agent":
        handle_agent(cmd_tokens)
    elif command == "doctor":
        handle_doctor(cmd_tokens)
    else:
        cmds.run_external_command(cmd_tokens)


def main():
    # Load history from HISTFILE on startup
    histfile = os.environ.get("HISTFILE")
    if histfile and os.path.exists(histfile):
        try:
            with open(histfile, 'r') as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        cmds.command_history.append(stripped)
                        readline.add_history(stripped)
            cmds.last_saved_index = len(cmds.command_history)
        except Exception:
            pass

    while True:
        try:
            line = input("$ ")
        except EOFError:
            print()
            cmds.save_history()  # Save history on Ctrl+D (EOF)
            break

        stripped_line = line.strip()
        if not stripped_line:
            continue

        # AI translation: "ai <natural language>" -> a shell command the user
        # confirms before it runs. The generated command then flows through the
        # normal execution path below.
        if stripped_line == "ai" or stripped_line.startswith("ai "):
            if llm_helper is None:
                print("ai: LLM helper unavailable (is GEMINI_API_KEY set?)")
                continue
            query = stripped_line[3:].strip()
            if not query:
                print("ai: usage: ai <what you want to do>")
                continue
            suggested = llm_helper.generate_shell_command(query)
            print(suggested)
            try:
                confirm = input("Run this command? [y/N] ").strip().lower()
            except EOFError:
                print()
                continue
            if confirm not in ("y", "yes"):
                continue
            stripped_line = suggested

        length = readline.get_current_history_length()
        if length == 0 or readline.get_history_item(length) != stripped_line:
            readline.add_history(stripped_line)

        cmds.command_history.append(stripped_line)

        run_line(stripped_line)


if __name__ == "__main__":
    main()
