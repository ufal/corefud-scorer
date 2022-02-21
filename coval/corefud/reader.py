from coval.corefud.mention import Mention
from udapi.core.document import Document
from udapi.block.read.conllu import Conllu

class DocAlignError(BaseException):
    def __init__(self, key_node, sys_node, misalign_source="Words"):
        self.key_node = key_node
        self.sys_node = sys_node
        self.misalign_source = misalign_source

    def __str__(self):
        return "{:s} in key and sys are not aligned: key={:s}, sys={:s}".format(
            self.misalign_source,
            str(self.key_node),
            str(self.sys_node))

def load_conllu(file_path):
    doc = Document()
    conllu_reader = Conllu(files=[file_path])
    conllu_reader.apply_on_document(doc)
    return doc

def check_doc_alignment(doc1, doc2):
    doc12_trees = zip(doc1.trees, doc2.trees)
    for tree1, tree2 in doc12_trees:
        if (tree1.newdoc and not tree2.newdoc) or (not tree1.newdoc and tree2.newdoc):
            raise DocAlignError(tree1, tree2, "Newdoc labels")
        if tree1.sent_id != tree2.sent_id:
            raise DocAlignError(tree1, tree2, "Sent IDs")
        doc12_nodes = zip(tree1.descendants_and_empty, tree2.descendants_and_empty)
        for node1, node2 in doc12_nodes:
            if node1.form != node2.form:
                raise DocAlignError(node1, node2, "Words")

def transform_cluster_for_eval(cluster, nohead=False):
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
    return [Mention(m.words, None if nohead else m.head) for m in cluster.mentions]

def get_coref_infos(key_file,
        sys_file,
        keep_singletons,
        print_debug=False):

    # loading the documents
    key_doc = load_conllu(key_file)
    sys_doc = load_conllu(sys_file)

    # checking if key and sys documents are aligned
    check_doc_alignment(key_doc, sys_doc)

    #TODO check if relations do not cross newdoc boundaries

    key_clusters = {cid: transform_cluster_for_eval(cluster) for cid, cluster in key_doc.coref_clusters.items()}
    sys_clusters = {cid: transform_cluster_for_eval(cluster, True) for cid, cluster in sys_doc.coref_clusters.items()}

    print(key_clusters)
    print(sys_clusters)

