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


def build_reference_lines(content: str, repo_url: str) -> list[str]:
    """Return embed-body lines describing every issue / MR ref in `content`.

    Issues come first, then merge requests; within each group, refs appear in
    the order they're first encountered. Returns an empty list when there are
    no references.
    """
    lines: list[str] = []
    for n in find_issues(content):
        lines.append(f"Issue #{n}: {issue_url(n, repo_url)}")
    for n in find_merge_requests(content):
        lines.append(f"Merge Request !{n}: {mr_url(n, repo_url)}")
    return lines
