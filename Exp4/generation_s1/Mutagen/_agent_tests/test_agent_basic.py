import os
import pytest

from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC


def test_easyid3_roundtrip_tag_only(tmp_path):
    p = tmp_path / "a.mp3"
    t = EasyID3()
    t["title"] = ["Song Title"]
    t["artist"] = ["Artist"]
    t.save(str(p))

    t2 = EasyID3(str(p))
    assert t2["title"] == ["Song Title"]
    assert t2["artist"] == ["Artist"]


def test_easyid3_multiple_values_overwrite_delete(tmp_path):
    p = tmp_path / "b.mp3"
    t = EasyID3()
    t["artist"] = ["A1", "A2"]
    t["title"] = "Old"
    t.save(str(p))

    t2 = EasyID3(str(p))
    assert t2["artist"] == ["A1", "A2"]
    assert t2["title"] == ["Old"]

    t2["title"] = ["New"]
    del t2["artist"]
    t2.save()

    t3 = EasyID3(str(p))
    assert t3["title"] == ["New"]
    with pytest.raises(KeyError):
        _ = t3["artist"]
    assert "artist" not in list(t3)


def test_id3_text_comm_apic_roundtrip_and_ops(tmp_path):
    p = tmp_path / "c.mp3"

    tags = ID3()
    tags.add(TIT2(3, text=["T1"]))
    tags.add(TPE1(3, text=["P1", "P2"]))
    tags.add(COMM(3, "eng", "d1", ["hello"]))
    tags.add(COMM(3, "eng", "d2", ["world"]))
    data1 = b"\x89PNG\r\n\x1a\n" + b"data1"
    data2 = b"\xff\xd8\xff" + b"data2"
    tags.add(APIC(3, "image/png", 3, "cover", data1))
    tags.add(APIC(3, "image/jpeg", 3, "other", data2))
    tags.save(str(p))

    tags2 = ID3(str(p))
    assert tags2["TIT2"].text == ["T1"]
    assert tags2["TPE1"].text == ["P1", "P2"]

    comms = tags2.getall("COMM")
    assert len(comms) == 2
    assert {(c.lang, c.desc, tuple(c.text)) for c in comms} == {("eng", "d1", ("hello",)), ("eng", "d2", ("world",))}

    apics = tags2.getall("APIC")
    assert len(apics) == 2
    assert apics[0].data.startswith(b"\x89PNG\r\n\x1a\n") or apics[1].data.startswith(b"\x89PNG\r\n\x1a\n")
    assert apics[0].data[:3] in (b"\x89PN", b"\xff\xd8\xff") or apics[1].data[:3] in (b"\x89PN", b"\xff\xd8\xff")

    # overwrite TIT2 via setall
    tags2.setall("TIT2", [TIT2(3, text=["T2"])])
    tags2.save()
    tags3 = ID3(str(p))
    assert tags3["TIT2"].text == ["T2"]
    assert len(tags3.getall("TIT2")) == 1

    # delall APIC
    tags3.delall("APIC")
    tags3.save()
    tags4 = ID3(str(p))
    assert tags4.getall("APIC") == []


def test_preserve_prefix_bytes_when_tagging_existing_file(tmp_path):
    p = tmp_path / "raw.mp3"
    prefix = b"NOTANMP3" * 1000
    p.write_bytes(prefix)

    t = EasyID3(str(p))
    t["title"] = ["X"]
    t.save()

    # ensure prefix preserved (file now longer because tag appended/replaced)
    new = p.read_bytes()
    assert new.startswith(prefix)

    # repeat save should not grow linearly
    size1 = os.path.getsize(p)
    t2 = EasyID3(str(p))
    t2["title"] = ["Y"]
    t2.save()
    size2 = os.path.getsize(p)
    assert size2 <= size1 + 200  # small change only
    assert EasyID3(str(p))["title"] == ["Y"]