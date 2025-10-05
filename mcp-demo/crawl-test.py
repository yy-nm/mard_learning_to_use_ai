# crawl4ai example code
import requests

kCrawHost = "http://192.168.3.109:11235"
kCrawlURL = f"{kCrawHost}/crawl"
kCrawlTask = f"{kCrawHost}/task/"


target_url = "https://news.163.com"

# Submit a crawl job
response = requests.post(
	kCrawlURL,
	json={"urls": [target_url], "priority": 10}
)
if response.status_code == 200:
	print("Crawl job submitted successfully.")
	
if "results" in response.json():
	results = response.json()["results"]
	print("Crawl job completed. Results:")
	for result in results:
		print(result)
else:
	task_id = response.json()["task_id"]
	print(f"Crawl job submitted. Task ID:: {task_id}")
	result = requests.get(f"{kCrawlTask}/{task_id}")
	if result.status_code == 200:
		print(f"Results retrieved for task ID {task_id}, data: {result.json()}")
		for res in result.json().get("results", []):
			print(res)
	else:
		print(f"Error: Unable to retrieve results for task ID {task_id}. Status code: {result.status_code}")
		pass
	pass