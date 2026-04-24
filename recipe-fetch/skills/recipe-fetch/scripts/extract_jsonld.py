#!/usr/bin/env python3
"""Extract Recipe JSON-LD from an HTML file or URL.

Usage:
    extract_jsonld.py <path_or_url>

Reads HTML from a local file path or fetches from a URL.
Finds <script type="application/ld+json"> blocks containing @type: Recipe.
Handles both top-level Recipe objects and @graph arrays.

Outputs a flat JSON object to stdout with keys:
    name, ingredients, instructions, image, og_image

Exit codes:
    0  Recipe found and printed
    1  No Recipe JSON-LD found (caller should fall back to WebFetch)
    2  Fetch/parse error
"""

import json
import re
import sys
import urllib.request


def fetch_html(source: str) -> str:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(
            source,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    else:
        with open(source, encoding="utf-8", errors="replace") as f:
            return f.read()


def find_recipe(html: str) -> dict | None:
    pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    for block in re.findall(pattern, html, re.DOTALL):
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue

        # Normalize to a list of candidates
        candidates = []
        if isinstance(data, list):
            candidates.extend(data)
        elif isinstance(data, dict):
            # Check for @graph pattern (common on WordPress recipe plugins)
            if "@graph" in data:
                candidates.extend(data["@graph"])
            else:
                candidates.append(data)

        for item in candidates:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            # @type can be a string or list
            types = item_type if isinstance(item_type, list) else [item_type]
            if "Recipe" in types:
                return item
    return None


def extract_og_image(html: str) -> str | None:
    match = re.search(
        r'<meta\s+(?:[^>]*?)property=["\']og:image["\'][^>]*?content=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<meta\s+(?:[^>]*?)content=["\']([^"\']+)["\'][^>]*?property=["\']og:image["\']',
            html,
            re.IGNORECASE,
        )
    return match.group(1) if match else None


def normalize_instructions(raw) -> list[str]:
    """Convert recipeInstructions (string, list of strings, or list of HowToStep) to flat list."""
    if isinstance(raw, str):
        # Split on numbered lines or newlines
        lines = re.split(r"\n+", raw.strip())
        return [re.sub(r"^\d+[\.\)]\s*", "", line).strip() for line in lines if line.strip()]

    if not isinstance(raw, list):
        return []

    steps = []
    for item in raw:
        if isinstance(item, str):
            steps.append(item.strip())
        elif isinstance(item, dict):
            # HowToStep or HowToSection
            if item.get("@type") == "HowToSection":
                # Nested section (e.g., "For the frosting:")
                section_name = item.get("name", "")
                if section_name:
                    steps.append(f"**{section_name}**")
                for sub in item.get("itemListElement", []):
                    if isinstance(sub, dict):
                        steps.append(sub.get("text", "").strip())
                    elif isinstance(sub, str):
                        steps.append(sub.strip())
            else:
                text = item.get("text", "").strip()
                if text:
                    steps.append(text)
    return [s for s in steps if s]


def normalize_image(raw) -> str | None:
    """Extract a single image URL from the image field (string, list, or ImageObject)."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        first = raw[0] if raw else None
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url")
    if isinstance(raw, dict):
        return raw.get("url")
    return None


def main():
    if len(sys.argv) != 2:
        print("Usage: extract_jsonld.py <path_or_url>", file=sys.stderr)
        sys.exit(2)

    source = sys.argv[1]

    try:
        html = fetch_html(source)
    except Exception as e:
        print(f"Error fetching: {e}", file=sys.stderr)
        sys.exit(2)

    recipe = find_recipe(html)
    if not recipe:
        print("No Recipe JSON-LD found", file=sys.stderr)
        sys.exit(1)

    og_image = extract_og_image(html)
    recipe_image = normalize_image(recipe.get("image"))

    result = {
        "name": recipe.get("name", "").strip(),
        "ingredients": recipe.get("recipeIngredient", []),
        "instructions": normalize_instructions(recipe.get("recipeInstructions", [])),
        "image": recipe_image or og_image,
        "og_image": og_image,
    }

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()  # trailing newline


if __name__ == "__main__":
    main()
