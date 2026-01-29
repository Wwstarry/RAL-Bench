"""
Main console interface
"""

import argparse
import sys
from stegano import lsb, red, exifHeader, wav


def main():
    """Main entry point for console interface"""
    parser = argparse.ArgumentParser(description='Stegano - Steganography library')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # LSB hide command
    lsb_hide = subparsers.add_parser('lsb-hide', help='Hide message in image using LSB')
    lsb_hide.add_argument('input', help='Input image file')
    lsb_hide.add_argument('output', help='Output image file')
    lsb_hide.add_argument('message', help='Message to hide')
    
    # LSB reveal command
    lsb_reveal = subparsers.add_parser('lsb-reveal', help='Reveal message from image')
    lsb_reveal.add_argument('input', help='Input image file')
    
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