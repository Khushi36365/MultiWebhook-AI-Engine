from pydantic import BaseModel
from typing import Optional, Dict, Any


class Tool(BaseModel):
    name: str
    description: str

    category: Optional[str] = "general"

    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = {}

    priority: Optional[int] = 100

    # CORE ADDITIONS
    input_schema: Optional[Dict[str, Any]] = {}
    output_schema: Optional[Dict[str, Any]] = {}

    example: Optional[Dict[str, Any]] = {}