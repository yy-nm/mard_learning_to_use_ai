from typing import List

import os
import sys
import argparse
import pysrt
from pathlib import Path
import math
import json

import subprocess


from pysrt import SubRipItem, SubRipTime

from pydub import AudioSegment
from pydub.silence import detect_silence

from moviepy.audio.io.AudioFileClip import AudioFileClip

if __name__ == "__main__":
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
	pass

from conf import kAPI_KEY_OPENROUTER as API_KEY # 后续再改成自己的 API_KEY
from conf import kAPI_KEY_TOGETHER
from conf import kSYSTEM_TRANSCRIBE_PROMPT, kUSER_TRANSCRIBE_PROMPT, kSYSTEM_TRANSLATE_PROMPT, kUSER_TRANSLATE_PROMPT

from aihelper import audiohelper
from aihelper import chathelper

try:
	from moviepy import VideoFileClip
	MOVIEPY_AVAILABLE = True
except ImportError:
	MOVIEPY_AVAILABLE = False
	print("Error: moviepy library not found. Please install it using: pip install moviepy")
	sys.exit(1)


kVENV_PATH = ''

# audio param only for ASR/NLP
kAUDIO_PARAM_CODEC = 'libopus'
kAUDIO_PARAM_BITRATE = '16K' # at least 32K for human listen
kAUDIO_PARAM_FPS = 16000
kAUDIO_PARAM_FFMPEG_PARAM = ["-ac", "1"]
kAUDIO_PARAM_FORMAT = "ogg"


def _extract_audio(video_path, output_path=None, audio_format=kAUDIO_PARAM_FORMAT, skip_seconds=0):
	"""
	Extract audio from a video file

	Args:
		video_path (str): Path to the video file
		output_path (str): Path for the output audio file (optional)
		audio_format (str): Audio format for output (default: mp3)

	Returns:
		str: Path to the extracted audio file
	"""
	print("Starting audio extraction...")
	# Check if video file exists
	if not os.path.exists(video_path):
		raise FileNotFoundError(f"Video file not found: {video_path}")

	# Load video file
	video = VideoFileClip(video_path)

	# Generate output path if not provided
	if output_path is None:
		video_name = Path(video_path).stem
		output_path = f"{video_name}.{audio_format}"
		pass

	if os.path.exists(output_path):
		print(f"Audio file already exists: {output_path}")
		# check audio duration is matched
		audio = AudioFileClip(output_path)
		# if audio.duration == video.duration:
		if math.fabs(audio.duration + skip_seconds - video.duration) / video.duration < 0.01:
			print("Audio duration matches video duration.")
			return output_path
		else:
			print("Audio duration does not match video duration.")
			os.remove(output_path)
			pass
		pass

	# Extract audio
	audio = video.audio

	if skip_seconds > 0:
		audio = audio.subclipped(skip_seconds)
		pass

	# Save audio file
	audio.write_audiofile(output_path, 
							codec=kAUDIO_PARAM_CODEC,
							bitrate=kAUDIO_PARAM_BITRATE,
							fps=kAUDIO_PARAM_FPS,
							ffmpeg_params=kAUDIO_PARAM_FFMPEG_PARAM)  # Mono audio

	# Close video and audio objects to free resources
	audio.close()
	video.close()

	return output_path


def check_audio_already_split(audio_path, output_dir, skip_seconds=0) -> List[str]:
	"""
	Check if the audio file has already been split into segments

	Args:
		audio_path (str): Path to the original audio file
		output_dir (str): Directory containing the audio segments

	Returns:
		bool: True if audio has been split, False otherwise
	"""
	audio_name = Path(audio_path).stem
	# Check for the existence of segment files
	segment_files = list(Path(output_dir).glob(f"{audio_name}_part_*.{kAUDIO_PARAM_FORMAT}"))
	total_duration = 0
	all_piece_path = []
	for file in segment_files:
		path = file.absolute()
		audio = AudioFileClip(path)
		total_duration += audio.duration
		all_piece_path.append(str(path))
		pass

	whole_audio = AudioFileClip(audio_path)
	if math.fabs(whole_audio.duration - total_duration - skip_seconds) / whole_audio.duration < 0.01:
		return all_piece_path
	# remove old file
	for path in all_piece_path:
		if os.path.exists(path):
			print(f"Removing old segment file: {path}")
			os.remove(path)
			pass
		pass
	return None


def _split_audio_at_silence(audio_segment, min_silence_len=1000, silence_thresh=-40):
	"""
	Find optimal split points at silence in audio

	Args:
		audio_segment (AudioSegment): Audio segment to analyze
		min_silence_len (int): Minimum length of silence in milliseconds (default: 1000ms)
		silence_thresh (int): Silence threshold in dBFS (default: -40dBFS)

	Returns:
		list: List of silence positions in milliseconds
	"""
	silences = detect_silence(audio_segment, 
								min_silence_len=min_silence_len, 
								silence_thresh=silence_thresh)

	# Return middle point of each silence period
	return [(start + end) // 2 for start, end in silences]


def _smart_split_audio(audio_path, segment_length_min=10, output_dir=None, skip_seconds=0, min_silence_len=1000, silence_thresh=-40):
	"""
	Split audio file into N-minute segments while avoiding dialogue interruptions

	Args:
		audio_path (str): Path to the audio file
		segment_length_min (int): Target length of each segment in minutes (default: 10)
		output_dir (str): Directory to save segments (optional)
		min_silence_len (int): Minimum length of silence in milliseconds (default: 1000ms)
		silence_thresh (int): Silence threshold in dBFS (default: -40dBFS)

	Returns:
		list: Paths to the created audio segments
	"""
	# Check if audio file exists
	if not os.path.exists(audio_path):
		raise FileNotFoundError(f"Audio file not found: {audio_path}")

	# Load audio file
	audio = AudioSegment.from_file(audio_path)

	# Generate output directory if not provided
	if output_dir is None:
		audio_name = Path(audio_path).stem
		output_dir = f"{audio_name}_segments"
		pass

	# Create output directory if it doesn't exist
	os.makedirs(output_dir, exist_ok=True)

	already_split_file_list = check_audio_already_split(audio_path, output_dir, skip_seconds=skip_seconds)
	if already_split_file_list:
		print("Audio already split into segments")
		return already_split_file_list

	# Calculate target segment length in milliseconds
	target_length_ms = segment_length_min * 60 * 1000

	# Find silence points
	silence_points = _split_audio_at_silence(audio, min_silence_len, silence_thresh)

	# Split audio at optimal points
	segments = []
	start_ms = 0
	segment_num = 1

	for silence_point in silence_points:
		# If we've reached or exceeded the target segment length, split here
		if silence_point - start_ms >= target_length_ms:
			# But make sure we don't split too early (at least 70% of target length)
			if silence_point - start_ms >= target_length_ms * 0.7:
				end_ms = silence_point
				segment = audio[start_ms:end_ms]
				
				# Generate output file path
				audio_name = Path(audio_path).stem
				output_path = os.path.join(output_dir, f"{audio_name}_part_{segment_num:03d}.{kAUDIO_PARAM_FORMAT}")
				
				# Export segment
				segment.export(output_path, format=kAUDIO_PARAM_FORMAT)
				segments.append(output_path)
				
				print(f"Exported: {output_path}")
				
				# Update start position for next segment
				start_ms = end_ms
				segment_num += 1

	# Handle the last segment
	if start_ms < len(audio):
		segment = audio[start_ms:]
		audio_name = Path(audio_path).stem
		output_path = os.path.join(output_dir, f"{audio_name}_part_{segment_num:03d}.{kAUDIO_PARAM_FORMAT}")
		segment.export(output_path, format=kAUDIO_PARAM_FORMAT)
		segments.append(output_path)
		print(f"Exported: {output_path}")

	return segments


def get_audio_from_video(video_path, output_path, audio_format=kAUDIO_PARAM_FORMAT, skip_seconds=0):
	return _extract_audio(video_path, output_path=output_path, audio_format=audio_format, skip_seconds=skip_seconds)


def check_video_and_folder(video_path):
	if not os.path.exists(video_path):
		raise FileNotFoundError(f"Audio file not found: {video_path}")

	video_dir = os.path.dirname(video_path)
	video_name = os.path.basename(video_path)
	folder_name = f".{video_name.split('.')[0]}"
	folder_path = os.path.join(video_dir, folder_name)
	# create same name folder in same directory
	# 创建 Path 对象
	directory_path = Path(folder_path)

	# parents=True 允许创建多层目录，exist_ok=True 表示已存在时不报错
	directory_path.mkdir(parents=True, exist_ok=True)
	return folder_path


def split_audio_to_small_pieces(audio_path, output_dir=None, segment_length_min=10, skip_seconds=0):
	return _smart_split_audio(audio_path, segment_length_min=segment_length_min, output_dir=output_dir, skip_seconds=skip_seconds)


def transcribe_audio_list_with_ai(audio_piece, srt_file_suffix = '.srt') -> List[str]:
	raw_file_suffix = '.raw'
	srt_raw_file_list = []
	for audio_file in audio_piece:
		srt_file_raw = audio_file + srt_file_suffix + raw_file_suffix
		if os.path.exists(srt_file_raw):
			srt_raw_file_list.append(srt_file_raw)
			continue
		promote = kUSER_TRANSCRIBE_PROMPT
		response = audiohelper.transcribe_audio_with_openrouter(API_KEY, audio_file, promote, system_message=kSYSTEM_TRANSCRIBE_PROMPT)

		raw_content = response.content.strip()
		with open(srt_file_raw, 'wb') as f:
			f.write(raw_content)
			print(f"Raw content saved to: {srt_file_raw}")
			pass

		srt_raw_file_list.append(srt_file_raw)
		pass
	
	srt_file_list = []
	for raw_file in srt_raw_file_list:
		print(f"Raw SRT file: {raw_file}")
		srt_file_name = raw_file.rstrip('.raw')
		if os.path.exists(srt_file_name):
			print(f"SRT file already exists: {srt_file_name}")
			srt_file_list.append(srt_file_name)
			continue

		content = None
		with open(raw_file, 'r', encoding='utf-8') as f:
			content = f.read()
			# print(content)
			pass
		if content is None:
			continue
		data = json.loads(content)
		if 'choices' in data and len(data['choices']) > 0 and 'message' in data['choices'][0] and 'content' in data['choices'][0]['message']:
			srt_raw_data = data['choices'][0]['message']['content']
			if deal_with_srt_raw_file_info(srt_raw_data, srt_file_name):
				srt_file_list.append(srt_file_name)
				pass
			else:
				# ai output not stable
				print(f"ai output not stable, please modify {raw_file} manually")
				pass
			pass
		pass

	return srt_file_list

def merge_srt_files(audio_piece, srt_file_list, output_file, skip_seconds: int = 0):

	if os.path.exists(output_file):
		return

	if len(audio_piece) != len(srt_file_list):
		raise ValueError("The number of audio pieces and SRT files must match.")
	count = len(audio_piece)
	offset = skip_seconds
	whole_srt = pysrt.SubRipFile()
	index = 0
	# 防止乱序
	audio_piece.sort()
	srt_file_list.sort()

	for i in range(count):
		audio_path = audio_piece[i]
		srt_path = srt_file_list[i]
		print(f"Merging {audio_path} with {srt_path} into {output_file}")
		audio = AudioFileClip(audio_path)
		if not audio:
			raise ValueError(f"Failed to load audio file: {audio_path}")
		duration = audio.duration
		# Read the SRT file
		subs = pysrt.open(srt_path, encoding='utf-8')
		# Adjust the start and end times based on the audio piece
		for sub in subs:
			whole_srt.append(
				SubRipItem(
					index=index,
					start=sub.start + pysrt.SubRipTime.from_ordinal(offset * 1000),
					end=sub.end + pysrt.SubRipTime.from_ordinal(offset * 1000),
					text=sub.text,
				)
			)
			index += 1
			pass
		offset += duration
		pass
	# Save the merged SRT file
	whole_srt.save(output_file, encoding='utf-8')
	print(f"Merged SRT file saved to: {output_file}")
	pass


def convert_jp_to_ch_srt_together_thread(subtitles: list, output_file: str):
	words = {sub.text for sub in subtitles if sub.text}

	messages = [
		{
			"role": "system",
			"content": kSYSTEM_TRANSLATE_PROMPT,
		},
	]
	promote_prefix = kUSER_TRANSLATE_PROMPT

	# result_list = chathelper.chat_list_with_ai_on_thread(
	# 	api_key=kAPI_KEY_TOGETHER,
	# 	promote_list=words,
	# 	promote_prefix=promote_prefix,
	# 	common_other_message=messages,
	# 	model_name="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
	# )
	result_list = chathelper.chat_list_with_ai_on_thread(
		api_key=API_KEY,
		promote_list=words,
		promote_prefix=promote_prefix,
		common_other_message=messages,
		model_name="google/gemini-3-flash-preview:floor", # :floor means sort by price: prioritize lowest price
		use_ai_platform='openrouter',
	)

	# result_list.sort(key=lambda x: x[0])
	translate_words_map = {}
	for info in result_list:
		if info:
			translate_words_map[info[0]] = info[1]
			pass
		pass

	for sub in subtitles:
		if sub.text not in translate_words_map:
			print(f"Warning: Subtitle text '{sub.text}' not found in translation map.")
			continue

		sub.text = translate_words_map[sub.text]
		pass

	print(f"Saving translated SRT to: {output_file}")
	subtitles.save(output_file, encoding='utf-8')
	print("Translation completed and saved.")
	return output_file


def load_srt(file_path):
	"""
	Load SRT file and return a list of subtitles.
	Args:
		file_path (str): Path to the SRT file
			
	Returns:
		list: List of subtitles
	"""
	print(f"Loading SRT file: {file_path}")
	subtitles = pysrt.open(file_path, encoding='utf-8')
	return subtitles


def translate_srt(srt_file, output_file):
	"""
	Translate SRT file using Together API.
	Args:
		srt_file (str): Path to the SRT file
	"""
	if os.path.exists(output_file):
		return

	print(f"Translating SRT file: {srt_file}")

	subtitles = load_srt(srt_file)
	if not subtitles:
		print("No subtitles found in the SRT file.")
		return

	# Translate subtitles from Japanese to Chinese
	convert_jp_to_ch_srt_together_thread(subtitles, output_file)
	pass

def run_demucs_single(
	audio_file: str,
	out_root: str,
	model: str = "htdemucs" # default model
):
	"""
	使用 uv run demucs 对单个音频进行分离
	"""
	cmd = [
		"uv", "run",
		"demucs",
		"-n", model,
		"--segment", "7",
		"-o", str(out_root),
		str(audio_file)
	]

	if kVENV_PATH:
		if sys.platform == "win32":
			path = 'Scripts\\activate.bat'
			whole_path = os.path.join(kVENV_PATH, path)
			cmd.insert(0, f"{whole_path} &&")
		elif sys.platform.startswith("linux") or sys.platform == "darwin":
			path = 'bin/activate'
			whole_path = os.path.join(kVENV_PATH, path)
			cmd.insert(0, f"source {whole_path} &&")
			pass
		pass

	cmd_line = ' '.join(cmd)
	print(f"Running demucs command: {cmd_line}")
	ret = subprocess.run(
		cmd_line,
		shell=True,
		# stdout=subprocess.STDOUT,
		# stderr=subprocess.STDOUT,
		capture_output=True,
	)

	if ret.returncode != 0:
		print(f"demucs run failed, ret code: {ret.returncode}, stdout: {ret.stdout.decode('utf-8')}")
		pass
	pass

def isolate_vocals_from_audio(audio_piece: List[str], tmp_folder: str) -> List[str]:
	convert_result = []
	default_vocals_file_name = 'vocals.wav'
	default_model_name = 'htdemucs'
	for audio_file in audio_piece:
		filename = os.path.basename(audio_file)
		file_path = os.path.dirname(audio_file)
		output_dir = file_path
		if not os.path.exists(output_dir):
			os.makedirs(output_dir, exist_ok=True)
			pass
		name, ext = os.path.splitext(filename)
		target_file = os.path.join(output_dir, default_model_name, name, default_vocals_file_name)
		if not os.path.exists(target_file):
			run_demucs_single(audio_file, output_dir, default_model_name)
			pass
		else:
			print(f"file exists: {target_file}, skip")
			pass
		if not os.path.exists(target_file):
			raise FileNotFoundError(f"File '{target_file}' not found.")

		convert_result.append(target_file)
		pass

	# compress audio
	result = []
	audio_suffix = '.after_demucs.ogg'
	for audio_file in convert_result:
		filename = os.path.basename(os.path.dirname(audio_file))
		name = f"{filename}{audio_suffix}"
		file_path = os.path.join(tmp_folder, name)
		if not os.path.exists(file_path):
			audio = AudioFileClip(audio_file)
			# audio.write_audiofile(file_path, codec='libopus', bitrate='32K', fps=16000, ffmpeg_params=["-ac", "1"])  # Mono audio
			audio.write_audiofile(file_path, codec='libopus', bitrate='16K', fps=16000,  ffmpeg_params=["-ac", "1"])  # Mono audio, only for ASR/NLP
			if not os.path.exists(file_path):
				raise FileNotFoundError(f"File '{file_path}' not found.")
			pass
		result.append(file_path)
		pass

	return result


def generate_srt_with_ai(video_path, once_done: bool = False, use_demucs: bool = False, skip_seconds: int = 0):

	tmp_folder = check_video_and_folder(video_path)
	video_file_name = os.path.basename(video_path)
	audio_file_name = video_file_name.split('.')[0] + '.' + kAUDIO_PARAM_FORMAT
	audio_path = os.path.join(tmp_folder, audio_file_name)
	audio_path = get_audio_from_video(video_path, output_path=audio_path, audio_format=kAUDIO_PARAM_FORMAT, skip_seconds=skip_seconds)
	print(f"Extracted audio to: {audio_path}")
	audio_piece = split_audio_to_small_pieces(audio_path, output_dir=tmp_folder, segment_length_min=5, skip_seconds=skip_seconds)
	print(f"Split audio into pieces: {audio_piece}")
	if use_demucs:
		audio_piece = isolate_vocals_from_audio(audio_piece, tmp_folder)
		pass
	# 开始使用 ai 进行识别
	# 将字幕文件进行合并
	# 使用 ai 进行反应
	srt_file_list = transcribe_audio_list_with_ai(audio_piece)
	output_file = audio_path + '.origin.srt'
	is_origin_srt_exists = False
	if os.path.exists(output_file):
		is_origin_srt_exists = True
		pass
	merge_srt_files(audio_piece, srt_file_list, output_file, skip_seconds)
	final_srt_file = video_path + '.srt'
	if not is_origin_srt_exists and not once_done:
		print(f"check origin srt first, then run again will translate it")
		return
	translate_srt(output_file, final_srt_file)
	print(f"Final translated SRT file saved to: {final_srt_file}")
	pass


def parse_timecode(timecode: str) -> SubRipTime:
	# 解析时间码，格式为 hh:mm:ss,ms
	# min_sec, ms = timecode.split(',')
	# ms = int(ms)
	time_list = timecode.split(',')
	if len(time_list) == 2:
		min_sec, ms = time_list
		if ms:
			ms = int(ms)
			pass
		else:
			ms = 0
			pass
	else:
		ms = 0
		min_sec = time_list[0]
		pass
	time_tuple = min_sec.split(':')
	if len(time_list) != 2 and len(time_tuple) == 3 and len(time_tuple[-1]) == 3:
		ms = int(time_tuple[-1])
		time_tuple = time_tuple[:-1]
		pass

	time_tuple: List[int] = list(map(int, time_tuple))
	hour = 0
	minute = 0
	second = 0
	if len(time_tuple) == 3:
		hour, minute, second = time_tuple
	elif len(time_tuple) == 2:
		minute, second = time_tuple
		pass

	return SubRipTime(hour, minute, second, ms)


def deal_with_srt_raw_file_info(text: str, output_file: str):
	lines = text.splitlines()
	
	subs = pysrt.SubRipFile()
	item = SubRipItem()
	step = 0
	for i in range(len(lines)):
		line = lines[i].strip()
		if step == 0:
			if line.isdigit():
				item.index = int(line)
				step += 1
			pass
		elif step == 1:
			start_end = line.split(' --> ')
			if len(start_end) == 2:
				item.start = parse_timecode(start_end[0])
				item.end = parse_timecode(start_end[1])
				step += 1
			pass
		elif step == 2:
			item.text = line
			step += 1
			pass
		elif step >= 3:
			if line:
				if line.isdigit():
					subs.append(item)
					item = SubRipItem()
					step  = 0

					item.index = int(line)
					step += 1
					continue
				item.text += '\n' + line
				step += 1
			else:
				step  = 0
				subs.append(item)
				item = SubRipItem()
				pass
			pass
		pass

	if item.index > 0 and item.text:
		subs.append(item)
		pass
	if len(subs) > 0:
		subs.save(output_file, encoding='utf-8')
		print(f"SRT file saved to: {output_file}")
		return True

	return False


def main():
	parser = argparse.ArgumentParser(description="translate srt from video files")
	parser.add_argument("video_path", help="Path to the video file")
	parser.add_argument("--once", default=True, action="store_true", help="do video all in once")
	parser.add_argument("--use-demucs", default=False, action="store_true", help="use demucs model to isolate the vocals, very slow")
	parser.add_argument("--venv-path", help="support venv environment")
	parser.add_argument("--skip-seconds", default=0, help="skip meaningless header in seconds")

	args = parser.parse_args()

	if args.venv_path:
		global kVENV_PATH
		kVENV_PATH = args.venv_path
		pass
	skip_seconds = int(args.skip_seconds) if args.skip_seconds else 0
	generate_srt_with_ai(args.video_path, args.once, args.use_demucs, skip_seconds)
	pass


if __name__ == "__main__":
	main()
	pass
