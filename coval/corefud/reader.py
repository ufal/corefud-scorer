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
        print("{:d} {:d}".format(tree1.bundle.number, tree2.bundle.number))
        if (tree1.newdoc and not tree2.newdoc) or (not tree1.newdoc and tree2.newdoc):
            raise DocAlignError(tree1, tree2, "Newdoc labels")
        if tree1.sent_id != tree2.sent_id:
            raise DocAlignError(tree1, tree2, "Sent IDs")
        doc12_nodes = zip(tree1.descendants_and_empty, tree2.descendants_and_empty)
        for node1, node2 in doc12_nodes:
            if node1.form != node2.form:
                raise DocAlignError(node1, node2, "Words")

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
