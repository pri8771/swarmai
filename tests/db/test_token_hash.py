"""V2A-003a / V2A-H2 — membership token hash helpers (no DB required)."""

from __future__ import annotations

import pytest

from swarm.db.lease_fencing import RawTokenPersistenceError, _assert_no_raw_token_fields
from swarm.db.token_hash import hash_membership_token, new_token_id, verify_membership_token


def test_hash_membership_token_is_stable_and_not_raw() -> None:
    token = "wt_example_secret_value"
    digest = hash_membership_token(token)
    assert digest == hash_membership_token(token)
    assert digest != token
    assert not digest.startswith("wt_")
    assert len(digest) == 64


def test_verify_membership_token_rejects_mismatch() -> None:
    token = "wt_abc"
    digest = hash_membership_token(token)
    assert verify_membership_token(token=token, token_hash=digest) is True
    assert verify_membership_token(token="wt_other", token_hash=digest) is False


def test_new_token_id_is_opaque_public_ref() -> None:
    a = new_token_id()
    b = new_token_id()
    assert a.startswith("wtok_")
    assert a != b


def test_resource_payload_rejects_raw_token_keys() -> None:
    with pytest.raises(RawTokenPersistenceError, match="raw_token_field_forbidden"):
        _assert_no_raw_token_fields({"membership_token": "wt_should_never_persist"})


def test_resource_payload_rejects_nested_raw_token_keys() -> None:
    with pytest.raises(RawTokenPersistenceError, match=r"raw_token_field_forbidden:.*token"):
        _assert_no_raw_token_fields({"meta": {"nested": [{"token": "wt_leaked"}]}})
