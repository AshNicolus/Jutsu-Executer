import os
import sys

# Expose builtin command names
BUILTINS = ["echo", "exit", "type", "pwd", "cd", "history"]

last_prefix = None
tab_press_count = 0

def get_executable_matches(prefix):
    matches = []
    path_env = os.environ.get("PATH", "")
    seen = set()

    for cmd in BUILTINS:
        if cmd.startswith(prefix):
            matches.append(cmd)
            seen.add(cmd)

    for directory in path_env.split(os.pathsep):
        if not os.path.isdir(directory):
            continue
        try:
            for filename in os.listdir(directory):
                if filename.startswith(prefix) and filename not in seen:
                    full_path = os.path.join(directory, filename)
                    if os.access(full_path, os.X_OK) and not os.path.isdir(full_path):
                        matches.append(filename)
                        seen.add(filename)
        except PermissionError:
            continue

    return sorted(matches)

def longest_common_prefix(strs):
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if prefix == "":
                return ""
    return prefix

def resolve_executable(exe_name):
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        candidate = os.path.join(directory, exe_name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None

def completer(text, state):
    global last_prefix, tab_press_count

    if state == 0:
        if text != last_prefix:
            tab_press_count = 0
            last_prefix = text
        tab_press_count += 1

        matches = get_executable_matches(text)

        if not matches:
            completer.matches = []
            return None

        if len(matches) == 1:
            completer.matches = [matches[0] + " "]
            tab_press_count = 0
        else:
            lcp = longest_common_prefix(matches)
            if lcp != text:
                completer.matches = [lcp]
            else:
                if tab_press_count == 1:
                    sys.stdout.write('\a')
                    sys.stdout.flush()
                    completer.matches = []
                elif tab_press_count == 2:
                    sys.stdout.write('\n')
                    sys.stdout.write('  '.join(matches) + '\n')
                    sys.stdout.write(f"$ {text}")
                    sys.stdout.flush()
                    completer.matches = []
                else:
                    tab_press_count = 0
                    completer.matches = []

    if state < len(completer.matches):
        return completer.matches[state]
    return None

def setup_readline(readline_module):
    """Configure the given readline module with the shell completer."""
    readline_module.set_completer(completer)
    try:
        readline_module.parse_and_bind("tab: complete")
    except Exception:
        # Some readline implementations raise on parse_and_bind; ignore.
        pass
