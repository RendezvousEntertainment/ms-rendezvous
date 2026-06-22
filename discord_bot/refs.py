"""Pure logic for detecting #nnn / !nnn references in message content
and rendering them as linked issue / merge-request lines.

Kept free of any discord.py imports so it can be unit-tested in isolation.
"""

import re
from typing import NamedTuple


class RefInfo(NamedTuple):
    """Metadata for a single ref needed to render its embed line.

    `state` is the human-readable status marker ("open", "closed",
    "merged", "draft") or "" when unknown — rendering omits the marker
    in the empty case.
    """

    title: str
    state: str = ""

# Match #nnn / !nnn only when not preceded by a word char, another # / !,
# or `<` (which would make it a Discord mention like `<#channel_id>`),
# so things like `username#1234`, `##123`, or `<#1234567890>` don't trigger.
ISSUE_RE = re.compile(r"(?<![\w!#<])#(\d+)\b")
MR_RE = re.compile(r"(?<![\w!#<])!(\d+)\b")


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
    issues: list[str],
    mrs: list[str],
    repo_url: str,
    info: dict[tuple[str, str], RefInfo] | None = None,
) -> list[str]:
    """Return embed-body lines for the given issue / MR refs.

    `issues` and `mrs` are the IID strings to render (callers obtain them
    via `find_issues` / `find_merge_requests`, plus any extras such as the
    `!open` listing). Each list is deduped defensively, preserving first
    occurrence.

    If `info` is provided, refs whose (kind, iid) key has a `RefInfo`
    entry are rendered with title (as a markdown link `[title](url)`)
    and/or status marker `(state)` between the number and the colon.
    Either field may be empty: a missing title falls back to plain
    `<url>` rendering, and a missing state simply omits the marker.
    `kind` is 'issue' or 'mr'.

    Issues come first, then merge requests. Returns an empty list when
    both inputs are empty.
    """
    info = info or {}
    lines: list[str] = []
    for n in _ordered_unique(issues):
        lines.append(_render_line("Issue", "#", n, issue_url(n, repo_url), info.get(("issue", n))))
    for n in _ordered_unique(mrs):
        lines.append(_render_line("Merge Request", "!", n, mr_url(n, repo_url), info.get(("mr", n))))
    return lines


def _render_line(label: str, sigil: str, n: str, url: str, ri: RefInfo | None) -> str:
    marker = f" ({ri.state})" if ri and ri.state else ""
    if ri and ri.title:
        return f"{label} {sigil}{n}{marker}: [{_escape_link_text(ri.title)}]({url})"
    return f"{label} {sigil}{n}{marker}: {url}"
