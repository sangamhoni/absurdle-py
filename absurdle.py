import sys

# For test purposes, do not change these imports.
# You can add more below this line if needed.
from collections import Counter


def load_answer_set_words(filename):
    with open(filename, "r") as f:
        # Strip out spaces, convert words to uppercase, filter to only 5-letter words
        return {word.strip().upper() for word in f if len(word.strip().upper()) == 5}


def get_result(remaining_word, guess):
    # Initially, label every letter W by default
    result = ["W"] * 5
    remaining_letters = Counter(remaining_word)  # occurrences left to assign to G or Y

    for i in range(len(guess)):
        # Right position
        if guess[i] == remaining_word[i]:
            result[i] = "G"
            remaining_letters[guess[i]] -= 1

    # Wrong position but in word somewhere (left to right, cap by remaining_letters)
    for i in range(len(guess)):
        if result[i] != "G" and remaining_letters.get(guess[i], 0) > 0:
            result[i] = "Y"
            remaining_letters[guess[i]] -= 1

    return "".join(result)


def get_adversarial_result(guess, answer_set, remaining_words):
    result = ["W"] * 5
    remaining_letters = Counter(answer_set)
    result_bucket = {}

    for word in remaining_words:
        result = get_result(word, guess)

        if result in result_bucket:
            result_bucket[result].append(word)
        else:
            result_bucket[result] = [word]

    # Find the result (key) whose bucket has the most words
    best_result = None
    best_count = -1

    for pattern, word_list in result_bucket.items():
        count = len(word_list)
        if count > best_count:
            best_count = count
            best_result = pattern
        elif count == best_count and (
            best_result is None or pattern > best_result
        ):  # lexicographically biggest when same number of words
            best_result = pattern

    remaining_words = result_bucket[
        best_result
    ]  # update remaining words to the best result bucket
    return (best_result, remaining_words)


def is_valid_guess(guess):
    # The guess must be a valid 5-letter word
    correct_length = len(guess) == 5
    only_letters = guess.isalpha()

    return correct_length and only_letters


def is_in_wordlist(guess, answer_set_words):
    return guess in answer_set_words


def get_guess(answer_set_words):
    guess = input("Enter a 5-letter guess: ").strip().upper()
    # Keep asking the user to try again until they enter a valid guess
    while not is_valid_guess(guess):
        guess = (
            input("Guess must be a valid word consisting of 5 letters, try again: ")
            .strip()
            .upper()
        )

    while not is_in_wordlist(guess, answer_set_words):
        guess = (
            input(
                "Guess must be a valid meaningful word within our list of possible words: "
            )
            .strip()
            .upper()
        )
    return guess


def main():
    if len(sys.argv) != 2:
        print("Usage: python wordle.py <word_list_file>")
        return
    words_file = sys.argv[1]
    # Load a list of valid five letter words from a file
    answer_set_words = load_answer_set_words(words_file)
    remaining_words = list(answer_set_words.copy())
    result = "WWWWW"
    # While the user hasn't won yet
    while result != "GGGGG":
        # Ask the user to guess, making sure it's a valid 5-lettered guess and in the wordlist
        guess = get_guess(answer_set_words)

        # Determine what the result string should be following the adversarial logic, e.g. WYGGY
        result, remaining_words = get_adversarial_result(
            guess, answer_set_words, remaining_words
        )
        print(guess, result)

    print("You win!")


if __name__ == "__main__":
    main()
