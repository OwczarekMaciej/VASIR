import openai
import os
from dotenv import find_dotenv, load_dotenv
import time
from datetime import datetime
import requests
import json

load_dotenv()
openai.api_key = os.environ.get("OPENAI_API_KEY")
ELLABS_API_KEY = os.environ.get("ELLABS_API_KEY")

RACHEL = "21m00Tcm4TlvDq8ikWAM"
GLINDA = "z9fAnlkpzviPz146aGWa"
ALICE = "Xb7hH8MSUJpSbSDYk0k2"

CHUNK_SIZE = 1024
VOICE_ID = ALICE

OUTPUT_PATH = "output1.mp3"
TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

client = openai.OpenAI()
model = "gpt-3.5-turbo-16k"

volume = 5

def change_volume(volume_level: int):
    volume = volume_level
    print("Volume changed to: " + str(volume))


headers = {
    "Accept": "application/json",
    "xi-api-key": ELLABS_API_KEY
}

data = {
    "text": '',  # Text you want to convert to speech
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.8,
        "similarity_boost": 0.5,
        "style": 0.0,
        "use_speaker_boost": True
    }
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "change_volume",
            "description": "Zmienia głośność pliku MP3 lub dostosowuje głośność rozmowy",
            "parameters": {
                "type": "object",
                "properties": {
                    "volume_level": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 10,
                        "default": 5,
                        "description": "Docelowy poziom głośności (od 1 do 10) dla pliku lub rozmowy"
                    }
                },
                "required": ["volume_level"]
            }
        }
    }
]

available_functions = {
    "change_volume": change_volume,
}

# assistant = client.beta.assistants.create(
#   name="Health assistant",
#   instructions="Jesteś oddanym osobistym asystentem zdrowia, biegłym w dostosowywaniu się do unikalnych potrzeb osób starszych. Twoje doświadczenie w opiece nad osobami starszymi zapewnia im uwagę i wsparcie, które zasługują. Staraj się formułować odpowiedzi w dwóch zdaniach i generuj odpowiedź tak, żeby była dostosowana do konwersji na mowę",
#   model="gpt-3.5-turbo-16k",
#   tools = tools
# )
assistant_id = "asst_5zX0mXbZySQsz5w4QgZFnujp"


def execute_function_call(function_name, arguments):
    function = available_functions.get(function_name, None)
    if function:
        arguments = json.loads(arguments)
        results = function(**arguments)
    else:
        results = f"Error: function {function_name} does not exist"
    return results


def create_message_and_run(assistant_id, query, thread=None):
    if not thread:
        thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    return run, thread


def get_function_details(run):

    print("\nrun.required_action\n", run.required_action)

    function_name = run.required_action.submit_tool_outputs.tool_calls[0].function.name
    arguments = run.required_action.submit_tool_outputs.tool_calls[0].function.arguments
    function_id = run.required_action.submit_tool_outputs.tool_calls[0].id

    print(f"function_name: {function_name} and arguments: {arguments}")

    return function_name, arguments, function_id


def submit_tool_outputs(run, thread, function_id, function_response):
    run = client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread.id,
        run_id=run.id,
        tool_outputs=[
            {
                "tool_call_id": function_id,
                "output": str(function_response),
            }
        ]
    )
    return run


def text_to_speech(text, tts_url):

    data["text"] = text
    response = requests.post(tts_url, headers=headers, json=data, stream=True)
    if response.ok:
        with open(OUTPUT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        print("Audio stream saved successfully.")
    else:
        print(response.text)


query = "Mów ciszej"
run, thread = create_message_and_run(assistant_id=assistant_id, query=query)


while True:
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    print("run status", run.status)

    if run.status == "requires_action":

        function_name, arguments, function_id = get_function_details(run)

        function_response = execute_function_call(function_name, arguments)

        run = submit_tool_outputs(run, thread, function_id, function_response)

        continue
    if run.status == "completed":

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        latest_message = messages.data[0]
        text = latest_message.content[0].text.value
        print(text)
        if text:
            text_to_speech(text, TTS_URL)
        else:
            print("No response received from assistant.")

        user_input = input()
        if user_input == "STOP":
            break

        run, thread = create_message_and_run(
            assistant_id=assistant_id, query=user_input, thread=thread)

        continue
    time.sleep(1)
