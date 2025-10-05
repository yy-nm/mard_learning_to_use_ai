# basic import 
from mcp.server.fastmcp import FastMCP
import math

import uvicorn

from pydantic import BaseModel


kPORT = 8000

# instantiate an MCP server client
mcp = FastMCP(
	name="online-calc",
	host="0.0.0.0",
	port=kPORT,
	# stateless_http=True,
	debug=True,
	log_level='DEBUG'
	)
# mcp = Server(
# 	name="online-calc",
# )

# DEFINE TOOLS

# define input and output info
class TwoNumbersInput(BaseModel):
	a: int
	b: int

class OneNumberInput(BaseModel):
	a: int

class FloatOutput(BaseModel):
	result: float

class IntOutput(BaseModel):
	result: int


#addition tool
@mcp.tool(name="add")
def add(a: int, b: int) -> int:
	"""Add two numbers"""
	return a + b

# subtraction tool
@mcp.tool(name="subtract")
def subtract(a: int, b: int) -> int:
	"""Subtract two numbers"""
	return a - b

# multiplication tool
@mcp.tool(name="multiply")
def multiply(a: int, b: int) -> int:
	"""Multiply two numbers"""
	return a * b

#  division tool
@mcp.tool(name="divide")
def divide(a: int, b: int) -> float:
	"""Divide two numbers"""
	return a / b

# power tool
@mcp.tool(name="power")
def power(a: int, b: int) -> int:
	"""Power of two numbers"""
	return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
	"""Square root of a number"""
	return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
	"""Cube root of a number"""
	return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
	"""factorial of a number"""
	return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
	"""log of a number"""
	return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
	"""remainder of two numbers divison"""
	return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
	"""sin of a number"""
	return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
	"""cos of a number"""
	return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
	"""tan of a number"""
	return float(math.tan(a))

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
	"""Get a personalized greeting"""
	return f"Hello, {name}!"


# execute and return the stdio output
if __name__ == "__main__":
	# mcp.run(transport="stdio")
	# mcp.run('streamable-http')
	# mcp.run(transport='streamable-http', host='0.0.0.0', port=kPORT)
	# uvicorn.run(mcp.streamable_http_app, host="0.0.0.0", port=kPORT, reload=True, log_level="debug")
	uvicorn.run(mcp.streamable_http_app, host="0.0.0.0", port=kPORT, log_level="debug")
	pass

# 初始化 MCP Server
# @app.post("/mcp")
# async def handle_mcp(request: Request):
# 	body = await request.json()

# 	# body 是 JSON-RPC 格式 {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
# 	response = await mcp.dispatch(body)

# 	# 如果是通知（没有 id），dispatch 可能返回 None
# 	return response or {}

