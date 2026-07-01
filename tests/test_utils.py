import pytest

from app.utils import decode_base62, encode_base62


@pytest.mark.parametrize("num", [0, 1, 61, 62, 1000, 123456789])
def test_base62_roundtrip(num):
    assert decode_base62(encode_base62(num)) == num


def test_base62_is_compact():
    # 62^3 - 1 should still encode in 3 characters
    assert len(encode_base62(62**3 - 1)) == 3
