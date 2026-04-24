---
name: youtube-data-api
description: "Query and manage YouTube channels, videos, playlists, and analytics using the YouTube Data API v3. Use this skill whenever the user mentions YouTube, their channel, video stats, subscriber counts, upload lists, playlists, video views, search results, or anything related to YouTube data. Trigger on phrases like 'check my YouTube', 'how are my videos doing', 'list my uploads', 'YouTube stats', 'video views', 'subscriber count', 'search YouTube for', 'my channel', or any reference to YouTube content management and analytics."
allowed-tools:
  - Bash(curl -s *:*)
  - Bash(python3 *:*)
---

# YouTube Data API v3

Query and manage YouTube channels, videos, playlists, comments, and search results via the YouTube Data API v3 using `curl`.

## Setup

### Getting an API Key (public data only)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services > Library**
4. Search for **YouTube Data API v3** and click **Enable**
5. Go to **APIs & Services > Credentials**
6. Click **Create Credentials > API Key**
7. (Recommended) Click the key to restrict it: under **API restrictions**, select **Restrict key** and choose **YouTube Data API v3**

An API key is sufficient for reading public data: channel info, public video stats, playlists, search, and comments. It does NOT support `mine=true` queries or any write operations.

### Setting Up OAuth 2.0 (private data and write access)

OAuth is required for:
- Querying your own channel with `mine=true`
- Uploading videos
- Managing playlists, captions, or channel settings
- Accessing YouTube Analytics or YouTube Reporting APIs
- Rating, commenting, or subscribing on behalf of a user

#### Create OAuth Credentials

1. In [Google Cloud Console](https://console.cloud.google.com/), go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. If prompted, configure the **OAuth consent screen** first:
   - Choose **External** (or Internal for Workspace orgs)
   - Fill in app name, support email, and developer contact
   - Add scopes (see below)
   - Add yourself as a test user (required while app is in "Testing" status)
4. For client type, choose **Desktop app** (best for CLI use)
5. Download the JSON file — save it as `client_secret.json`

#### OAuth Scopes

| Scope | Access |
|---|---|
| `youtube.readonly` | Read-only access to account, videos, playlists |
| `youtube` | Full read/write (manage videos, playlists, etc.) |
| `youtube.upload` | Upload videos only |
| `youtube.force-ssl` | Read/write, requires SSL (needed for comments, captions) |
| `yt-analytics.readonly` | YouTube Analytics read access |
| `yt-analytics-monetary.readonly` | Analytics including revenue data |

#### Authorize via gcloud

If you use `gcloud`, you can get an OAuth token with YouTube scopes:

```bash
gcloud auth application-default login \
  --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/youtube.readonly

# Then use the token:
TOKEN=$(gcloud auth application-default print-access-token)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"
```

#### Authorize via Python (standalone)

```python
# pip install google-auth-oauthlib google-api-python-client
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
credentials = flow.run_local_server(port=0)

youtube = build("youtube", "v3", credentials=credentials)
response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
print(response)
```

To persist credentials across sessions, save and reload them:

```python
import json
from google.oauth2.credentials import Credentials

# Save after first auth
with open("token.json", "w") as f:
    f.write(credentials.to_json())

# Reload later
credentials = Credentials.from_authorized_user_file("token.json", SCOPES)
```

### Configuration

Store your API key in an environment variable or config file:

```bash
# Environment variable
export YOUTUBE_API_KEY="your-api-key-here"

# Or a config file
echo "YOUTUBE_API_KEY=your-api-key-here" > ~/.config/youtube-api/.env
chmod 600 ~/.config/youtube-api/.env
source ~/.config/youtube-api/.env
```

On first use, check if the key is available. If not, ask the user how they'd like to provide it (env var, config file, secret manager, etc.).

All API key requests use: `&key=$YOUTUBE_API_KEY`
All OAuth requests use: `-H "Authorization: Bearer $TOKEN"`

## Base URL

```
https://www.googleapis.com/youtube/v3
```

## Quota

The YouTube Data API has a daily quota of **10,000 units** (default). Costs vary by endpoint:
- `list` operations: 1 unit
- `search`: 100 units (expensive — prefer other endpoints when possible)
- `insert` (upload, create playlist): 50 units
- `update` / `delete`: 50 units

Avoid unnecessary `search` calls. If you already have a channel ID, use `playlistItems.list` with the uploads playlist to get videos instead of searching.

## Endpoints Reference

### Channels

Get channel details by ID, handle, or username:

```bash
# By handle
curl -s "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails,brandingSettings&forHandle=HANDLE&key=$YOUTUBE_API_KEY"

# By channel ID
curl -s "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id=CHANNEL_ID&key=$YOUTUBE_API_KEY"

# Own channel (OAuth required)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&mine=true"
```

Key `part` values: `snippet` (title, description, thumbnails, country), `statistics` (viewCount, subscriberCount, videoCount), `contentDetails` (uploads playlist ID), `brandingSettings` (keywords, banner, trailer).

The uploads playlist ID is in `contentDetails.relatedPlaylists.uploads` — it's the channel ID with `UC` replaced by `UU`.

### Videos

Get video details by ID (up to 50 IDs per request):

```bash
curl -s "https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id=VIDEO_ID1,VIDEO_ID2&key=$YOUTUBE_API_KEY"
```

Key `part` values:
- `snippet` — title, description, publishedAt, channelId, tags, categoryId, thumbnails
- `statistics` — viewCount, likeCount, commentCount
- `contentDetails` — duration, dimension, definition, caption
- `status` — uploadStatus, privacyStatus, embeddable, license
- `topicDetails` — topic categories

### Playlist Items (Uploads)

List all videos in a playlist (including a channel's uploads):

```bash
# Get uploads playlist for a channel: replace UC with UU in channel ID
curl -s "https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails,snippet&playlistId=UPLOADS_PLAYLIST_ID&maxResults=50&key=$YOUTUBE_API_KEY"
```

Returns up to 50 items per page. Use `nextPageToken` to paginate:

```bash
curl -s "...&pageToken=NEXT_PAGE_TOKEN&key=$YOUTUBE_API_KEY"
```

Each item's `contentDetails.videoId` can be used with the Videos endpoint to get full stats.

### Playlists

List a channel's playlists:

```bash
curl -s "https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&channelId=CHANNEL_ID&maxResults=50&key=$YOUTUBE_API_KEY"
```

### Search

Search across YouTube (100 quota units per call — use sparingly):

```bash
# Search a specific channel's videos
curl -s "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=CHANNEL_ID&q=QUERY&type=video&order=viewCount&maxResults=25&key=$YOUTUBE_API_KEY"

# General YouTube search
curl -s "https://www.googleapis.com/youtube/v3/search?part=snippet&q=search+terms&type=video&maxResults=10&key=$YOUTUBE_API_KEY"
```

Filters: `type` (video, channel, playlist), `order` (date, rating, viewCount, relevance), `publishedAfter`/`publishedBefore` (ISO 8601), `videoDuration` (short, medium, long).

### Comments

List comments on a video:

```bash
curl -s "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId=VIDEO_ID&maxResults=100&order=relevance&key=$YOUTUBE_API_KEY"
```

Each thread's `snippet.topLevelComment.snippet` has: `textDisplay`, `authorDisplayName`, `likeCount`, `publishedAt`.

### Subscriptions (OAuth required)

```bash
# List authenticated user's subscriptions
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/youtube/v3/subscriptions?part=snippet&mine=true&maxResults=50"
```

### Video Categories

```bash
curl -s "https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode=US&key=$YOUTUBE_API_KEY"
```

## Common Patterns

**Get all videos with stats for a channel:**
```bash
# Step 1: Get channel info and uploads playlist ID
CHANNEL_ID="UC..."
UPLOADS_PLAYLIST=$(echo "$CHANNEL_ID" | sed 's/^UC/UU/')

# Step 2: Get all video IDs from uploads playlist
VIDEO_IDS=$(curl -s "https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId=$UPLOADS_PLAYLIST&maxResults=50&key=$YOUTUBE_API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(','.join(item['contentDetails']['videoId'] for item in data['items']))
")

# Step 3: Get full stats for all videos
curl -s "https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id=$VIDEO_IDS&key=$YOUTUBE_API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
videos = []
for item in data['items']:
    views = int(item['statistics'].get('viewCount', 0))
    title = item['snippet']['title']
    published = item['snippet']['publishedAt'][:10]
    videos.append((views, title, published))
videos.sort(reverse=True)
for views, title, pub in videos:
    print(f'{views:>10,}  {pub}  {title}')
"
```

**Paginate through large playlists (50+ items):**
```bash
python3 -c "
import json, os, urllib.request

API_KEY = os.environ['YOUTUBE_API_KEY']
PLAYLIST = 'UU...'
video_ids = []
page_token = ''

while True:
    url = f'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={PLAYLIST}&maxResults=50&key={API_KEY}'
    if page_token:
        url += f'&pageToken={page_token}'
    data = json.loads(urllib.request.urlopen(url).read())
    video_ids.extend(item['contentDetails']['videoId'] for item in data['items'])
    page_token = data.get('nextPageToken', '')
    if not page_token:
        break

print(f'Total videos: {len(video_ids)}')
print(','.join(video_ids))
"
```

**Compare video performance:**
```bash
curl -s "https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id=ID1,ID2,ID3&key=$YOUTUBE_API_KEY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data['items']:
    s = item['statistics']
    title = item['snippet']['title'][:50]
    print(f'{title:<50}  views={s[\"viewCount\"]:>8}  likes={s.get(\"likeCount\",\"?\"):>6}  comments={s.get(\"commentCount\",\"?\"):>5}')
"
```

## Error Handling

- **403 Forbidden / quotaExceeded** — daily quota exhausted. Wait until midnight Pacific Time for reset.
- **403 insufficientPermissions** — endpoint requires OAuth, not just an API key.
- **400 keyInvalid** — API key is wrong or the YouTube Data API is not enabled in the Google Cloud project.
- **404 videoNotFound / channelNotFound** — ID doesn't exist or content is private.
- **401 authError** — OAuth token is expired or invalid. Re-authenticate.

## Limitations

- **API key** — read-only access to public data. No `mine=true`, no write operations.
- **OAuth** — required for private data, write operations, and YouTube Analytics.
- **No real-time analytics** — for revenue, watch time, demographics, use the YouTube Analytics API (separate, requires OAuth with `yt-analytics.readonly` scope).
- **50 IDs per request** — batch video/channel lookups are capped at 50. Paginate for larger sets.
- **Search is expensive** — 100 quota units per call. Prefer `playlistItems` + `videos` when you already have a channel ID.
