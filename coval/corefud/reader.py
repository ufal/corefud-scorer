from udapi.core.document import Document
from udapi.block.read.conllu import Conllu

def load_conllu(file_path):
    doc = Document()
    conllu_reader = Conllu(files=[file_path])
    conllu_reader.apply_on_document(doc)
    return doc


def get_coref_infos(key_file,
        sys_file,
        keep_singletons,
        print_debug=False):

    key_doc = load_conllu(key_file)
    sys_doc = load_conllu(sys_file)

