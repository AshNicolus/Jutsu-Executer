# Jutsu-Executer

A small Python interactive shell with optional AI commands backed by Google Gemini.

The shell is a simple REPL. It supports a set of builtins, pipelines, redirection, tab completion, and command history. It also adds four AI commands. You can translate plain English into a shell command, ask a question about a file, run a multi-step plan, and diagnose a command that failed.

## Project layout

All source lives in the `shell/` folder, split into separate modules:

- `main.py`: the REPL and command dispatch. This is the entry point.
- `completer.py`: tab completion and PATH lookup. Exposes `setup_readline`, `BUILTINS`, and `AI_COMMANDS`.
- `parser.py`: tokenizer and redirection parsing (`shell_tokenize`, `split_redirection`).
- `commands.py`: builtins and command execution (history, echo, cd, type, pipelines, redirection, external commands).
- `llm_helper.py`: the Gemini functions used by the AI commands.

## Features

Shell:

- Builtins: `echo`, `exit`, `type`, `pwd`, `cd`, `history`.
- Tab completion for builtins, AI commands, and executables on `PATH`.
- Tokenization with single and double quotes, escapes, pipes (`|`), and redirection (`>`, `>>`, `2>`, `2>>`).
- Pipelines and external command execution through `subprocess`.
- In-memory history with optional `HISTFILE` persistence and `history -w|-r|-a`.

AI commands (require a Gemini API key):

- `ai <request>`: translate plain English into a shell command. The command is shown and you confirm before it runs.
- `ask <file> <question>`: ask a question about the contents of a file.
- `agent <goal>`: generate a multi-step plan, show it, confirm, then run each step.
- `doctor <command>`: run a command and, if it fails, explain why and suggest a fix.

Auto-doctor: when any external command exits with a non-zero status, the shell explains the failure and suggests a fix on its own, the same as running `doctor` by hand. Set `JUTSU_AUTO_DOCTOR=0` to turn it off.

If the API key is missing, the shell still runs. The AI commands report that they are unavailable.

## Setup

1. Create and activate a virtual environment:

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```pwsh
pip install -r requirements.txt
```

On Windows the standard library `readline` module is often missing. If you hit completion or parsing issues, install `pyreadline3`:

```pwsh
pip install pyreadline3
```

3. Add your Gemini API key to a `.env` file in the project root:

```
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.5-flash
```

The `.env` file is gitignored, so the key is not committed. You can get a key from Google AI Studio. `GEMINI_MODEL` is optional and defaults to `gemini-2.5-flash`.

## Running

Run the shell from the project root:

```pwsh
python .\shell\main.py
```

## Examples

Run a builtin:

```text
$ echo Hello world
Hello world
```

Pipe and redirect:

```text
$ echo "one\ntwo" | grep one > out.txt
```

Translate plain English into a command:

```text
$ ai create an empty file called notes.txt
New-Item -ItemType File -Name "notes.txt"
Run this command? [y/N] y
```

Ask about a file:

```text
$ ask commands.py what does save_history do
```

Run a multi-step plan:

```text
$ agent set up a new python project named demo
```

Diagnose a failing command:

```text
$ doctor python --badflag
```

## Notes

- The shell covers a subset of POSIX shell behavior, not the full set. It is meant for simple scripting and experimentation. Variable expansion, globbing, and operators like `&&` and `||` are not supported.
- On Windows, bare command names resolve through `PATHEXT`, so `git` finds `git.exe`. Scripts such as `.bat` and `.cmd` may not run the same way as `.exe` files.
- The `ai` and `agent` commands can produce commands that change or delete files. Read what is suggested before you confirm.

## License

MIT. See [LICENSE](LICENSE).
