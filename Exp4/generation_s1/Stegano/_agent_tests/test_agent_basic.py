import os
import math
import wave
import struct
import pytest
from PIL import Image

from stegano import lsb, red, exifHeader, wav
from stegano.lsb.generators import eratosthenes


def test_imports():
    assert hasattr(lsb, "hide") and hasattr(lsb, "reveal")
    assert hasattr(red, "hide") and hasattr(red, "reveal")
    assert hasattr(exifHeader, "hide") and hasattr(exifHeader, "reveal")
    assert hasattr(wav, "hide") and hasattr(wav, "reveal")


def test_eratosthenes_primes():
    g = eratosthenes()
    primes = [next(g) for _ in range(10)]
    assert primes == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_lsb_roundtrip_sequential_rgb():
    img = Image.new("RGB", (64, 64), (120, 130, 140))
    out = lsb.hide(img, "hello world")
    assert out.size == img.size
    assert lsb.reveal(out) == "hello world"


def test_lsb_roundtrip_generator_and_shift():
    img = Image.new("RGB", (80, 80), (10, 20, 30))
    msg = "generator message"
    out = lsb.hide(img, msg, generator=eratosthenes(), shift=10)
    assert lsb.reveal(out, generator=eratosthenes(), shift=10) == msg
    with pytest.raises(Exception):
        # wrong shift should not successfully decode
        lsb.reveal(out, generator=eratosthenes(), shift=0)


def test_lsb_auto_convert_rgb_behavior():
    img_l = Image.new("L", (50, 50), 128)
    with pytest.raises(ValueError):
        lsb.hide(img_l, "x", auto_convert_rgb=False)
    out = lsb.hide(img_l, "x", auto_convert_rgb=True)
    assert out.mode == "RGB"
    assert out.size == img_l.size
    assert lsb.reveal(out) == "x"


def test_lsb_rgba_preserves_alpha():
    img = Image.new("RGBA", (40, 40), (1, 2, 3, 200))
    out = lsb.hide(img, "alpha", auto_convert_rgb=False)
    assert out.mode == "RGBA"
    assert out.getchannel("A").tobytes() == img.getchannel("A").tobytes()
    assert lsb.reveal(out) == "alpha"


def test_lsb_capacity_error():
    img = Image.new("RGB", (2, 2), (0, 0, 0))  # capacity 12 bits => 1 byte payload at most after length framing => impossible
    with pytest.raises(ValueError):
        lsb.hide(img, "hi")


def test_red_roundtrip_rgb_and_rgba_alpha_preserved():
    img = Image.new("RGB", (80, 80), (100, 150, 200))
    out = red.hide(img, "red secret")
    assert out.size == img.size
    assert red.reveal(out) == "red secret"

    img_a = Image.new("RGBA", (80, 80), (100, 150, 200, 77))
    out_a = red.hide(img_a, "rgba secret")
    assert out_a.getchannel("A").tobytes() == img_a.getchannel("A").tobytes()
    assert red.reveal(out_a) == "rgba secret"


def test_red_capacity_error():
    img = Image.new("RGB", (4, 4), (0, 0, 0))  # 16 bits, but framing alone is 32 bits
    with pytest.raises(ValueError):
        red.hide(img, "x")


def test_exif_hide_reveal_jpeg(tmp_path):
    # create a simple jpeg
    inp = tmp_path / "in.jpg"
    outp = tmp_path / "out.jpg"
    img = Image.new("RGB", (64, 64), (12, 34, 56))
    img.save(inp, "JPEG")

    exifHeader.hide(str(inp), str(outp), secret_message=b"abc")
    assert outp.exists()
    got = exifHeader.reveal(str(outp))
    assert got == b"abc"

    # no payload case
    blank = tmp_path / "blank.jpg"
    img.save(blank, "JPEG")
    assert exifHeader.reveal(str(blank)) == b""


def _make_wav(path, duration_s=0.25, sr=8000, freq=440.0):
    n = int(duration_s * sr)
    samples = []
    for i in range(n):
        t = i / sr
        v = int(20000 * math.sin(2 * math.pi * freq * t))
        samples.append(v)
    frames = struct.pack("<" + "h" * n, *samples)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(frames)


def test_wav_hide_reveal_roundtrip(tmp_path):
    inp = tmp_path / "in.wav"
    outp = tmp_path / "out.wav"
    _make_wav(inp, duration_s=0.5)

    wav.hide(str(inp), "audio secret", str(outp))
    assert outp.exists()
    assert wav.reveal(str(outp)) == "audio secret"

    # parameters preserved
    with wave.open(str(inp), "rb") as r1, wave.open(str(outp), "rb") as r2:
        assert r1.getparams() == r2.getparams()


def test_wav_capacity_error(tmp_path):
    inp = tmp_path / "short.wav"
    outp = tmp_path / "out.wav"
    _make_wav(inp, duration_s=0.02, sr=8000)  # very short
    with pytest.raises(ValueError):
        wav.hide(str(inp), "this message is too long for the tiny audio", str(outp))