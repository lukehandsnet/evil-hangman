#!/usr/bin/env python3
"""
Evil Hangman Game (Command Line Version)

This game cheats by dynamically changing the target word based on the player's guesses.
Instead of selecting a word at the beginning, it maintains a list of possible words and
narrows down the list after each guess to maximize the difficulty for the player.
"""

import random
import collections
import os
import sys

class EvilHangman:
    def __init__(self, dictionary_file='engmix.txt'):
        """Initialize the Evil Hangman game with a dictionary file."""
        self.all_words = self._load_dictionary(dictionary_file)
        self.word_length = 0
        self.max_guesses = 0
        self.guesses_left = 0
        self.guessed_letters = set()
        self.current_pattern = []
        self.possible_words = []
        self.game_over = False
        self.won = False

    def _load_dictionary(self, dictionary_file):
        """Load words from the dictionary file."""
        words = {}
        # Try different encodings
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
        """Return a list of available word lengths."""
        return sorted([length for length, words in self.all_words.items() 
                      if length >= 3 and len(words) > 10])

    def start_game(self, word_length, max_guesses):
        """Start a new game with the specified word length and maximum guesses."""
        if word_length not in self.all_words or len(self.all_words[word_length]) < 2:
            return False
        
        self.word_length = word_length
        self.max_guesses = max_guesses
        self.guesses_left = max_guesses
        self.guessed_letters = set()
        self.current_pattern = ['_'] * word_length
        self.possible_words = self.all_words[word_length].copy()
        self.game_over = False
        self.won = False
        return True

    def _get_word_patterns(self, guess):
        """Group words by their pattern based on the current guess."""
        patterns = collections.defaultdict(list)
        
        for word in self.possible_words:
            # Create a pattern based on where the guessed letter appears
            pattern = self.current_pattern.copy()
            for i, letter in enumerate(word):
                if letter == guess:
                    pattern[i] = guess
            
            # Convert pattern list to tuple for dictionary key
            pattern_key = tuple(pattern)
            patterns[pattern_key].append(word)
            
        return patterns

    def make_guess(self, guess):
        """Process a player's guess and update the game state."""
        guess = guess.lower()
        
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
        best_pattern = max(patterns.items(), key=lambda x: len(x[1]))
        best_pattern_key, best_words = best_pattern
        
        # Update the current pattern and possible words
        old_pattern = ''.join(self.current_pattern)
        self.current_pattern = list(best_pattern_key)
        new_pattern = ''.join(self.current_pattern)
        self.possible_words = best_words
        
        # Check if the guess was "correct" (from the player's perspective)
        if old_pattern == new_pattern:
            self.guesses_left -= 1
            print(f"Sorry, '{guess}' is not in the word. {self.guesses_left} guesses left.")
        else:
            print(f"Good guess! '{guess}' is in the word.")
        
        # Check if the game is over
        if '_' not in self.current_pattern:
            self.game_over = True
            self.won = True
            print(f"Congratulations! You won! The word was: {''.join(self.current_pattern)}")
        elif self.guesses_left <= 0:
            self.game_over = True
            # Choose a random word from the remaining possible words
            final_word = random.choice(self.possible_words)
            print(f"Game over! You ran out of guesses. The word was: {final_word}")
            
        return True
    
    def display_game_state(self):
        """Display the current game state."""
        print("\n" + "=" * 40)
        print(f"Word: {' '.join(self.current_pattern)}")
        print(f"Guesses left: {self.guesses_left}")
        print(f"Guessed letters: {', '.join(sorted(self.guessed_letters))}")
        print(f"Remaining possible words: {len(self.possible_words)}")
        print("=" * 40 + "\n")

def main():
    """Main function to run the game."""
    game = EvilHangman()
    
    # Get available word lengths
    available_lengths = game.get_available_lengths()
    
    print("Welcome to Evil Hangman!")
    print("This game cheats by changing the target word based on your guesses.")
    print("Available word lengths:", available_lengths)
    
    # Get word length from user
    while True:
        try:
            word_length = int(input("Enter word length: "))
            if word_length in available_lengths:
                break
            else:
                print(f"Please enter a valid word length from {available_lengths}")
        except ValueError:
            print("Please enter a valid number")
    
    # Get max guesses from user
    while True:
        try:
            max_guesses = int(input("Enter maximum number of guesses (6-12): "))
            if 6 <= max_guesses <= 12:
                break
            else:
                print("Please enter a number between 6 and 12")
        except ValueError:
            print("Please enter a valid number")
    
    # Start the game
    if not game.start_game(word_length, max_guesses):
        print("Failed to start game. Please try again.")
        return
    
    print(f"\nGame started with {word_length}-letter word. You have {max_guesses} guesses.")
    
    # Main game loop
    while not game.game_over:
        game.display_game_state()
        
        # Get guess from user
        while True:
            guess = input("Enter your guess (a single letter): ").strip().lower()
            if len(guess) == 1 and guess.isalpha():
                break
            else:
                print("Please enter a single letter")
        
        game.make_guess(guess)
    
    # Final game state
    game.display_game_state()
    
    # Ask to play again
    play_again = input("Would you like to play again? (y/n): ").strip().lower()
    if play_again == 'y':
        main()
    else:
        print("Thanks for playing Evil Hangman!")

if __name__ == "__main__":
    main()