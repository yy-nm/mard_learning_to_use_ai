
import requests
import base64
import os

# from together import Together


def encode_audio_to_base64(audio_path):
	with open(audio_path, "rb") as audio_file:
		return base64.b64encode(audio_file.read()).decode('utf-8')
	pass


# def audio_file_format(audio_path) -> str:
# 	file_name, file_extension = os.path.splitext(audio_path)
# 	file_format = 'wav'
# 	if file_extension == ".wav":
# 		file_format = "wav"
# 	elif file_extension == ".mp3":
# 		file_format = "mp3"
# 	elif file_extension == ".aiff":
# 		file_format = "aiff"
# 	elif file_extension == ".aac":
# 		file_format = "aac"
# 	elif file_extension == ".ogg":
# 		file_format = "ogg"
# 	elif file_extension == ".flac":
# 		file_format = "flac"
# 	elif file_extension == ".m4a":
# 		file_format = "m4a"
# 	return file_format

# openrouter support audio transcribe only 
# gemini-2.5-flash
# gemini-2.0-flash
# gemini-2.5-flash-lite
def transcribe_audio_with_openrouter(api_key: str, audio_path: str, promote: str, 
									# model_name = "google/gemini-2.5-flash",
									# model_name = "google/gemini-2.5-pro",
									model_name = "google/gemini-3-flash-preview:floor", #
									url = "https://openrouter.ai/api/v1/chat/completions",
									system_message: str = None
									):

	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json"
	}
	# Read and encode the audio file
	base64_audio = encode_audio_to_base64(audio_path)
	# file_format = audio_file_format(audio_path)

	messages = [
		{
			"role": "user",
			"content": [
				{
					"type": "text",
					"text": promote,
				},
				{
					"type": "input_audio",
					"input_audio": {
						"data": base64_audio,
						"format": "wav"
					}
				},
			]
		}
	]
	if system_message:
		messages.insert(0, {
			"role": "system",
			"content": system_message
		})
		pass

	payload = {
		"model": model_name,
		"messages": messages,
		# "provider": {'sort': 'price',} # prioritize lowest price
		'response_format': 'verbose_json',
	}

	response = requests.post(url, headers=headers, json=payload)
	return response


# together only support openai/whisper-large-v3 model
# def transcribe_audio_with_together(api_key: str, audio_path: str, promote: str, model_name = "openai/whisper-large-v3", language = None, response_format="verbose_json", timestamp_granularities="word"):
# 	client = Together(
# 		api_key=api_key
# 	)
#
# 	print("Converting audio to SRT with Together...")
# 	print(f"File path: {audio_path}")
#
# 	audio_file = open(audio_path, "rb")
#
# 	response = client.audio.transcriptions.create(
# 		file=audio_file,
# 		model=model_name,
# 		language=language,
# 		response_format=response_format,
# 		timestamp_granularities=timestamp_granularities,
# 		prompt=promote,
# 	)
# 	return response

