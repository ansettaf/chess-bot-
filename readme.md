# Chess.com Training Bot

A comprehensive **Chess.com training and analysis bot** powered by [Stockfish](https://stockfishchess.org/).  
This bot is designed for **training purposes and analysis games only**, **NOT for live competitive play**.  

---

## Features

- Automatically plays **analysis/training games** on Chess.com.
- Uses the **Stockfish engine** to calculate optimal moves.
- Supports multiple move execution strategies:
  - Drag-and-drop on the board.
  - JavaScript injection.
  - Keyboard input simulation.
- Logs moves in **JSON format** for review.
- Handles popups, cookie banners, and Chess.com UI changes.
- Supports **headless mode** for background operation.

---

## Requirements

- Python 3.10+
- Chrome browser installed
- Stockfish chess engine
- Python packages:

```bash
pip install selenium python-chess stockfish webdriver-manager
```

---

## Installation

1. **Clone this repository:**

```bash
git clone https://github.com/ansettaf/chess-bot-.git
cd chess-bot-
```

2. **Download Stockfish:**  
Get the appropriate version for your system from [Stockfish Downloads](https://stockfishchess.org/download/).

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Update configuration in `my_bot.py`:**

```python
STOCKFISH_PATH = "/path/to/stockfish"
CHESS_COM_USERNAME = "your_username"
CHESS_COM_PASSWORD = "your_password"
HEADLESS_MODE = False
LOG_MOVES = True
MAX_MOVES = 100
CONTINUOUS_PLAY = False
```

---

## Usage

Run the bot with:

```bash
python my_bot.py
```

- Plays a single game by default.
- Optional continuous play mode (`CONTINUOUS_PLAY = True`) for multiple games.
- Moves are logged in files like `chess_moves_YYYYMMDD_HHMMSS.json`.

---

## Notes

- **Do not use this bot for live competitive games**; it violates Chess.com’s terms of service.
- Designed strictly for training and analysis.
- Headless mode allows running the bot without opening a browser window.
- Popups and UI changes on Chess.com may require updating selectors in the bot.

---

## Troubleshooting

- If Stockfish is not found:

```
Error: Stockfish not found at /path/to/stockfish
```

  - Make sure the path is correct and executable.
  - Ensure Chrome is installed and up to date.
  - Update Selenium WebDriver if needed:

```bash
pip install --upgrade webdriver-manager
```

---

## License

MIT License – see LICENSE for details.