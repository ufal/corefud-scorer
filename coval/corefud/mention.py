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

        def __hash__(self):
            return hash((self._sentord, self._wordord))
            
    def __init__(self, nodes, head=None):
        self.words = [Mention.WordOrd(n) for n in nodes]
        if head:
            self.head = Mention.WordOrd(head)

    def _exact_match(self, other):
        if len(self.words) != len(other.words):
            return False
        sorted_words_zip = zip(sorted(self.words), sorted(other.words))
        return all(self_w == other_w for self_w, other_w in sorted_words_zip)

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
        

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._partial_left_right_match(other)
        return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self.words))

    def __str__(self):
        return "({:s})".format(",".join(self.words))
