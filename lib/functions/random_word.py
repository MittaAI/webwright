import random


def random_word(sentence: str) -> dict:
    """
    Outputs a random word from a given sentence.

    :param sentence: The sentence from which to pick a random word.
    :type sentence: str
    :return: A dictionary containing the random word.
    :rtype: dict
    """
    words = sentence.split()
    if not words:
        return {'success': False, 'error': 'The sentence is empty'}
    random_word = random.choice(words)
    return {'success': True, 'random_word': random_word}
