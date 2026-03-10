import numpy as np
import pvcobra, pvporcupine, ollama
from pvrecorder import PvRecorder
from pywhispercpp.model import Model
from config import Config


def setup_environment():
    # Check for required environment variables
    if not Config.PICOVOICE_LICENSE_KEY:
        print("Warning: PICOVOICE_LICENSE_KEY required but not found in environment variables")

    # Check if Ollama is running
    try:
        import requests
        response = requests.get("http://localhost:11434")
        if response.status_code != 200:
            print("Warning: Ollama server not accessible at http://localhost:11434")
    except:
        print("Warning: Could not connect to Ollama server")


def run_assistant():
    """
    Contains the main loop, which handles the following:
    1. Listens for wake word.
    2. Collects audio samples until
        a. we have enough for Whisper to transcribe and
        b. the user has stopped talking for a certain amount of time.
    3. Sends audio samples to Whisper for transcription.
    4. Sends transcription to Ollama for response generation.
    5. Play back the generated response.
    """
    porcupine = pvporcupine.create(access_key=Config.PICOVOICE_LICENSE_KEY, keywords=['picovoice'])
    cobra = pvcobra.create(access_key=Config.PICOVOICE_LICENSE_KEY)
    whisper = Model(model=Config.WHISPER_MODEL)
    # Recorder must match the frame_length of the engines
    recorder = PvRecorder(frame_length=porcupine.frame_length)

    print("Assistant Active. Say 'Picovoice' to start...")

    try:
        # Listen indefinitely for wake word...
        recorder.start()
        while True:
            pcm = recorder.read()

            # When we detect the wake word...
            if porcupine.process(pcm) >= 0:
                print("\n[Wake Word Detected] How can I help?")

                # Start capturing the user's voice input until they stop talking...
                user_audio_buffer = []

                silent_frames = 0 # Track silence to know when to submit user query
                total_recorded_frames_for_this_submission = 0 # Track total recorded frames to know when we've met the minimum length for whisper.

                samples_per_second = Config.SAMPLE_RATE / porcupine.frame_length

                samples_of_silence_required_before_user_done = Config.SECONDS_OF_SILENCE_BEFORE_SUBMITTING_TO_OLLAMA * samples_per_second

                # Continue capturing input until break conditions are met below...
                while True:
                    pcm = recorder.read()
                    user_audio_buffer.extend(pcm)

                    is_speech = cobra.process(pcm) >= Config.VOICE_DETECTION_THRESHOLD

                    # Start a counter for consecutive silence.
                    if not is_speech:
                        silent_frames += 1
                        print(f"silent_frames: {silent_frames}")
                    else:
                        silent_frames = 0
                        print(f"silent_frames: {silent_frames}")

                    # Increment recorded frames by number of frames in this chunk.
                    frames_in_current_chunk = len(pcm) / porcupine.frame_length
                    total_recorded_frames_for_this_submission += frames_in_current_chunk
                    print(f"recorded_frames: {total_recorded_frames_for_this_submission}")

                    # Stop collecting audio when...
                    if (
                        # The user has stopped speaking for long enough to indicate that they are done speaking, and
                        silent_frames > samples_of_silence_required_before_user_done and
                        # We've hit the minimum audio length for Whisper to transcribe.
                        total_recorded_frames_for_this_submission > Config.MIN_RECORDED_FRAMES_FOR_TRANSCRIPTION
                    ):
                        break

                print("[Processing with Ollama...]")

                # Convert the speech we have as a raw PCM list into a float32 numpy array for Whisper.
                audio_np = np.array(user_audio_buffer, dtype=np.float32) / Config.BIT_DEPTH

                # Transcribe the voice input...
                print("[Transcribing...]")
                segments = whisper.transcribe(audio_np)
                user_text = " ".join([s.text for s in segments])
                print(f"User: {user_text}")

                response = ollama.chat(model=Config.OLLAMA_MODEL, messages=[{'role': 'user', 'content': user_text}])
                print(f"AI: {response['message']['content']}")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recorder.stop()
        porcupine.delete()
        cobra.delete()
        recorder.delete()

def audio_player():
    """
    Handles TTS audio playback.
    Checks after every streaming audio chunk if user tried to interrupt.
    Sets global user_is_speaking flag if so.
    """
    pass

def interruption_handler():
    """
    Contains a loop which checks for interruptions.
    If global user_is_speaking boolean is true, terminates the streaming audio response and handles cleanup of current response.
    """
    pass

if __name__ == "__main__":
    setup_environment()
    run_assistant()
