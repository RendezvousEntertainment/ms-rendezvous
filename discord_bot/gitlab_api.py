"""GitLab REST API helpers for resolving issue / MR titles.

Kept free of any discord.py imports so the network logic can be exercised
independently of the bot integration.
"""

import asyncio
from urllib.parse import quote

import aiohttp

_TIMEOUT = aiohttp.ClientTimeout(total=5)


async def fetch_titles(
    session: aiohttp.ClientSession,
    domain: str,
    repo: str,
    issues: list[str],
    merge_requests: list[str],
    token: str,
) -> dict[tuple[str, str], str]:
    """Look up titles for a batch of issue / MR refs from GitLab.

    Returns a dict keyed by (kind, iid) where kind is 'issue' or 'mr'.
    Refs that fail to resolve (missing token, non-200, network error,
    timeout) are simply absent from the returned dict — callers should
    fall back to plain-URL rendering for those.
    """
    if not token or (not issues and not merge_requests):
        return {}

    project = quote(repo, safe="")
    base = f"{domain.rstrip('/')}/api/v4/projects/{project}"
    headers = {"PRIVATE-TOKEN": token}

    async def _one(
        kind: str, iid: str, path: str
    ) -> tuple[tuple[str, str], str] | None:
        try:
            async with session.get(
                f"{base}/{path}/{iid}", headers=headers, timeout=_TIMEOUT
            ) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
        title = data.get("title") if isinstance(data, dict) else None
        if not isinstance(title, str):
            return None
        return ((kind, iid), title)

    coros = [_one("issue", n, "issues") for n in issues]
    coros += [_one("mr", n, "merge_requests") for n in merge_requests]
    results = await asyncio.gather(*coros)
    return dict(r for r in results if r is not None)
