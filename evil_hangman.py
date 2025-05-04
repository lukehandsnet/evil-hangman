#!/usr/bin/env python3
"""
Evil Hangman Game (Web Version)

This game cheats by dynamically changing the target word based on the player's guesses.
Instead of selecting a word at the beginning, it maintains a list of possible words and
narrows down the list after each guess to maximize the difficulty for the player.

The game uses a Flask web server to provide a browser-based interface for playing
the game, with API endpoints for getting available word lengths, starting a game,
making guesses, and retrieving the current game state.
"""

import random  # Used for selecting a random word when player loses
import collections  # Used for defaultdict to group words by pattern
import os  # Used to ensure templates directory exists
from flask import Flask, render_template, request, jsonify  # Web framework

class EvilHangman:
    """The main game engine class for Evil Hangman.
    
    This class handles the game logic, including word selection, 
    pattern matching, and game state management.
    """
    
    def __init__(self, dictionary_file='engmix.txt'):
        """Initialize the Evil Hangman game with a dictionary file.
        
        Args:
            dictionary_file (str): Path to the dictionary file containing words.
                                  Default is 'engmix.txt'.
        """
        self.all_words = self._load_dictionary(dictionary_file)  # Dictionary of all words by length
        self.word_length = 0  # Length of the current word
        self.max_guesses = 0  # Maximum number of incorrect guesses allowed
        self.guesses_left = 0  # Number of incorrect guesses remaining
        self.guessed_letters = set()  # Set of letters already guessed
        self.current_pattern = []  # Current word pattern with revealed letters
        self.possible_words = []  # List of words that still match the current pattern
        self.game_over = False  # Flag indicating if the game is over
        self.won = False  # Flag indicating if the player won
        self.message = ""  # Message to display to the player

    def _load_dictionary(self, dictionary_file):
        """Load words from the dictionary file.
        
        This method attempts to open the dictionary file with various encodings
        to ensure compatibility across different systems. Words are organized
        by length for efficient lookup later.
        
        Args:
            dictionary_file (str): Path to the dictionary file.
            
        Returns:
            dict: A dictionary mapping word lengths to lists of words of that length.
            
        Raises:
            ValueError: If the dictionary file cannot be loaded with any encoding.
        """
        words = {}  # Dictionary to store words organized by length
        # Try different encodings to handle various file encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(dictionary_file, 'r', encoding=encoding) as f:
                    for line in f:
                        word = line.strip().lower()
                        # Only include words with alphabetic characters
                        if word and all(c.isalpha() for c in word):
                            length = len(word)
                            if length not in words:
                                words[length] = []
                            words[length].append(word)
                # If we get here, the file was read successfully
                print(f"Successfully loaded dictionary with {encoding} encoding")
                break
            except UnicodeDecodeError:
                print(f"Failed to load with {encoding} encoding, trying next...")
                continue
        
        if not words:
            raise ValueError("Could not load dictionary with any encoding")
            
        return words

    def get_available_lengths(self):
        """Return a list of available word lengths.
        
        This method filters the dictionary to only include word lengths
        that have enough words (more than 10) and are reasonably long (at least 3 letters).
        
        Returns:
            list: A sorted list of available word lengths.
        """
        return sorted([length for length, words in self.all_words.items() 
                      if length >= 3 and len(words) > 10])

    def start_game(self, word_length, max_guesses):
        """Start a new game with the specified word length and maximum guesses.
        
        Initializes a new game with the given parameters, setting up the initial
        game state with all words of the requested length as possible target words.
        
        Args:
            word_length (int): The length of the word to guess.
            max_guesses (int): The maximum number of incorrect guesses allowed.
            
        Returns:
            bool: True if the game was successfully started, False otherwise.
        """
        # Verify that there are enough words of the requested length
        if word_length not in self.all_words or len(self.all_words[word_length]) < 2:
            return False
        
        # Initialize game state
        self.word_length = word_length
        self.max_guesses = max_guesses
        self.guesses_left = max_guesses
        self.guessed_letters = set()
        self.current_pattern = ['_'] * word_length  # Initialize with all blanks
        self.possible_words = self.all_words[word_length].copy()  # All words of this length
        self.game_over = False
        self.won = False
        self.message = f"Game started with {word_length}-letter word. You have {max_guesses} guesses."
        return True

    def _get_word_patterns(self, guess):
        """Group words by their pattern based on the current guess.
        
        This is the core "evil" function that groups all possible words based on
        where the guessed letter would appear. For example, if the current pattern
        is "_ _ _ _" and the guess is "e", words might be grouped as:
        - "_ _ _ _" (no e's): [word1, word2, ...]
        - "_ e _ _" (e in position 2): [word3, word4, ...]
        - "_ _ e _" (e in position 3): [word5, word6, ...]
        - etc.
        
        Args:
            guess (str): The letter that was guessed.
            
        Returns:
            dict: A dictionary mapping patterns (as tuples) to lists of words matching those patterns.
        """
        patterns = collections.defaultdict(list)
        
        for word in self.possible_words:
            # Create a pattern based on where the guessed letter appears
            pattern = self.current_pattern.copy()
            for i, letter in enumerate(word):
                if letter == guess:
                    pattern[i] = guess
            
            # Convert pattern list to tuple for dictionary key
            # (lists can't be dictionary keys because they're mutable)
            pattern_key = tuple(pattern)
            patterns[pattern_key].append(word)
            
        return patterns

    def make_guess(self, guess):
        """Process a player's guess and update the game state.
        
        This method is where the "evil" behavior happens. After a player guesses a letter,
        the method:
        1. Groups all possible words by their pattern (where the guessed letter appears)
        2. Selects the largest group of words (making it most likely the guess is wrong)
        3. Updates the game state with the new pattern and possible words
        4. Checks if the game is over (win or loss)
        
        Args:
            guess (str): The letter that was guessed.
            
        Returns:
            bool: True if the guess was processed successfully, False otherwise.
        """
        guess = guess.lower()  # Convert to lowercase for consistency
        
        # Check if the game is already over
        if self.game_over:
            self.message = "Game is already over. Start a new game."
            return False
            
        # Check if the letter has already been guessed
        if guess in self.guessed_letters:
            self.message = f"You already guessed '{guess}'. Try another letter."
            return False
            
        # Add the letter to guessed letters
        self.guessed_letters.add(guess)
        
        # Get word patterns based on the guess
        patterns = self._get_word_patterns(guess)
        
        # Find the pattern with the most words (the most evil choice)
        # This maximizes the number of words still in play
        best_pattern = max(patterns.items(), key=lambda x: len(x[1]))
        best_pattern_key, best_words = best_pattern
        
        # Update the current pattern and possible words
        old_pattern = ''.join(self.current_pattern)
        self.current_pattern = list(best_pattern_key)
        new_pattern = ''.join(self.current_pattern)
        self.possible_words = best_words
        
        # Check if the guess was "correct" (from the player's perspective)
        # If the pattern didn't change, the guess was "wrong"
        if old_pattern == new_pattern:
            self.guesses_left -= 1
            self.message = f"Sorry, '{guess}' is not in the word. {self.guesses_left} guesses left."
        else:
            self.message = f"Good guess! '{guess}' is in the word."
        
        # Check if the game is over
        if '_' not in self.current_pattern:  # No more blanks means player won
            self.game_over = True
            self.won = True
            self.message = f"Congratulations! You won! The word was: {''.join(self.current_pattern)}"
        elif self.guesses_left <= 0:  # No more guesses means player lost
            self.game_over = True
            # Choose a random word from the remaining possible words
            final_word = random.choice(self.possible_words)
            self.message = f"Game over! You ran out of guesses. The word was: {final_word}"
            
        return True
    
    def get_game_state(self):
        """Return the current game state as a dictionary.
        
        This method packages up all relevant game state information for use by
        the web API, including the current word pattern, guessed letters,
        number of guesses left, and game status.
        
        Returns:
            dict: A dictionary containing the current game state.
        """
        return {
            'word_length': self.word_length,  # Length of the word
            'max_guesses': self.max_guesses,  # Maximum allowed guesses
            'guesses_left': self.guesses_left,  # Remaining guesses
            'guessed_letters': sorted(list(self.guessed_letters)),  # Letters already guessed
            'current_pattern': ''.join(self.current_pattern),  # Current word pattern
            'game_over': self.game_over,  # Whether the game is over
            'won': self.won,  # Whether the player won
            'message': self.message,  # Message to display to the player
            'remaining_words': len(self.possible_words)  # Number of words still possible
        }

# Create Flask app and initialize game instance
app = Flask(__name__)  # Initialize Flask application
game = EvilHangman()   # Create a single game instance for the web application

@app.route('/')
def index():
    """Render the main game page.
    
    This route serves the HTML template for the game interface.
    """
    return render_template('index.html')

@app.route('/api/lengths', methods=['GET'])
def get_lengths():
    """Return available word lengths.
    
    This API endpoint returns a list of valid word lengths that can be
    used to start a new game.
    
    Returns:
        JSON response containing an array of valid word lengths.
    """
    return jsonify(game.get_available_lengths())

@app.route('/api/start', methods=['POST'])
def start_game():
    """Start a new game.
    
    This API endpoint starts a new game with the specified word length
    and maximum number of guesses.
    
    Expected JSON payload:
        {
            "word_length": integer,
            "max_guesses": integer
        }
    
    Returns:
        JSON response containing the initial game state or an error message.
    """
    data = request.json
    word_length = int(data.get('word_length', 5))  # Default to 5 if not specified
    max_guesses = int(data.get('max_guesses', 8))  # Default to 8 if not specified
    
    success = game.start_game(word_length, max_guesses)
    if success:
        return jsonify(game.get_game_state())
    else:
        return jsonify({'error': 'Invalid word length or max guesses'}), 400

@app.route('/api/guess', methods=['POST'])
def make_guess():
    """Process a player's guess.
    
    This API endpoint processes a player's guess and returns the updated game state.
    
    Expected JSON payload:
        {
            "guess": string (single letter)
        }
    
    Returns:
        JSON response containing the updated game state or an error message.
    """
    data = request.json
    guess = data.get('guess', '').lower()
    
    # Validate the guess
    if not guess or len(guess) != 1 or not guess.isalpha():
        return jsonify({'error': 'Invalid guess. Please enter a single letter.'}), 400
    
    game.make_guess(guess)
    return jsonify(game.get_game_state())

@app.route('/api/state', methods=['GET'])
def get_state():
    """Return the current game state.
    
    This API endpoint returns the current state of the game, including
    the word pattern, guessed letters, and remaining guesses.
    
    Returns:
        JSON response containing the current game state.
    """
    return jsonify(game.get_game_state())

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    # Run the Flask app on port 55186, accessible from any network interface
    app.run(host='0.0.0.0', port=55186, debug=True)