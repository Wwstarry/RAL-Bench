"""
WAV audio steganography implementation
"""

import wave
import struct


def hide(input_wav_file, message, output_wav_file, encoding="UTF-8"):
    """
    Hide a message in a WAV file using LSB.
    
    Args:
        input_wav_file: Path to input WAV file
        message: String message to hide
        output_wav_file: Path to output WAV file
        encoding: Text encoding (default: UTF-8)
        
    Returns:
        Path to output file
    """
    # Open input WAV file
    with wave.open(input_wav_file, 'rb') as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)
    
    # Convert frames to list of samples
    sample_width = params.sampwidth
    num_samples = len(frames) // sample_width
    
    if sample_width == 1:
        fmt = f'{num_samples}B'
    elif sample_width == 2:
        fmt = f'{num_samples}h'
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")
    
    samples = list(struct.unpack(fmt, frames))
    
    # Encode message
    message_bytes = message.encode(encoding)
    message_bytes += b'\x00\x00\x00\x00'  # Null terminator
    
    # Convert to bits
    bits = []
    for byte in message_bytes:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    
    if len(bits) > len(samples):
        raise ValueError("Message too long for audio file")
    
    # Hide bits in samples
    for i, bit in enumerate(bits):
        samples[i] = (samples[i] & ~1) | bit
    
    # Pack samples back to bytes
    modified_frames = struct.pack(fmt, *samples)
    
    # Write output WAV file
    with wave.open(output_wav_file, 'wb') as wav_out:
        wav_out.setparams(params)
        wav_out.writeframes(modified_frames)
    
    return output_wav_file


def reveal(input_wav_file, encoding="UTF-8"):
    """
    Reveal a hidden message from a WAV file.
    
    Args:
        input_wav_file: Path to WAV file
        encoding: Text encoding (default: UTF-8)
        
    Returns:
        Decoded message string
    """
    # Open WAV file
    with wave.open(input_wav_file, 'rb') as wav_in:
        params = wav_in.getparams()
        frames = wav_in.readframes(params.nframes)
    
    # Convert frames to samples
    sample_width = params.sampwidth
    num_samples = len(frames) // sample_width
    
    if sample_width == 1:
        fmt = f'{num_samples}B'
    elif sample_width == 2:
        fmt = f'{num_samples}h'
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")
    
    samples = struct.unpack(fmt, frames)
    
    # Extract bits
    bits = []
    null_count = 0
    
    for sample in samples:
        bit = sample & 1
        bits.append(bit)
        
        # Check for null terminator every 8 bits
        if len(bits) % 8 == 0:
            byte_val = 0
            for i in range(8):
                byte_val = (byte_val << 1) | bits[-(8-i)]
            
            if byte_val == 0:
                null_count += 1
                if null_count == 4:
                    # Found terminator
                    bits = bits[:-32]
                    message_bytes = bytearray()
                    for i in range(0, len(bits), 8):
                        if i + 8 <= len(bits):
                            byte_val = 0
                            for j in range(8):
                                byte_val = (byte_val << 1) | bits[i + j]
                            message_bytes.append(byte_val)
                    
                    return message_bytes.decode(encoding, errors='ignore')
            else:
                null_count = 0
    
    return ""