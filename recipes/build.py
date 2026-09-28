#!/usr/bin/env python3
"""Build the recipes section: convert each Markdown recipe to HTML with pandoc and generate the grid page.

Usage:
  python3 recipes/build.py [SOURCE_DIR]                Build pages from SOURCE_DIR (default: recipes/md)
  python3 recipes/build.py --fingerprint [SOURCE_DIR]  Print the recipes' fingerprint and exit
"""

import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

RECIPES_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = RECIPES_DIR / "md"
RECIPE_TEMPLATE = RECIPES_DIR / "recipe.html"
INDEX_TEMPLATE = RECIPES_DIR / "index-template.html"


def fingerprint(md_files):
    """Return a SHA-256 hash of the recipes' file names and contents, used to detect changes between deploys."""
    digest = hashlib.sha256()
    for path in md_files:
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def slugify(name):
    """Convert a recipe name to a lowercase, hyphenated ASCII slug, dropping non-ASCII characters."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def sort_key(name):
    """Sort alphabetically, ignoring case and leading punctuation such as "(Crispy) Tofu"."""
    return re.sub(r"^[^0-9A-Za-z]+", "", name).casefold()


def strip_tags(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def pandoc(*args, text=None):
    return subprocess.run(["pandoc", *args], input=text, capture_output=True, text=True, check=True).stdout


def read_metadata(md_path, meta_template):
    """Return the recipe's frontmatter as a dict of HTML strings, as rendered by pandoc."""
    return json.loads(pandoc(str(md_path), "-t", "html", "--template", meta_template))


def add_columns(markdown):
    """Wrap the first Ingredients/Instructions heading pair in pandoc fenced divs so they render side by side.

    Both headings are normalized to level 1 (shifted down at render time). The Instructions section ends at
    the next heading of the same or higher level, or at the end of the file.
    """
    lines = markdown.split("\n")
    heading = re.compile(r"^(#+)\s+(.*?)\s*$")

    def find(title, start):
        for i in range(start, len(lines)):
            match = heading.match(lines[i])
            if match and match.group(2).casefold() == title:
                return i, len(match.group(1))
        return None, None

    ingredients, _ = find("ingredients", 0)
    if ingredients is None:
        return markdown
    instructions, level = find("instructions", ingredients + 1)
    if instructions is None:
        return markdown

    end = len(lines)
    for i in range(instructions + 1, len(lines)):
        match = heading.match(lines[i])
        if match and len(match.group(1)) <= level:
            end = i
            break

    lines[ingredients] = "# Ingredients"
    lines[instructions] = "# Instructions"
    return "\n".join(
        lines[:ingredients]
        + ["::: {.recipe-columns}", "::: {.ingredients}"]
        + lines[ingredients:instructions]
        + [":::", "::: {.instructions}"]
        + lines[instructions:end]
        + [":::", ":::", ""]
        + lines[end:]
    )


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def format_tags(tags):
    return "[" + ", ".join(tags).lower() + "]" if tags else ""


def format_source(source):
    """Render a source as HTML: bare URLs become links labeled with their domain, anything else is kept as-is."""
    text = strip_tags(source)
    if re.fullmatch(r"https?://\S+", text):
        domain = urlparse(text).netloc.removeprefix("www.")
        return f'<a href="{html.escape(text)}">{html.escape(domain)}</a>'
    return source


def build(source_dir):
    md_files = sorted(source_dir.glob("*.md"))
    if not md_files:
        sys.exit(f"No Markdown files found in {source_dir}")

    # Remove pages from the previous build (every directory except the Markdown source)
    for path in RECIPES_DIR.iterdir():
        if path.is_dir() and path.resolve() != source_dir.resolve() and path.name != "__pycache__":
            shutil.rmtree(path)

    recipes = []
    slugs = {}
    with tempfile.TemporaryDirectory() as tmp:
        meta_template = Path(tmp) / "meta.json"
        meta_template.write_text("$meta-json$\n")

        for md_path in md_files:
            name = md_path.stem
            slug = slugify(name)
            if not slug:
                sys.exit(f"Recipe name has no ASCII characters to build a URL from: {name}")
            if slug in slugs:
                sys.exit(f"Recipes {slugs[slug]!r} and {name!r} both map to /recipes/{slug}/")
            slugs[slug] = name

            meta = read_metadata(md_path, meta_template)
            tags = [strip_tags(tag) for tag in as_list(meta.get("Dish Type"))]
            sources = [format_source(source) for source in as_list(meta.get("Source"))]

            meta_line = ""
            if tags:
                meta_line += f'<span class="recipe-tags">{html.escape(format_tags(tags))}</span>'
            if sources:
                meta_line += f'<span class="recipe-source">Source: {", ".join(sources)}</span>'

            page = pandoc(
                "-f", "markdown",
                "-t", "html",
                "--template", str(RECIPE_TEMPLATE),
                "--shift-heading-level-by=2",
                "-M", f"title={name}",
                "-V", f"meta-line={meta_line}",
                text=add_columns(md_path.read_text()),
            )
            out_dir = RECIPES_DIR / slug
            out_dir.mkdir()
            (out_dir / "index.html").write_text(page)
            recipes.append((name, slug, tags))

    cards = []
    for name, slug, tags in sorted(recipes, key=lambda recipe: sort_key(recipe[0])):
        search_text = " ".join([name, *tags]).lower()
        cards.append(
            f'<a class="recipe-card" href="{slug}/" data-search="{html.escape(search_text)}">\n'
            f"  <h3>{html.escape(name)}</h3>\n"
            f'  <p class="recipe-tags">{html.escape(format_tags(tags))}</p>\n'
            f"</a>"
        )

    index = pandoc(
        "-f", "markdown",
        "-t", "html",
        "--template", str(INDEX_TEMPLATE),
        "-M", "title=Recipes",
        "-V", "cards=" + "\n".join(cards),
        text="",
    )
    (RECIPES_DIR / "index.html").write_text(index)
    (RECIPES_DIR / "version.txt").write_text(fingerprint(md_files) + "\n")
    print(f"Built {len(recipes)} recipes from {source_dir}")


def main():
    args = sys.argv[1:]
    print_fingerprint = "--fingerprint" in args
    args = [arg for arg in args if arg != "--fingerprint"]
    source_dir = Path(args[0]).expanduser() if args else DEFAULT_SOURCE

    if print_fingerprint:
        print(fingerprint(sorted(source_dir.glob("*.md"))))
    else:
        build(source_dir)


if __name__ == "__main__":
    main()
