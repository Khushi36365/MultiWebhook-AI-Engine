from fastapi import APIRouter
from core.database import tools_collection
from models.tool_model import Tool


from services.tool_executor import execute_tool

from core.database import analytics_collection

router = APIRouter()

# Add tool
@router.post("/tools")
def add_tool(tool: Tool):

    data = tool.model_dump()

    print("SAVING TOOL:", data)

    # insert tool
    result = tools_collection.insert_one(data)

    # DO NOT return ObjectId directly
    return {
        "status": "tool added",
        "tool_id": str(result.inserted_id)   
    }

# Get all tools
@router.get("/tools")
def get_tools():
    tools = list(tools_collection.find({}, {"_id": 0}))
    return {"tools": tools}


# tool test
@router.post("/tools/test")
async def test_tool(data: dict):

    tool_name = data.get("tool_name")
    input_data = data.get("input", {})

    # 🔍 find tool
    tool = tools_collection.find_one({"name": tool_name}, {"_id": 0})

    if not tool:
        return {"status": "error", "message": "Tool not found"}

    # execute tool
    result = await execute_tool(tool, input_data)

    return {
        "status": "success",
        "tool": tool_name,
        "input": input_data,
        "output": result
    }


@router.get("/tools/analytics")
def get_analytics():

    data = list(analytics_collection.find({}, {"_id": 0}))

    return {"analytics": data}


@router.get("/tools/analytics/summary")
def analytics_summary():

    pipeline = [
        {
            "$group": {
                "_id": "$tool",
                "count": {"$sum": 1},
                "success_rate": {
                    "$avg": {
                        "$cond": [{"$eq": ["$success", True]}, 1, 0]
                    }
                },
                "avg_latency": {"$avg": "$latency"},
                "last_used": {"$max": "$timestamp"}
            }
        }
    ]

    result = list(analytics_collection.aggregate(pipeline))

    return {"summary": result}