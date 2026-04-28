import re
from groq import Groq

from core.config import GROQ_API_KEY
from utils.memory import chat_memory, user_context, user_state
from core.database import tools_collection
from services.tool_executor import execute_tool
from utils.intent import detect_intents


from utils.memory import chat_memory, user_context, user_state

# -------------------------
# LOAD SYSTEM PROMPT
# -------------------------
with open("prompts/system_prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

client = Groq(api_key=GROQ_API_KEY)


# -------------------------
# MODEL SELECTION
# -------------------------
def select_model(user_message):
    if "fast" in user_message.lower():
        return "llama-3.1-8b-instant"
    return "openai/gpt-oss-20b"


# -------------------------
# USER INFO EXTRACTION
# -------------------------
def clean_email(email: str):
    return email.strip().lower().rstrip(".,! ")

def extract_user_info(message, context):

    msg = message.lower()
    new_data = {}

    # email extraction
    def is_valid_email(email: str):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email)

    email_match = re.search(r'[\w\.-]+@[\w\.-]+', message)

    if email_match:
        cleaned = clean_email(email_match.group(0))

        if is_valid_email(cleaned):
            new_data["email"] = cleaned

    # name extraction (FIXED)
    name_match = re.search(
        r"(?:my name is|i am)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*?)(?=\s+and|\s*$)",
        message.lower()
    )

    if name_match:
        extracted_name = name_match.group(1).strip()

        # CLEAN EXTRA WORDS (extra safety)
        extracted_name = re.sub(r"\b(and|my|email|is)\b.*", "", extracted_name).strip()

        new_data["name"] = extracted_name.title()

    # other user (existing)
    other_match = re.search(
        r"(?:details of|get details of|data of|email of)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)",
        msg
    )
    if other_match and "my" not in msg:
        new_data["name"] = other_match.group(1).title()

    # only use to_match as a fallback — don't overwrite a properly extracted name
    if "name" not in new_data:
        to_match = re.search(r"to\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)*)", msg)

        if to_match:
            name = to_match.group(1).strip()
            name = re.split(r"\b(and|email|with|please)\b", name)[0].strip()
            new_data["name"] = name.title()

    return new_data

# -------------------------
# HANDLERS
# -------------------------

async def handle_save_user(ctx, session_id, tools):

    name = ctx.get("name")
    email = ctx.get("email")

    # EMAIL VALIDATION (ADD HERE)
    if email and not re.match(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        email
    ):
        return "That doesn't look like a valid email. Please enter a correct one.", []

    # PARTIAL DATA HANDLING
    if email and not name:
        return "Got your email 👍 Now please tell me your name.", []

    if name and not email:
        return "Got your name 👍 Now please provide your email.", []

    if not name and not email:
        return "Please provide your name and email.", []

    tool = next((t for t in tools if t["name"] == "save_user_data"), None)

    res = await execute_tool(tool, {
        "name": name,
        "email": email,
        "session_id": session_id
    })

    # HANDLE ERROR FIRST
    if res.get("status") == "error":
        return res.get("message", "Something went wrong"), [
            {"tool": "save_user_data", "output": res}
        ]

    # HANDLE EXISTS
    if res.get("status") == "exists":
        return "User already exists", [
            {"tool": "save_user_data", "output": res}
        ]

    # SUCCESS
    return "User saved successfully", [
        {"tool": "save_user_data", "output": res}
    ]

async def handle_get_user(req, ctx, session_id, tools):

    print('ctx', ctx)

    tool = next((t for t in tools if t["name"] == "get_user_data"), None)

    email = ctx.get("email")
    name = ctx.get("name")

    msg = req.message.lower()

    # -------------------------
    # CASE 1: "MY DATA"
    # -------------------------
    if "my" in msg:

        email = ctx.get("email")
        name = ctx.get("name")

        # prefer email
        if email:
            payload = {"email": email}

        # fallback to name
        elif name:
            payload = {"name": name}

        # nothing known
        else:
            return "I don't have your details yet. Please tell me your name and email first.", []

    # -------------------------
    # CASE 2: OTHER USER
    # -------------------------
    else:

        # try name first
        if name:
            payload = {"name": name}

        elif email:
            payload = {"email": email}

        else:
            return "Please specify whose data you want.", []

    # -------------------------
    # EXECUTE TOOL
    # -------------------------
    res = await execute_tool(tool, payload)

    # AUTO FALLBACK IF EMAIL FAILED
    if not res.get("data") and "email" in payload and ctx.get("name"):

        fallback_res = await execute_tool(tool, {
            "name": ctx.get("name")
        })

        if fallback_res.get("data"):
            res = fallback_res

    tools_used = [{
        "tool": "get_user_data",
        "input": payload,
        "output": res
    }]

    if not res.get("data"):
        return "No data found", tools_used

    user = res["data"][0]

    # -------------------------
    # RESPONSE
    # -------------------------
    if "email" in msg:
        return f"Your email is {user.get('email')}", tools_used

    elif "name" in msg:
        return f"Your name is {user.get('name')}", tools_used

    return f"Name: {user.get('name')}, Email: {user.get('email')}", tools_used

async def handle_send_email(req, ctx, session_id, tools, force=False):


    msg = req.message.lower().strip()


    # QUESTION DETECTION (GENERIC PENDING ACTION)
    if not force and any(x in msg for x in ["can you", "could you", "would you", "will you"]):

        pending_data = ctx.copy()

        # EXTRACT NAME FROM MESSAGE
        match = re.search(r"to\s+([a-zA-Z]+)", msg)
        if match:
            pending_data["name"] = match.group(1).title()

        user_state[session_id] = {
            "pending_action": {
                "intent": "send_email",
                "data": pending_data
            }
        }

        print("STORED PENDING:", user_state[session_id])  # DEBUG

        return "Yes 👍 I can send the email. Do you want me to proceed?", []



    # FIX 2: SAFETY GUARD (ADD THIS BLOCK HERE)
    msg = req.message.lower()
    if not force and not any(x in msg for x in ["send", "email", "mail"]):
        return "Sure 👍", []

    email = ctx.get("email")
    name = ctx.get("name")

    # if email missing but name exists → fetch from DB
    if not email and name:

        get_tool = next((t for t in tools if t["name"] == "get_user_data"), None)

        res = await execute_tool(get_tool, {
            "name": name
        })

        if res.get("data"):
            email = res["data"][0].get("email")

            # FIX 4: keep context consistent
            ctx["email"] = email
            ctx["name"] = name   # ✅ ADD THIS LINE

        else:
            return f"I couldn't find {name} in database", []
        

    tools_used = []

    # check user exists
    get_tool = next((t for t in tools if t["name"] == "get_user_data"), None)

    check_res = await execute_tool(get_tool, {
        "email": email,
        "session_id": session_id
    })

    tools_used.append({"tool": "get_user_data", "output": check_res})

    if not check_res.get("data"):

        if not name:
            return "Please provide name before sending email", tools_used

        save_tool = next((t for t in tools if t["name"] == "save_user_data"), None)

        save_res = await execute_tool(save_tool, {
            "name": name,
            "email": email,
            "session_id": session_id
        })

        tools_used.append({"tool": "save_user_data", "output": save_res})

    # email content
    subject = "Welcome!" if "welcome" in req.message.lower() else "Hello"


    display_name = name or (email.split("@")[0].title() if email else "there")

    body = f"""
Hi {display_name},

Welcome! We are happy to have you with us.

Best regards,
Team
"""

    email_tool = next((t for t in tools if t["name"] == "send_email"), None)

    send_res = await execute_tool(email_tool, {
        "to": email,
        "subject": subject,
        "body": body
    })

    tools_used.append({"tool": "send_email", "output": send_res})

    return "Email sent successfully", tools_used


# -------------------------
# MAIN CHAT HANDLER
# -------------------------
async def handle_chat(req):

    session_id = req.session_id or "default"

    # -------------------------
    # INIT MEMORY
    # -------------------------
    chat_memory.setdefault(session_id, [])
    user_context.setdefault(session_id, {})
    user_state.setdefault(session_id, {})

    history = chat_memory[session_id]
    ctx = user_context[session_id]

    # -------------------------
    # EXTRACT CONTEXT (FIXED)
    # -------------------------
    new_data = extract_user_info(req.message, ctx)

    # Case 1: BOTH name + email in same message
    if "name" in new_data and "email" in new_data:
        ctx["name"] = new_data["name"]
        ctx["email"] = new_data["email"]

    # Case 2: ONLY email
    elif "email" in new_data:
        ctx["email"] = new_data["email"]
        ctx.pop("name", None)

    # Case 3: ONLY name
    elif "name" in new_data:
        ctx["name"] = new_data["name"]
        ctx.pop("email", None)

    # --- 
    # handle 
    # ----

    msg = req.message.lower().strip()

    # BLOCK FAKE ACTION REQUESTS (ADD HERE)
    if any(x in msg for x in ["pretend", "imagine", "assume"]):
        return {
            "reply": "I only perform real actions when explicitly requested. Let me know what you'd like me to do 👍",
            "tools_used": [],
            "session_id": session_id
        }

    # CANCEL
    if msg in ["no", "cancel", "stop", "nah"]:
        user_state[session_id] = {}
        return {
            "reply": "Got it 👍 I won't proceed with that.",
            "tools_used": [],
            "session_id": session_id
        }

    # HANDLE CONFIRMATION (GENERIC)
    if msg in ["ok", "yes", "yeah", "yup", "sure"]:


        state = user_state.get(session_id, {})

        # SAFETY FIX (prevents crash)
        if not isinstance(state, dict):
            state = {}
            user_state[session_id] = {}

        pending = state.get("pending_action")

        if pending:

            intent = pending.get("intent")
            data = pending.get("data", {})

            tools = list(tools_collection.find({}, {"_id": 0}))

            # HANDLER REGISTRY (basic version)
            if intent == "send_email":
                reply, tools_used = await handle_send_email(req, data, session_id, tools, force=True)

            elif intent == "get_user":
                reply, tools_used = await handle_get_user(req, data, session_id, tools)

            else:
                reply, tools_used = "Action not supported yet", []

            # clear state
            user_state[session_id] = {}

            return {
                "reply": reply,
                "tools_used": tools_used,
                "session_id": session_id
            }
        

    # -------------------------
    # INTENT ROUTING
    # -------------------------
    intents = detect_intents(req.message)
    intents = list(dict.fromkeys(intents))  # remove duplicates

    tools = list(tools_collection.find({}, {"_id": 0}))

    final_reply = []
    all_tools_used = []

    # IMPORTANT: DO NOT BLOCK INTENTS
    for intent in intents:

        if intent == "save_user":
            reply, tools_used = await handle_save_user(ctx, session_id, tools)

            # STOP EVERYTHING if save fails
            if "real email address" in reply.lower() or "invalid" in reply.lower():
                return {
                    "reply": reply,
                    "tools_used": tools_used,
                    "session_id": session_id
                }

        elif intent == "send_email":
            reply, tools_used = await handle_send_email(req, ctx, session_id, tools)

        elif intent == "get_user":
            reply, tools_used = await handle_get_user(req, ctx, session_id, tools)
        
        else:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(history)
            messages.append({"role": "user", "content": req.message})

            response = client.chat.completions.create(
                model=select_model(req.message),
                messages=messages
            )

            reply = response.choices[0].message.content
            tools_used = []

        final_reply.append(reply)
        all_tools_used.extend(tools_used)

    # -------------------------
    # SAVE MEMORY (FIXED)
    # -------------------------
    history.append({"role": "user", "content": req.message})
    history.append({
        "role": "assistant",
        "content": "\n".join(final_reply)
    })

    chat_memory[session_id] = history[-10:]

    return {
        "reply": "\n".join(final_reply),
        "tools_used": all_tools_used,
        "session_id": session_id
    }