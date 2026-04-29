from refs import (
    build_reference_lines,
    find_issues,
    find_merge_requests,
    issue_url,
    mr_url,
)

REPO_URL = "https://example.test/owner/repo"


def test_issue_url():
    assert issue_url("123", REPO_URL) == f"{REPO_URL}/-/issues/123"


def test_mr_url():
    assert mr_url("42", REPO_URL) == f"{REPO_URL}/-/merge_requests/42"


def test_find_issues_basic():
    assert find_issues("see #5") == ["5"]
    assert find_issues("#1 then #2 then #3") == ["1", "2", "3"]


def test_find_issues_dedup_preserves_first_occurrence_order():
    assert find_issues("#7 #3 #7 #3 #1") == ["7", "3", "1"]


def test_find_issues_ignores_username_discriminator():
    # `username#1234` should not match — `#` preceded by a word char
    assert find_issues("hi user#1234") == []


def test_find_issues_ignores_double_hash():
    # markdown-style `##123` should not match
    assert find_issues("##123 here") == []


def test_find_issues_no_match_when_followed_by_letters():
    # `\b` after \d+ rules out `#123abc`
    assert find_issues("#123abc") == []


def test_find_issues_at_string_boundaries():
    assert find_issues("#9") == ["9"]
    assert find_issues("look at (#42)!") == ["42"]


def test_find_merge_requests_basic():
    assert find_merge_requests("merged !17") == ["17"]


def test_find_merge_requests_ignores_bot_commands():
    # `!hello` / `!ping` are bot commands — not digits, must not match
    assert find_merge_requests("!hello world") == []
    assert find_merge_requests("!ping") == []


def test_find_merge_requests_ignores_double_bang():
    assert find_merge_requests("!!42") == []


def test_refs_require_non_word_char_before_sigil():
    # `#123!4` — issue `#123` matches (it's at start), but MR `!4` is rejected
    # because `!` is preceded by a word char (`3`). This mirrors GitLab's
    # conservative reference detection and prevents false hits inside tokens.
    assert find_issues("#123!4") == ["123"]
    assert find_merge_requests("#123!4") == []
    # Refs separated by whitespace work as expected.
    assert find_issues("#123 !4") == ["123"]
    assert find_merge_requests("#123 !4") == ["4"]


def test_build_reference_lines_empty_when_no_refs():
    assert build_reference_lines("just a normal message", REPO_URL) == []
    assert build_reference_lines("", REPO_URL) == []


def test_build_reference_lines_issue_only():
    assert build_reference_lines("see #5", REPO_URL) == [
        f"Issue #5: {REPO_URL}/-/issues/5",
    ]


def test_build_reference_lines_mr_only():
    assert build_reference_lines("merged !7", REPO_URL) == [
        f"Merge Request !7: {REPO_URL}/-/merge_requests/7",
    ]


def test_build_reference_lines_issues_then_mrs():
    # Issues should be listed first, then merge requests, even if the MR
    # appears earlier in the source text.
    text = "shipped !12 which closes #5 and #6"
    assert build_reference_lines(text, REPO_URL) == [
        f"Issue #5: {REPO_URL}/-/issues/5",
        f"Issue #6: {REPO_URL}/-/issues/6",
        f"Merge Request !12: {REPO_URL}/-/merge_requests/12",
    ]


def test_build_reference_lines_dedups():
    text = "#5 #5 !7 !7"
    assert build_reference_lines(text, REPO_URL) == [
        f"Issue #5: {REPO_URL}/-/issues/5",
        f"Merge Request !7: {REPO_URL}/-/merge_requests/7",
    ]


def test_build_reference_lines_ignores_noise():
    text = "user#1234 said ##99 about !hello but linked #5"
    assert build_reference_lines(text, REPO_URL) == [
        f"Issue #5: {REPO_URL}/-/issues/5",
    ]
