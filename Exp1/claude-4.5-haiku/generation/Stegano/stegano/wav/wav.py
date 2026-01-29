"""
WAV audio steganography implementation
"""

import wave
import struct


def hide(input_file, message, output_file, **kwargs):
    """
    Hide a message in a WAV audio file using LSB steganography.
    
    Args:
        input_file: Path to input WAV file
        message: String message to hide
        output_file: Path where output WAV file will be written
        **kwargs: Additional arguments
    
    Returns:
        None (writes to output_file)
    """
    if isinstance(message, str):
        message_bytes = message.encode('UTF-8')
    else:
        message_bytes = message
    
    # Open input WAV file
    with wave.open(input_file, 'rb') as wav_in:
        n_channels = wav_in.getnchannels()
        sample_width = wav_in.getsampwidth()
        framerate = wav_in.getframerate()
        n_frames = wav_in.getnframes()
        
        # Read audio data
        audio_data = wav_in.readframes(n_frames)
    
    # Convert audio data to samples
    samples = _audio_to_samples(audio_data, sample_width, n_channels)
    
    # Encode message
    message_bits = _bytes_to_bits(message_bytes)
    
    # Add length header (32 bits)
    length = len(message_bytes)
    length_bits = _int_to_bits(length, 32)
    all_bits = length_bits + message_bits
    
    # Hide message in LSB of samples
    bit_index = 0
    for i in range(len(samples)):
        if bit_index >= len(all_bits):
            break
        
        bit = all_bits[bit_index]
        bit_index += 1
        
        # Modify LSB
        samples[i] = (samples[i] & ~1) | bit
    
    # Convert samples back to audio data
    audio_data = _samples_to_audio(samples, sample_width, n_channels)
    
    # Write output WAV file
    with wave.open(output_file, 'wb') as wav_out:
        wav_out.setnchannels(n_channels)
        wav_out.setsampwidth(sample_width)
        wav_out.setframerate(framerate)
        wav_out.writeframes(audio_data)


def reveal(input_file, **kwargs):
    """
    Reveal a hidden message from a WAV audio file.
    
    Args:
        input_file: Path to input WAV file
        **kwargs: Additional arguments
    
    Returns:
        Decoded message string
    """
    # Open WAV file
    with wave.open(input_file, 'rb') as wav_in:
        n_channels = wav_in.getnchannels()
        sample_width = wav_in.getsampwidth()
        n_frames = wav_in.getnframes()
        
        # Read audio data
        audio_data = wav_in.readframes(n_frames)
    
    # Convert audio data to samples
    samples = _audio_to_samples(audio_data, sample_width, n_channels)
    
    # Extract bits from LSB
    extracted_bits = []
    for sample in samples:
        bit = sample & 1
        extracted_bits.append(bit)
    
    # Extract length (first 32 bits)
    if len(extracted_bits) < 32:
        raise ValueError("Audio file too small to contain message")
    
    length_bits = extracted_bits[:32]
    length = _bits_to_int(length_bits)
    
    # Extract message bits
    message_bits = extracted_bits[32:32 + length * 8]
    
    if len(message_bits) < length * 8:
        raise ValueError("Incomplete message in audio")
    
    # Convert bits to bytes
    message_bytes = _bits_to_bytes(message_bits)
    
    return message_bytes.decode('UTF-8')


def _audio_to_samples(audio_data, sample_width, n_channels):
    """Convert audio data to list of samples"""
    samples = []
    
    if sample_width == 1:
        for i in range(0, len(audio_data), n_channels):
            for ch in range(n_channels):
                if i + ch < len(audio_data):
                    sample = audio_data[i + ch]
                    samples.append(sample)
    elif sample_width == 2:
        for i in range(0, len(audio_data), 2 * n_channels):
            for ch in range(n_channels):
                if i + 2*ch + 1 < len(audio_data):
                    sample = struct.unpack('<h', audio_data[i + 2*ch:i + 2*ch + 2])[0]
                    samples.append(sample & 0xFFFF)
    else:
        # For other sample widths, treat as bytes
        for byte in audio_data:
            samples.append(byte)
    
    return samples


def _samples_to_audio(samples, sample_width, n_channels):
    """Convert list of samples back to audio data"""
    audio_data = b''
    
    if sample_width == 1:
        for sample in samples:
            audio_data += bytes([sample & 0xFF])
    elif sample_width == 2:
        for sample in samples:
            audio_data += struct.pack('<h', sample & 0xFFFF)
    else:
        for sample in samples:
            audio_data += bytes([sample & 0xFF])
    
    return audio_data


def _bytes_to_bits(data):
    """Convert bytes to list of bits"""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes(bits):
    """Convert list of bits to bytes"""
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            byte_bits.extend([0] * (8 - len(byte_bits)))
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        bytes_list.append(byte)
    return bytes(bytes_list)


def _int_to_bits(value, num_bits):
    """Convert integer to list of bits"""
    bits = []
    for i in range(num_bits - 1, -1, -1):
        bits.append((value >> i) & 1)
    return bits


def _bits_to_int(bits):
    """Convert list of bits to integer"""
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value