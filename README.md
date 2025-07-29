# Discord Quiz Bot

A Discord bot that runs interactive quiz games with multiple choice and written questions. Players join the game and receive questions via DM, then submit their answers privately.

## Features

- **Multiple Choice Quiz**: Classic A/B/C/D format with automatic scoring
- **Written Question Quiz**: Open-ended questions with manual scoring
- **DM Integration**: Questions sent to players via private messages
- **Real-time Scoring**: Automatic score tracking and leaderboards
- **Timer System**: Configurable time limits for each question
- **Google Sheets Integration**: Questions loaded from Google Sheets
- **Easy Setup**: Simple commands to start and join games

## Commands

- `@bot start` - Start a new game (choose between 'mc' or 'wt')
- `join` - Join the current game
- `cancel` - Cancel the current game
- `@bot help` - Show help information

## Setup

### Prerequisites

- Python 3.8+
- Discord Bot Token
- Google Sheets API credentials (for question loading)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/discord-quiz-bot.git
cd discord-quiz-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Discord token:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

4. Set up Google Sheets API:
   - Create a Google Cloud project
   - Enable Google Sheets API
   - Create service account credentials
   - Share your question sheets with the service account email

5. Update the sheet URLs in `main.py`:
   - `MC_SHEET_URL`: URL for multiple choice questions
   - `WT_SHEET_URL`: URL for written questions

### Running the Bot

```bash
python main.py
```

## Game Types

### Multiple Choice (MC)
- Questions with A/B/C/D options
- Automatic scoring based on correct answers
- 10-second time limit per question

### Written Test (WT)
- Open-ended questions
- Manual scoring by the bot owner
- 30-second time limit per question

## File Structure

```
├── main.py              # Main bot file with Discord event handlers
├── buzzer_game.py       # Game logic for both quiz types
├── sheet_questions.py   # Google Sheets integration
├── responses.py         # Response templates and formatting
├── requirements.txt     # Python dependencies
├── discloud.config     # Discloud deployment configuration
└── README.md           # This file
```

## Configuration

### Google Sheets Format

**Multiple Choice Questions:**
- Column A: Question text
- Column B: Option A
- Column C: Option B
- Column D: Option C
- Column E: Option D
- Column F: Correct answer (a, b, c, or d)

**Written Questions:**
- Column A: Question text
- Column B: Expected answer (optional)

### Environment Variables

- `DISCORD_TOKEN`: Your Discord bot token

## Deployment

### Local Development
```bash
python main.py
```

### Discloud Deployment
The project includes Discloud configuration for easy deployment to Discloud hosting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub. 