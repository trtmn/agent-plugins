Undo a promotion that the self-improvement pipeline made. Usage: `/self-improvement:revert <PROMO-hex>` (e.g. `/self-improvement:revert PROMO-a3f7c1`).

Run the revert script and show its output:

```bash
bash ~/.claude/self-improvement/revert.sh <PROMO-hex>
```

The script:
1. Looks up the `[PROMO-<hex>]` entry in `~/.learnings/CHANGELOG.md` to find the target CLAUDE.md, section, and exact promoted text.
2. Removes that promoted block from the target CLAUDE.md.
3. Appends a `[REVERT-<hex>]` entry to `~/.learnings/CHANGELOG.md` (append-only — the original PROMO entry is never edited or deleted).

If `<PROMO-hex>` isn't found, or the promoted text can no longer be located verbatim in the target file (it was hand-edited since), the script reports that and makes no changes — re-run with the exact PROMO id, or remove the text manually and add a REVERT note yourself.

If no argument is given, list the most recent `[PROMO-<hex>]` entries from the CHANGELOG so I can pick one.
