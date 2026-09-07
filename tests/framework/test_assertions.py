"""断言重写后的行为兼容性：成功条件不变，失败仍抛出 AssertionError。"""

from types import SimpleNamespace

import pytest

from core.assertions import Assert


@pytest.mark.parametrize(
    "name, passing, failing",
    [
        ("equal", (1, 1), (1, 2)),
        ("not_equal", (1, 2), (1, 1)),
        ("is_true", (True,), (False,)),
        ("is_false", (False,), (True,)),
        ("contains", ([1], 1), ([1], 2)),
        ("not_contains", ([1], 2), ([1], 1)),
        ("is_none", (None,), (1,)),
        ("not_none", (1,), (None,)),
        ("not_empty", ([1],), ([],)),
        ("length", ([1], 1), ([1], 2)),
        ("greater", (2, 1), (1, 2)),
        ("less", (1, 2), (2, 1)),
        ("between", (2, 1, 3), (4, 1, 3)),
        ("approx", (1, 1.001), (1, 2)),
        ("match_regex", ("abc", "a.*"), ("abc", "^z")),
        ("status_code", (SimpleNamespace(status_code=200),), (SimpleNamespace(status_code=500),)),
        ("json_value", ({"x": 1}, "x", 1), ({"x": 1}, "x", 2)),
        ("jsonpath", ({"x": {"y": 1}}, "$.x.y", 1), ({"x": {"y": 1}}, "$.x.y", 2)),
        ("jsonpath_exists", ({"x": 1}, "$.x"), ({"x": ""}, "$.x")),
        ("match_schema", ({"x": 1}, {"type": "object"}), ([], {"type": "object"})),
    ],
)
def test_assertion_success_and_failure_contract(name, passing, failing):
    assertion = getattr(Assert, name)
    assertion(*passing)
    with pytest.raises(AssertionError):
        assertion(*failing)
