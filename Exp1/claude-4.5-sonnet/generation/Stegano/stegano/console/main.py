"""
Main console entry point
"""

import argparse
import sys
from stegano import lsb, red, exifHeader, wav


def main():
    """
    Main console interface
    """
    parser = argparse.ArgumentParser(description='Stegano - Steganography tool')
    parser.add_argument('--version', action='version', version='stegano 0.11.3')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # LSB hide
    lsb_hide = subparsers.add_parser('lsb-hide', help='Hide message using LSB')
    lsb_hide.add_argument('-i', '--input', required=True, help='Input image')
    lsb_hide.add_argument('-m', '--message', required=True, help='Message to hide')
    lsb_hide.add_argument('-o', '--output', required=True, help='Output image')
    
    # LSB reveal
    lsb_reveal = subparsers.add_parser('lsb-reveal', help='Reveal message using LSB')
    lsb_reveal.add_argument('-i', '--input', required=True, help='Input image')
    
    args = parser.parse_args()
    
    if args.command == 'lsb-hide':
        img = lsb.hide(args.input, args.message)
        img.save(args.output)
        print(f"Message hidden in {args.output}")
    elif args.command == 'lsb-reveal':
        message = lsb.reveal(args.input)
        print(message)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()