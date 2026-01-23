
import os
import json
import time
from pathlib import Path

from openai import OpenAI

# =========================
# 基础配置
# =========================
# MODEL = "gpt-4.1-mini"
BATCH_INPUT_FILE = Path("batch_test.jsonl")
POLL_INTERVAL = 5  # 秒
# kBATCH_URL = "/v1/responses"

# openrouter not support batch api
# MODEL = "openai/gpt-4o-mini"
# kAPI_KEY_OPENROUTER = os.getenv("API_KEY_OPENROUTER", "")
# kURL = 'https://openrouter.ai/api/v1'
# client = OpenAI(
# 	base_url=kURL,
# 	api_key=kAPI_KEY_OPENROUTER,
# )
# qwen
# MODEL = "qwen3-max"
# kBATCH_URL = "/v1/chat/completions" # 正常情况
# kBATCH_URL = "/v1/embeddings" # embedding
MODEL = "batch-test-model" # 测试
kBATCH_URL = "/v1/chat/ds-test" # 测试
API_KEY_QWEN = os.getenv("API_KEY_QWEN", "")
kURL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
client = OpenAI(
	base_url=kURL,
	api_key=API_KEY_QWEN,
)

# =========================
# Step 1: 构造 JSONL 请求文件
# =========================
def create_batch_input_file():
    requests = [
        {
            "custom_id": "req-001",
            "method": "POST",
            "url": kBATCH_URL,
            "body": {
                "model": MODEL,
                "messages":[{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":"你好！有什么可以帮助你的吗？"}],
            }
        },
        {
            "custom_id": "req-002",
            "method": "POST",
            "url": kBATCH_URL,
            "body": {
                "model": MODEL,
                "messages":[{"role":"system","content":"You are a helpful assistant."},{"role":"user","content":"What is 2+2?"}],
            }
        }
    ]

    with BATCH_INPUT_FILE.open("w", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    assert BATCH_INPUT_FILE.exists()


# =========================
# Step 2: 上传 batch 文件
# =========================
def upload_batch_file():
	# with BATCH_INPUT_FILE.open("rb") as f:
	#     file_obj = client.files.create(
	#         file=f,
	#         purpose="batch"
	#     )
	file_obj = client.files.create(file=BATCH_INPUT_FILE, purpose="batch")
	assert file_obj.purpose == "batch"
	return file_obj.id


# =========================
# Step 3: 创建 Batch
# =========================
def create_batch(input_file_id: str):
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint=kBATCH_URL,
        completion_window="24h",
    )

    assert batch.status in ("validating", "in_progress")
    return batch.id


# =========================
# Step 4: 轮询 Batch 状态
# =========================
def wait_for_batch_completion(batch_id: str):
    while True:
        batch = client.batches.retrieve(batch_id=batch_id)
        print(f"[Batch status] {batch.status}")

        if batch.status == "completed":
            return batch.output_file_id

        if batch.status in ("failed", "expired", "cancelled"):
            raise RuntimeError(f"Batch failed: {batch.status}")

        time.sleep(POLL_INTERVAL)


# =========================
# Step 5: 下载并解析结果
# =========================
def download_and_validate_results(output_file_id: str):
    content = client.files.content(output_file_id)

    results = []
    for line in content.text.splitlines():
        obj = json.loads(line)
        results.append(obj)

    # ===== 测试断言 =====
    assert len(results) == 2

    custom_ids = {r["custom_id"] for r in results}
    assert custom_ids == {"req-001", "req-002"}

    for r in results:
        response = r["response"]
        output_text = response["body"]['choices'][0]['message']["content"]
        assert isinstance(output_text, str)
        assert len(output_text) > 0

        print(f"{r['custom_id']}: {output_text}")


# =========================
# 主测试流程
# =========================
def test_batch_api_end_to_end():
    create_batch_input_file()
    input_file_id = upload_batch_file()
    batch_id = create_batch(input_file_id)
    output_file_id = wait_for_batch_completion(batch_id)
    download_and_validate_results(output_file_id)


if __name__ == "__main__":
    test_batch_api_end_to_end()
