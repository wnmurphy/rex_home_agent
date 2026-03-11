import threading
import queue
import time

import pvcheetah
import pvcobra, pvporcupine, ollama
import pvorca
from pvrecorder import PvRecorder
from pvspeaker import PvSpeaker

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
    recorder = PvRecorder(frame_length=Config.AUDIO_FRAME_LENGTH_IN_SAMPLES)
    porcupine = pvporcupine.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        keyword_paths=[Config.PORCUPINE_WAKE_WORD_PATH]
    )
    cobra = pvcobra.create(access_key=Config.PICOVOICE_LICENSE_KEY)
    cheetah = pvcheetah.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        enable_automatic_punctuation=True,
        endpoint_duration_sec=Config.SECONDS_OF_SILENCE_THAT_INDICATES_USER_IS_DONE_SPEAKING,
    )
    orca = pvorca.create(
        access_key=Config.PICOVOICE_LICENSE_KEY,
        # model_path=Config.TTS_MODEL_PATH
    )
    speaker = PvSpeaker(sample_rate=orca.sample_rate, bits_per_sample=16)
    speaker.start()
    audio_queue = queue.Queue()

    def _play_audio_worker():
        while True:
            next_pcm = audio_queue.get()
            if next_pcm is None:
                break
            speaker.write(next_pcm)
            audio_queue.task_done()

    playback_thread = threading.Thread(target=_play_audio_worker, daemon=True)
    playback_thread.start()

    print("Assistant Active. Say 'Hey Rex' to start...")

    try:
        # Listen indefinitely.
        recorder.start()
        while True:
            pcm = recorder.read()

            # When we detect the wake word...
            if porcupine.process(pcm) >= 0:
                print("\n[Wake Word Detected] How can I help?")

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

                # Send the user input to Ollama to generate a response.
                print(f"User: {current_voice_submission}")
                response_stream = ollama.chat(
                    model=Config.OLLAMA_MODEL,
                    messages=[{'role': 'user', 'content': current_voice_submission}],
                    stream=True,
                )

                # Open Orca stream
                stream = orca.stream_open()

                # Take the streaming response from Ollama and play it back.
                for text_chunk in response_stream:
                    text_segment = text_chunk['message']['content']
                    if text_segment:
                        pcm = stream.synthesize(text_segment)
                        if pcm is not None:
                            audio_queue.put(pcm)

                # Get the final tail of the audio from Orca.
                final_pcm = stream.flush()
                if final_pcm is not None:
                    audio_queue.put(final_pcm)

                # Close the Orca stream.
                stream.close()

                # Wait here for the background worker to finish playing the audio.
                audio_queue.join()


    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Spin everything down gracefully.
        recorder.stop()
        recorder.delete()
        porcupine.delete()
        cobra.delete()
        cheetah.delete()
        orca.delete()
        speaker.stop()
        speaker.delete()

        # Send sentinel and close thread.
        audio_queue.put(None)
        playback_thread.join()


if __name__ == "__main__":
    setup_environment()
    run_assistant()
