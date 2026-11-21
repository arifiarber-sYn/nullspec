# Specs first

Wrote the diary-index spec before the code: requirements with acceptance criteria,
a design section naming the modules and the SQLite schema, and a task ledger with
eight checkboxes. Keeping the ledger in git means the plan cannot drift silently.

The spec-guard hook blocks an edit that would leave a spec invalid, so a half-written
requirements file fails loudly instead of quietly becoming the source of truth.
