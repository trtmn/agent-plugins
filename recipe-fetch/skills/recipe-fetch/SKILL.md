---
name: recipe-fetch
description: >
  Fetch one or more recipes from URLs and save them as properly formatted Obsidian markdown notes
  in the user's vault. Use this skill whenever the user provides a recipe URL (or a list of URLs)
  and wants it saved to Obsidian — including requests like "save this recipe", "grab this recipe",
  "add to my cookbook", "fetch from this link", or any variation. When multiple URLs are given,
  dispatch them as parallel background agents so all fetch simultaneously. This skill knows exactly
  where images and recipe files live in the vault and handles image download, type verification,
  and format conversion automatically.
allowed-tools:
  - Bash(python3 *)
  - Bash(curl *)
  - Bash(file *)
  - Bash(sips *)
  - Bash(test *)
  - Bash(ls *)
  - WebFetch
  - Read
  - Write
---

# Recipe Fetch Skill

Fetch a recipe from one or more URLs and save to the Obsidian vault as correctly formatted markdown.

## Vault Paths

- **Vault root**: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>`
- **Recipe files**: `Recipes/<Recipe Title>.md`
- **Recipe images**: `Files/recipes/<kebab-case-title>.jpg`
- **Vault-relative image ref**: `Files/recipes/<kebab-case-title>.jpg`

## Handling Multiple URLs

When the user provides more than one URL, dispatch a **separate background agent per URL** in the same turn. Each agent runs this skill independently and saves its recipe. This lets all fetches happen simultaneously rather than one at a time.

## Per-Recipe Workflow

### 1. Extract recipe data (JSON-LD first, WebFetch fallback)

**Primary method — JSON-LD structured data (preferred):**

Most recipe sites embed machine-readable recipe data in `<script type="application/ld+json">` blocks. This is the most reliable extraction method because it returns verbatim structured data with no AI summarization risk.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/recipe-fetch/scripts/extract_jsonld.py" "<URL>"
```

If exit code is **0**, the script outputs a JSON object with `name`, `ingredients`, `instructions`, `image`, and `og_image`. Use these fields directly — they are verbatim from the site's own structured data.

If exit code is **1** (no JSON-LD found), fall back to the WebFetch method below.

**Fallback method — WebFetch:**

Only use this when JSON-LD extraction fails (exit code 1). Use WebFetch to get the full page. In a single pass, extract:
- Recipe title
- All ingredients (verbatim, every line)
- All instructions (verbatim, every step)
- The `og:image` URL (used to download the recipe photo)

**If the page has multiple recipe components** (e.g., cake + frosting, meatballs + sauce), fetch ALL of them. Use explicit language: "Extract ALL recipes on this page including [component A] AND [component B]."

### 2. Check for existing file

Before writing anything:
```bash
test -f "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>/Recipes/<Recipe Title>.md"
```
If the file exists, read it and **stop** — report the conflict to the user and ask whether to overwrite, merge, or skip.

### 3. Download and verify the image

Use the `image` field from JSON-LD (or `og_image` as fallback). For WebFetch extractions, use the `og:image` URL.

```bash
# Download (slug = lowercase kebab-case of recipe title)
curl -L -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -o "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>/Files/recipes/<slug>.jpg" \
  "<image URL>"

# Verify actual file type
file -b "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/<VaultName>/Files/recipes/<slug>.jpg"
```

**If the type is WebP or PNG**: Convert to JPEG in-place:
```bash
sips -s format jpeg "/path/to/<slug>.jpg" --out "/path/to/<slug>.jpg"
```

**If `file -b` reports HTML** (error page returned instead of image): The initial curl user-agent was blocked. Retry with the full Chrome user-agent string shown above. If it still fails, skip the image and omit the image line from the markdown — do not leave a broken image reference.

### 4. Write the recipe file

Use the exact format defined in the vault (no YAML frontmatter):

```markdown
# Recipe Title

![Recipe Title|250](Files/recipes/slug.jpg)

## Ingredients

- ingredient 1
- ingredient 2

## Instructions

1. Step one.
2. Step two.

## Attribution

Recipe from [Site Name](https://original-url)

#Tag1 #Tag2 #Tag3
```

**Rules:**
- Copy all ingredients and instructions **verbatim** — never rephrase, paraphrase, scale, or omit anything
- When using JSON-LD data, the ingredients and instructions are already verbatim — write them exactly as returned
- HTML entities (e.g., `&#8217;` for `'`, `&amp;` for `&`) must be decoded to plain text before writing
- Omit the image line entirely if download failed
- Include `## Attribution` for all URL-sourced recipes
- Tags go on the **last line**, space-separated `#PascalCase` tags, after a blank line following Attribution
- **Never include** ratings, star ratings, vote counts, or review information

### 5. Tags

Use 3–5 PascalCase tags covering:
- **Meal category** (pick one): `#Dessert` `#MainDish` `#SideDish` `#Breakfast` `#Soup` `#Appetizer` `#Sauce` `#Condiment` `#Snack` `#Drink`
- **Key ingredients**: e.g., `#Chicken` `#Chocolate` `#Lemon` `#Pumpkin`
- **Cooking method** (if notable): `#InstantPot` `#SlowCooker` `#AirFryer` `#Grilling` `#NoBake`

### 6. Verify and report

After writing:
- Confirm the file exists at the expected path
- Confirm the image exists (if downloaded)
- Report back: recipe title, saved path, image status, tags applied, extraction method used (JSON-LD or WebFetch)

## Verbatim Content Rule

Copy ALL recipe text exactly as written on the source page — ingredients, measurements, and instructions. Do not improve grammar, reorder steps, simplify language, or make any editorial changes. The only exceptions are removing ratings/reviews, decoding HTML entities, and reformatting for markdown structure.
