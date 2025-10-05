
# basic import 
from mcp.server.fastmcp import FastMCP

import uvicorn
import requests
import logging
import json


kCrawHost = "http://192.168.3.109:11235"
kCrawlURL = f"{kCrawHost}/crawl"
kCrawlTask = f"{kCrawHost}/task/"

kPORT = 8001


# instantiate an MCP server client
mcp = FastMCP(
	name="web-crawler",
	host="0.0.0.0",
	port=kPORT,
	# stateless_http=True,
	debug=True,
	log_level='DEBUG'
	)


# crawl4ai example code
# import requests

# # Submit a crawl job
# response = requests.post(
# 	"http://localhost:11235/crawl",
# 	json={"urls": ["https://example.com"], "priority": 10}
# )
# if response.status_code == 200:
# 	print("Crawl job submitted successfully.")
	
# if "results" in response.json():
# 	results = response.json()["results"]
# 	print("Crawl job completed. Results:")
# 	for result in results:
# 		print(result)
# else:
# 	task_id = response.json()["task_id"]
# 	print(f"Crawl job submitted. Task ID:: {task_id}")
# 	result = requests.get(f"http://localhost:11235/task/{task_id}")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def crawl_whole_web_info(url: str) -> str:
	"""Crawl whole web info from a given URL"""
	response = requests.post(kCrawlURL, json={"urls": [url], "priority": 10})

	if response.status_code != 200:
		return f"Error: Unable to crawl the URL {url}. Status code: {response.status_code}"
	
	if "results" in response.json():
		results = response.json()["results"]
		logging.info("Crawl job completed. Results:")
		return deal_with_crawl_result(results, url)
	else:
		task_id = response.json()["task_id"]
		logging.info(f"Crawl job submitted. Task ID:: {task_id}")
		result = requests.post(f"{kCrawlTask}/{task_id}")
		if result.status_code != 200:
			return f"Error: Unable to retrieve results for task ID {task_id}. Status code: {result.status_code}"
		logging.info(f"Results retrieved for task ID {task_id}")
		
		results = response.json()["results"]
		return deal_with_crawl_result(results, url)
	pass


def deal_with_crawl_result(results: list, original_url: str) -> str:
	output = []
	for result in results:
		data = deal_with_crawl_single_result(result, original_url)
		if data:
			output.append(data)
			pass
		pass

	return '\n'.join(output)

def deal_with_crawl_single_result(result: dict, original_url: str) -> str:
	# process the crawl result here
	url = result.get("url", "")
	logging.info(f"url: {url}, status_code: {result['status_code']}")
	logging.info(f"url: {url}, error_message: {result['error_message']}")

	if not result['success']:
		logging.info(f"url: {url}, crawl not success")
		return ""

	if url != original_url:
		logging.info(f"url: {url}, not match origin url: {original_url}")
		return ""
	
	markdown = result.get("markdown", "")
	markdown_data = json.dumps(markdown, ensure_ascii=False)
	# logging.info(f"url: {url}, markdown data: {markdown_data}")

	logging.info(f"url: {url}, length of html: {len(result['html'])}")
	logging.info(f"url: {url}, length of fit_html: {len(result['fit_html'])}")
	logging.info(f"url: {url}, length of cleaned_html: {len(result['cleaned_html'])}")
	logging.info(f"url: {url}, length of markdown_data: {len(markdown_data)}")
	# return result['html']
	result_candidate_list = ['html', 'fit_html', 'cleaned_html']
	output_data = ''
	output_len = 0
	for candidate in result_candidate_list:
		if candidate in result and result[candidate]:
			if len(result[candidate]) < output_len or output_len == 0:
				output_data = result[candidate]
				output_len = len(result[candidate])
				pass
			pass
		pass
	if len(markdown_data) < output_len:
		output_data = markdown_data
		output_len = len(markdown_data)
		pass

	return output_data



# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
	"""Get a personalized greeting"""
	return f"Hello, {name}!"


# execute and return the stdio output
if __name__ == "__main__":
	uvicorn.run(mcp.streamable_http_app, host="0.0.0.0", port=kPORT, log_level="debug")
	pass

