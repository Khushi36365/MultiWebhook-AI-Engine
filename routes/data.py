from fastapi import APIRouter,Query
from core.database import collection


from pymongo.errors import DuplicateKeyError

import re


router = APIRouter()

@router.post("/save")
def save(data: dict):

    # -------------------------
    # SESSION
    # -------------------------
    data["session_id"] = data.get("session_id", "default")

    # -------------------------
    # CLEAN EMAIL
    # -------------------------
    email = data.get("email", "").strip().lower().rstrip(".,! ")
    name = data.get("name", "").strip().title()


    # -------------------------
    # EMAIL VALIDATION
    # -------------------------
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_pattern, email):
        return {
            "status": "error",
            "message": "Invalid email format"
        }

    # -------------------------
    # BLOCK FAKE DOMAINS ONLY
    # -------------------------
    blocked_domains = ["example.com", "test.com", "dummy.com"]

    domain = email.split("@")[-1]

    if domain in blocked_domains:
        return {
            "status": "error",
            "message": "Please use a real email address"
        }

    if not email or not name:
        return {
            "status": "error",
            "message": "Name and email are required"
        }

    data["email"] = email
    data["name"] = name

    # -------------------------
    # REMOVE INTERNAL FIELDS
    # -------------------------
    forbidden_fields = [
        "email_exists",
        "existing_user",
        "verified",
        "checked_email",
        "last_checked_email"
    ]

    for field in forbidden_fields:
        data.pop(field, None)

    # -------------------------
    # OPTIONAL: PRE-CHECK (clean UX)
    # -------------------------
    existing = collection.find_one({"email": email})

    if existing:
        return {
            "status": "exists",
            "message": "This email already exists"
        }

    # -------------------------
    # INSERT
    # -------------------------
    try:
        result = collection.insert_one(data)

        return {
            "status": "saved",
            "id": str(result.inserted_id)
        }

    except DuplicateKeyError:
        return {
            "status": "exists",
            "message": "This email already exists"
        }
    


@router.get("/get")
def get(
    name: str = Query(None),
    email: str = Query(None),
    session_id: str = Query(None)
):

    query = {}

    if email:
        query["email"] = email

    elif name:
        query["name"] = {"$regex": f"^{name}$", "$options": "i"}

    else:
        return {
            "status": "error",
            "message": "Please provide name or email"
        }

    data = list(collection.find(
        query,
        {
            "_id": 0,
            "email_exists": 0,
            "existing_user": 0,
            "verified": 0,
            "checked_email": 0,
            "last_checked_email": 0
        }
    ))

    return {"data": data}