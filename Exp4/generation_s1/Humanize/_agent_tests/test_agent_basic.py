import datetime as dt

import humanize


def test_imports_and_exports():
    assert hasattr(humanize, "intcomma")
    assert hasattr(humanize, "ordinal")
    assert hasattr(humanize, "naturalsize")
    assert hasattr(humanize, "precisedelta")
    assert hasattr(humanize, "naturaldelta")
    assert hasattr(humanize, "naturaltime")

    import humanize.number
    import humanize.time
    import humanize.filesize
    import humanize.lists
    import humanize.i18n


def test_intcomma_basic_and_decimal_and_sign():
    assert humanize.intcomma(0) == "0"
    assert humanize.intcomma(1000) == "1,000"
    assert humanize.intcomma(-1000000) == "-1,000,000"
    assert humanize.intcomma("1234567.89") == "1,234,567.89"


def test_intcomma_preserves_leading_zeros_for_digit_strings():
    assert humanize.intcomma("001234") == "001,234"


def test_ordinal_basic_and_teens_and_negative():
    assert humanize.ordinal(1) == "1st"
    assert humanize.ordinal(2) == "2nd"
    assert humanize.ordinal(3) == "3rd"
    assert humanize.ordinal(4) == "4th"
    assert humanize.ordinal(11) == "11th"
    assert humanize.ordinal(12) == "12th"
    assert humanize.ordinal(13) == "13th"
    assert humanize.ordinal(21) == "21st"
    assert humanize.ordinal(112) == "112th"
    assert humanize.ordinal(-1) == "-1st"


def test_naturalsize_decimal_and_binary_and_gnu():
    assert humanize.naturalsize(0) == "0 B"
    assert humanize.naturalsize(1000) == "1 kB"
    assert humanize.naturalsize(1536, binary=True) == "1.5 KiB"
    assert humanize.naturalsize(1024, binary=True, GNU=True) == "1K"
    assert humanize.naturalsize(500, binary=True, GNU=True) == "500B"


def test_time_naturaldelta_naturaltime_precisedelta():
    assert humanize.naturaldelta(dt.timedelta(seconds=1)) == "1 second"
    assert humanize.naturaldelta(3600) == "1 hour"

    now = dt.datetime.now()
    s1 = humanize.naturaltime(now - dt.timedelta(seconds=10), when=now)
    assert s1.endswith("ago")

    s2 = humanize.naturaltime(now + dt.timedelta(minutes=3), when=now)
    assert s2.startswith("in ")

    p = humanize.precisedelta(3661)
    assert "1 hour" in p and "1 minute" in p and "1 second" in p

    assert humanize.precisedelta(59, minimum_unit="minutes") == "1 minute"


def test_natural_list():
    from humanize.lists import natural_list

    assert natural_list([]) == ""
    assert natural_list(["a"]) == "a"
    assert natural_list(["a", "b"]) == "a and b"
    assert natural_list(["a", "b", "c"]) == "a, b, and c"
    assert natural_list(["a", "b", "c"], oxford_comma=False) == "a, b and c"