import time
import datetime as dt
import pytest

import jwt


def test_roundtrip_hs256():
    payload = {"a": 1, "b": "x"}
    token = jwt.encode(payload, "secret", algorithm="HS256")
    out = jwt.decode(token, "secret", algorithms=["HS256"])
    assert out == payload


def test_wrong_key_raises_invalid_signature():
    token = jwt.encode({"a": 1}, "secret", algorithm="HS256")
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "wrong", algorithms=["HS256"])


def test_missing_algorithms_when_verifying_raises_decode_error():
    token = jwt.encode({"a": 1}, "secret", algorithm="HS256")
    with pytest.raises(jwt.DecodeError):
        jwt.decode(token, "secret", algorithms=None)
    with pytest.raises(jwt.DecodeError):
        jwt.decode(token, "secret", algorithms=[])


def test_no_algorithms_needed_when_verify_signature_false():
    token = jwt.encode({"a": 1}, "secret", algorithm="HS256")
    out = jwt.decode(token, None, algorithms=None, options={"verify_signature": False})
    assert out["a"] == 1


def test_expired_raises_and_leeway_allows():
    now = int(time.time())
    token = jwt.encode({"sub": "u", "exp": now - 5}, "secret", algorithm="HS256")

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, "secret", algorithms=["HS256"])

    out = jwt.decode(token, "secret", algorithms=["HS256"], leeway=10)
    assert out["sub"] == "u"


def test_verify_exp_can_be_disabled():
    now = int(time.time())
    token = jwt.encode({"exp": now - 100, "a": 1}, "secret", algorithm="HS256")
    out = jwt.decode(token, "secret", algorithms=["HS256"], options={"verify_exp": False})
    assert out["a"] == 1


def test_bad_token_segments_raise_decode_error():
    with pytest.raises(jwt.DecodeError):
        jwt.decode("a.b", "secret", algorithms=["HS256"])


def test_datetime_exp_supported():
    exp = dt.datetime.fromtimestamp(time.time() + 60)
    token = jwt.encode({"exp": exp, "a": 1}, "secret", algorithm="HS256")
    out = jwt.decode(token, "secret", algorithms=["HS256"])
    assert out["a"] == 1