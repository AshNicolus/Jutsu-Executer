def shell_tokenize(line):
    tokens = []
    i = 0
    current_token = ""
    in_single = False
    in_double = False

    while i < len(line):
        c = line[i]

        if in_single:
            if c == "'":
                in_single = False
            else:
                current_token += c
            i += 1
        elif in_double:
            if c == '"':
                in_double = False
                i += 1
            elif c == '\\' and i + 1 < len(line):
                next_char = line[i + 1]
                if next_char in ('"', '\\', '$', '`', '\n'):
                    current_token += next_char
                    i += 2
                else:
                    current_token += c
                    i += 1
            else:
                current_token += c
                i += 1
        else:
            if c == "'":
                in_single = True
                i += 1
            elif c == '"':
                in_double = True
                i += 1
            elif c == '\\' and i + 1 < len(line):
                next_char = line[i + 1]
                current_token += next_char
                i += 2
            elif c == '|':
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append("|")
                i += 1
            elif c.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                i += 1
            else:
                current_token += c
                i += 1
    if current_token:
        tokens.append(current_token)
    return tokens

def split_redirection(tokens):
    stdout_file = None
    stderr_file = None
    append_stdout = False
    append_stderr = False
    cmd_tokens = tokens[:]

    i = len(cmd_tokens) - 2
    while i >= 0:
        op = cmd_tokens[i]
        if op in (">", "1>") and i + 1 < len(cmd_tokens):
            stdout_file = cmd_tokens[i + 1]
            append_stdout = False
            cmd_tokens = cmd_tokens[:i]
            i -= 2
        elif op in (">>", "1>>") and i + 1 < len(cmd_tokens):
            stdout_file = cmd_tokens[i + 1]
            append_stdout = True
            cmd_tokens = cmd_tokens[:i]
            i -= 2
        elif op == "2>" and i + 1 < len(cmd_tokens):
            stderr_file = cmd_tokens[i + 1]
            append_stderr = False
            cmd_tokens = cmd_tokens[:i]
            i -= 2
        elif op == "2>>" and i + 1 < len(cmd_tokens):
            stderr_file = cmd_tokens[i + 1]
            append_stderr = True
            cmd_tokens = cmd_tokens[:i]
            i -= 2
        else:
            break

    return cmd_tokens, stdout_file, stderr_file, append_stdout, append_stderr
