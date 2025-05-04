#!/usr/bin/env python3
"""
Evil Hangman Game (Command Line Version)

This game cheats by dynamically changing the target word based on the player's guesses.
Instead of selecting a word at the beginning, it maintains a list of possible words and
narrows down the list after each guess to maximize the difficulty for the player.

This version provides a text-based command line interface for playing the game,
allowing users to select word length and maximum guesses, then make letter guesses
until they win or lose.
"""

import random       # Used for selecting a random word when player loses
import collections  # Used for defaultdict to group words by pattern
import os           # Used for file operations
import sys          # Used for program termination

class EvilHangman:
    """The main game engine class for Evil Hangman.
    
    This class handles the game logic, including word selection, 
    pattern matching, and game state management. Identical to the web version
    except for the output method (prints to console instead of returning messages).
    """
    
    def __init__(self, dictionary_file='engmix.txt'):
        """Initialize the Evil Hangman game with a dictionary file.
        
        Args:
            dictionary_file (str): Path to the dictionary file containing words.
                                  Default is 'engmix.txt'.
        """
        self.all_words = self._load_dictionary(dictionary_file)  # Dictionary of all words by length
        self.word_length = 0        # Length of the current word
        self.max_guesses = 0        # Maximum number of incorrect guesses allowed
        self.guesses_left = 0       # Number of incorrect guesses remaining
        self.guessed_letters = set() # Set of letters already guessed
        self.current_pattern = []   # Current word pattern with revealed letters
        self.possible_words = []    # List of words that still match the current pattern
        self.game_over = False      # Flag indicating if the game is over
        self.won = False            # Flag indicating if the player won

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
            print("Game is already over. Start a new game.")
            return False
            
        # Check if the letter has already been guessed
        if guess in self.guessed_letters:
            print(f"You already guessed '{guess}'. Try another letter.")
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
            print(f"Sorry, '{guess}' is not in the word. {self.guesses_left} guesses left.")
        else:
            print(f"Good guess! '{guess}' is in the word.")
        
        # Check if the game is over
        if '_' not in self.current_pattern:  # No more blanks means player won
            self.game_over = True
            self.won = True
            print(f"Congratulations! You won! The word was: {''.join(self.current_pattern)}")
        elif self.guesses_left <= 0:  # No more guesses means player lost
            self.game_over = True
            # Choose a random word from the remaining possible words
            final_word = random.choice(self.possible_words)
            print(f"Game over! You ran out of guesses. The word was: {final_word}")
            
        return True
    
    def display_game_state(self):
        """Display the current game state to the console.
        
        This method prints the current word pattern, remaining guesses,
        guessed letters, and the number of possible words remaining.
        It's used to provide feedback to the player after each guess.
        """
        print("\n" + "=" * 40)  # Print a separator line for readability
        print(f"Word: {' '.join(self.current_pattern)}")  # Show word with spaces between letters
        print(f"Guesses left: {self.guesses_left}")  # Show remaining guesses
        print(f"Guessed letters: {', '.join(sorted(self.guessed_letters))}")  # Show guessed letters
        print(f"Remaining possible words: {len(self.possible_words)}")  # Debug info about word count
        print("=" * 40 + "\n")  # Print a separator line for readability

def main():
    """Main function to run the game.
    
    This function handles the game flow for the command-line version:
    1. Setting up the game (word length, max guesses)
    2. Running the main game loop
    3. Processing user input
    4. Displaying game state after each guess
    5. Handling game completion and restart
    """
    game = EvilHangman()  # Create a new game instance
    
    # Get available word lengths from the dictionary
    available_lengths = game.get_available_lengths()
    
    # Display welcome message and game information
    print("Welcome to Evil Hangman!")
    print("This game cheats by changing the target word based on your guesses.")
    print("Available word lengths:", available_lengths)
    
    # Get word length from user with input validation
    while True:
        try:
            word_length = int(input("Enter word length: "))
            if word_length in available_lengths:
                break
            else:
                print(f"Please enter a valid word length from {available_lengths}")
        except ValueError:
            print("Please enter a valid number")
    
    # Get maximum guesses from user with input validation
    while True:
        try:
            max_guesses = int(input("Enter maximum number of guesses (6-12): "))
            if 6 <= max_guesses <= 12:
                break
            else:
                print("Please enter a number between 6 and 12")
        except ValueError:
            print("Please enter a valid number")
    
    # Start the game with selected parameters
    if not game.start_game(word_length, max_guesses):
        print("Failed to start game. Please try again.")
        return
    
    print(f"\nGame started with {word_length}-letter word. You have {max_guesses} guesses.")
    
    # Main game loop - continues until the game is over
    while not game.game_over:
        # Display current game state (word pattern, guesses left, etc.)
        game.display_game_state()
        
        # Get guess from user with input validation
        while True:
            guess = input("Enter your guess (a single letter): ").strip().lower()
            if len(guess) == 1 and guess.isalpha():
                break
            else:
                print("Please enter a single letter")
        
        # Process the guess and update game state
        game.make_guess(guess)
    
    # Display final game state after win/loss
    game.display_game_state()
    
    # Ask if player wants to play again
    play_again = input("Would you like to play again? (y/n): ").strip().lower()
    if play_again == 'y':
        main()  # Recursive call to start a new game
    else:
        print("Thanks for playing Evil Hangman!")

if __name__ == "__main__":
    # Execute main function only if script is run directly (not imported)
    main()