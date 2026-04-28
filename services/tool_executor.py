import httpx
import asyncio
import time
from datetime import datetime
from core.database import analytics_collection


# -------------------------
# INPUT VALIDATION
# -------------------------
def validate_input(tool, data):
    schema = tool.get("input_schema", {})
    required_fields = schema.get("required", [])

    for field in required_fields:
        if field not in data or data[field] is None:
            return False, f"Missing field: {field}"

    return True, None


# -------------------------
# TOOL EXECUTION
# -------------------------
async def execute_tool(tool, data):

    print("EXECUTE TOOL CALLED:", tool.get("name"))

    start_time = time.time()
    success = False
    response_data = {}

    # 1. VALIDATION
    is_valid, error = validate_input(tool, data)
    if not is_valid:
        return {
            "status": "error",
            "message": error
        }

    # 2. RETRY SYSTEM
    retries = 2

    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                method = tool.get("method", "POST").upper()

                request_args = {
                    "method": method,
                    "url": tool.get("url"),
                    "headers": {
                        "Content-Type": "application/json",
                        **(tool.get("headers") or {})
                    }
                }

                if method == "GET":
                    request_args["params"] = data   
                else:
                    request_args["json"] = data

                response = await client.request(**request_args)

                try:
                    response_data = response.json()
                except:
                    response_data = {"response": response.text}

                success = True
                break  # exit retry loop (NOT function)

        except Exception as e:

            if attempt < retries:
                await asyncio.sleep(1)
                continue

            response_data = {
                "status": "error",
                "message": str(e)
            }

    # -------------------------
    # ANALYTICS LOGGING
    # -------------------------
    latency = int((time.time() - start_time) * 1000)

    print("📊 TRYING TO STORE ANALYTICS...")

    try:
        analytics_collection.insert_one({
            "tool": tool.get("name"),
            "success": success,
            "latency": latency,
            "timestamp": datetime.utcnow()
        })
        print("✅ ANALYTICS STORED:", tool.get("name"))

    except Exception as e:
        print("❌ ANALYTICS ERROR:", str(e))

    return response_data