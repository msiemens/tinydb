# Crash-safety work on this fork

This is a fork of [msiemens/tinydb](https://github.com/msiemens/tinydb) (MIT, by Markus Siemens
and contributors). Everything on `master` is upstream code. Work for this project lives on the
`crash-safety` branch.

## Goal

Make TinyDB survive `kill -9` at any moment without changing its public API.

## Planned milestones

1. Kill-test harness: a child process doing random writes is killed at random points; the parent
   reopens the file and checks it against an in-memory model of acknowledged writes.
2. Atomic writes for `JSONStorage` (write to a temp file, fsync, rename), so the harness passes
   for single operations.
3. Write-ahead log storage, with replay and truncation on open.
4. Multi-document transactions (`with db.transaction(): ...`) that apply fully or not at all.
5. Secondary indexes on fields, kept in sync with inserts, updates and removes.
6. Local dashboard page with kill-test tallies and indexed vs. full-scan timings.

## Success bar

- 1,000 random `kill -9` tests never corrupt data or half-apply a transaction.
- TinyDB's existing test suite passes unchanged (baseline on this fork: 227 passed, 1 skipped).
- Indexed queries run at least 50x faster than full scans on a 100,000-document table.
