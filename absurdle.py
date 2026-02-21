from colorama import Back
from random import choice
import sys
# For test purposes, do not change these imports.
# You can add more below this line if needed.
from collections import Counter

COLOR_MAP = {'G': Back.GREEN, 'Y': Back.YELLOW, 'W': Back.WHITE}


def show_result(result, guess):
    # Display the result using the colorama library
    for i in range(len(result)):
        print(COLOR_MAP[result[i]] + guess[i], end='')
    print(Back.RESET)


def load_five_letter_words(filename):
    with open(filename, 'r') as f:
        # Strip out spaces, convert words to uppercase, filter to only 5-letter words
        return [word.strip().upper() for word in f if len(word.strip().upper()) == 5]


def get_result(secret_word, guess):
    # Initially, label every letter W by default
    result = ['W'] * 5
    remaining_letters = Counter(secret_word)  # occurrences left to assign to G or Y

    for i in range(len(guess)):
        # Right position
        if guess[i] == secret_word[i]:
            result[i] = 'G'
            remaining_letters[guess[i]] -= 1

    # Wrong position but in word somewhere (left to right, cap by remaining_letters)
    for i in range(len(guess)):
        if result[i] != 'G' and remaining_letters.get(guess[i], 0) > 0:
            result[i] = 'Y'
            remaining_letters[guess[i]] -= 1

    return ''.join(result)


def is_valid_guess(guess):
    # The guess must be a valid 5-letter word
    correct_length = len(guess) == 5
    only_letters = guess.isalpha()

    return correct_length and only_letters

def is_in_wordlist(guess, five_letter_words):
    return guess in set(five_letter_words)

def get_guess(five_letter_words):
    guess = input('Enter a 5-letter guess: ').strip().upper()
    # Keep asking the user to try again until they enter a valid guess
    while not is_valid_guess(guess):
        guess = input('Guess must be a valid word consisting of 5 letters, try again: ').strip().upper()
    
    while not is_in_wordlist(guess, five_letter_words):
        guess = input('Guess must be a valid meaningful word within our list of possible words: ').strip().upper()
    return guess


def main():
    if len(sys.argv) != 2:
        print('Usage: python wordle.py <word_list_file>')
        return
    words_file = sys.argv[1]
    # Load a list of valid five letter words from a file
    five_letter_words = load_five_letter_words(words_file)
    # Randomly select a secret word from the list
    secret_word = choice(five_letter_words)
    result = 'WWWWW'
    # While the user hasn't won yet
    while result != 'GGGGG':
        # Ask the user to guess
        guess = get_guess(five_letter_words)
        # Determine what the result string should be, e.g. WYGGY
        result = get_result(secret_word, guess)
        # Display the guess using the colors from the result string
        show_result(result, guess)
    print('You win!')


if __name__ == '__main__':
    main()

