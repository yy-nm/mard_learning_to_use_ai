
import os

def write_image_2_file(data: bytes, output_path: str):
	with open(output_path, "wb") as f:
		f.write(data)
		pass
	print(f"Image saved to: {output_path}")
	pass


def check_file_is_generated(file_path: str) -> bool:
	dir_path = os.path.dirname(file_path)
	file_name = os.path.basename(file_path)
	length = len(file_name)
	for root, dirs, files in os.walk(dir_path):
		for file in files:
			if file.startswith(file_name) and file[length] == '.':
				return True
			pass
		pass
	return False


def check_file_match_generated_file(file_name: str, suffix_name: str) -> bool:
	file_name, file_extension = os.path.splitext(file_name)
	if file_name.endswith(suffix_name):
		return True
	return False
