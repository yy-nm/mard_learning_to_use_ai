
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

# kImageGeneratePromote = '''
# 创建一张图， 图片为卡通风格， 图上有如下内容
# 一只小狐狸背书书包上学
# '''
kImageGeneratePromote = '''
一只唐老鸭船长站在战舰船头指挥方向， 后面是一只身穿大副服的可达鸭双手抱着脑袋。
'''

kImageSizeDefault = "1K" # 1K, 2K, 4K # 4K 会生成两张内容， 一张 1K 第二张 4K
kModelDefaultName = 'google/gemini-3-pro-image-preview:floor' # nano banan pro, use :floor to prioritize lowest price

def _do_image_edit(promote: str, output_path: str,  model_name: str = kModelDefaultName):

	result = imagehelper.chat_image_with_nano_banana_via_openrouter(
		api_key=kAPI_KEY_OPENROUTER,
		promote=promote,
		model_name=model_name,
		image_size=kImageSizeDefault,
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


def do_nano_banana_image_with_http(promote: str, output_path: str, model_name: str = kModelDefaultName):
	is_stream = kImageSizeDefault == '4K'
	result = imagehelper.chat_image_with_nano_banana_via_openrouter_with_url(
		api_key=kAPI_KEY_OPENROUTER,
		model_name=model_name,
		promote=promote,
		image_size=kImageSizeDefault,
		stream=is_stream, # 4k use stream
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


def do_action(promote: str, output_path: str):
	# _do_image_edit(promote, output_path)
	do_nano_banana_image_with_http(promote, output_path)
	pass


def main():
	parser = argparse.ArgumentParser(description="generate image with nano banana pro model")
	parser.add_argument("--promote", default=kImageGeneratePromote, help="prompt for image generation")
	parser.add_argument("--output", default="./generate_image.jpg", help="Path to the output image file")

	args = parser.parse_args()
	do_action(args.promote, args.output)
	pass


if __name__ == "__main__":
	main()
	pass
