import numpy as np
import pvcobra, pvporcupine, ollama
from pvrecorder import PvRecorder
from pywhispercpp.model import Model
from config import Config

def run_assistant():
    porcupine = pvporcupine.create(access_key=Config.PICOVOICE_LICENSE_KEY, keywords=['picovoice'])
    cobra = pvcobra.create(access_key=Config.PICOVOICE_LICENSE_KEY)
    whisper = Model(model='base.en')
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
                silent_frames = 0
                recorded_frames = 0 # Track how many frames we've recorded

                user_is_done_speaking = silent_frames < Config.SECONDS_OF_SILENCE_BEFORE_SUBMITTING_TO_OLLAMA / 2

                we_have_enough_audio_for_whisper = recorded_frames > Config.MIN_RECORDED_FRAMES

                while user_is_done_speaking and we_have_enough_audio_for_whisper:
                    pcm = recorder.read()
                    user_audio_buffer.extend(pcm)

                    if cobra.process(pcm) < 0.2: # Threshold for silence
                        silent_frames += 1
                    else:
                        silent_frames = 0

                print("[Processing with Ollama...]")

                # Convert the speech we have as a raw PCM list into a float32 numpy array for Whisper.
                audio_np = np.array(user_audio_buffer, dtype=np.float32) / 32768.0

                # Transcribe the voice input...
                print("[Transcribing...]")
                # segments = whisper.transcribe(audio_np)
                # user_text = " ".join([s.text for s in segments])
                # print(f"User: {user_text}")


                response = ollama.chat(model=Config.OLLAMA_MODEL, messages=[{'role': 'user', 'content': "Hey, what's up?"}])

                # response = ollama.chat(model=Config.OLLAMA_MODEL, messages=[{'role': 'user', 'content': user_text}])
                print(f"AI: {response['message']['content']}")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recorder.stop()
        porcupine.delete()
        cobra.delete()
        recorder.delete()

if __name__ == "__main__":
    run_assistant()





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