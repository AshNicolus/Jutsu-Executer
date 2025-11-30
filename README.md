# Jutsu-Executer — shell

This folder contains a small Python-based interactive shell used by the Jutsu-Executer project. It was split into simple, focused modules to improve readability and maintainability.

## Files

- `main.py` — REPL orchestration and readline setup. The script is the entrypoint for running the shell.
- `completer.py` — tab-completion logic and PATH-based executable lookup. Exposes `setup_readline(readline_module)` and `BUILTINS`.
- `parser.py` — tokenizer and redirection parser: `shell_tokenize(line)` and `split_redirection(tokens)`.
- `commands.py` — builtins and command execution: history handling, `echo`, `cd`, `type`, pipeline handling, redirection, and running external commands.

## Features

- Basic builtins: `echo`, `exit`, `type`, `pwd`, `cd`, `history`.
- Tab completion for builtin names and executables on `PATH`.
- Command tokenization supporting single/double quotes, escapes, pipes (`|`) and simple redirections (`>`, `>>`, `2>`, `2>>`).
- Pipelines and running external commands using `subprocess`.
- In-memory command history with optional `HISTFILE` persistence.

## Quick start

1. Create and activate a virtual environment (recommended):

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. (Windows) Install a readline-compatible package if not available. On Windows, the stdlib `readline` is often missing; `pyreadline3` is a commonly used replacement:

```pwsh
pip install pyreadline3
```

3. Run the shell from the `shell` directory:

```pwsh
python .\main.py
```

If you run `python main.py` from inside the `shell` directory it will import the local modules directly. If you import the package from elsewhere, prefer running with the package context (e.g., `python -m shell.main`).

## Example usage

- Run an external command:

```text
$ ls -la
```

- Use a builtin:

```text
$ echo Hello world
Hello world
```

- Pipe commands and redirect output:

```text
$ echo "one\ntwo" | grep one > out.txt
```

- View history or save/load it via `HISTFILE` or the `history -w|-r|-a` flags.

## Notes and Windows tips

- On Windows the `readline` module may be missing. Installing `pyreadline3` usually provides equivalent features. If you run into completion/parsing differences on Windows, try running inside WSL/Unix-like environment.
- The shell is intentionally small and does not implement full POSIX shell semantics — it focuses on a subset useful for simple scripting and experimentation.

