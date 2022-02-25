import logging
from collections import defaultdict
from coval.corefud.mention import Mention
from udapi.core.document import Document
from udapi.block.read.conllu import Conllu

class DataAlignError(BaseException):
    def __init__(self, key_node, sys_node, misalign_source="Words"):
        self.key_node = key_node
        self.sys_node = sys_node
        self.misalign_source = misalign_source

    def __str__(self):
        return "{:s} in key and sys are not aligned: key={:s}, sys={:s}".format(
            self.misalign_source,
            str(self.key_node),
            str(self.sys_node))

class CorefFormatError(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return message

def load_conllu(file_path):
    doc = Document()
    conllu_reader = Conllu(files=[file_path])
    conllu_reader.apply_on_document(doc)
    return doc

def check_data_alignment(data1, data2):
    data12_trees = zip(data1.trees, data2.trees)
    for tree1, tree2 in data12_trees:
        if tree1.newdoc != tree2.newdoc:
            raise DataAlignError(tree1, tree2, "Newdoc labels")
        if tree1.sent_id != tree2.sent_id:
            raise DataAlignError(tree1, tree2, "Sent IDs")
        data12_nodes = zip(tree1.descendants_and_empty, tree2.descendants_and_empty)
        for node1, node2 in data12_nodes:
            if node1.form != node2.form:
                raise DataAlignError(node1, node2, "Words")

def split_data_to_docs(data):
    word2docid = {}
    docord = 0
    docid = None
    for tree in data.trees:
        if tree.newdoc:
            docord += 1
            docid = tree.newdoc if tree.newdoc is not True else docord
        for node in tree.descendants_and_empty:
            word2docid[node] = docid
    doc_clusters = defaultdict(lambda: defaultdict(list))

    for cid, cluster in data.coref_clusters.items():
        mention_doc = None
        for mention in cluster.mentions:
            words_docs = list(set([word2docid[w] for w in mention.words]))
            if len(words_docs) > 1:
                mention_str = ", ".join([str(w) for w in mention.words])
                raise CorefFormatError("Mention cannot cross a document boundary. The following does: " + mention_str)
            if mention_doc and mention_doc != words_docs[0]:
                logging.warning("Cluster {:s} spans two documents ({:s}, {:s}). It will be split.")
            mention_doc = words_docs[0]
            doc_clusters[mention_doc][cid].append(mention)
    return doc_clusters

def transform_clusters_for_eval(clusters, nohead=False):
    # TODO: CorefMentions sets the first mention's word as its head if no head is specified
    # This is problematic for partial matching of key and sys mention.
    # For continuous mentions, a key mention is partially matched by the sys mention,
    # if the sys mention lies within the key mention and covers its head/min at the same time.
    # It requires the sys mention to have no head/min annotated.
    # All key mentions in CorefUD data should have their head annotated as they are automatically
    # added based on the dependency tree. This is, however, a result of running the MoveHead block.
    # Otherwise, the first mention node is declared to be its head. 
    # Users applying UDAPI for their own data does not have to know it and thus the partial
    # matching is not going to work properly for them.
    transformed_clusters = []
    for cluster in clusters.values():
        transformed_cluster = [Mention(m.words, None if nohead else m.head) for m in cluster]
        transformed_clusters.append(transformed_cluster)
    return transformed_clusters

def process_clusters(clusters, keep_singletons):
    removed_singletons = 0
    processed_clusters = []
    for cluster in clusters:
        if not keep_singletons and len(cluster) == 1:
            removed_singletons += 1
            continue
        processed_clusters.append(cluster)
    return processed_clusters, removed_singletons

def get_mention_assignments(clusters):
    mention_cluster_ids = {}
    for cluster_id, cluster in enumerate(clusters):
        for m in cluster:
            mention_cluster_ids[m] = cluster_id
    return mention_cluster_ids

def get_coref_infos(key_file,
        sys_file,
        keep_singletons,
        print_debug=False):

    # loading the documents
    key_data = load_conllu(key_file)
    sys_data = load_conllu(sys_file)

    # checking if key and sys data are aligned
    check_data_alignment(key_data, sys_data)

    # split data into documents and collect the clusters per document
    # also checking if relations do not cross document boundaries
    key_doc_clusters = split_data_to_docs(key_data)
    sys_doc_clusters = split_data_to_docs(sys_data)

    doc_coref_infos = {}

    for docname in key_doc_clusters:
        assert docname in sys_doc_clusters

        key_clusters = transform_clusters_for_eval(key_doc_clusters[docname])
        sys_clusters = transform_clusters_for_eval(sys_doc_clusters[docname], True)

        key_clusters, key_removed_singletons = process_clusters(key_clusters, keep_singletons)
        sys_clusters, sys_removed_singletons = process_clusters(sys_clusters, keep_singletons)

        key_mention_to_cluster = get_mention_assignments(key_clusters)
        sys_mention_to_cluster = get_mention_assignments(sys_clusters)

        # for an unknown reason, coval.eval expects the tuple where 
        # key_mention_to_cluster and sys_mention_to_cluster are 
        # in the opposite order than key_cluster and sys_cluster
        doc_coref_infos[docname] = (key_clusters, sys_clusters,
            sys_mention_to_cluster, key_mention_to_cluster)

        logging.debug("Singletons removed: key={:d}, sys={:d}".format(key_removed_singletons, sys_removed_singletons))

    return doc_coref_infos
