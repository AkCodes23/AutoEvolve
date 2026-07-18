# JOURNAL

Append one row per experiment, newest at the bottom. Never rewrite history. Re-read this
before proposing the next change. The `signal` column is whatever tells "better" for the
task: a number, a red-to-green test count, or an acceptance check. `status` is `keep` or
`revert` (a crashed or broken run is a `revert`, with the reason in `why`).

```
commit  | signal              | status | what changed                     | why
------- | ------------------- | ------ | -------------------------------- | -----------------------------
9f3a1c2 | tests 12->13 green  | keep   | example row (delete me)          | shows the format
```
