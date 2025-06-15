import torch
import librosa
import numpy as np
import sys, os
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

# Load model and processor (match sizes!)
processor = AutoProcessor.from_pretrained("openai/whisper-small")
model = AutoModelForSpeechSeq2Seq.from_pretrained("openai/whisper-small")

def chunk_audio(audio_array, chunk_duration_sec=30, sampling_rate=16000):
    """Split audio into chunks of specified duration (in seconds)."""
    chunk_size = sampling_rate * chunk_duration_sec
    return [
        audio_array[i:i + chunk_size]
        for i in range(0, len(audio_array), chunk_size)
    ]

def transcribe_chunk(chunk_array, sampling_rate=16000, max_new_tokens=444):
    """Transcribe a single audio chunk using Whisper."""
    # Pad or trim to 30 seconds
    target_length = sampling_rate * 30
    if len(chunk_array) > target_length:
        chunk_array = chunk_array[:target_length]
    else:
        chunk_array = np.pad(chunk_array, (0, target_length - len(chunk_array)), 'constant')

    # Prepare input
    inputs = processor(
        chunk_array,
        sampling_rate=sampling_rate,
        return_tensors="pt",
        return_attention_mask=True
    )

    # Generate transcription
    with torch.no_grad():
        predicted_ids = model.generate(
            inputs.input_features,
            attention_mask=inputs.attention_mask,
            max_new_tokens=max_new_tokens,
            num_beams=1,
            temperature=0.0,
            early_stopping=False,
            return_dict_in_generate=False,
            forced_decoder_ids=None
        )

    # Decode result
    transcription = processor.batch_decode(
        predicted_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True
    )[0]

    return transcription.strip()

def transcribe_audio(audio_path, output_dir="output"):
    """Transcribe an entire .wav file using chunking and save to markdown."""
    audio_array, _ = librosa.load(audio_path, sr=16000, mono=True)
    audio_chunks = chunk_audio(audio_array)

    full_transcription = ""
    for i, chunk in enumerate(audio_chunks):
        print(f"Transcribing chunk {i+1}/{len(audio_chunks)}...")
        chunk_text = transcribe_chunk(chunk)
        full_transcription += chunk_text + " "

    # Save to markdown
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_transcription.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_transcription.strip())

    return {"text": full_transcription.strip(), "output_path": output_path}

if __name__ == "__main__":

    audio_file = r"C:/Users/Qualcomm/Desktop/class_audio.wav"
    try:
        result = transcribe_audio(audio_file)

        print(f"\n✅ Transcription saved to: {result['output_path']}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)