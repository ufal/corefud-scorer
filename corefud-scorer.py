import sys
import argparse
from coval.eval import evaluator
from coval.corefud import reader

__author__ = 'michnov'

def main():
    argparser = argparse.ArgumentParser(description="Coreference scorer for documents in CorefUD 1.0 scheme")
    argparser.add_argument('key_file', type=str, help='path to the key/reference file')
    argparser.add_argument('sys_file', type=str, help='path to the system/response file')
    argparser.add_argument('-m', '--metrics', choices=['all', 'lea', 'muc', 'bcub', 'ceafe', 'ceafm', 'blanc'], nargs='*', default='all', help='metrics to be used for evaluation')
    argparser.add_argument('-s', '--keep-singletons', action='store_true', default=False, help='evaluate also singletons; ignored otherwise')
    argparser.add_argument('-x', '--exact-match', action='store_true', default=False, help='use exact match for matching key and system mentions; partial match otherwise')
    args = argparser.parse_args()
    
    metric_dict = {
        'lea': evaluator.lea, 'muc': evaluator.muc,
        'bcub': evaluator.b_cubed, 'ceafe': evaluator.ceafe,
        'ceafm': evaluator.ceafm, 'blanc': [evaluator.blancc,evaluator.blancn]}
  
    if 'all' in args.metrics:
        args.metrics = metric_dict.keys()
    args.metrics = [(name, metric_dict[name]) for name in args.metrics]

    msg = 'The scorer is evaluating coreference {:s} singletons, with {:s} matching of mentions using the following metrics: {:s}.'.format(
        'including' if args.keep_singletons else 'excluding',
        'exact' if args.exact_match else 'partial',
        ", ".join([name for name, f in args.metrics]))
    print(msg)

    evaluate(args.key_file, args.sys_file, args.metrics, args.exact_match, args.keep_singletons)

def evaluate(key_file, sys_file, metrics, exact_matching, keep_singletons):

    coref_infos = reader.get_coref_infos(key_file, sys_file, exact_matching, keep_singletons)
    
    conll = 0
    conll_subparts_num = 0
  
    for name, metric in metrics:  
        recall, precision, f1 = evaluator.evaluate_documents(coref_infos,
            metric,
            beta=1,
            only_split_antecedent=False)
        if name in ["muc", "bcub", "ceafe"]:
            conll += f1
            conll_subparts_num += 1

        print(name)
        print('Recall: %.2f' % (recall * 100),
            ' Precision: %.2f' % (precision * 100),
            ' F1: %.2f' % (f1 * 100))

    if conll_subparts_num == 3:
        conll = (conll / 3) * 100
        print('CoNLL score: %.2f' % conll)

main()
