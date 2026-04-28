from pymongo import MongoClient
from core.config import MONGO_URL

client = MongoClient(MONGO_URL)

db = client["ai_agent_webhook_dynamic"]
collection = db["users"]
tools_collection = db["tools"]
analytics_collection = db["tool_analytics"]

collection.create_index("email", unique=True)
