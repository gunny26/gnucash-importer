#!/usr/bin/python3
import math

def activation_function_custom(value):
    """activation function"""
    return 1 / (1 + math.e ** (1 / value))

def activation_function_logistic(value):
    """activation function"""
    return 1 / (1 + math.e ** (-value))

class Categorizer(object):

    def __init__(self, category, level=0.8, activation_function=activation_function_logistic):
        """
        category will be the name of this categorizer
        level will be the level at which some token is valid

        category <str> some string to name this category
        threshhold <float> above this value, this will identify correct category
        activation_function <func> threshold function
        """
        self.__data = {} # token values
        self.__category = category # store
        self.__threshhold = level # store
        # indicate how much tokens this Categorizhow much tokens this
        # Categorizer has learned
        self.__learned = 0

    @property
    def learned(self):
        return self.__learned

    @property
    def category(self):
        return self.__category

    def to_data(self):
        """
        return internal state as dict
        """
        return self.__dict__

    @classmethod
    def from_data(cls, data):
        """
        recreate state from given data <dict>
        TODO: check values
        """
        self = cls.__new__(cls)
        self.__dict__ = data
        return self

    def add_tokens(self, tokens):
        """
        learn all possible tokens for this category from trusted source
        """
        for token in tokens:
            if token not in self.__data:
                self.__data[token] = 1
            else:
                self.__data[token] += 1

    def train(self, tokens, category):
        """
        train categorizer with set of tokens AND category

        this set of tokens is proven to belong to category
        this will adjust weight-values for tokens

        every category == self, will increase value of all tokens in it
        """
        result = self.predict(tokens)
        # positive marking, add +1 to every token
        if result < self.__threshhold and category == self.__category:
            # these set of tokens defines category
            for token in tokens:
                if token in self.__data:
                    self.__data[token] += 1
        if result > self.__threshhold and category != self.__category:
            # this set of tokens DOES NOT define category
            # any occurance will decrease propability
            for token in tokens:
                if token in self.__data:
                    self.__data[token] -= 1
        self.__learned += 1 # count up learned counter

    def remember(self):
        """
        calculate actual value, and discard tokens below some threshold
        tokens with value below some threshold will be removed
        """
        total = sum(self.__data.values())
        for token in list(self.__data.keys()):
            # thats the activation function
            # go to https://en.wikipedia.org/wiki/Activation_function
            # this one f(x) = 1 / (1+ e ^ -x)
            value = 1 / (1 + 2.71828 ** (1 / self.__data[token]))
            if value < 0.80:
                print("{} deleting token {} value is {}".format(self.__category, token, value))
                del self.__data[token]
            self.__data[token] = value

    def predict(self, tokens):
        """
        return numerical value for this set of tokens
        it is task of network to choose categorizer with highest value
        """
        result = 0.0
        token_found = False
        for token in tokens:
            if token in self.__data:
                result += self.__data[token]
                token_found = True
        if token_found is True:
            return 1 / (1 + 2.71828 ** (1 / result))
        else:
            return 0.0

    def stats(self):
        """
        return statistics
        """
        return self.__data

    def tokens(self):
        """
        return tokens
        """
        return self.__data.keys()
