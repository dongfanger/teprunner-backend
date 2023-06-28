import allure


@allure.title("等于")
def test_assert_equal():
    assert 1 == 1


@allure.title("不等于")
def test_assert_not_equal():
    assert 1 != 2


@allure.title("大于")
def test_assert_greater_than():
    assert 2 > 1


@allure.title("小于")
def test_assert_less_than():
    assert 1 < 2


@allure.title("大于等于")
def test_assert_less_or_equals():
    assert 2 >= 1
    assert 2 >= 2


@allure.title("小于等于")
def test_assert_greater_or_equals():
    assert 1 <= 2
    assert 1 <= 1


@allure.title("长度相等")
def test_assert_length_equal():
    assert len("abc") == len("123")


@allure.title("长度大于")
def test_assert_length_greater_than():
    assert len("hello") > len("123")


@allure.title("长度小于")
def test_assert_length_less_than():
    assert len("hi") < len("123")


@allure.title("长度大于等于")
def test_assert_length_greater_or_equals():
    assert len("hello") >= len("123")
    assert len("123") >= len("123")


@allure.title("长度小于等于")
def test_assert_length_less_or_equals():
    assert len("123") <= len("hello")
    assert len("123") <= len("123")


@allure.title("字符串相等")
def test_assert_string_equals():
    assert "dongfanger" == "dongfanger"


@allure.title("以...开头")
def test_assert_startswith():
    assert "dongfanger".startswith("don")


@allure.title("以...结尾")
def test_assert_startswith():
    assert "dongfanger".endswith("er")


@allure.title("正则匹配")
def test_assert_regex_match():
    import re
    assert re.findall(r"don.*er", "dongfanger")


@allure.title("包含")
def test_assert_contains():
    assert "fang" in "dongfanger"
    assert 2 in [2, 3]
    assert "x" in {"x": "y"}.keys()


@allure.title("类型匹配")
def test_assert_type_match():
    assert isinstance(1, int)
    assert isinstance(0.2, float)
    assert isinstance(True, bool)
    assert isinstance(3e+26j, complex)
    assert isinstance("hi", str)
    assert isinstance([1, 2], list)
    assert isinstance((1, 2), tuple)
    assert isinstance({"a", "b", "c"}, set)
    assert isinstance({"x": 1}, dict)
