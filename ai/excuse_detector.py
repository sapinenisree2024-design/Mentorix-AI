def detect_excuse(text):

    excuses = [

        "tired",
        "busy",
        "tomorrow",
        "lazy",
        "sleepy",
        "not motivated"

    ]

    for excuse in excuses:

        if excuse in text.lower():

            return True

    return False