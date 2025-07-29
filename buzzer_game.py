import random
import asyncio  # at first, i was going to use time.sleep(), but after looking things up online, i found that most people use asyncio for discord bots. it allows the program to do multitasking, like counting down and responding players at the same time
from sheet_questions import get_questions_from_sheet
# written question next week animation? sleep?


# initializing variables
# class
class BuzzerGame:
    def __init__(self):
        # initialize game variables
        # dictionaries
        self.questions = {}  # stores all questions from the sheet
        self.players = {}    # stores player data (name, score, dm_channel)
        self.answers = {}    # stores current question answers
        self.remaining_questions = []
        self.current_question = None
        self.current_question_number = 0
        self.time_limit = 10
        self.total_questions = 0
        self.game_started = False
        self.question_active = False
        # will store the countdown task (used to cancel early if needed)
        self.answer_timer = None
        self.current_channel = None
        self.timer_task = None
        self.time_left = 0

    def get_questions_from_sheet(self, sheet_url=None):
        return get_questions_from_sheet(sheet_url)

    def reset_quiz(self):
        # reset all game data to start new game
        # dictionaries
        self.questions = {}
        self.players = {}
        self.answers = {}
        self.remaining_questions = []
        self.current_question = None
        self.current_question_number = 0
        self.game_started = False
        self.question_active = False
        self.current_channel = None
        self.total_questions = 0

        # stop countdown timer if still running
        if self.answer_timer and not self.answer_timer.done():
            self.answer_timer.cancel()
            self.answer_timer = None

    def start_game(self, num_questions, sheet_url=None):
        # start new game with random questions
        if num_questions > self.total_questions:  # error handling
            return f"oops! you picked {num_questions} questions, but i only have {self.total_questions} right now 😅"

        all_questions = list(self.questions.keys())
        random.shuffle(all_questions)
        self.remaining_questions = all_questions[:num_questions]

        # dictionaries
        self.answers = {}
        self.current_question = None
        self.game_started = True
        self.question_active = False
        self.current_question_number = 0

        return f"game started with {num_questions} questions!"

    def add_player(self, player_id, player_name, dm_channel):
        # add new player to game
        if player_id not in self.players:
            # dictionaries
            self.players[player_id] = {
                "name": player_name,
                "score": 0,
                "dm_channel": dm_channel
            }
            return f"👋 {player_name} has joined the game!"
        return f"{player_name} is already in the game!"

    def has_more_questions(self):
        return len(self.remaining_questions) > 0

    def get_next_question(self):
        # get and format next question
        if not self.has_more_questions():
            return None, None

        self.current_question = self.remaining_questions.pop(0)
        self.current_question_number += 1
        # dictionaries
        question_data = self.questions[self.current_question]

        formatted = "**NEW QUESTION**\n\n"
        formatted += f"**Question {self.current_question_number}:** {self.current_question}\n\n"
        formatted += "**Options:**\n"
        formatted += "\n".join(question_data["choices"])
        formatted += f"\n\n**Time Limit:** {self.time_limit} seconds"
        formatted += "\n\nType your answer (a, b, c, or d) in this DM!"

        image_link = question_data.get("image_link")
        if image_link and image_link.strip():
            return formatted, image_link
        return formatted, None

    def submit_answer(self, player_id, answer):
        # handle player's answer submission
        if not self.current_question:
            return "no active question!"

        if player_id not in self.players:
            return f"you are not in the game! type 'join' to join first."

        answer = answer.lower()
        if answer not in ["a", "b", "c", "d"]:
            return "please choose a valid option (a, b, c, or d)."

        # dictionaries
        self.answers[player_id] = answer
        return f"your answer has been submitted!"

    def check_answers(self):
        # check answers and update scores
        if not self.current_question:
            return "no active question!"

        # dictionaries
        question_data = self.questions[self.current_question]
        correct_answer = question_data["answer"]
        explanation = question_data["explanation"]

        results = []
        for player_id, answer in self.answers.items():
            normalized_answer = ''.join(answer.split())

            # split answer into magnitude and unit
            player_magnitude = ''.join(
                c for c in normalized_answer if c.isdigit() or c == '.')
            player_unit = ''.join(
                c for c in normalized_answer if not c.isdigit() and c != '.')

            correct_magnitude = ''.join(
                c for c in correct_answer if c.isdigit() or c == '.')
            correct_unit = ''.join(
                c for c in correct_answer if not c.isdigit() and c != '.')

            score = 0
            if player_magnitude == correct_magnitude:
                score += 2  # 2 points for correct magnitude
            if player_unit.lower() == correct_unit.lower():
                score += 1  # 1 point for correct unit

            if score > 0:
                self.players[player_id]["score"] += score
                name = self.players[player_id]["name"]
                if score == 3:
                    results.append(
                        f"{name} got it completely right! +3 points 🎉")
                else:
                    results.append(
                        f"{name} got {score} points! ({score/3*100:.0f}% correct)")
            else:
                name = self.players[player_id]["name"]
                results.append(f"{name} missed this one.")

        display_answer = question_data.get(
            "answer_with_space", question_data["answer"])
        results.append(f"\n**correct answer: {display_answer}**")
        results.append(f"**explanation:** {explanation}")

        # dictionaries
        self.answers = {}
        return "\n".join(results)

    def get_scores(self):
        # get current game scores
        if not self.players:
            return "no players in the game!"

        score_text = "**Scores:**\n"
        for player_id, data in self.players.items():
            score_text += f"{data['name']}: {data['score']} points\n"
        return score_text

    def get_winner(self):
        # find game winner(s)
        if not self.players:
            return "no players in the game!"

        max_score = max(player["score"] for player in self.players.values())
        winners = [player["name"]
                   for player in self.players.values() if player["score"] == max_score]

        if len(winners) == 1:
            return f"winner: {winners[0]} with {max_score} points!"
        return f"tie! winners: {', '.join(winners)} with {max_score} points each!"

    async def start_question_timer(self, channel):
        # start timer for current question
        self.current_channel = channel
        self.question_active = True

        # if someone restarted the timer too fast, kill the old one
        if self.answer_timer and not self.answer_timer.done():
            self.answer_timer.cancel()

        self.answer_timer = asyncio.create_task(
            self.question_timer_task(channel))

    async def question_timer_task(self, channel):
        # handle question timer and countdown
        progress_msg = await channel.send("game in progress...")
        progress_dots = ["...", "..", ".", "..", "..."]
        dot_index = 0

        next_question, next_image = self.get_next_question()
        if next_question:
            for player_id, player_data in self.players.items():
                await player_data["dm_channel"].send("----------------------------------------")
                await player_data["dm_channel"].send(next_question)
                if next_image:
                    await player_data["dm_channel"].send(next_image)

        countdown_msgs = {}
        for player_id, player_data in self.players.items():
            countdown_msgs[player_id] = await player_data["dm_channel"].send("⏰ **10** seconds remaining!")

        for i in range(9, 0, -1):
            await progress_msg.edit(content=f"game in progress{progress_dots[dot_index]}")
            dot_index = (dot_index + 1) % len(progress_dots)

            if self.all_players_answered():
                for player_id, msg in countdown_msgs.items():
                    await msg.edit(content="⏰ all players have answered!")
                await self.handle_all_answered(channel, None)
                return

            await asyncio.sleep(1)
            for player_id, msg in countdown_msgs.items():
                await msg.edit(content=f"⏰ **{i}** seconds remaining!")

        await asyncio.sleep(1)
        if not self.question_active:
            return

        if self.current_question:
            await self.handle_timeout(channel)

    def all_players_answered(self):
        # check if all players submitted answers
        if len(self.answers) != len(self.players) or not self.players:
            return False

        return all(
            player_id in self.answers and self.answers[player_id] in [
                "a", "b", "c", "d"]
            for player_id in self.players
        )

    async def handle_all_answered(self, channel, countdown_msg):
        # handle when all players answered
        results = self.check_answers()
        formatted_results = f"**Question {self.current_question_number} Results:**\n\n" + results

        for player_id, player_data in self.players.items():
            await player_data["dm_channel"].send(formatted_results)
            if not self.has_more_questions():
                await player_data["dm_channel"].send("🎉 **game over!** 🎉\n\nplease check the main channel to see the final results and winner!")

        self.question_active = False
        if not self.game_started:
            return

        await asyncio.sleep(5)
        if not self.game_started:
            return

        if self.has_more_questions():
            await self.show_next_question(channel)
        else:
            await self.end_game(channel)

    async def handle_timeout(self, channel):
        # handle when time runs out
        for player_id, player_data in self.players.items():
            if player_id not in self.answers:
                self.players[player_id]["score"] -= 2000
                await channel.send(f"⏰ {player_data['name']} didn't answer in time! -2000 points!")

        results = self.check_answers()
        formatted_results = f"**Question {self.current_question_number} Results:**\n\n" + results

        for player_id, player_data in self.players.items():
            await player_data["dm_channel"].send(formatted_results)
            if not self.has_more_questions():
                await player_data["dm_channel"].send("🎉 **game over!** 🎉\n\nplease check the main channel to see the final results and winner!")

        self.question_active = False
        if not self.game_started:
            return

        await asyncio.sleep(5)
        if not self.game_started:
            return

        if self.has_more_questions():
            await self.show_next_question(channel)
        else:
            await self.end_game(channel)

    async def show_next_question(self, channel):
        # show next question or end game
        if not self.has_more_questions():
            await self.end_game(channel)
            return

        self.question_active = True
        await self.start_question_timer(channel)

    async def end_game(self, channel):
        # end game and show final results
        if self.answer_timer and not self.answer_timer.done():
            self.answer_timer.cancel()
            self.answer_timer = None

        results_message = "🎉 **game over!** 🎉\n\n"
        results_message += "**final scores:**\n"

        sorted_players = sorted(
            self.players.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        for player_id, player_data in sorted_players:
            results_message += f"{player_data['name']}: {player_data['score']} points\n"

        results_message += f"\n**winner:** {self.get_winner()}"

        await channel.send(results_message)

        for player_id, player_data in self.players.items():
            if 'dm_channel' not in player_data:
                continue

            dm_message = "🎉 **game over!** 🎉\n\n"
            dm_message += "please check the main channel to see the final results and winner!"
            await player_data['dm_channel'].send(dm_message)

        self.reset_quiz()
        self.game_started = False


# class
class WrittenQuestionGame:
    def __init__(self):
        # initialize game variables
        # dictionaries
        self.questions = {}  # stores all questions from the sheet
        self.players = {}    # stores player data (name, score, dm_channel)
        self.answers = {}    # stores current question answers
        self.remaining_questions = []
        self.current_question = None
        self.current_question_number = 0
        self.time_limit = 30
        self.total_questions = 0
        self.game_started = False
        self.question_active = False
        # will store the countdown task (used to cancel early if needed)
        self.answer_timer = None
        self.current_channel = None

    def get_questions_from_sheet(self, sheet_url=None):
        return get_questions_from_sheet(sheet_url)

    def reset_quiz(self):
        # reset all game data to start new game
        # dictionaries
        self.questions = {}
        self.players = {}
        self.answers = {}
        self.remaining_questions = []
        self.current_question = None
        self.current_question_number = 0
        self.game_started = False
        self.question_active = False
        self.current_channel = None
        self.total_questions = 0

        # stop countdown timer if still running
        if self.answer_timer and not self.answer_timer.done():
            self.answer_timer.cancel()
            self.answer_timer = None

    def start_game(self, num_questions, sheet_url=None):
        # start new game with random questions
        if num_questions > self.total_questions:  # error handling
            return f"oops! you picked {num_questions} questions, but i only have {self.total_questions} right now 😅"

        all_questions = list(self.questions.keys())
        random.shuffle(all_questions)
        self.remaining_questions = all_questions[:num_questions]

        # dictionaries
        self.answers = {}
        self.current_question = None
        self.game_started = True
        self.question_active = False
        self.current_question_number = 0

        return f"game started with {num_questions} questions!"

    def add_player(self, player_id, player_name, dm_channel):
        # add new player to game
        if player_id not in self.players:
            # dictionaries
            self.players[player_id] = {
                "name": player_name,
                "score": 0,
                "dm_channel": dm_channel
            }
            return f"👋 {player_name} has joined the game!"
        return f"{player_name} is already in the game!"

    def has_more_questions(self):
        return len(self.remaining_questions) > 0

    def get_next_question(self):
        # get and format next question
        if not self.has_more_questions():
            return None, None

        self.current_question = self.remaining_questions.pop(0)
        self.current_question_number += 1
        # dictionaries
        question_data = self.questions[self.current_question]

        formatted = "**NEW QUESTION**\n\n"
        formatted += f"**Question {self.current_question_number}:** {self.current_question}\n\n"
        formatted += "**Instructions:**\n"
        formatted += "Please type your answer in this DM. You have 30 seconds to write your response.\n"
        formatted += f"\n**Time Limit:** {self.time_limit} seconds"

        image_link = question_data.get("image_link")
        if image_link and image_link.strip():
            return formatted, image_link
        return formatted, None

    def submit_answer(self, player_id, answer):
        # handle player's answer submission
        if not self.current_question:
            return "no active question!"

        if player_id not in self.players:
            return f"you are not in the game! type 'join' to join first."

        self.answers[player_id] = answer
        return f"your answer has been submitted!"

    def check_answers(self):
        # check answers and update scores
        if not self.current_question:
            return "no active question!"

        # dictionaries
        question_data = self.questions[self.current_question]
        correct_answer = question_data["answer"]
        explanation = question_data["explanation"]

        results = []
        for player_id, answer in self.answers.items():
            normalized_answer = ''.join(answer.split())

            # split answer into magnitude and unit
            player_magnitude = ''.join(
                c for c in normalized_answer if c.isdigit() or c == '.')
            player_unit = ''.join(
                c for c in normalized_answer if not c.isdigit() and c != '.')

            correct_magnitude = ''.join(
                c for c in correct_answer if c.isdigit() or c == '.')
            correct_unit = ''.join(
                c for c in correct_answer if not c.isdigit() and c != '.')

            score = 0
            if player_magnitude == correct_magnitude:
                score += 2
            if player_unit.lower() == correct_unit.lower():
                score += 1

            if score > 0:
                self.players[player_id]["score"] += score
                name = self.players[player_id]["name"]
                if score == 3:
                    results.append(
                        f"{name} got it completely right! +3 points 🎉")
                else:
                    results.append(
                        f"{name} got {score} points! ({score/3*100:.0f}% correct)")
            else:
                name = self.players[player_id]["name"]
                results.append(f"{name} missed this one.")

        display_answer = question_data.get(
            "answer_with_space", question_data["answer"])
        results.append(f"\n**correct answer: {display_answer}**")
        results.append(f"**explanation:** {explanation}")

        # dictionaries
        self.answers = {}
        return "\n".join(results)

    def get_scores(self):
        # get current game scores
        if not self.players:
            return "no players in the game!"

        score_text = "**Scores:**\n"
        for player_id, data in self.players.items():
            score_text += f"{data['name']}: {data['score']} points\n"
        return score_text

    def get_winner(self):
        # find game winner(s)
        if not self.players:
            return "no players in the game!"

        max_score = max(player["score"] for player in self.players.values())
        winners = [player["name"]
                   for player in self.players.values() if player["score"] == max_score]

        if len(winners) == 1:
            return f"winner: {winners[0]} with {max_score} points!"
        return f"tie! winners: {', '.join(winners)} with {max_score} points each!"

    async def start_question_timer(self, channel):
        # start timer for current question
        self.current_channel = channel
        self.question_active = True

        # if someone restarted the timer too fast, kill the old one
        if self.answer_timer and not self.answer_timer.done():
            self.answer_timer.cancel()

        self.answer_timer = asyncio.create_task(
            self.question_timer_task(channel))

    async def question_timer_task(self, channel):
        # handle question timer and countdown
        progress_msg = await channel.send("game in progress...")
        progress_dots = ["...", "..", ".", "..", "..."]
        dot_index = 0

        next_question, next_image = self.get_next_question()
        if next_question:
            for player_id, player_data in self.players.items():
                await player_data["dm_channel"].send("----------------------------------------")
                await player_data["dm_channel"].send(next_question)
                if next_image:
                    await player_data["dm_channel"].send(next_image)

        countdown_msgs = {}
        for player_id, player_data in self.players.items():
            countdown_msgs[player_id] = await player_data["dm_channel"].send("⏰ **30** seconds remaining!")

        for i in range(29, 0, -1):
            await progress_msg.edit(content=f"game in progress{progress_dots[dot_index]}")
            dot_index = (dot_index + 1) % len(progress_dots)

            if self.all_players_answered():
                for player_id, msg in countdown_msgs.items():
                    await msg.edit(content="⏰ all players have answered!")
                await self.handle_all_answered(channel, None)
                return

            await asyncio.sleep(1)
            for player_id, msg in countdown_msgs.items():
                await msg.edit(content=f"⏰ **{i}** seconds remaining!")

        await asyncio.sleep(1)
        if not self.question_active:
            return

        if self.current_question:
            await self.handle_timeout(channel)

    def all_players_answered(self):
        # check if all players submitted answers
        if len(self.answers) != len(self.players) or not self.players:
            return False

        return all(player_id in self.answers for player_id in self.players)

    async def handle_all_answered(self, channel, countdown_msg):
        # handle when all players answered
        results = self.check_answers()
        formatted_results = f"**Question {self.current_question_number} Results:**\n\n" + results

        for player_id, player_data in self.players.items():
            await player_data["dm_channel"].send(formatted_results)
            if not self.has_more_questions():
                await player_data["dm_channel"].send("🎉 **game over!** 🎉\n\nplease check the main channel to see the final results and winner!")

        self.question_active = False
        if not self.game_started:
            return

        await asyncio.sleep(5)
        if not self.game_started:
            return

        if self.has_more_questions():
            await self.show_next_question(channel)
        else:
            await self.end_game(channel)

    async def handle_timeout(self, channel):
        # handle when time runs out
        for player_id, player_data in self.players.items():
            if player_id not in self.answers:
                self.players[player_id]["score"] -= 2000
                await channel.send(f"⏰ {player_data['name']} didn't answer in time! -2000 points!")

        results = self.check_answers()
        formatted_results = f"**Question {self.current_question_number} Results:**\n\n" + results

        for player_id, player_data in self.players.items():
            await player_data["dm_channel"].send(formatted_results)
            if not self.has_more_questions():
                await player_data["dm_channel"].send("🎉 **game over!** 🎉\n\nplease check the main channel to see the final results and winner!")

        self.question_active = False
        if not self.game_started:
            return

        await asyncio.sleep(5)
        if not self.game_started:
            return

        if self.has_more_questions():
            await self.show_next_question(channel)
        else:
            await self.end_game(channel)

    async def show_next_question(self, channel):
        # show next question or end game
        if not self.has_more_questions():
            await self.end_game(channel)
            return

        self.question_active = True
        await self.start_question_timer(channel)

    async def end_game(self, channel):
        # end game and show final results
        if self.answer_timer and not self.answer_timer.done():
            self.answer_timer.cancel()
            self.answer_timer = None

        results_message = "🎉 **game over!** 🎉\n\n"
        results_message += "**final scores:**\n"

        sorted_players = sorted(
            self.players.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )

        for player_id, player_data in sorted_players:
            results_message += f"{player_data['name']}: {player_data['score']} points\n"

        results_message += f"\n**winner:** {self.get_winner()}"

        await channel.send(results_message)

        for player_id, player_data in self.players.items():
            if 'dm_channel' not in player_data:
                continue

            dm_message = "🎉 **game over!** 🎉\n\n"
            dm_message += "please check the main channel to see the final results and winner!"
            await player_data['dm_channel'].send(dm_message)

        self.reset_quiz()
        self.game_started = False
