from gitlab_api import _issue_state, _mr_state


def test_issue_state_opened_maps_to_open():
    assert _issue_state({"state": "opened"}) == "open"


def test_issue_state_closed():
    assert _issue_state({"state": "closed"}) == "closed"


def test_issue_state_unknown_returns_empty():
    assert _issue_state({"state": "locked"}) == ""
    assert _issue_state({}) == ""


def test_mr_state_opened_maps_to_open():
    assert _mr_state({"state": "opened", "draft": False}) == "open"


def test_mr_state_closed():
    assert _mr_state({"state": "closed", "draft": False}) == "closed"


def test_mr_state_merged():
    assert _mr_state({"state": "merged", "draft": False}) == "merged"


def test_mr_state_draft_takes_precedence_over_opened():
    # Draft MRs are server-side `state == "opened"` — the draft flag wins.
    assert _mr_state({"state": "opened", "draft": True}) == "draft"


def test_mr_state_legacy_work_in_progress_flag_treated_as_draft():
    # Older GitLab payloads use `work_in_progress` instead of `draft`.
    assert _mr_state({"state": "opened", "work_in_progress": True}) == "draft"


def test_mr_state_unknown_returns_empty():
    assert _mr_state({"state": "locked"}) == ""
    assert _mr_state({}) == ""
