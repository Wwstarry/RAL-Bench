import argparse
from stegano import lsb, red, exifHeader, wav

def main():
    parser = argparse.ArgumentParser(description="Steganography tool")
    parser.add_argument("mode", choices=["hide", "reveal"], help="Mode of operation")
    parser.add_argument("backend", choices=["lsb", "red", "exifHeader", "wav"], help="Steganography backend")
    parser.add_argument("input", help="Input file")
    parser.add_argument("--message", help="Message to hide")
    parser.add_argument("--output", help="Output file")
    args = parser.parse_args()

    if args.backend == "lsb":
        if args.mode == "hide":
            image = lsb.hide(args.input, args.message)
            image.save(args.output)
        elif args.mode == "reveal":
            print(lsb.reveal(args.input))
    elif args.backend == "red":
        if args.mode == "hide":
            image = red.hide(args.input, args.message)
            image.save(args.output)
        elif args.mode == "reveal":
            print(red.reveal(args.input))
    elif args.backend == "exifHeader":
        if args.mode == "hide":
            exifHeader.hide(args.input, args.output, args.message.encode())
        elif args.mode == "reveal":
            print(exifHeader.reveal(args.input).decode())
    elif args.backend == "wav":
        if args.mode == "hide":
            wav.hide(args.input, args.message, args.output)
        elif args.mode == "reveal":
            print(wav.reveal(args.input))

if __name__ == "__main__":
    main()