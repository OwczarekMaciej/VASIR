import openai
import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration Constants
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELLABS_API_KEY = os.environ.get("ELLABS_API_KEY")

# To wszystko potrzebne do Eleven labs no i ten key na górze

RACHEL = "21m00Tcm4TlvDq8ikWAM"
GLINDA = "z9fAnlkpzviPz146aGWa"
ALICE = "Xb7hH8MSUJpSbSDYk0k2"
VOICE_ID = ALICE

CHUNK_SIZE = 1024
OUTPUT_PATH = "output1.mp3"
TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"


# Configure OpenAI client with API key
OPENAI_MODEL = "gpt-3.5-turbo-16k"
ASSISTANT_ID = "asst_Kwbvp3hjUNrG18BrgJpQimd7"
THREAD_ID = "thread_I8uuNvB15WGyOUCM36ryvDiD"

openai.api_key = OPENAI_API_KEY

def send_query_to_openai(client, thread_id, assistant_id, message):
    client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=message
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions="Odpowiedź sformułuj w prosty i uprzejmy sposób. Ogranicz swoją odpowiedź do kilku zdań.",
    )
    return run.id


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    while True:
        try:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                print(f"Assistant Response: {response}")
                return response
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)


def text_to_speech(text, tts_url, xi_api_key):
    headers = {
        "Accept": "application/json",
        "xi-api-key": xi_api_key
    }

    data = {
        "text": text, # Text you want to convert to speech
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.8,
            "similarity_boost": 0.5,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    response = requests.post(tts_url, headers=headers, json=data, stream=True)
    if response.ok:
        with open(OUTPUT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        print("Audio stream saved successfully.")
    else:
        print(response.text)



if __name__ == "__main__":
    client = openai.OpenAI()
    message = "Ile kroków dziennie powinienem robić?"
    run_id = send_query_to_openai(client, THREAD_ID, ASSISTANT_ID, message)
    response_text = wait_for_run_completion(client, THREAD_ID, run_id)
    if response_text:
        text_to_speech(response_text, TTS_URL, ELLABS_API_KEY)
    else:
        print("No response received from assistant.")