from endstone_utilitystone.util.text import colorize, stripColors, shorten, joinNames
from endstone_utilitystone.util.durations import parseDuration, formatDuration, formatTimestamp
import math
import time


class TestColorize:
    def test_no_ampersand(self):
        assert colorize("hello") == "hello"

    def test_empty_string(self):
        assert colorize("") == ""

    def test_none_like(self):
        assert colorize(None) is None

    def test_simple_color(self):
        result = colorize("&aHello")
        assert "\u00a7" in result
        assert "a" in result
        assert "Hello" in result

    def test_double_ampersand(self):
        result = colorize("&&a")
        assert result == "&a"

    def test_invalid_code(self):
        result = colorize("&xHello")
        assert result == "&xHello"


class TestStripColors:
    def test_no_section(self):
        assert stripColors("hello") == "hello"

    def test_empty(self):
        assert stripColors("") == ""

    def test_strips_codes(self):
        result = stripColors("\u00a7aHello\u00a7r")
        assert result == "Hello"


class TestShorten:
    def test_within_limit(self):
        assert shorten("hello", 10) == "hello"

    def test_exceeds_limit(self):
        result = shorten("hello world", 5)
        assert len(result) == 5
        assert result.endswith("...")

    def test_zero_limit(self):
        assert shorten("hello", 0) == "hello"


class TestJoinNames:
    def test_empty(self):
        assert joinNames([]) == "none"

    def test_single(self):
        assert joinNames(["alice"]) == "alice"

    def test_multiple(self):
        result = joinNames(["charlie", "alice", "bob"])
        assert result == "alice, bob, charlie"

    def test_custom_empty(self):
        assert joinNames([], "nobody") == "nobody"


class TestParseDuration:
    def test_seconds(self):
        assert parseDuration("30s") == 30

    def test_minutes(self):
        assert parseDuration("15m") == 900

    def test_hours(self):
        assert parseDuration("2h") == 7200

    def test_days(self):
        assert parseDuration("7d") == 604800

    def test_weeks(self):
        assert parseDuration("3w") == 1814400

    def test_months(self):
        assert parseDuration("1mo") == 2629800

    def test_years(self):
        assert parseDuration("1y") == 31557600

    def test_combined(self):
        assert parseDuration("1d12h") == 129600

    def test_permanent(self):
        assert parseDuration("perm") == math.inf
        assert parseDuration("forever") == math.inf
        assert parseDuration("permanent") == math.inf

    def test_bare_number(self):
        assert parseDuration("30") == 1800

    def test_invalid(self):
        assert parseDuration("abc") is None
        assert parseDuration("") is None
        assert parseDuration(None) is None

    def test_zero(self):
        assert parseDuration("0") is None


class TestFormatDuration:
    def test_none(self):
        assert formatDuration(None) == "unknown"

    def test_permanent(self):
        assert formatDuration(math.inf) == "permanent"

    def test_zero(self):
        assert formatDuration(0) == "moments"

    def test_seconds_only(self):
        result = formatDuration(45)
        assert "45s" in result

    def test_minutes(self):
        result = formatDuration(120)
        assert "2m" in result

    def test_hours(self):
        result = formatDuration(7200)
        assert "2h" in result

    def test_days(self):
        result = formatDuration(172800)
        assert "2d" in result


class TestFormatTimestamp:
    def test_zero(self):
        assert formatTimestamp(0) == "never"

    def test_none(self):
        assert formatTimestamp(None) == "never"

    def test_valid(self):
        result = formatTimestamp(time.time())
        assert "2026" in result
