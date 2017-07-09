import itertools
import re
import string

OSX_EPOCH = 978307200

# List of symbols we don't want to check
SYMBOLS = " ".join(string.punctuation).split(" ") + ["-----", "---", "...", """, """, "'ve"]

GREETINGS_KEYS = ("hello", "hi", "greetings", "sup", "what's up")
greetings_response = itertools.cycle(
    ["Hi, nice to meet you. What is your name?",
     "Hey! Would you mind telling me your name?",
     "Hi, who is this?",
     "Hello, may I have your name before we proceed?"])



def tokens(sentence):
    # removes punctuation
    return [w if w not in SYMBOLS else '' for w in re.split('\W+', sentence)]


def cleaned(resp):
    # make unicode for spaCy
    return u"{0}".format(resp)

