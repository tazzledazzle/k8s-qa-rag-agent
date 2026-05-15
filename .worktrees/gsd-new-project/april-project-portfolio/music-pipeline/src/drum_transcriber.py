import os
import numpy as np
import librosa
import pretty_midi
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_drums_to_midi(drum_wav_path: str, output_dir: str = "./output") -> str:
    """
    Transcribes an isolated drum stem to MIDI using a deterministic
    spectral-energy onset detection approach.

    This replaces the Omnizart implementation for M2 compatibility.

    Args:
        drum_wav_path: Path to the isolated drum WAV file.
        output_dir: Directory to save the resulting MIDI file.

    Returns:
        The path to the generated MIDI file.
    """
    logger.info(f"Transcribing drums from: {drum_wav_path}")

    try:
        # 1. Load the audio file
        y, sr = librosa.load(drum_wav_path, sr=None)

        # 2. Detect onsets
        # backtrack=True helps align onsets with the actual start of the transient
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)

        # 3. Create PrettyMIDI object
        # program=0 is standard, is_drum=True tells PM it's a drum track (Channel 10)
        midi_data = pretty_midi.PrettyMIDI()
        drum_track = pretty_midi.Instrument(program=0, is_drum=True)

        # Frequency band definitions (General MIDI Drum Map compatibility)
        # MIDI 36: Bass Drum 1 (Kick)
        # MIDI 38: Acoustic Snare
        # MIDI 42: Closed Hi-Hat
        BANDS = {
            'kick': (0, 200),
            'snare': (200, 3000),
            'hat': (3000, 10000)
        }
        MIDI_MAP = {
            'kick': 36,
            'snare': 38,
            'hat': 42
        }

        # Window size for spectral analysis (100ms)
        window_size = int(0.1 * sr)

        for t in onset_times:
            # Extract window starting at onset
            start_sample = int(t * sr)
            end_sample = start_sample + window_size

            if end_sample > len(y):
                end_sample = len(y)

            window = y[start_sample:end_sample]
            if len(window) == 0:
                continue

            # Compute Power Spectral Density (PSD) using FFT
            # Use a Hanning window to reduce spectral leakage
            fft_window = window * np.hanning(len(window))
            spectrum = np.abs(np.fft.rfft(fft_window))
            freqs = np.fft.rfftfreq(len(window), 1/sr)

            # Calculate energy in each band
            energies = {}
            for name, (low, high) in BANDS.items():
                mask = (freqs >= low) & (freqs <= high)
                energies[name] = np.sum(spectrum[mask]**2)

            # Determine dominant sound (or multiple if they both cross a threshold)
            # We use a relative threshold to avoid triggering on tiny noise
            max_energy = max(energies.values())
            if max_energy == 0:
                continue

            # Trigger any band that has at least 30% of the max energy
            # This allows simultaneous kick and snare/hat hits
            for name, energy in energies.items():
                if energy > 0.3 * max_energy:
                    pitch = MIDI_MAP[name]
                    # Create a short note (100ms)
                    note = pretty_midi.Note(
                        velocity=100,
                        pitch=pitch,
                        start=t,
                        end=t + 0.1
                    )
                    drum_track.notes.append(note)

        midi_data.instruments.append(drum_track)

        # 4. Save output
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_name = Path(drum_wav_path).stem + "_transcribed.mid"
        final_path = str(output_path / file_name)

        midi_data.write(final_path)
        logger.info(f"Successfully saved MIDI to: {final_path}")

        return final_path

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise e
