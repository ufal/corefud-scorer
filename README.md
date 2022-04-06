# CorefUD scorer

## About

CorefUD scorer is a scorer for coreference and anaphoric relations that are harmonized under the same scheme defined by the CorefUD 1.0 project.

The scorer builds on the following projects:

- original Coreference scorer [Pradhan et al, 2014] developed for scoring the CoNLL 2011 and 2012 shared tasks using the OntoNotes corpus [Pradhan et al, 2011; Pradhan et al, 2012]: https://github.com/conll/reference-coreference-scorers
- its reimplementation in Python by Moosavi, also extended to compute the LEA score [Moosavi and Strube, 2016] and to evaluate non-referring expressions evaluation and cover singletons [Poesio et al, 2018]: https://github.com/ns-moosavi/LEA-coreference-scorer
- Universal Anaphora scorer, which is an adaptation of the previous two scorers to the Universal Anaphora guidelines mostly implemented by Juntao Yu [Khosla et al, 2021], extended to evaluate also bridging, discourse deixis and split antecedents: https://github.com/juntaoy/universal-anaphora-scorer

Unlike any of the previous scorers, CorefUD scorer is adjusted to process and correctly evaluate also non-contiguous mentions.

It supports both exact match and partial match of mentions. Partial match is an alternative to minimum span evaluation by the UA scorer. In addtion, the evaluation can be run with singletons taken into account.

For the time being, the scorer is able to evaluate coreference only, excluding split antecedents, bridging and other relations.

## Installation

CorefUD scorer uses [Udapi](https://github.com/udapi/udapi-python) (>=0.3.0) for working with the CorefUD 1.0 format.
You can install it from PyPI together with the remaining dependencies in a standard way by running Pip3:

`pip3 install -r requirements.txt`

## Usage

Scorer can be run with the following command:

`python corefud-scorer.py [OPTIONS...] [key] [system]`

where `key` and `system` are the location of the key (gold) and system (predicted) files.

Options:

- `-m, --metrics METRIC[ METRIC]*`: select specific metrics to be evaluated; default: `all`; possible values: `[muc|bcub|ceafe|ceafm|blanc|lea|all]`
- `-s, --keep-singletons`: evaluate also singletons; otherwise any singletons in the key or system files are ignored
- `-x, --exact-match`: mentions in the key and sys files are matched only if they are exactly the same; otherwise the partial match is applied

## Details on Evaluation Metrics and Evaluation Modes

By default, the CorefUD scorer calculates all evaluation metrics using partial match and ignoring all singletons.

### Evaluation Metrics

Evaluation using any of the following metrics is supported:
- MUC [Vilain et al, 1995]
- B-cubed [Bagga and Baldwin, 1998]
- CEAF in the entity (CEAFe) and mention (CEAFm) variant [Luo, 2005]
- BLANC [Recasens and Hovy, 2011]
- LEA [Moosavi and Strube, 2016]
- the averaged CoNLL score (the average of the F1 values of MUC, B-cubed and CEAFe) [Denis and Baldridge, 2009a; Pradhan et al., 2014].

You can also only select specific metrics by including one or some of the `muc`, `bcub`, `ceafe`, `ceafm`, `blanc` and `lea` options in the input arguments.
CoNLL score is reported automatically if all MUC, B-cubed and CEAFe are calculated.
For instance, the following command only reports the CEAFe and LEA scores:

`python corefud-scorer.py -m ceafe lea -- key sys`

The symbol `--` needs to be used to delimit the two required positional arguments (`key` and `sys`) from a list of metrics to be calculated.
Alternatively, potentially unlimited list of metrics may be passed as the last argument:

`python corefud-scorer.py key sys -m ceafe lea`

### TODO

### References
  
  Amit Bagga and Breck Baldwin.  1998.
  Algorithms for scoring coreference chains.
  In Proceedings of LREC, pages 563–566.

  Pascal Denis and Jason Baldridge.  2009.
  Global joint models for coreference resolution and named entity classification.
  Procesamiento del Lenguaje Natural, (42):87–96.

  Sopan Khosla, Juntao Yu, Ramesh Manuvinakurike, Vincent Ng, Massimo Poesio, Michael Strube, and Carolyn Rosé. 2021.
  The CODI-CRAC 2021 Shared Task on Anaphora, Bridging, and Discourse Deixis in Dialogue.
  In Proceedings of the CODI-CRAC 2021 Shared Task on Anaphora, Bridging, and Discourse Deixis in Dialogue, pages 1–15.
  
  Xiaoqiang Luo. 2005.
  On coreference resolution performance metrics.
  In Proceedings of HLT-EMNLP, pages 25–32.

  Nafise Sadat Moosavi and Michael Strube. 2016.
  Which Coreference Evaluation Metric Do You Trust? A Proposal for a Link-based Entity Aware Metric.
  In Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics.

  Massimo Poesio, Yulia Grishina, Varada Kolhatkar, Nafise  Moosavi, Ina  Roesiger, Adam  Roussel, Fabian Simonjetz, Alexandra Uma, Olga Uryupina, Juntao Yu, and Heike Zinsmeister. 2018.
  Anaphora resolution with the ARRAU corpus.
  In Proc. of the NAACL Worskhop on Computational Models of Reference, Anaphora and Coreference (CRAC), pages 11–22, New Orleans.

  Sameer Pradhan, Lance Ramshaw, Mitchell Marcus, Martha Palmer, Ralph Weischedel, and Nianwen Xue.  2011.
  CoNLL-2011 shared task: Modeling unrestricted coreference in OntoNotes.
  In Proceedings of CoNLL: Shared Task, pages 1–27.

  Sameer Pradhan, Alessandro Moschitti, Nianwen Xue, Olga Uryupina, Yuchen Zhang.   2012.
  CoNLL-2012 Shared Task: Modeling Multilingual Unrestricted Coreference in OntoNotes
  In Proceedings of the Joint Conference on EMNLP and CoNLL: Shared Task, pages 1-40

  Sameer Pradhan, Xiaoqiang Luo, Marta Recasens, Eduard Hovy, Vincent Ng, and Michael Strube. 2014.
  Scoring coreference partitions of predicted mentions: A reference implementation.
  In Proceedings of the 52nd Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers),
  Baltimore, Md., 22–27 June 2014, pages 30–35.

  Marta Recasens and Eduard Hovy.  2011.
  BLANC: Implementing the Rand Index for coreference evaluation.
  Natural Language Engineering, 17(4):485–510.

  Marc Vilain, John Burger, John Aberdeen, Dennis Connolly, and Lynette Hirschman. 1995.
  A model theoretic coreference scoring scheme.
  In Proceedings of the 6th Message Understanding Conference, pages 45–52.
