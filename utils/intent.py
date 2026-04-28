def detect_intents(message: str):
    msg = message.lower().strip()

    intents = []

    # -------------------------
    # SAVE USER (SMART)
    # -------------------------
    if (
        "@" in msg and
        any(x in msg for x in [
            "i am", "my name", "this is", "it's me"
        ])
    ):
        intents.append("save_user")

    # -------------------------
    # SEND EMAIL (STRICT)
    # -------------------------
    if (
        "send" in msg and "email" in msg
    ) or any(x in msg for x in [
        "send mail",
        "email to",
        "send a welcome email",
        "welcome email"
    ]):
        intents.append("send_email")

    # -------------------------
    # GET USER DATA
    # -------------------------
    if any(x in msg for x in [
        "my email",
        "show my data",
        "get my data",
        "details",
        "get details",
        "fetch data",
        "what is my email",
        "who am i",
        
        # ADD THESE
        "email of",
        "email id of",
        "give me email",
        "get email",
        "show email",
        "email for"
    ]):
        intents.append("get_user")

    # -------------------------
    # REMOVE DUPLICATES
    # -------------------------
    intents = list(dict.fromkeys(intents))

    # -------------------------
    # DEFAULT FALLBACK
    # -------------------------
    return intents if intents else ["chat"]