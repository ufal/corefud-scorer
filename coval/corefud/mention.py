import sys
from collections import defaultdict

class MentionDict:
    def __init__(self, d):
        self.dict = d
        self.word2mention = defaultdict(list)
        for m in d:
            if not isinstance(m, Mention):
                raise TypeError("An instance of MentionDict must be initialized by a dictionary indexed by {:s} classes, got {:s}.".format(
                        Mention.__name__,
                        str(type(m))))
            for w in m.words:
                self.word2mention[w].append(m)

    def _fuzzy_find(self, m1):
        for w in m1.words:
            if w in self.word2mention:
                for m2 in self.word2mention[w]:
                    if m1 == m2:
                        return m2
        return None

    def __contains__(self, m1):
        if isinstance(m1, Mention):
            m2 = self._fuzzy_find(m1)
            return m2 is not None
        return NotImplemented

    def __getitem__(self, m1):
        if isinstance(m1, Mention):
            m2 = self._fuzzy_find(m1)
            if m2 is not None:
                return self.dict[m2]
            else:
                raise KeyError(m2)
        return NotImplemented

class Mention:
    
    class WordOrd:
        def __init__(self, node):
            self._sentord = node.root.bundle.number
            self._wordord = node.ord

        def __lt__(self, other):
            if isinstance(other, self.__class__):
                if self._sentord == other._sentord:
                    return self._wordord < other._wordord
                else:
                    return self._sentord < other._sentord
            return NotImplemented
        
        def __eq__(self, other):
            if isinstance(other, self.__class__):
                if self._sentord == other._sentord \
                    and self._wordord == other._wordord:
                    return True
                else:
                    return False
            return NotImplemented

        def __ne__(self, other):
            return not self.__eq__(other)

        def __le__(self, other):
            return self.__lt__(other) or self.__eq__(other)

        def __str__(self):
            return "{:d}-{:d}".format(self._sentord, self._wordord)

        def __repr__(self):
            return str(self)

        def __hash__(self):
            return hash((self._sentord, self._wordord))
            
    def __init__(self, nodes, head=None):
        self.words = [Mention.WordOrd(n) for n in nodes]
        self.wordsset = set(self.words)
        if head:
            self.head = Mention.WordOrd(head)
        else:
            self.head = None

    def _exact_match(self, other):
        if len(self.words) != len(other.words):
            return False
        sorted_words_zip = zip(sorted(self.words), sorted(other.words))
        return all(self_w == other_w for self_w, other_w in sorted_words_zip)

    def _partial_subset_match(self, other):
        if self.head:
            return (other.wordsset.issubset(self.wordsset) \
                and self.head in other.wordsset)
        elif other.head:
            return (self.wordsset.issubset(other.wordsset) \
                and other.head in self.wordsset)
        else:
            return self._exact_match(other)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._partial_subset_match(other)
        return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self.words))

    def __str__(self):
        return "({:s})".format(",".join([str(w)+"*" if self.head and self.head == w else str(w) for w in self.words]))

    def __repr__(self):
        return str(self)

###### UNUSED MENTION MATCHING STRATEGIES #######

    def _left_right_match(self, other):
        if self.words[0] == other.words[0] \
            and self.words[-1] == other.words[-1]:
            return True
        return False

    def _partial_left_right_match(self, other):
        if self.head:
            return (other.words[0] >= self.words[0] \
                and other.words[0] <= self.head \
                and other.words[-1] <= self.words[-1] \
                and other.words[-1] >= self.head)
        elif other.head:
            return (self.words[0] >= other.words[0] \
                and self.words[0] <= other.head \
                and self.words[-1] <= other.words[-1] \
                and self.words[-1] >= other.head)
        else:
            return self._left_right_match(other)
