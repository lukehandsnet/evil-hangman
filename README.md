# Evil Hangman

A cheating version of the classic Hangman game that dynamically changes the target word based on the player's guesses to make the game as difficult as possible.

## How It Works

Unlike traditional Hangman where a word is chosen at the beginning, Evil Hangman maintains a list of possible words and narrows down the list after each guess to maximize the difficulty:

1. When the player guesses a letter, the game groups all possible words by their letter patterns
2. The game chooses the largest group (to maximize chances of avoiding the guessed letter)
3. This makes the game much more challenging as the target word is constantly changing

## Features

- Web-based interface with Flask
- Command-line interface for terminal play
- Customizable word length and maximum guesses
- Visual keyboard for letter selection
- Debug information showing the number of remaining possible words

## Running the Game

### Web Version

```bash
python evil_hangman.py
```

Then open your browser to http://localhost:55186

### Command Line Version

```bash
python evil_hangman_cli.py
```

## Requirements

- Python 3.6+
- Flask (for web version)

## Dictionary

The game uses the `engmix.txt` dictionary file, which contains over 84,000 English words.