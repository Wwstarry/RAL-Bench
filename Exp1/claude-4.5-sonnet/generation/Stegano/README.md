# Stegano

A pure Python steganography library providing multiple steganography techniques.

## Features

- **LSB (Least Significant Bit)**: Hide messages in image pixels using LSB technique
- **Red Channel**: Hide messages in the red channel of RGB images
- **EXIF Header**: Hide messages in JPEG/TIFF EXIF metadata
- **WAV Audio**: Hide messages in WAV audio files

## Installation

```bash
pip install -e .
```

## Usage

### LSB Steganography

```python
from stegano import lsb

# Hide a message
secret_image = lsb.hide("input.png", "Secret message")
secret_image.save("output.png")

# Reveal a message
message = lsb.reveal("output.png")
print(message)
```

### Red Channel Steganography

```python
from stegano import red

# Hide a message
secret_image = red.hide("input.png", "Secret message")
secret_image.save("output.png")

# Reveal a message
message = red.reveal("output.png")
print(message)
```

### EXIF Header Steganography

```python
from stegano import exifHeader

# Hide a message
exifHeader.hide("input.jpg", "output.jpg", b"Secret message")

# Reveal a message
message = exifHeader.reveal("output.jpg")
print(message)
```

### WAV Audio Steganography

```python
from stegano import wav

# Hide a message
wav.hide("input.wav", "Secret message", "output.wav")

# Reveal a message
message = wav.reveal("output.wav")
print(message)
```

## License

MIT License