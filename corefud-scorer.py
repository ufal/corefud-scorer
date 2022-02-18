import sys
from coval.eval import evaluator
from coval.corefud import reader

__author__ = 'michnov'

def main():
  metric_dict = {
      'lea': evaluator.lea, 'muc': evaluator.muc,
      'bcub': evaluator.b_cubed, 'ceafe': evaluator.ceafe,
      'ceafm':evaluator.ceafm, 'blanc':[evaluator.blancc,evaluator.blancn]}
  key_file = sys.argv[1]
  sys_file = sys.argv[2]
  
  if 'remove_singletons' in sys.argv or 'remove_singleton' in sys.argv:
    keep_singletons = False
  else:
    keep_singletons = True
  
  if 'all' in sys.argv:
    metrics = [(k, metric_dict[k]) for k in metric_dict]
  else:
    metrics = []
    for name in metric_dict:
      if name in sys.argv:
        
        metrics.append((name, metric_dict[name]))

  if len(metrics) == 0:
    metrics = [(name, metric_dict[name]) for name in metric_dict]
  
  print('The scorer is evaluating ', msg)

  evaluate(key_file, sys_file, metrics, keep_singletons)

def evaluate(key_file, sys_file, metrics, keep_singletons):

    # TODO: extract clusters
    
    conll = 0
    conll_subparts_num = 0
  
    for name, metric in metrics:  
        recall, precision, f1 = evaluator.evaluate_documents(doc_coref_infos,
            metric,
            beta=1,
            only_split_antecedent=only_split_antecedent)
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
