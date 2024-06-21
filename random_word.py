import random

sentence = "the quick brown fox jumped over the lazy dog"
words = sentence.split()
random_word = random.choice(words)
print(random_word)