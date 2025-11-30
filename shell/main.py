import os
import sys
import readline

from completer import setup_readline, BUILTINS
import parser
import commands as cmds

setup_readline(readline)
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

        length = readline.get_current_history_length()
        if length == 0 or readline.get_history_item(length) != stripped_line:
            readline.add_history(stripped_line)

        cmds.command_history.append(stripped_line)

        tokens = parser.shell_tokenize(stripped_line)
        if not tokens:
            continue

        cmd_tokens, stdout_file, stderr_file, append_stdout, append_stderr = parser.split_redirection(tokens)
        if not cmd_tokens:
            continue

        if '|' in cmd_tokens:
            cmds.run_pipeline(cmd_tokens)
            continue

        command = cmd_tokens[0]

        if stdout_file is not None or stderr_file is not None:
            cmds.run_with_redirection(cmd_tokens, stdout_file, stderr_file,
                                      append_stdout, append_stderr, set(BUILTINS))
            continue

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
        else:
            cmds.run_external_command(cmd_tokens)


if __name__ == "__main__":
    main()
