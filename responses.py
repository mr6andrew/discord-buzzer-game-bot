# I didn't connect this part to the main file because i didn't want to mess with the code


import random
import os
from dotenv import load_dotenv

load_dotenv()


def get_response(user_input: str) -> str:
    lowered = user_input.lower()

    # Simple keyword-based responses
    if lowered == '':
        return "Well, you are awfully silent"
    elif "hello" in lowered:
        return "Hello there!"
    elif "hi" in lowered:
        return "Hi!"
    elif "bye" in lowered:
        return "See you 😗"
    elif "roll dice" in lowered:
        return f'You rolled: {random.randint(1, 6)}'
    elif "are you ai" in lowered:
        return "I would say I'm mixed"
    elif "when" and "meeting" in lowered:
        return f'''Our club meetings are every Monday and Wednesday at lunch! Our prebuild meeting will be on Wednesday afterschool. We're in room 113'''
    elif "where" and "meeting" in lowered:
        return f''' We're at room 113'''
    elif "your name" in lowered:
        return random.choice(["My name is mr6a", "mr6a", "I'm mr6a. Nice to meet you!"])
    elif "who are you" in lowered:
        return random.choice(["My name is mr6a", "mr6a", "I'm mr6a. Nice to meet you!"])
    elif "who you are" in lowered:
        return random.choice(["My name is mr6a", "mr6a", "I'm mr6a. Nice to meet you!"])
    elif "who made you" in lowered:
        return "Andrew"
    elif "what can you" in lowered:
        return "I want to keep it as a secret"
    elif "help" in lowered or "info" in lowered:
        return """
**how to play:**
1. type 'start' to begin a new game
2. type 'join' to join the game
3. when a question appears, type a, b, c, or d to answer
4. type 'cancel' to end the current game

**other commands:**
- say 'hello' or 'hi' to greet me
- say 'bye' to say goodbye
- type 'roll dice' for a random number
- ask 'are you ai?'
- ask 'when is the meeting?' or 'where is the meeting?'
- ask 'what is your name?' or 'who are you?'
- ask 'who made you?'
- ask 'what can you do?'
"""

    # Simple fallback response for unrecognized input
    return "I'm not sure how to respond to that. Try asking me something else!"
