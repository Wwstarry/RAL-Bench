from mailpile.vcard import VCardLine

def test_parse_simple():
    line = 'EMAIL:foo@bar.com'
    vcl = VCardLine.parse(line)
    assert vcl.name == 'EMAIL'
    assert vcl.value == 'foo@bar.com'
    assert vcl.params == {}

def test_parse_params():
    line = 'TEL;TYPE=HOME,VOICE;VALUE=uri:tel:+1-111-555-1212'
    vcl = VCardLine.parse(line)
    assert vcl.name == 'TEL'
    assert vcl.value == 'tel:+1-111-555-1212'
    assert vcl.params['TYPE'] == 'HOME,VOICE'
    assert vcl.params['VALUE'] == 'uri'

def test_serialize():
    vcl = VCardLine('FN', {'LANGUAGE': 'en'}, 'John Doe')
    s = vcl.serialize()
    assert s == 'FN;LANGUAGE=en:John Doe'

def test_roundtrip():
    line = 'EMAIL;TYPE=INTERNET:foo@bar.com'
    vcl = VCardLine.parse(line)
    assert vcl.serialize() == line

if __name__ == '__main__':
    test_parse_simple()
    test_parse_params()
    test_serialize()
    test_roundtrip()
    print('vcard tests passed')