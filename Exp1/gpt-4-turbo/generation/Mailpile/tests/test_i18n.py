from mailpile.i18n import _, gettext_passthrough

def test_gettext_passthrough():
    s = 'Hello World'
    assert gettext_passthrough(s) == s
    assert _(s) == s

if __name__ == '__main__':
    test_gettext_passthrough()
    print('i18n tests passed')