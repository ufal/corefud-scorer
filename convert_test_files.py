import sys
import re

def convert_coref(annot):
    if annot == "-":
        return "_"
    is_open = False
    parts = [p for p in re.split(r'([()])', annot) if p != ""]
    new_parts = []
    for part in parts:
        if part == "(":
            is_open = True
        elif part != ")" and is_open:
            part = "e" + part + "-x-1-"
        elif part != ")" and not is_open:
            part = "e" + part
        new_parts.append(part)
    return "Entity="+"".join(new_parts) 

docname = None
sent_i = 1
i = 1
for line in sys.stdin:
    line = line.rstrip()
    if line.startswith("#begin"):
        m = re.match(r"#begin document \((.*)\);", line)
        docname = m.group(1)
        print("# newdoc id = {:s}".format(docname))
        print("# global.Entity = eid-etype-head-other")
        print("# sent_id = {:s}-{:d}".format(docname, sent_i))
        print("# text = sentence")
    elif line.startswith("#end"):
        continue
    elif line == "":
        print("")
        i = 1
        sent_i += 1
        print("# sent_id = {:s}-{:d}".format(docname, sent_i))
        print("# text = sentence")
    else:
        cols = line.split("\t")
        coref = convert_coref(cols[-1])
        # if len(cols) == 2:
        feats = [str(i)] + ["_"]*5 + ["0"] + ["_"]*2 + [coref]
        print("\t".join(feats))
        i += 1
print()
