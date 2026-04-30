"""Pure logic for detecting #nnn / !nnn references in message content
and rendering them as linked issue / merge-request lines.

Kept free of any discord.py imports so it can be unit-tested in isolation.
"""

import re

# Match #nnn / !nnn only when not preceded by a word char or another # / !,
# so things like `username#1234` or `##123` don't trigger.
ISSUE_RE = re.compile(r"(?<![\w!#])#(\d+)\b")
MR_RE = re.compile(r"(?<![\w!#])!(\d+)\b")


def _ordered_unique(numbers: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in numbers:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def find_issues(content: str) -> list[str]:
    return _ordered_unique(ISSUE_RE.findall(content))


def find_merge_requests(content: str) -> list[str]:
    return _ordered_unique(MR_RE.findall(content))


def issue_url(n: str, repo_url: str) -> str:
    return f"{repo_url}/-/issues/{n}"


def mr_url(n: str, repo_url: str) -> str:
    return f"{repo_url}/-/merge_requests/{n}"


def _escape_link_text(s: str) -> str:
    """Escape characters that would break a `[text](url)` markdown link."""
    return (
        s.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def build_reference_lines(
    content: str,
    repo_url: str,
    titles: dict[tuple[str, str], str] | None = None,
) -> list[str]:
    """Return embed-body lines describing every issue / MR ref in `content`.

    If `titles` is provided, refs whose (kind, iid) key has a title in the
    dict are rendered as a markdown link `[title](url)`. Refs without a
    title in the dict fall back to a plain `<url>` rendering. `kind` is
    'issue' or 'mr'.

    Issues come first, then merge requests; within each group, refs appear
    in the order they're first encountered. Returns an empty list when
    there are no references.
    """
    titles = titles or {}
    lines: list[str] = []
    for n in find_issues(content):
        url = issue_url(n, repo_url)
        title = titles.get(("issue", n))
        if title:
            lines.append(f"Issue #{n}: [{_escape_link_text(title)}]({url})")
        else:
            lines.append(f"Issue #{n}: {url}")
    for n in find_merge_requests(content):
        url = mr_url(n, repo_url)
        title = titles.get(("mr", n))
        if title:
            lines.append(
                f"Merge Request !{n}: [{_escape_link_text(title)}]({url})"
            )
        else:
            lines.append(f"Merge Request !{n}: {url}")
    return lines
