import os
import sys
import subprocess
import completer

# Shared history state
command_history = []
last_saved_index = 0

def save_history():
    """Writes the in-memory command history to HISTFILE upon exit."""
    histfile = os.environ.get("HISTFILE")
    if histfile:
        try:
            with open(histfile, 'w') as f:
                for cmd in command_history:
                    f.write(cmd + '\n')
        except Exception as e:
            print(f"Error saving history: {e}", file=sys.stderr)

def execute_history(tokens=None):
    global last_saved_index

    # Check flags
    if tokens and len(tokens) > 1:
        flag = tokens[1]
        
        if flag == "-r":
            if len(tokens) < 3:
                print("history: -r: filename argument required", file=sys.stderr)
                return
            history_file_path = tokens[2]
            try:
                with open(history_file_path, 'r') as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped:
                            command_history.append(stripped)
                last_saved_index = len(command_history)
            except FileNotFoundError:
                print(f"history: {history_file_path}: No such file or directory", file=sys.stderr)
            except Exception as e:
                print(f"history: {history_file_path}: {e}", file=sys.stderr)
            return

        if flag == "-w":
            if len(tokens) < 3:
                print("history: -w: filename argument required", file=sys.stderr)
                return
            history_file_path = tokens[2]
            try:
                with open(history_file_path, 'w') as f:
                    for cmd in command_history:
                        f.write(cmd + '\n')
                last_saved_index = len(command_history)
            except Exception as e:
                print(f"history: {history_file_path}: {e}", file=sys.stderr)
            return

        if flag == "-a":
            if len(tokens) < 3:
                print("history: -a: filename argument required", file=sys.stderr)
                return
            history_file_path = tokens[2]
            try:
                with open(history_file_path, 'a') as f:
                    for i in range(last_saved_index, len(command_history)):
                        f.write(command_history[i] + '\n')
                last_saved_index = len(command_history)
            except Exception as e:
                print(f"history: {history_file_path}: {e}", file=sys.stderr)
            return

    # Handle 'history [n]'
    n = None
    if tokens and len(tokens) > 1:
        try:
            n = int(tokens[1])
        except ValueError:
            print(f"history: {tokens[1]}: numeric argument required", file=sys.stderr)
            return

    total_count = len(command_history)
    start_index = 0
    
    if n is not None:
        start_index = max(0, total_count - n)

    for i in range(start_index, total_count):
        cmd = command_history[i]
        print(f"{i + 1:4}  {cmd}")

def execute_echo(tokens):
    if len(tokens) <= 1:
        print()
        return
    output = " ".join(tokens[1:])
    print(output)

def handle_cd(tokens):
    if len(tokens) < 2:
        return
    target = tokens[1]
    if target == "~":
        home = os.environ.get("HOME")
        if home:
            try:
                os.chdir(home)
            except Exception as e:
                print(f"cd: {home}: {e}")
        else:
            print("cd: HOME not set")
    else:
        try:
            os.chdir(target)
        except FileNotFoundError:
            print(f"cd: {target}: No such file or directory")
        except NotADirectoryError:
            print(f"cd: {target}: Not a directory")
        except PermissionError:
            print(f"cd: {target}: Permission denied")

def handle_type(tokens, builtins):
    if len(tokens) < 2:
        print("type: missing operand")
        return
    cmd_to_check = tokens[1]
    if cmd_to_check in builtins:
        print(f"{cmd_to_check} is a shell builtin")
    else:
        path_env = os.environ.get("PATH", "")
        found = False
        for directory in path_env.split(os.pathsep):
            candidate = os.path.join(directory, cmd_to_check)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                print(f"{cmd_to_check} is {candidate}")
                found = True
                break
        if not found:
            print(f"{cmd_to_check}: not found")

def run_builtin_in_pipeline(cmd_tokens, builtins, input_fd, output_fd):
    saved_stdin_fd = os.dup(sys.stdin.fileno())
    saved_stdout_fd = os.dup(sys.stdout.fileno())

    try:
        if input_fd != sys.stdin.fileno():
            os.dup2(input_fd, sys.stdin.fileno())
        
        if output_fd != sys.stdout.fileno():
            os.dup2(output_fd, sys.stdout.fileno())

        cmd = cmd_tokens[0]
        try:
            if cmd == "echo":
                execute_echo(cmd_tokens)
            elif cmd == "pwd":
                print(os.getcwd())
            elif cmd == "cd":
                handle_cd(cmd_tokens)
            elif cmd == "type":
                handle_type(cmd_tokens, builtins)
            elif cmd == "exit":
                save_history()  # Save history before exiting
                sys.exit(0)
            elif cmd == "history":
                execute_history(cmd_tokens)
        except Exception as e:
            print(f"Error in builtin {cmd}: {e}", file=sys.stderr)

    finally:
        os.dup2(saved_stdin_fd, sys.stdin.fileno())
        os.dup2(saved_stdout_fd, sys.stdout.fileno())
        os.close(saved_stdin_fd)
        os.close(saved_stdout_fd)

def run_pipeline(cmd_tokens):
    commands = []
    current = []
    for token in cmd_tokens:
        if token == '|':
            commands.append(current)
            current = []
        else:
            current.append(token)
    if current:
        commands.append(current)

    builtins = set(completer.BUILTINS)
    n = len(commands)
    procs = []
    pipe_fds = []

    for _ in range(n - 1):
        r, w = os.pipe()
        pipe_fds.append((r, w))

    for i, cmd in enumerate(commands):
        is_builtin = cmd[0] in builtins
        
        if i == 0:
            stdin_fd = sys.stdin.fileno()
        else:
            stdin_fd = pipe_fds[i - 1][0]

        if i == n - 1:
            stdout_fd = sys.stdout.fileno()
        else:
            stdout_fd = pipe_fds[i][1]

        if is_builtin:
            run_builtin_in_pipeline(cmd, builtins, stdin_fd, stdout_fd)
        else:
            exe_path = completer.resolve_executable(cmd[0])
            if exe_path is None:
                print(f"{cmd[0]}: command not found", file=sys.stderr)
            else:
                p_in = stdin_fd if stdin_fd != sys.stdin.fileno() else None
                p_out = stdout_fd if stdout_fd != sys.stdout.fileno() else None
                try:
                    proc = subprocess.Popen(cmd, executable=exe_path, stdin=p_in, stdout=p_out)
                    procs.append(proc)
                except Exception as e:
                    print(f"Failed to start {cmd[0]}: {e}", file=sys.stderr)

        if i > 0:
            os.close(pipe_fds[i - 1][0])
        if i < n - 1:
            os.close(pipe_fds[i][1])

    for proc in procs:
        proc.wait()

def run_with_redirection(cmd_tokens, stdout_file, stderr_file, append_stdout, append_stderr, builtins):
    command = cmd_tokens[0]
    stdout_f = None
    stderr_f = None
    try:
        if stdout_file is not None:
            stdout_mode = "a" if append_stdout else "w"
            stdout_f = open(stdout_file, stdout_mode)
        if stderr_file is not None:
            stderr_mode = "a" if append_stderr else "w"
            stderr_f = open(stderr_file, stderr_mode)

        if command in builtins:
            run_builtin_with_redirection(cmd_tokens, builtins, stdout_f, stderr_f)
        else:
            run_external_with_redirection(cmd_tokens, stdout_f, stderr_f)
    except OSError as e:
        print(f"{stdout_file or stderr_file}: {e}", file=sys.stderr)
    finally:
        if stdout_f is not None:
            stdout_f.close()
        if stderr_f is not None:
            stderr_f.close()

def run_builtin_with_redirection(cmd_tokens, builtins, stdout_f, stderr_f):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    if stdout_f is not None:
        sys.stdout = stdout_f
    if stderr_f is not None:
        sys.stderr = stderr_f
    try:
        cmd = cmd_tokens[0]
        if cmd == "echo":
            execute_echo(cmd_tokens)
        elif cmd == "pwd":
            print(os.getcwd())
        elif cmd == "cd":
            handle_cd(cmd_tokens)
        elif cmd == "type":
            handle_type(cmd_tokens, builtins)
        elif cmd == "exit":
            save_history()
            sys.exit(0)
        elif cmd == "history":
            execute_history(cmd_tokens)
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

def run_external_with_redirection(cmd_tokens, stdout_f, stderr_f):
    exe_name = cmd_tokens[0]
    exe_path = completer.resolve_executable(exe_name)
    if exe_path is None:
        print(f"{exe_name}: command not found", file=sys.stderr)
        return
    try:
        subprocess.run(
            cmd_tokens,
            executable=exe_path,
            stdout=stdout_f if stdout_f is not None else None,
            stderr=stderr_f if stderr_f is not None else None,
        )
    except Exception as e:
        print(f"{exe_name}: failed to execute: {e}", file=sys.stderr)

def run_external_command(tokens):
    exe_name = tokens[0]
    exe_path = completer.resolve_executable(exe_name)
    if exe_path is None:
        print(f"{exe_name}: command not found")
        return
    try:
        subprocess.run(tokens, executable=exe_path)
    except Exception as e:
        print(f"{exe_name}: failed to execute: {e}")

def run_capturing(tokens):
    """Run an external command, echo its output, and return (returncode, stderr).

    Used by 'doctor' mode so the captured error text can be sent for analysis.
    """
    exe_name = tokens[0]
    exe_path = completer.resolve_executable(exe_name)
    if exe_path is None:
        message = f"{exe_name}: command not found"
        print(message, file=sys.stderr)
        return None, message
    try:
        result = subprocess.run(tokens, executable=exe_path, capture_output=True, text=True)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return result.returncode, result.stderr
    except Exception as e:
        message = f"{exe_name}: failed to execute: {e}"
        print(message, file=sys.stderr)
        return None, message
