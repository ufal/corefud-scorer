import logging
import numpy as np
from scipy.optimize import linear_sum_assignment

class Reader:
    class DataAlignError(BaseException):
        def __init__(self, key_node, sys_node, misalign_source="Words",key_name='key',sys_name='sys'):
            self.key_node = key_node
            self.sys_node = sys_node
            self.misalign_source = misalign_source
            self.key_name = key_name
            self.sys_name = sys_name

        def __str__(self):
            return "{:s} in key and sys are not aligned: {:s}={:s}, {:s}={:s}".format(
                self.misalign_source,
                self.key_name,
                str(self.key_node),
                self.sys_name,
                str(self.sys_node))

    class CorefFormatError(BaseException):
        def __init__(self, message):
            self.message = message

        def __str__(self):
            return self.message

    def __init__(self,**kwargs):
        self._doc_coref_infos = {}
        self._doc_non_referring_infos={}
        self._doc_bridging_infos={}
        self._doc_discourse_deixis_infos = {}

        self._doc_mention_aligns = {}

        self.keep_singletons = kwargs.get("keep_singletons",False)
        self.keep_split_antecedents = kwargs.get("keep_split_antecedents",False)
        self.keep_bridging = kwargs.get("keep_bridging",False)
        self.keep_non_referring = kwargs.get("keep_non_referring",False)
        self.evaluate_discourse_deixis = kwargs.get("evaluate_discourse_deixis",False)
        self.matching = kwargs.get("match", "exact")
        self.keep_zeros = kwargs.get("keep_zeros", False)
        self.zero_match_method = kwargs.get("zero_match_method", 'linear')
        self.allow_boundary_crossing = kwargs.get("allow_boundary_crossing",False)
        self.np_only = kwargs.get('np_only',False)
        self.remove_nested_mentions = kwargs.get('remove_nested_mentions',False)

    #the minimum requirement is to implement the coreference part
    @property
    def doc_coref_infos(self):
        return self._doc_coref_infos

    @property
    def doc_non_referring_infos(self):
        return NotImplemented

    @property
    def doc_bridging_infos(self):
        return NotImplemented

    @property
    def doc_discourse_deixis_infos(self):
        return NotImplemented

    @property
    def doc_mention_aligns(self):
        return self._doc_mention_aligns

    def get_coref_infos(self, key_file, sys_file):
        return NotImplemented

    def get_mention_to_clusterid_map(self, entities):
        mention_to_clusterid = {}
        for clusterid, cluster in enumerate(entities):
            for m in cluster:
                if m in mention_to_clusterid:
                    logging.warning(
                        "Mention span {:s} has been already indexed with cluster_id = {:d}. New cluster_id = {:d}".format(
                            str(m), mention_to_clusterid[m], clusterid))
                mention_to_clusterid[m] = clusterid
        return mention_to_clusterid

    def get_assignments_by_match_score(self, key_mention_set, sys_mention_set, matching):
        # no need for match scoring if:
        #   - exact matching
        #   - no remaining unmatched mentions
        if not key_mention_set or not sys_mention_set or matching == "exact":
            return []
        assigns = []
        # sort the mentions in order by start and end indices so that the KM algorithm can make
        # the alignment using same rule as corefUD:
        # 1. pick the mention that overlaps with m with proportionally smallest difference
        # 2. if still more than one n remain, pick the one that starts earlier in the document
        # 3. if still more than one n remain, pick the one that ends earlier in the document
        # 1 were done using similarity score based on proportional token overlapping,
        # 2 and 3 were done by sorting so that the mentions were sorted with the starts and ends.
        key_mentions = sorted(key_mention_set)
        sys_mentions = sorted(sys_mention_set)
        if matching == "partial-craft":
            key_used = {km: False for km in key_mentions}
            for sm in sys_mentions:
                for km in key_mentions:
                    # if not key_used[j] and km.similarity_scores(sm, method='craft') > 0:
                    if km.match_score(sm, matching) > 0:
                        if not key_used[km]:
                            key_used[km] = True
                            # print(str(km), str(sm))
                            assigns.append((km, sm))
                        break
        # matching in ["partial-corefud", "head", "zero-dependent"]
        else:
            similarity = np.zeros((len(key_mentions), len(sys_mentions)))
            for i, km in enumerate(key_mentions):
                for j, sm in enumerate(sys_mentions):
                    similarity[i, j] = km.match_score(sm, matching)
            # print(similarity)
            key_ind, sys_ind = linear_sum_assignment(-similarity)
            assigns = [(key_mentions[k], sys_mentions[s])
                for k, s in zip(key_ind, sys_ind)
                if similarity[k, s] > 0
            ]
        return assigns

    def find_mention_alignment(self, key_mention_set, sys_mention_set):
        key_non_aligned = key_mention_set.copy()
        sys_non_aligned = sys_mention_set.copy()

        logging.debug(f'Total key mentions: {len(key_mention_set)}')
        logging.debug(f'Total response mentions: {len(sys_mention_set)}')

        # (1) obtain alignment between zeros by the dependent match method
        zero_aligns = []
        if self.keep_zeros and self.zero_match_method == 'dependent':
            key_zeros = {m for m in key_mention_set if m.is_zero}
            sys_zeros = {m for m in sys_mention_set if m.is_zero}
            if key_zeros and sys_zeros:
                zero_aligns = self.get_assignments_by_match_score(key_zeros, sys_zeros, "zero-dependent")
                key_non_aligned = key_non_aligned - {km for km, sm in zero_aligns}
                sys_non_aligned = sys_non_aligned - {sm for km, sm in zero_aligns}
        logging.debug(f'Aligned zeros with zeros: {len(zero_aligns)}')

        # (2) get aligment of mentions with exact (or super-exact if head match) matching
        exact_matched_key = {km: km for km in key_non_aligned if km in sys_non_aligned}
        exact_matched_sys = {sm: sm for sm in sys_non_aligned if sm in key_non_aligned}
        assert(set(exact_matched_key.keys()) == set(exact_matched_sys.keys()))
        exact_aligns = [(exact_matched_key[km_key], exact_matched_sys[km_key]) for km_key in exact_matched_key]
        key_non_aligned = key_non_aligned - set(exact_matched_key.values())
        sys_non_aligned = sys_non_aligned - set(exact_matched_sys.values())
        logging.debug(f'Exactly or super-exactly matched mentions: {len(exact_aligns)}')

        # (3) filter out not yet aligned split antecedents
        key_non_aligned = {km for km in key_non_aligned if not km.is_split_antecedent}
        sys_non_aligned = {sm for sm in sys_non_aligned if not sm.is_split_antecedent}

        # (4) get alignment by any kind of partial matching
        partial_aligns = self.get_assignments_by_match_score(key_non_aligned, sys_non_aligned, self.matching)
        key_non_aligned = key_non_aligned - {km for km, sm in partial_aligns}
        sys_non_aligned = sys_non_aligned - {sm for km, sm in partial_aligns}
        logging.debug(f'Partially correct identified mentions: {len(partial_aligns)}')
        logging.debug(f'No identified: {len(key_non_aligned)}')
        logging.debug(f'Invented: {len(sys_non_aligned)}')

        return exact_aligns + partial_aligns + zero_aligns

    def get_nonexact_mention_align_dict(self, mention_aligns):
        mention_align_dict = {}
        mention_align_dict.update({km: sm for km, sm in mention_aligns if km != sm})
        mention_align_dict.update({sm: km for km, sm in mention_aligns if km != sm})
        return mention_align_dict

    def get_mention_assignments(self, key_clusters, sys_clusters):
        key_mention_to_clusterid = self.get_mention_to_clusterid_map(key_clusters)
        sys_mention_to_clusterid = self.get_mention_to_clusterid_map(sys_clusters)

        key_mention_set = set([m for cl in key_clusters for m in cl])
        sys_mention_set = set([m for cl in sys_clusters for m in cl])

        mention_aligns = self.find_mention_alignment(key_mention_set, sys_mention_set)
        nonexact_mention_align_dict = self.get_nonexact_mention_align_dict(mention_aligns)

        return key_mention_to_clusterid, sys_mention_to_clusterid, nonexact_mention_align_dict, mention_aligns
