# AGENTS.md

## Core Rules

1. **Do not guess.**
   - Verify assumptions by inspecting the relevant files, configuration, documentation, or runtime behavior.
   - If something cannot be verified, clearly state the uncertainty before implementing it.

2. **Always verify and test changes.**
   - Run the most relevant available checks after every implementation: tests, type checks, linters, builds, or focused runtime checks.
   - If no automated test exists, create a focused verification or explain exactly what was manually verified.
   - Do not claim a change works without actually verifying it.

3. **Read complete files before modifying them.**
   - Never make a change based on a snippet, partial output, or assumed file contents.
   - Read the entire relevant file first.
   - For files larger than the tool output limit, continue reading with offsets until the complete file has been inspected.
   - After editing, inspect the complete resulting file when practical and verify the diff.

4. **Do not use `grep` to read or search files.**
   - Use the `read` tool to read file contents.
   - Use `rg` for searches and pattern matching.
   - Do not use plain `grep`, `cat`, or partial `sed` output as a substitute for reading a file.

5. **Keep implementations modular.**
   - Split functionality into focused modules with clear responsibilities.
   - Avoid god files, oversized modules, hidden global state, and unrelated responsibilities in one file.
   - Prefer small, composable functions and explicit interfaces.
   - Before adding code to an existing module, consider whether the responsibility belongs in a new module.

## Workflow

1. Inspect the repository structure and relevant documentation.
2. Read every file that will be changed in full.
3. Identify existing patterns, dependencies, and available verification commands.
4. Implement the smallest modular change that solves the task.
5. Run relevant tests and checks.
6. Review the complete diff for accidental changes, regressions, and violations of these rules.
7. Report what was changed and what verification was performed.
