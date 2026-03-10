import pvcheetah
import pvcobra, pvporcupine, ollama
from pvrecorder import PvRecorder
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
    cheetah = pvcheetah.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        enable_automatic_punctuation=True,
        endpoint_duration_sec=Config.SECONDS_OF_SILENCE_THAT_INDICATES_USER_IS_DONE_SPEAKING,
    )
    recorder = PvRecorder(frame_length=porcupine.frame_length) # Must match the frame_length of the engines.

    print("Assistant Active. Say 'Picovoice' to start...")

    try:
        # Listen indefinitely.
        recorder.start()
        while True:
            pcm = recorder.read()

            # When we detect the wake word...
            if porcupine.process(pcm) >= 0:
                print("\n[Wake Word Detected] How can I help?")

                silent_frames = 0 # Track silence to know when user has finished speaking.

                current_voice_submission = ""

                # After wake word, capture input until break conditions are met below.
                while True:
                    pcm = recorder.read()

                    # Transcribe the input as the user is speaking.
                    partial_transcript, is_endpoint = cheetah.process(pcm)
                    if partial_transcript:
                        current_voice_submission += partial_transcript
                    if is_endpoint:
                        final_transcript = cheetah.flush()
                        current_voice_submission += final_transcript
                        print(f"current_voice_submission: {current_voice_submission}")
                        break

                print(f"User: {current_voice_submission}")
                response = ollama.chat(
                    model=Config.OLLAMA_MODEL,
                    messages=[{'role': 'user', 'content': current_voice_submission}],
                )
                print(f"AI: {response['message']['content']}")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recorder.stop()
        porcupine.delete()
        cobra.delete()
        recorder.delete()
        cheetah.delete()


if __name__ == "__main__":
    setup_environment()
    run_assistant()
