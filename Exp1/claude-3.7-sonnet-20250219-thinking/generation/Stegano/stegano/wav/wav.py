"""
WAV steganography implementation.
Hides and reveals messages in PCM audio samples.
"""
import wave
import struct
from typing import Union, Optional

def hide(
    input_file: str,
    message: str,
    output_file: str,
    lsb_bits: int = 1,
    encoding: str = "UTF-8"
) -> None:
    """
    Hide a message in a WAV audio file.
    
    Args:
        input_file: Path to the input WAV file
        message: Message to hide
        output_file: Path where the output WAV file will be saved
        lsb_bits: Number of least significant bits to use
        encoding: Character encoding for the message
        
    Returns:
        None
    """
    # Validate the number of LSB bits
    if lsb_bits < 1 or lsb_bits > 8:
        raise ValueError("lsb_bits must be between 1 and 8")
    
    # Open the WAV file
    try:
        wav_file = wave.open(input_file, 'rb')
    except:
        raise ValueError(f"Failed to open WAV file: {input_file}")
    
    # Get file parameters
    num_channels = wav_file.getnchannels()
    sample_width = wav_file.getsampwidth()
    num_frames = wav_file.getnframes()
    framerate = wav_file.getframerate()
    
    # Convert message to binary, add null terminator
    message_bytes = (message + '\0').encode(encoding)
    binary_message = ''.join(format(b, '08b') for b in message_bytes)
    
    # Check if the message fits in the audio file
    max_bits = num_frames * num_channels * lsb_bits
    if len(binary_message) > max_bits:
        raise ValueError(
            f"Message too large. Maximum capacity: {max_bits // 8} bytes, "
            f"Message size: {len(message_bytes)} bytes"
        )
    
    # Read all audio data
    audio_data = bytearray(wav_file.readframes(num_frames))
    wav_file.close()
    
    # Create a mask for clearing the LSBs we'll be using
    clear_mask = (0xFF << lsb_bits) & 0xFF
    
    # Embed the message
    binary_index = 0
    for i in range(0, len(audio_data), sample_width):
        if binary_index >= len(binary_message):
            break
        
        # Process each byte in the sample (assuming little-endian)
        for j in range(min(sample_width, len(audio_data) - i)):
            if binary_index >= len(binary_message):
                break
            
            # Determine how many bits we can embed in this byte
            bits_to_embed = min(lsb_bits, len(binary_message) - binary_index)
            
            # Extract the bits from the message
            message_bits = binary_message[binary_index:binary_index + bits_to_embed]
            binary_index += bits_to_embed
            
            # Clear the LSBs in the audio byte
            audio_data[i + j] &= clear_mask
            
            # Embed the message bits
            audio_data[i + j] |= int(message_bits.ljust(lsb_bits, '0'), 2)
    
    # Create the output WAV file
    output_wav = wave.open(output_file, 'wb')
    output_wav.setparams((num_channels, sample_width, framerate, num_frames, 'NONE', 'not compressed'))
    output_wav.writeframes(audio_data)
    output_wav.close()

def reveal(
    input_file: str,
    lsb_bits: int = 1,
    encoding: str = "UTF-8"
) -> str:
    """
    Reveal a message hidden in a WAV audio file.
    
    Args:
        input_file: Path to the WAV file
        lsb_bits: Number of least significant bits used
        encoding: Character encoding for the message
        
    Returns:
        The hidden message
    """
    # Validate the number of LSB bits
    if lsb_bits < 1 or lsb_bits > 8:
        raise ValueError("lsb_bits must be between 1 and 8")
    
    # Open the WAV file
    try:
        wav_file = wave.open(input_file, 'rb')
    except:
        raise ValueError(f"Failed to open WAV file: {input_file}")
    
    # Get file parameters
    num_channels = wav_file.getnchannels()
    sample_width = wav_file.getsampwidth()
    num_frames = wav_file.getnframes()
    
    # Read all audio data
    audio_data = bytearray(wav_file.readframes(num_frames))
    wav_file.close()
    
    # Create a mask for extracting the LSBs
    extract_mask = (1 << lsb_bits) - 1
    
    # Extract the message
    binary_message = ""
    null_byte_found = False
    
    for i in range(0, len(audio_data), sample_width):
        if null_byte_found:
            break
        
        # Process each byte in the sample
        for j in range(min(sample_width, len(audio_data) - i)):
            # Extract the LSBs
            lsbs = audio_data[i + j] & extract_mask
            binary_message += format(lsbs, f'0{lsb_bits}b')
            
            # Check if we have complete bytes
            while len(binary_message) >= 8:
                byte = binary_message[:8]
                binary_message = binary_message[8:]
                
                # Check if this is a null byte (end of message)
                if byte == '00000000':
                    null_byte_found = True
                    break
                
                # Otherwise, this is part of the message
    
    # Convert binary to text
    message_bytes = bytearray()
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = int(binary_message[i:i+8], 2)
            message_bytes.append(byte)
    
    # Try to decode the message
    try:
        message = message_bytes.decode(encoding)
    except UnicodeDecodeError:
        message = message_bytes.decode(encoding, errors="replace")
    
    return message