import random

def random_word(sentence):
    words = sentence.split()
    return random.choice(words)

sentence = "this is a test of the random word function"
print(random_word(sentence))