# Video Subtitle Translation with AI

## Instructions

### Step 1. Generate Original Subtitles
```bash
python translate_video_srt_with_ai.py {video_path}
```

### Step 2. Translate Subtitles
```bash
python translate_video_srt_with_ai.py {video_path}
```

### One-Step Command
Generate and translate in a single run:
```bash
python translate_video_srt_with_ai.py {video_path} --once
```


## Environment Variables
You must set the following environment variables before running the script:

- API_KEY_TOGETHER → Together API key
- API_KEY_OPENROUTER → OpenRouter API key


## Models Used
- OpenRouter: `google/gemini-2.5-pro` → Audio to text
- Together: `meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo` → Translation

> Currently supports Japanese movies → Chinese subtitles.


## Dependencies
Install required Python libraries:

```bash
pip install openai together pydantic moviepy pysrt pydub audioop-lts
```

Dependencies list:
- openai
- together
- pydantic
- moviepy
- pysrt
- pydub
- audioop-lts

at last install ffmpeg and add to PATH
