import wave
import struct
from stegano.tools.utils import get_mask_and_val, str_to_bin, bin_to_str

def hide(input_file, message, output_file):
    """
    Hide a message in a WAV file using LSB of audio samples.
    """
    wav_in = wave.open(input_file, 'rb')
    params = wav_in.getparams()
    num_frames = wav_in.getnframes()
    frames = bytearray(wav_in.readframes(num_frames))
    wav_in.close()
    
    message_str = str(message) + "\x00"
    binary_message = str_to_bin(message_str)
    
    # Iterate over bytes of the frames
    # Note: This modifies the LSB of every byte. 
    # For 16-bit audio, this modifies the LSB of both the MSB and LSB bytes of the sample.
    # This is the standard "naive" implementation.
    
    try:
        for i in range(len(frames)):
            try:
                bit = next(binary_message)
            except StopIteration:
                break
            
            frames[i] = get_mask_and_val(frames[i], bit)
    except StopIteration:
        pass
        
    wav_out = wave.open(output_file, 'wb')
    wav_out.setparams(params)
    wav_out.writeframes(frames)
    wav_out.close()

def reveal(input_file):
    """
    Reveal a message from a WAV file.
    """
    wav_in = wave.open(input_file, 'rb')
    frames = bytearray(wav_in.readframes(wav_in.getnframes()))
    wav_in.close()
    
    extracted_bits = []
    
    for byte_val in frames:
        extracted_bits.append(byte_val & 1)
        
        if len(extracted_bits) % 8 == 0:
            last_byte_bits = extracted_bits[-8:]
            val = 0
            for b in last_byte_bits:
                val = (val << 1) | b
            
            if val == 0:
                return bin_to_str(extracted_bits[:-8])
                
    return bin_to_str(extracted_bits)