
### 使用说明
---
生成原始字幕文件: `python translate_video_srt_with_ai.py {video_path}`
再执行一次， 进行翻译: `python translate_video_srt_with_ai.py {video_path}`

一次性生成指令: `python translate_video_srt_with_ai.py {video_path} --once`

需要设置以下环境变量
together api key: API_KEY_TOGETHER
open router api key: API_KEY_OPENROUTER

用到的 model 如下：
open router: google/gemini-2.5-pro 用于 audio -> text
together: meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo 用于翻译



### 依赖
---
需要安装 python 库
- openai
- together
- pydantic
- moviepy
- pysrt
- pydub
- audioop-lts

