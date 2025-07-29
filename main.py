# i wrote all the code in the main file by following a youtube tutorial (link here:https://www.youtube.com/watch?v=UYJDKSah-Ww).
# i also used chatgpt to help with discord related commands because that's an area where i lack knowledge. after using chatgpt, i try to understand what it wrote and add comment next the the code

from typing import Final
import os
from dotenv import load_dotenv  # Load environment variables from .env file
from discord import Intents, Message, Client, TextChannel, DMChannel
import asyncio
from buzzer_game import BuzzerGame, WrittenQuestionGame

# Load environment variables
load_dotenv()
# Get bot token from environment variables
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("oops! couldn't find the discord token. make sure it's in your .env file!")

# Setup Discord client with required permissions
intents: Intents = Intents.default()
intents.message_content = True  # Allow bot to read message content
intents.dm_messages = True  # Enable DM messages
client: Client = Client(intents=intents)

# Initialize game variables
quiz = None  # Will be set based on game type
game_type = None  # Will store 'mc' or 'wt'
# Multiple choice questions
MC_SHEET_URL = "https://docs.google.com/spreadsheets/d/1VIpeHGOLNNegPWIfrlg8bqpSKOvwmk5se2od8LXEYS8/export?format=csv&gid=0"
# Written test questions
WT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1Ww2R9XDo_4lMZMdtflYbq025t3GcClRWzTJFvRVJN8Q/export?format=csv&gid=0"

# Youtube + chatgpt (it also help me to add comments so I can understand the code/debug)


@client.event
async def on_ready() -> None:
    """Called when the bot is ready and connected to Discord"""
    print(f'{client.user} is now running!')
    print('bot is ready!')


@client.event
async def on_message(message: Message) -> None:
    """Main message handler - processes all messages the bot can see"""
    # Ignore bot's own messages to prevent loops
    if message.author == client.user:
        return

    content = message.content.strip().lower()
    user_message = content.upper()

    # Handle DM messages (player answers)
    if isinstance(message.channel, DMChannel):
        await handle_dm_message(message, content, user_message)
        return

    # Handle game setup phase
    if content == "join":
        await handle_player_join(message)
        return

    # Handle number input for questions
    if content.isdigit():
        print(f"DEBUG: Received number input: {content}")
        if len(quiz.players) > 0:  # Only process if there are players
            await handle_question_count(message)
            return
        else:
            await message.channel.send("Please join the game first by typing 'join'!")
            return

    # Handle other game messages in text channels
    if isinstance(message.channel, TextChannel):
        await handle_game_message(message, content, user_message)


async def handle_dm_message(message, content, user_message):
    """Handle messages in DMs - processes player answers"""
    if not quiz:  # First check if quiz exists
        await message.channel.send("No game in progress! Please start a game in the main channel first.")
        return

    player_id = str(message.author.id)

    # Only process answers during active questions
    if not quiz.game_started or not quiz.question_active:
        await message.channel.send("No active question! Please wait for the next question.")
        return

    # Only process if player is in the game
    if player_id not in quiz.players:
        await message.channel.send("You are not in the game! Please join the game in the main channel first.")
        return

    # Handle answer submission based on game type
    if game_type == 'mc':
        if user_message in ["A", "B", "C", "D"]:
            response = quiz.submit_answer(player_id, user_message.lower())
            await message.channel.send(response)

            # Notify main channel that player has answered
            if quiz.current_channel:
                await quiz.current_channel.send(f"✅ {quiz.players[player_id]['name']} has submitted their answer!")
        else:
            await message.channel.send("Please choose a valid option (a, b, c, or d).")
    else:  # wt
        # For written test, accept any non-empty answer
        if content.strip():
            response = quiz.submit_answer(player_id, content)
            await message.channel.send(response)

            # Notify main channel that player has answered
            if quiz.current_channel:
                await quiz.current_channel.send(f"✅ {quiz.players[player_id]['name']} has submitted their answer!")
        else:
            await message.channel.send("Please type your answer!")


async def handle_player_join(message):
    """Handle player joining the game - creates DM channel and adds player to game"""
    if not quiz:  # First check if quiz exists
        await message.channel.send("No game in progress! Type 'start' to start a new game.")
        return

    player_id = str(message.author.id)
    print(
        f"DEBUG: Player {message.author.name} (ID: {player_id}) trying to join")
    print(f"DEBUG: Current players: {quiz.players}")

    if player_id in quiz.players:
        await message.channel.send(f"{message.author.mention} has already joined the game!")
    else:
        # Create DM channel with player
        try:
            dm_channel = await message.author.create_dm()
            response = quiz.add_player(
                player_id, message.author.name, dm_channel)
            print(f"DEBUG: After adding player: {quiz.players}")
            await message.channel.send(response)

            # Send welcome message to DM
            await dm_channel.send("Welcome to the game! Questions will be sent to you here, and you can submit your answers in this DM.")
            await dm_channel.send("Please wait in the main channel for the game to start. You'll need to enter the number of questions you want to play!")

            # Show player list in main channel
            players = [player["name"] for player in quiz.players.values()]
            player_count = len(players)
            await message.channel.send(f"Current players ({player_count}): {', '.join(players)}")
            await message.channel.send("Type a number to set how many questions you want to play!")
        except Exception as e:
            print(f"Error creating DM channel: {e}")
            await message.channel.send(f"⚠️ {message.author.mention}, I couldn't send you a DM. Please check your privacy settings and try again.")


async def handle_question_count(message):
    """Handle setting the number of questions - starts the game with selected questions"""
    if not quiz:  # First check if quiz exists
        await message.channel.send("No game in progress! Type 'start' to start a new game.")
        return

    try:
        num_questions = int(message.content)
        print(f"DEBUG: User requested {num_questions} questions")
        print(f"DEBUG: Total available questions: {quiz.total_questions}")

        if num_questions < 1:
            await message.channel.send("Please choose a number greater than 0!")
            return

        if num_questions > quiz.total_questions:
            await message.channel.send(f"Please choose a number between 1 and {quiz.total_questions}!")
            return

        # Get the appropriate sheet URL based on game type
        sheet_url = MC_SHEET_URL if game_type == 'mc' else WT_SHEET_URL
        print(f"DEBUG: Using sheet URL: {sheet_url}")

        # Start the game with the selected number of questions and sheet URL
        result = quiz.start_game(num_questions, sheet_url)
        if result.startswith("Error"):
            await message.channel.send(result)
            return

        await message.channel.send(result)

        # Send countdown messages to all players
        for player_id, player_data in quiz.players.items():
            try:
                await player_data["dm_channel"].send("Game starting in 5 seconds...")
            except Exception as e:
                print(f"Error sending countdown to {player_data['name']}: {e}")
                await message.channel.send(f"⚠️ Could not send countdown to {player_data['name']}. Please check your DM settings.")

        await asyncio.sleep(5)  # Wait 5 seconds before starting
        await quiz.show_next_question(message.channel)

    except ValueError:
        await message.channel.send("Please enter a valid number!")


async def handle_game_message(message, content, user_message):
    """Handle messages during active gameplay - processes game commands"""
    # Handle commands
    if content == "cancel":
        await handle_cancel(message)
    # Handle bot mentions
    elif client.user in message.mentions:
        await handle_bot_command(message)


async def handle_cancel(message):
    """Handle game cancellation - resets all game state"""
    global quiz, game_type

    if not quiz:
        await message.channel.send("No game in progress!")
        return

    # Reset everything
    if quiz.answer_timer and not quiz.answer_timer.done():
        quiz.answer_timer.cancel()
    quiz.reset_quiz()  # Reset the quiz state
    quiz = None  # Reset the quiz object
    game_type = None  # Reset the game type
    await message.channel.send("Game cancelled!")


async def handle_bot_command(message):
    """Handle commands that mention the bot - processes start and help commands"""
    command = message.content.replace(
        f"<@{client.user.id}>", "").strip().lower()

    if command == "start":
        await handle_game_start(message)
    elif command == "help":
        await show_help(message)


async def handle_game_start(message):
    """Handle starting a new game - initializes game type and quiz object"""
    global quiz, game_type

    # Always reset game state when starting a new game
    quiz = None
    game_type = None

    # Ask for game type
    await message.channel.send("Please choose the game type:\nType 'mc' for Multiple Choice\nType 'wt' for Written Test")

    def check_game_type(m):
        return m.author == message.author and m.channel == message.channel and m.content.lower() in ['mc', 'wt']

    try:
        game_type_msg = await client.wait_for('message', check=check_game_type, timeout=30.0)
        game_type = game_type_msg.content.lower()

        # Initialize appropriate game class
        if game_type == 'mc':
            quiz = BuzzerGame()
            sheet_url = MC_SHEET_URL
            print(f"DEBUG: Using MC sheet URL: {sheet_url}")
        else:  # wt
            quiz = WrittenQuestionGame()
            sheet_url = WT_SHEET_URL
            print(f"DEBUG: Using WT sheet URL: {sheet_url}")

        # Load questions from appropriate Google Sheet
        print(f"DEBUG: Loading questions from sheet: {sheet_url}")
        questions = quiz.get_questions_from_sheet(sheet_url)
        if not questions:
            await message.channel.send("Error: Could not load questions from Google Sheet. Please try again later.")
            quiz = None
            game_type = None
            return

        quiz.questions = questions
        quiz.total_questions = len(questions)
        print(f"DEBUG: Loaded {quiz.total_questions} questions")

        if quiz.total_questions == 0:
            await message.channel.send("Error: No questions were loaded from the sheet. Please try again later.")
            quiz = None
            game_type = None
            return

        quiz.game_started = True
        quiz.current_channel = message.channel

        await message.channel.send(f"New {game_type.upper()} game starting! Type 'join' to join the game.")
        await message.channel.send(f"After joining, type a number between 1 and {quiz.total_questions} to set how many questions you want to play!")

    except asyncio.TimeoutError:
        await message.channel.send("No game type selected. Game start cancelled.")
        quiz = None
        game_type = None
        return

# When user types 'help'......


async def show_help(message):
    """Show help message"""
    help_text = """
**how to play:**
1. mention me and type 'start' to begin a new game
2. type 'join' to join the game
3. questions will be sent to your DMs
4. submit your answers in the DM channel
5. type 'cancel' to end the current game
"""
    await message.channel.send(help_text)


def main() -> None:
    try:
        print("starting bot...")
        client.run(TOKEN)
    except Exception as e:
        print(f"oops! something went wrong: {str(e)}")


if __name__ == '__main__':
    main()
