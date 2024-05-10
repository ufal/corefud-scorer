class Mention:
    def __init__(self, matching="exact"):
        # here we only include the properties might be used outside the mention class,
        # and assign a default value to make sure no error even if fuction not used by
        # specific format
        self._words = []  # store all word indies
        self._wordsset = set()
        self._minset = set()
        self._is_referring = True  # for non-referring
        self._is_split_antecedent = False  # for split-antecedent
        self._split_antecedent_sets = set()  # for split-antecedent
        self._is_zero = False
        # in case of the "head" matching, the two mentions are considered to be the same
        # only if their spans as well as their min sets are the same
        if matching == "head":
            self._eq_match = self._super_exact_match
            self._hash_match = self._super_exact_match_hash
        # for the remaining matching types, it is sufficient for the spans to be tha same
        else:
            self._eq_match = self._exact_match
            self._hash_match = self._exact_match_hash

    ############## Properties ###############

    @property
    def words(self):
        return self._words

    @property
    def start(self):
        return self._words[0]

    @property
    def end(self):
        return self._words[-1]

    @property
    def is_zero(self):
        return self._is_zero

    @property
    def is_referring(self):
        return self._is_referring

    @property
    def is_split_antecedent(self):
        return self._is_split_antecedent

    @property
    def split_antecedent_sets(self):
        return self._split_antecedent_sets

    ############## Operators ###############

    def __getitem__(self, i):
        return self._words[i]

    def __len__(self):
        return len(self._words)

    def __eq__(self, other):
        return self._eq_match(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            if self._words[0] == other._words[0]:
                if self._words[-1] == other._words[-1]:
                    return len(self._words) < len(other._words)
                else:
                    return self._words[-1] < other._words[-1]
            else:
                return self._words[0] < other._words[0]
        return NotImplemented

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __hash__(self):
        if self.is_split_antecedent:
            return hash(frozenset(self.split_antecedent_sets))
        return self._hash_match()

    def __str__(self):
        if self.is_split_antecedent:
            return "({:s})".format(",".join([str(cl[0]) for cl in self.split_antecedent_sets]))
        return "({:s})".format(
            ",".join([str(w) + "*" if self._minset and w in self._minset else str(w) for w in self._words]))

    def __repr__(self):
        return str(self)

    def intersection(self, other):
        if isinstance(other, self.__class__):
            if self._words[0] > other._words[-1] or \
                other._words[0] > self._words[-1]:
                return []
            return self._wordsset.intersection(other._wordsset)
        return NotImplemented

    ############## Matching types #################

    # both mention span and its min set must be matched exactly
    def _super_exact_match(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        # for split-antecedent we check all the members are the same
        if self.is_split_antecedent or other.is_split_antecedent:
            return self.split_antecedent_sets == other.split_antecedent_sets

        # check if the mention spans are the same
        # TODO rewrite using _wordsset
        if len(self._words) != len(other._words):
            return False
        words_zip = zip(self._words, other._words)
        if not all(self_w == other_w for self_w, other_w in words_zip):
            return False

        # check if the min spans / heads are the same
        return self._minset == other._minset

    # mention span must be matched
    def _exact_match(self, other):
        if isinstance(other, self.__class__):
            # for split-antecedent we check all the members are the same
            if self.is_split_antecedent or other.is_split_antecedent:
                return self.split_antecedent_sets == other.split_antecedent_sets
            else:
                if len(self._words) != len(other._words):
                    return False
                words_zip = zip(self._words, other._words)
                return all(self_w == other_w for self_w, other_w in words_zip)

    def match_score(self, other, matching):
        if not isinstance(other, self.__class__):
            return NotImplemented
        if matching == "zero-dependent":
            return self.zero_dependent_match_score(other)
        if matching == "partial-craft":
            return self.craft_partial_match_score(other)
        if matching == "partial-corefud":
            return self.corefud_partial_match_score(other)
        if matching == "head":
            return self.head_match_score(other)
        # exact match
        if self.__eq__(other):
            return 1.0
        return 0.0

    # Default (with MIN tag) similar to the CorefUD that allow the response to be part of the key, in the
    #             sametime the response must include all the words in MIN(head), if the above condition is
    #             satisfied then a non-zero similarity score based on the proportion of the common words
    #             (num_of_common_words/total_words_in_key) will be returned otherwise 0 will be returned.
    # self = key mention, other = sys mention
    def corefud_partial_match_score(self, other):
        if self._minset and self._minset.issubset(other._wordsset) and other._wordsset.issubset(
            self._wordsset):
            return len(self._wordsset & other._wordsset) * 1.0 / len(self._wordsset)
        return 0.0

    # CRAFT (with craft tag) same as the CRAFT 2019 CR task that use the first key span as the MIN and any
    #             response that overlapping with the MIN (start>=MIN[0] and end <=MIN[1]) will receive a
    #             non-zero similarity score otherwise a zero will be returned.
    # self = key mention, other = sys mention
    def craft_partial_match_score(self, other):
        # only support UA format yet
        return NotImplemented

    # self = key mention, other = sys mention
    def head_match_score(self, other):
        # only support CorefUD format yet
        return NotImplemented
    
    def zero_dependent_match_score(self, other):
        return NotImplemented

    def _exact_match_hash(self):
        return hash(frozenset(self._words))

    def _super_exact_match_hash(self):
        return hash((frozenset(self._words), frozenset(self._minset)))
