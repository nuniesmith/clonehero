import os
import librosa
import numpy as np
from pathlib import Path
from loguru import logger

OUTPUT_DIR = Path("processed_songs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NOTE_MAPPING = 6  # Number of note types in Clone Hero

def analyze_audio(file_path: str):
    """Analyze audio to detect tempo, beats, and note positions."""
    try:
        y, sr = librosa.load(file_path, sr=None)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        peaks = librosa.util.peak_pick(
            onset_env, pre_max=3, post_max=3, pre_avg=5, post_avg=5, delta=0.5, wait=10
        )
        note_times = librosa.frames_to_time(peaks, sr=sr)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        note_frequencies = np.argmax(chroma, axis=0)

        hammer_ons, pull_offs, tapping_notes = classify_note_types(note_times)

        return tempo, beat_times, note_times, note_frequencies, hammer_ons, pull_offs, tapping_notes
    except Exception as e:
        logger.error(f"Error analyzing audio: {str(e)}")
        raise

def classify_note_types(note_times):
    """Classify notes into hammer-ons, pull-offs, and tapping notes."""
    hammer_ons, pull_offs, tapping_notes = [], [], []

    for i in range(1, len(note_times)):
        interval = note_times[i] - note_times[i - 1]
        if interval < 0.08:
            tapping_notes.append(note_times[i])  # Very fast tapping
        elif interval < 0.15:
            hammer_ons.append(note_times[i]) if i % 2 == 0 else pull_offs.append(note_times[i])

    return hammer_ons, pull_offs, tapping_notes

def generate_notes_chart(song_name, beat_times, note_times, note_frequencies, hammer_ons, pull_offs, tapping_notes, output_path):
    """Generate a notes.chart file based on detected beats and notes."""
    try:
        with output_path.open("w") as f:
            f.write(f"[Song]\n{{\n  Name = {song_name}\n  Artist = Unknown\n  Charter = AI\n}}\n")
            f.write("\n[SyncTrack]\n{\n")
            for time in beat_times:
                f.write(f"  {int(time * 1000)} = TS {int(time * 1000)}\n")  # Tempo changes
            f.write("}\n\n[ExpertSingle]\n{\n")
            for i, time in enumerate(note_times):
                note = note_frequencies[i] % NOTE_MAPPING  # Map to six notes
                note_type = "H" if time in hammer_ons else "P" if time in pull_offs else "T" if time in tapping_notes else "N"
                f.write(f"  {int(time * 1000)} = {note_type} {note} 0\n")  # Assigning notes with HO/PO/T support
            f.write("}\n")
    except Exception as e:
        logger.error(f"Error writing notes.chart: {str(e)}")
        raise

def process_song_file(file_path: str):
    """Process an uploaded song file and generate Clone Hero assets."""
    try:
        logger.info(f"Processing song file: {file_path}")

        tempo, beat_times, note_times, note_frequencies, hammer_ons, pull_offs, tapping_notes = analyze_audio(file_path)

        song_name = Path(file_path).stem
        song_output_dir = OUTPUT_DIR / song_name
        song_output_dir.mkdir(parents=True, exist_ok=True)
        notes_chart_path = song_output_dir / "notes.chart"

        generate_notes_chart(song_name, beat_times, note_times, note_frequencies, hammer_ons, pull_offs, tapping_notes, notes_chart_path)

        return {
            "message": "Song processed successfully",
            "notes_chart": str(notes_chart_path),
            "tempo": tempo
        }
    except Exception as e:
        logger.error(f"Error processing song: {str(e)}")
        return {"error": str(e)}