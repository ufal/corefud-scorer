import sys
from collections import defaultdict

class MentionDict:
    """Dictionary indexed by `Mention` objects that, unlike a standard dictionary, allows for retrieving values that are indexed
    by the key mentions which match the query mention only fuzzilly.

    For calculating coreference evaluation scores, key clusters must be searched if they contain a sys mention (or vice versa).
    For efficiency reasons, the key clusters to be searched were implemented as dictionaries of cluster IDs indexed by mentions.
    The search in `coval/eval/evaluation.py` is then performed by `if sys_mention in key_mention2clusterid`, running the dict's
    `__contains__` operator. Default behaviour of the operator is that if first calculates a hash of the query and fails if no
    key in the dictionary has the same hash.

    Nevertheless, this is unwanted behaviour if the dictionary is required to support fuzzy matching of its keys with the query.
    A naive, yet inefficient solution, would be to implement `key_mention2clusterid` as a list of key-value pairs, performing
    the fuzzy match in O(n) time.

    `MentionDict` class takes advantage of the fact that the fuzzy matching between two mentions is based on set-subset relations.
    Internally, all mentions used as keys in `MentionDict` are stored in the `_word2mention` dict of lists indexed by words that
    mentions consist of. For a given query mention `qm`, search in the MentionDict `D` then proceeds in two steps:
        1. fuzzy search of `qm` among the keys in `D`, getting no result or a key mention `km`
            - go through all words `qw` in `qm` and using the `D._word2mention` indexed by words find the best matching mention
              `km` that contains `qw` and fuzzily matches `qm`
        2. retrieving the cluster ID value associated with `km`
            - having obtained `km`, we can use exact matching of a standard dictionary to retrieve the value
    """
    def __init__(self, d):
        self._dict = d
        self._word2mention = defaultdict(list)
        for m in d:
            if not isinstance(m, Mention):
                raise TypeError("An instance of MentionDict must be initialized by a dictionary indexed by {:s} classes, got {:s}.".format(
                        Mention.__name__,
                        str(type(m))))
            for w in m._words:
                self._word2mention[w].append(m)

    def _fuzzy_find(self, qm):
        """Given a query mention `qm`, retrieve a mention out of the key mentions `km` that fuzzilly matches best `qm`.
        Candidate key mentions are collected by taking all key mentions that contain any word from `qm`.
        The candidate key mentions `km`s are subsequently filtered using the following criteria:
        1. `km` must be (fuzzilly) equal to `qm`
        2. if more than a single `km` is equal, return the one that overlaps with the query with proportionally smallest difference
        3. if still more than one `km` remain, return the one that starts earlier in the document
        4. if still more than one `km` remain, return the one that ends earlier in the document
        There should not be more than one matching key after the last criterion.
        """
        # collect candidate mentions as a set of all key mentions that contain any word from the query mention
        candidate_mentions = set()
        for qw in qm._words:
            if qw in self._word2mention:
                for km in self._word2mention[qw]:
                    candidate_mentions.add(km)

        # the retrieved key mention must be equal to the one in the query
        equal_mentions = [km for km in candidate_mentions if qm == km]
        if not equal_mentions:
            return None
        if len(equal_mentions) == 1:
            return equal_mentions[0]
        # if more than one is equal, retrieve the one that overlaps with the query with proportionally smallest difference
        equal_mentions_diff = [len(qm.symmetric_difference(km)) / len(qm.union(km)) for km in equal_mentions]
        min_diff = min(equal_mentions_diff)
        min_diff_mentions = [km for i, km in enumerate(equal_mentions) if equal_mentions_diff[i] == min_diff]
        if len(min_diff_mentions) == 1:
            return min_diff_mentions[0]
        # if still more than one mention fit, retrieve the one that starts earlier
        min_diff_mentions.sort(key=lambda km: km.words[0])
        starts_first_mentions = [km for km in min_diff_mentions if km.words[0] == min_diff_mentions[0].words[0]]
        if len(starts_first_mentions) == 1:
            return starts_first_mentions[0]
        # if still more than one mention fit, retrieve the one that ends earlier
        starts_first_mentions.sort(key=lambda km: km.words[-1])
        ends_first_mentions = [km for km in starts_first_mentions if km.words[-1] == starts_first_mentions[0].words[-1]]
        return ends_first_mentions[0]

    def __contains__(self, m1):
        if isinstance(m1, Mention):
            m2 = self._fuzzy_find(m1)
            return m2 is not None
        return NotImplemented

    def __getitem__(self, m1):
        if isinstance(m1, Mention):
            m2 = self._fuzzy_find(m1)
            if m2 is not None:
                return self._dict[m2]
            else:
                raise KeyError(m2)
        return NotImplemented

class Mention:
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
            
    def __init__(self, nodes, head=None):
        self._words = [Mention.WordOrd(n) for n in nodes]
        self._words.sort()
        self._wordsset = set(self._words)
        if head:
            self._head = Mention.WordOrd(head)
        else:
            self._head = None

    @property
    def words(self):
        return self._words

    def _exact_match(self, other):
        """Mentions `self` and `other` are matched exactly, if all words the mentions are
        formed by are identical.
        """
        if len(self._words) != len(other._words):
            return False
        words_zip = zip(self._words, other._words)
        return all(self_w == other_w for self_w, other_w in words_zip)

    def _partial_subset_match(self, other):
        """Mentions `self` and `other` can be matched partially/fuzzilly only if a head
        is defined for at least one of the mentions. The other mention is then expected
        not to have a head specified. In that case, the two mentions are matched if the
        mention without a head is a subset of the mention with the head and the word
        that corresponds to the head belongs to this subset. If none of the mentions
        has a head specified, resort to exact matching.
        """
        if self._head:
            return (other._wordsset.issubset(self._wordsset) \
                and self._head in other._wordsset)
        elif other._head:
            return (self._wordsset.issubset(other._wordsset) \
                and other._head in self._wordsset)
        else:
            return self._exact_match(other)

    def __eq__(self, other):
        """Two mentions are equal if they match partially/fuzzilly.
        If none of them has a head specified, use exact matching.
        """
        if isinstance(other, self.__class__):
            return self._partial_subset_match(other)
        return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self._words))

    def __str__(self):
        return "({:s})".format(",".join([str(w)+"*" if self._head and self._head == w else str(w) for w in self._words]))

    def __repr__(self):
        return str(self)

    def symmetric_difference(self, other):
        """Symmetric difference between two mentions is a symmetric difference between
        sets of the words they are formed by. This is required to find the best out of
        multiple matching mentions.
        """
        if isinstance(other, self.__class__):
            return self._wordsset.symmetric_difference(other._wordsset)
        return NotImplemented

    def union(self, other):
        """Union of two mentions is a union of the sets of words they are formed by.
        This is required to find the best out of multiple matching mentions.
        """
        if isinstance(other, self.__class__):
            return self._wordsset.union(other._wordsset)
        return NotImplemented

###### UNUSED MENTION MATCHING STRATEGIES #######

    def _left_right_match(self, other):
        if self._words[0] == other._words[0] \
            and self._words[-1] == other._words[-1]:
            return True
        return False

    def _partial_left_right_match(self, other):
        if self._head:
            return (other._words[0] >= self._words[0] \
                and other._words[0] <= self._head \
                and other._words[-1] <= self._words[-1] \
                and other._words[-1] >= self._head)
        elif other._head:
            return (self._words[0] >= other._words[0] \
                and self._words[0] <= other._head \
                and self._words[-1] <= other._words[-1] \
                and self._words[-1] >= other._head)
        else:
            return self._left_right_match(other)
