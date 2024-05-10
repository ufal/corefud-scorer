from scorer.base.mention import Mention


class CorefUDMention(Mention):
    """Representation of (potentially non-contiguous) mention for the evaluation script.
    It must allow mention matching in two documents that are aligned, yet likely marked with different coreference relations.
    A mention is thus defined only by position of the words (sentence ord and word ord) the mention is formed by.

    As mentions are allowed to be non-contiguous, matching of such mentions must be supported. Matching only the start and
    the end of the mentions is insufficient in this case. Matching in this class is therefore based on matching the sets
    of words that form the mentions.

    The class allows for both exact and partial matching. This is controlled by the head of the mention which can be specified
    as well. If head is defined for at least one of the mentions in comparison, the mentions can be matched by partial/fuzzy
    matching. If none of the two mentions have a head specified, the mentions are compared using the exact matching.
    """

    class WordOrd:
        """Representation of a mention word for evaluation purposes.
        A word is defined only by its position within the document, i.e. ordinal number of the word within a sentence and the
        sentence within the document. For this reason, comaprison operators are defined for the class.
        """

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
            return f"{self._sentord}-{self._wordord}"

        def __repr__(self):
            return str(self)

        def __hash__(self):
            return hash((self._sentord, self._wordord))

    def __init__(self, nodes, head, matching="head"):
        super().__init__(matching=matching)
        self._words = [CorefUDMention.WordOrd(n) for n in nodes]
        self._words.sort()
        self._wordsset = set(self._words)
        if head:
            self._minset.add(CorefUDMention.WordOrd(head))
            self._is_zero = head.is_empty()
            # head deps stored as a list of (parent WordOrd, deprel string) tuples
            # TODO: storing head deps separately from the minset is not ideal
            self._head_deps = [(CorefUDMention.WordOrd(dep["parent"]), dep["deprel"]) for dep in head.deps]
        else:
            self._is_zero = nodes[0].is_empty()
            self._head_deps = [(CorefUDMention.WordOrd(dep["parent"]), dep["deprel"]) for dep in nodes[0].deps]

    # head matching as defined in CRAC 2023 shared task
    # if there are multiple candidates sharing the same head
    # the overlap ratio (and the its position within the document)
    # is used to disambiguate
    # self = key mention, other = sys mention
    def head_match_score(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self.__eq__(other):
            return 1.0
        # the head is guaranteed to be a single one
        assert len(self._minset) == 1
        if self._minset == other._minset:
            return len(self._wordsset & other._wordsset) * 1.0 / len(self._wordsset)
        return 0.0
    
    def _f_score(self, set1, set2):
        common = set1 & set2
        p = len(common) / len(set1)
        r = len(common) / len(set2)
        if p > 0 and r > 0:
            return 2*p*r/(p+r)
        return 0

    def zero_dependent_match_score(self, other):
        self_head = list(self._minset).pop()
        other_head = list(other._minset).pop()
        if self_head._sentord != other_head._sentord:
            return 0.0
        score = 0.0
        # the f-score of predicting both parent and deprel of deps: weigh it by the factor 10
        self_deps = set(self._head_deps)
        other_deps = set(other._head_deps)
        score += 10 * self._f_score(self_deps, other_deps)
        # the f-score of predicting just the parent: weigh it by the factor 1
        self_deps = set([parent for parent, deprel in self._head_deps])
        other_deps = set([parent for parent, deprel in other._head_deps])
        score += self._f_score(self_deps, other_deps)
        return score
