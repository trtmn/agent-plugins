---
name: mastodon-cli
description: "Interact with Mastodon using the `toot` CLI — post statuses, read timelines, check notifications, search, follow/unfollow, boost, favourite, and manage your account. Use this skill whenever the user mentions Mastodon, tooting, fediverse, their timeline, mentions, boosts, favourites, followers, or anything related to social media posting on Mastodon. Also trigger when the user asks to check what's happening on social media, wants to share something publicly, asks about trending topics, or says things like 'post this', 'toot this', 'check my mentions', 'what's on my timeline', 'who followed me', or 'boost that'. Even casual references like 'share this on masto' or 'what's trending' should trigger this skill."
---

# Mastodon CLI via `toot`

The user has the `toot` CLI installed and authenticated against their Mastodon instance. Use `toot` for all Mastodon interactions. Never use browser automation or direct API calls.

## Safety: Confirm Before Visible Actions

Any action that is publicly visible or modifies state requires explicit confirmation from the user before executing. This includes:

- Posting a status (`toot post`)
- Boosting (`toot reblog`)
- Favouriting (`toot favourite`)
- Following/unfollowing
- Blocking/muting
- Deleting a status
- Pinning/unpinning

**Exception:** If the user explicitly tasks you to post (e.g., "post this to masto", "toot this out"), go ahead without a separate confirmation step — they already told you to do it.

Read-only actions (timelines, search, notifications, viewing profiles) never need confirmation.

## Command Reference

### Reading

| Task | Command |
|---|---|
| Home timeline | `toot timelines home` |
| Public/federated | `toot timelines public` |
| Local timeline | `toot timelines public --local` |
| Hashtag timeline | `toot timelines tag <hashtag>` |
| User's posts | `toot timelines account <account>` |
| Favourited posts | `toot timelines favourites` |
| Single status | `toot status <id>` |
| Thread | `toot thread <id>` |
| Notifications | `toot notifications` |
| Bookmarks | `toot bookmarks` |
| Search | `toot search "<query>"` (optionally `-t accounts\|statuses\|hashtags`) |

Add `--limit N` to control how many results come back (default 20, max 40). Add `--json` for machine-readable output when you need to process the data.

### Posting

```
toot post "Status text here"
```

Key flags:
- `-v public|unlisted|private|direct` — visibility (default: public)
- `-m <file>` — attach media (repeat for multiple)
- `-d "description"` — alt text for media (one per `-m`, always include for accessibility)
- `-s` — mark as sensitive
- `-p "CW text"` — content warning / spoiler
- `-r <status_id>` — reply to a status
- `-R` — reply to your last post (continue thread)
- `--scheduled-in "1h30m"` — schedule for later
- `-l en` — language code
- `--poll-option "A" --poll-option "B"` — create a poll

Character limit is 500. If the user's text is longer, let them know and offer to trim or split into a thread.

### Interactions

| Task | Command |
|---|---|
| Boost | `toot reblog <id>` |
| Unboost | `toot unreblog <id>` |
| Favourite | `toot favourite <id>` |
| Unfavourite | `toot unfavourite <id>` |
| Bookmark | `toot bookmark <id>` |
| Unbookmark | `toot unbookmark <id>` |
| Pin to profile | `toot pin <id>` |
| Unpin | `toot unpin <id>` |
| Delete | `toot delete <id>` |

### People

| Task | Command |
|---|---|
| View profile | `toot whois <account>` |
| Follow | `toot follow <account>` |
| Unfollow | `toot unfollow <account>` |
| Block | `toot block <account>` |
| Unblock | `toot unblock <account>` |
| Mute | `toot mute <account>` |
| Unmute | `toot unmute <account>` |
| List followers | `toot followers <account>` |
| List following | `toot following <account>` |
| Follow requests | `toot follow-requests` |

### Account & Instance

| Task | Command |
|---|---|
| Your profile | `toot whoami` |
| Instance info | `toot instance` |
| Manage lists | `toot lists` |
| Manage tags | `toot tags` |

## Tips

- When displaying timeline or notification output, present it cleanly — don't dump raw terminal escape codes. Summarize if there are many results.
- Status IDs are needed for replies, boosts, favourites, etc. When showing statuses, note the ID so the user can refer to it.
- For threads: use `toot post -R "next part"` to continue replying to your own last post rather than manually tracking IDs.
- Media uploads: `toot post -m image.png -d "A photo of..."` — always include alt text descriptions for accessibility.
- The `--json` flag on most commands gives structured output, useful when you need to extract specific data (e.g., getting a status ID from search results).
