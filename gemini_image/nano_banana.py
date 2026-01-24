
import os
import argparse
import sys
import base64
import json

if __name__ == "__main__":
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
	pass

from aihelper import imagehelper

from image_common import write_image_2_file, check_file_is_generated, check_file_match_generated_file


kAPI_KEY_OPENROUTER = os.getenv("API_KEY_OPENROUTER", "")

# kTargetImageFile = './img6.jpg'
kTargetImageFolder = './imgs'

kImagePromote = '''
请将图片中的人物制作成手办模型放在电脑桌上， 手办本身带着底座， 手办的风格是二次元风格，
手办旁边的位置上放着手办的包装盒， 包装盒上仅仅显示手办图样，
背景的电脑上显示制作手办的3D软件界面， 界面里显示当前图片，
整体风格为二次元写实风格， 
最后请将图内容直接下发。
'''
kResultFileSuffix = ".nano_banana_result.json"
kResultMultiFileSuffix = ".nano_banana_result.multi.json"

# kImagePromoteForOpenAI = '''
# 请将这张人物照片转换为日本动画角色风格，柔和色调，使用手绘的人物设计风格， 怀旧童话。保持原始照片中的面部表情和姿势，但用日本动画标志性的人物比例和面部特征重新绘制。
# 最后请将图内容直接下发。
# '''
# kImagePromoteForOpenAI = 'restyle the phone into studio ghibli art.'
kImagePromoteForOpenAI = '请用皮卡四风格重绘这张人物照片，保持原始照片中的面部表情和姿势。最后请将图内容直接下发。'
kResultFileSuffixForOpenAI = ".openai.json.png"
kModelNameForOpenAI = "openai/gpt-5"


def do_image_edit(image_path: str, file_suffix: str = kResultFileSuffix, promote: str = kImagePromote, model_name: str = "google/gemini-2.5-flash-image-preview"):
	file = image_path
	if not os.path.isabs(file):
		file = os.path.abspath(file)
		pass
	print(f"file: {file}")

	result_image_path = file + file_suffix
	if check_file_is_generated(result_image_path):
		print(f"result_image_path exists, skip: {result_image_path}")
		return
	_do_image_edit(file, result_image_path, promote, model_name)
	pass

def _do_image_edit(input_path: str, output_path: str, promote: str = kImagePromote, model_name: str = "google/gemini-2.5-flash-image-preview"):

	if not os.path.exists(input_path):
		print(f"input_path not exists: {input_path}")
		return

	result = imagehelper.chat_image_with_nano_banana_via_openrouter(
		api_key=kAPI_KEY_OPENROUTER,
		promote=promote,
		model_name=model_name,
		image_path=input_path,
		# image_size="4k",
	)

	if result is None:
		return

	print(f"image count: {len(result)}")
	index = 0
	for entry in result:
		filename = f"{output_path}.{index}.{entry[1]}"
		write_image_2_file(entry[0], filename)
		index += 1
		pass

	pass


def do_nano_banana_image_with_http(image_path: str, promote: str = kImagePromote, model_name: str = "google/gemini-2.5-flash-image-preview"):
	file = image_path
	if not os.path.isabs(file):
		file = os.path.abspath(file)
		pass
	print(f"file: {file}")

	result_image_path = file + kResultFileSuffix

	if check_file_is_generated(result_image_path):
		print(f"result_image_path exists, skip: {result_image_path}")
		return

	result = imagehelper.chat_image_with_nano_banana_via_openrouter_with_url(
		api_key=kAPI_KEY_OPENROUTER,
		model_name=model_name,
		promote=promote,
		image_path=file,
		image_size="4k",
	)

	if result is None:
		return

	print(f"image count: {len(result)}")
	index = 0
	for entry in result:
		filename = f"{result_image_path}.{index}.{entry[1]}"
		write_image_2_file(entry[0], filename)
		index += 1
		pass
	pass


def do_nano_banana_image_list_with_http(image_path: list[str], promote: str = kImagePromote,  model_name: str = "google/gemini-2.5-flash-image-preview"):
	file_list = []
	file = None
	for entry in image_path:
		if not os.path.isabs(entry):
			entry = os.path.abspath(entry)
			pass
		if file is None:
			file = entry
			pass
		file_list.append(entry)
		pass
	print(f"file: {file_list}")

	result_image_path = file + kResultMultiFileSuffix

	if check_file_is_generated(result_image_path):
		print(f"result_image_path exists, skip: {result_image_path}")
		return

	result = imagehelper.chat_image_with_nano_banana_via_openrouter_with_url(
		api_key=kAPI_KEY_OPENROUTER,
		model_name=model_name,
		promote=promote,
		image_path_list=file_list,
		# image_size="4k",
	)

	if result is None:
		return

	print(f"image count: {len(result)}")
	index = 0
	for entry in result:
		filename = f"{result_image_path}.{index}.{entry[1]}"
		write_image_2_file(entry[0], filename)
		index += 1
		pass

	pass


# def decode_base64_image(data: bytes, output_path: str):
# 	# 去掉可能的前后空白字符
# 	data = data.strip()
# 	# 补齐长度
# 	missing_padding = len(data) % 4
# 	if missing_padding:
# 		data += b'=' * (4 - missing_padding)
# 		pass
#
# 	header, encoded = data.split(b",", 1)
# 	data = base64.b64decode(encoded)
# 	with open(output_path, "wb") as f:
# 		f.write(data)
# 		pass
# 	print(f"Image saved to: {output_path}, header: {header}")
# 	pass


def test_case():
	# file = os.path.join(os.path.dirname(__file__), kTargetImageFile)
	folder = kTargetImageFolder
	if not os.path.isabs(folder):
		folder = os.path.join(os.path.dirname(__file__), folder)
		pass
	print(f"folder: {folder}")
	for entry in os.listdir(folder):
		file_name = entry.lower()
		if file_name.endswith(('.png', '.jpg', '.jpeg')) and not check_file_match_generated_file(entry, kResultFileSuffix):
			file_path = os.path.join(folder, entry)
			# do_image_edit(file_path)
			# do_image_edit(file_path, model_name="google/gemini-3-pro-image-preview")
			# do_image_edit(file_path, file_suffix=kResultFileSuffixForOpenAI, promote=kImagePromoteForOpenAI, model_name=kModelNameForOpenAI)
			# do_nano_banana_image_with_http(file_path)
			do_nano_banana_image_with_http(file_path, model_name="google/gemini-3-pro-image-preview")
			pass
		pass
	# do_image_edit(file)
	# do_nano_banana_image_with_http(file)
	# test_decode_image()
	pass


def test_case_2():
	folder = kTargetImageFolder
	if not os.path.isabs(folder):
		folder = os.path.join(os.path.dirname(__file__), folder)
		pass
	print(f"folder: {folder}")
	file_list = []
	for entry in os.listdir(folder):
		file_name = entry.lower()
		if file_name.endswith(('.png', '.jpg', '.jpeg')) and not entry.endswith(kResultFileSuffix):
			file_path = os.path.join(folder, entry)
			file_list.append(file_path)
			pass
		pass

	# max image size； 目前来说有大小限制， 可能卡在中间服务器的处理上限上（比如服务器限制请求长度比如 1M）
	# 目前似乎只最多支持两张图片的上传
	if len(file_list) > 2:
		file_list = file_list[:2]
		pass

	promote = '''
	请将这几张图里的人物放在同一场景里展示
	'''
	do_nano_banana_image_list_with_http(file_list, promote, model_name="google/gemini-3-pro-image-preview")
	pass

def do_action(input_path: str, output_path: str):
	_do_image_edit(input_path, output_path)
	pass


def main():
	parser = argparse.ArgumentParser(description="edit image with nano banana model")
	parser.add_argument("--input", help="Path to the image file")
	parser.add_argument("--output", help="Path to the output image file")

	args = parser.parse_args()

	# test_case()
	# test_case_2()
	do_action(args.input, args.output)
	pass


if __name__ == "__main__":
	main()
	pass
