"""GitLab REST API helpers for resolving issue / MR titles.

Kept free of any discord.py imports so the network logic can be exercised
independently of the bot integration.
"""

import asyncio
import logging
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
    fall back to plain-URL rendering for those. Failures are logged so
    operators can tell *why* a title didn't appear.
    """
    if not issues and not merge_requests:
        return {}
    if not token:
        logging.warning(
            "fetch_titles: no GitLab token configured; "
            "skipping title lookup for %d issue(s) and %d MR(s) "
            "(set BOT_GITLAB_TOKEN to enable)",
            len(issues),
            len(merge_requests),
        )
        return {}

    project = quote(repo, safe="")
    base = f"{domain.rstrip('/')}/api/v4/projects/{project}"
    headers = {"PRIVATE-TOKEN": token}

    async def _one(
        kind: str, iid: str, path: str
    ) -> tuple[tuple[str, str], str] | None:
        url = f"{base}/{path}/{iid}"
        try:
            async with session.get(
                url, headers=headers, timeout=_TIMEOUT
            ) as r:
                if r.status != 200:
                    body = (await r.text())[:200]
                    logging.warning(
                        "fetch_titles: %s %s returned HTTP %s: %s",
                        kind,
                        iid,
                        r.status,
                        body,
                    )
                    return None
                try:
                    data = await r.json()
                except (aiohttp.ContentTypeError, ValueError) as e:
                    logging.warning(
                        "fetch_titles: %s %s returned non-JSON body: %s",
                        kind,
                        iid,
                        e,
                    )
                    return None
        except asyncio.TimeoutError:
            logging.warning(
                "fetch_titles: %s %s timed out after %ss (url=%s)",
                kind,
                iid,
                _TIMEOUT.total,
                url,
            )
            return None
        except aiohttp.ClientError as e:
            logging.warning(
                "fetch_titles: %s %s network error: %s (url=%s)",
                kind,
                iid,
                e,
                url,
            )
            return None
        title = data.get("title") if isinstance(data, dict) else None
        if not isinstance(title, str):
            logging.warning(
                "fetch_titles: %s %s response missing 'title' field "
                "(keys=%s)",
                kind,
                iid,
                list(data.keys()) if isinstance(data, dict) else type(data).__name__,
            )
            return None
        return ((kind, iid), title)

    coros = [_one("issue", n, "issues") for n in issues]
    coros += [_one("mr", n, "merge_requests") for n in merge_requests]
    results = await asyncio.gather(*coros)
    return dict(r for r in results if r is not None)
