#!/usr/bin/python3
"""
learning Network
"""
import json
# own modules
from Categorizer import Categorizer as Categorizer


class Network(object):
    """
    build Network of Categorizers
    """

    def __init__(self):
        self.categorizers = {}

    def read(self, category, tokens):
        """
        set initial categories
        first time reading
        """
        if category not in self.categorizers:
            self.categorizers[category] = Categorizer(category)
        self.categorizers[category].add_tokens(tokens)

    def train(self, category, tokens):
        """
        train network with data, should be good data
        category is given
        """
        self.categorizers[category].train(category, tokens)

    def predict(self, tokens):
        """
        return possible category for given tokens
        """
        results = {}
        for category in self.categorizers:
            results[self.categorizers[category].predict(tokens)] = category
        max_result = max(results.keys())
        return max_result, results[max_result]

    def tokens(self, category):
        """
        return tokens used for given category
        for analyzing purposes
        """
        return self.categorizers[category].tokens()

    def stats(self, category):
        """
        retunr some stats of given category
        """
        return self.categorizers[category].stats()

    def remember(self):
        """
        call this after training
        """
        print("remember called")
        for category, data in sorted(self.categorizers.items()):
            print(category, data.learned)
            if data.learned < 10:
                del self.categorizers[category]
            else:
                data.remember()

    def to_json(self):
        """
        return state of network as json formatted data
        dump network states to json format
        """
        data = {}
        for categorizer in self.categorizers.values():
            data[categorizer.category] = categorizer.to_data()
        return json.dumps(data, indent=4, sort_keys=True)

    @classmethod
    def from_json(cls, data):
        """
        recreate network from given filedescriptor
        data must be json format
        """
        data = json.loads(data)
        self = cls.__new__(cls)
        self.categorizers = {}
        for key, value in data.items():
            self.categorizers[key] = Categorizer.from_data(value)
        return self
