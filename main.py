import openai
import os;
from dotenv import find_dotenv, load_dotenv
import time
import logging
from datetime import datetime
import requests

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
ellabs_api_key = os.environ.get("ELLABS_API_KEY")
# defaults to getting the key using os.environ.get("OPENAI_API_KEY")
# if you saved the key under a different environment variable name, you can do something like:
# client = OpenAI(
#   api_key=os.environ.get("CUSTOM_ENV_NAME"),
# )

RACHEL = "21m00Tcm4TlvDq8ikWAM"
GLINDA = "z9fAnlkpzviPz146aGWa"
ALICE = "Xb7hH8MSUJpSbSDYk0k2"

# Define constants for the script
CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
XI_API_KEY = ellabs_api_key  # Your API key for authentication
VOICE_ID = ALICE  # ID of the voice model to use
OUTPUT_PATH = "output1.mp3"  # Path to save the output audio file

# Construct the URL for the Text-to-Speech API request
tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"


#OPENAI PART

client = openai.OpenAI()
model = "gpt-3.5-turbo-16k"

# # Najpierw trzeba wygenerować IDki, pojawią się w konsoli 
# # ==  Create our Assistant (Uncomment this to create your assistant) ==
# health_assistant = client.beta.assistants.create(
#     name="Health Care Assistant",
#     instructions="""Jesteś oddanym osobistym asystentem zdrowia, biegłym w dostosowywaniu się do unikalnych potrzeb osób starszych. Dzięki Twojemu wsparciu, pozostają one na właściwej ścieżce z harmonogramami leków, planami ćwiczeń i dietą. Twoje doświadczenie w opiece nad osobami starszymi zapewnia im uwagę i wsparcie, które zasługują. """,
#     model=model,
# )
# asistant_id = health_assistant.id
# print(asistant_id)


# # === Thread (uncomment this to create your Thread) ===
# thread = client.beta.threads.create(
#     messages=[
#         {
#             "role": "user",
#             "content": "Co powinienem zrobić kiedy moje ciśnienie jest wysokie?",
#         }
#     ]
# )
# thread_id = thread.id
# print(thread_id)

# === Hardcode our ids ===
asistant_id = "asst_Kwbvp3hjUNrG18BrgJpQimd7"
thread_id = "thread_I8uuNvB15WGyOUCM36ryvDiD"

# ==== Create a Message ====
message = "Ile kroków dziennie powinienem robić?"
message = client.beta.threads.messages.create(
    thread_id=thread_id, role="user", content=message
)

# === Run our Assistant ===
run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=asistant_id,
    instructions="Odpowiedź sformułuj w prosty i uprzejmy sposób. Ogranicz swoją odpowiedź do kilku zdań.",
)


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """

    Waits for a run to complete and prints the elapsed time.:param client: The OpenAI client object.
    :param thread_id: The ID of the thread.
    :param run_id: The ID of the run.
    :param sleep_interval: Time in seconds to wait between checks.
    """
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


# === Run ===
response_text = wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)

# ==== Steps --- Logs ==
run_steps = client.beta.threads.runs.steps.list(
    thread_id=thread_id, run_id=run.id)
print(f"Steps---> {run_steps.data[0]}")



# Set up headers for the API request, including the API key for authentication
headers = {
    "Accept": "application/json",
    "xi-api-key": XI_API_KEY
}

# Set up the data payload for the API request, including the text and voice settings
data = {
    "text": response_text, # Text you want to convert to speech
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.8,
        "similarity_boost": 0.5,
        "style": 0.0,
        "use_speaker_boost": True
    }
}


# Make the POST request to the TTS API with headers and data, enabling streaming response
resp = requests.post(tts_url, headers=headers, json=data, stream=True)

# Check if the request was successful
if resp.ok:
    # Open the output file in write-binary mode
    with open(OUTPUT_PATH, "wb") as f:
        # Read the response in chunks and write to the file
        for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
            f.write(chunk)
    # Inform the user of success
    print("Audio stream saved successfully.")
else:
    # Print the error message if the request was not successful
    print(resp.text)
