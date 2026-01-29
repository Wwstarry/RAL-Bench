import sys
from PIL import Image
from ..lsb import hide as lsb_hide, reveal as lsb_reveal
from ..red import hide as red_hide, reveal as red_reveal
from ..wav import hide as wav_hide, reveal as wav_reveal
from ..exifHeader import hide as exif_hide, reveal as exif_reveal

def main(argv=None):
    """
    Minimal console entry.
    Usage examples (not exhaustive):
    - Hide in image LSB: lsb_hide input.png "secret" output.png
    - Reveal from image LSB: lsb_reveal input.png
    """
    argv = argv or sys.argv[1:]
    if not argv:
        print("Stegano console minimal usage:")
        print("lsb hide <in> <message> <out>")
        print("lsb reveal <in>")
        print("red hide <in> <message> <out>")
        print("red reveal <in>")
        print("wav hide <in.wav> <message> <out.wav>")
        print("wav reveal <in.wav>")
        print("exif hide <in.jpg|.tif> <message> <out>")
        print("exif reveal <in.jpg|.tif>")
        return 0

    cmd = argv[0].lower()
    try:
        if cmd == "lsb":
            sub = argv[1].lower()
            if sub == "hide":
                in_path, msg, out_path = argv[2], argv[3], argv[4]
                im = Image.open(in_path)
                out_img = lsb_hide(im, msg)
                out_img.save(out_path)
                print("LSB hide done:", out_path)
            elif sub == "reveal":
                in_path = argv[2]
                im = Image.open(in_path)
                print(lsb_reveal(im))
            else:
                print("Unknown lsb subcommand.")
        elif cmd == "red":
            sub = argv[1].lower()
            if sub == "hide":
                in_path, msg, out_path = argv[2], argv[3], argv[4]
                im = Image.open(in_path)
                out_img = red_hide(im, msg)
                out_img.save(out_path)
                print("Red hide done:", out_path)
            elif sub == "reveal":
                in_path = argv[2]
                im = Image.open(in_path)
                print(red_reveal(im))
            else:
                print("Unknown red subcommand.")
        elif cmd == "wav":
            sub = argv[1].lower()
            if sub == "hide":
                in_path, msg, out_path = argv[2], argv[3], argv[4]
                wav_hide(in_path, msg, out_path)
                print("WAV hide done:", out_path)
            elif sub == "reveal":
                in_path = argv[2]
                print(wav_reveal(in_path))
            else:
                print("Unknown wav subcommand.")
        elif cmd == "exif":
            sub = argv[1].lower()
            if sub == "hide":
                in_path, msg, out_path = argv[2], argv[3], argv[4]
                exif_hide(in_path, out_path, secret_message=msg)
                print("EXIF hide done:", out_path)
            elif sub == "reveal":
                in_path = argv[2]
                data = exif_reveal(in_path)
                try:
                    print(data.decode("utf-8"))
                except Exception:
                    print(repr(data))
            else:
                print("Unknown exif subcommand.")
        else:
            print("Unknown command.")
    except Exception as e:
        print("Error:", e)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())