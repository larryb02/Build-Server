## Style Guide and Best Practices:
- Always avoid n + 1 database queries. Use subqueries, bulk inserts/updates, and other methods when acceptable
- Always end a file with a new line
- Always import modules at the top level -- no inline imports unless specifically requested or absolutely necessary

## Error Handling Philosophy: Fail Loud, Never Fake

Prefer a visible failure over a silent fallback.

- Never silently swallow errors to keep things "working."
  Surface the error. Don't substitute placeholder data.
- Fallbacks are acceptable only when disclosed. Show a
  banner, log a warning, annotate the output.
- Design for debuggability, not cosmetic stability.

Priority order:
1. Works correctly with real data
2. Falls back visibly — clearly signals degraded mode
3. Fails with a clear error message
4. Silently degrades to look "fine" — never do this
