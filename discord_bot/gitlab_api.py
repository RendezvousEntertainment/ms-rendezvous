"""GitLab REST API helpers for resolving issue / MR metadata.

Kept free of any discord.py imports so the network logic can be exercised
independently of the bot integration.
"""

import asyncio
import logging
from urllib.parse import quote

import aiohttp
from refs import RefInfo

_TIMEOUT = aiohttp.ClientTimeout(total=5)


def _issue_state(data: dict) -> str:
    """Map a GitLab issue payload's `state` to a renderable marker."""
    state = data.get("state")
    if state == "opened":
        return "open"
    if state == "closed":
        return "closed"
    return ""


def _mr_state(data: dict) -> str:
    """Map a GitLab MR payload to a renderable marker.

    Draft MRs are still `state == "opened"` server-side, so the draft
    flag takes precedence over the raw state.
    """
    if data.get("draft") is True or data.get("work_in_progress") is True:
        return "draft"
    state = data.get("state")
    if state == "opened":
        return "open"
    if state == "closed":
        return "closed"
    if state == "merged":
        return "merged"
    return ""

async def fetch_open_merge_requests(
    session: aiohttp.ClientSession,
    domain: str,
    repo: str,
    token: str
) -> list[str]:
    """
        Fetch all open merge request IIDs (max of 20)
    """
    if not token:
        logging.warning(
            "fetch_open_merge_requests: no GitLab token configured; "
            "skipping lookup for open merge requests "
            "(set BOT_GITLAB_TOKEN to enable)",
        )
        return []
    project = quote(repo, safe="")
    base = f"{domain.rstrip('/')}/api/v4/projects/{project}"
    headers = {"PRIVATE-TOKEN": token}
    async with session.get(f"{base}/merge_requests?state=opened") as r:
        if r.status != 200:
            body = (await r.text())[:200]
            logging.warning(
                "fetch_open_merge_requests: returned HTTP %s: %s",
                r.status,
                body,
            )
            return None
        try:
            data = await r.json()
        except (aiohttp.ContentTypeError, ValueError) as e:
            logging.warning(
                "fetch_open_merge_requests: returned non-JSON body: %s",
                e,
            )
            return None
    return [str(mr['iid']) for mr in data]



async def fetch_ref_info(
    session: aiohttp.ClientSession,
    domain: str,
    repo: str,
    issues: list[str],
    merge_requests: list[str],
    token: str,
) -> dict[tuple[str, str], RefInfo]:
    """Look up titles + states for a batch of issue / MR refs from GitLab.

    Returns a dict keyed by (kind, iid) where kind is 'issue' or 'mr'.
    Refs that fail to resolve (missing token, non-200, network error,
    timeout) are simply absent from the returned dict — callers should
    fall back to plain-URL rendering for those. Failures are logged so
    operators can tell *why* a ref didn't appear.
    """
    if not issues and not merge_requests:
        return {}
    if not token:
        logging.warning(
            "fetch_ref_info: no GitLab token configured; "
            "skipping lookup for %d issue(s) and %d MR(s) "
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
    ) -> tuple[tuple[str, str], RefInfo] | None:
        url = f"{base}/{path}/{iid}"
        try:
            async with session.get(
                url, headers=headers, timeout=_TIMEOUT
            ) as r:
                if r.status != 200:
                    body = (await r.text())[:200]
                    logging.warning(
                        "fetch_ref_info: %s %s returned HTTP %s: %s",
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
                        "fetch_ref_info: %s %s returned non-JSON body: %s",
                        kind,
                        iid,
                        e,
                    )
                    return None
        except asyncio.TimeoutError:
            logging.warning(
                "fetch_ref_info: %s %s timed out after %ss (url=%s)",
                kind,
                iid,
                _TIMEOUT.total,
                url,
            )
            return None
        except aiohttp.ClientError as e:
            logging.warning(
                "fetch_ref_info: %s %s network error: %s (url=%s)",
                kind,
                iid,
                e,
                url,
            )
            return None
        title = data.get("title") if isinstance(data, dict) else None
        if not isinstance(title, str):
            logging.warning(
                "fetch_ref_info: %s %s response missing 'title' field "
                "(keys=%s)",
                kind,
                iid,
                list(data.keys()) if isinstance(data, dict) else type(data).__name__,
            )
            return None
        state = _issue_state(data) if kind == "issue" else _mr_state(data)
        return ((kind, iid), RefInfo(title=title, state=state))

    coros = [_one("issue", n, "issues") for n in issues]
    coros += [_one("mr", n, "merge_requests") for n in merge_requests]
    results = await asyncio.gather(*coros)
    return dict(r for r in results if r is not None)
