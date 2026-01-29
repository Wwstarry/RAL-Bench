from mailpile.util import CleanText, base36, unbase36, chunks, dict_get_path

def test_CleanText():
    assert CleanText('  Foo  Bar  ') == 'Foo Bar'
    assert CleanText('Foo\nBar', collapse=True) == 'Foo Bar'
    assert CleanText('Foo', lower=True) == 'foo'
    assert CleanText(' Foo\tBar ', strip=True, collapse=True) == 'Foo Bar'

def test_base36():
    assert base36(0) == '0'
    assert base36(35) == 'z'
    assert base36(36) == '10'
    assert base36(123456789) == '21i3v9'

def test_unbase36():
    assert unbase36('0') == 0
    assert unbase36('z') == 35
    assert unbase36('10') == 36
    assert unbase36('21i3v9') == 123456789

def test_chunks():
    lst = [1,2,3,4,5]
    assert list(chunks(lst, 2)) == [[1,2],[3,4],[5]]

def test_dict_get_path():
    d = {'a': {'b': {'c': 42}}}
    assert dict_get_path(d, ['a','b','c']) == 42
    assert dict_get_path(d, ['a','x'], default='nope') == 'nope'

if __name__ == '__main__':
    test_CleanText()
    test_base36()
    test_unbase36()
    test_chunks()
    test_dict_get_path()
    print('util tests passed')