# CorefUD scorer

## About

CorefUD scorer is a scorer for coreference and anaphoric relations that are harmonized under the same scheme defined by the [CorefUD 1.0](https://ufal.mff.cuni.cz/corefud) project.

The scorer builds on the following projects:

- [original Coreference scorer](https://github.com/conll/reference-coreference-scorers) [Pradhan et al, 2014] developed for scoring the CoNLL 2011 and 2012 shared tasks using the OntoNotes corpus [Pradhan et al, 2011; Pradhan et al, 2012],
- its [reimplementation in Python by Moosavi](https://github.com/ns-moosavi/LEA-coreference-scorer), also extended to compute the LEA score [Moosavi and Strube, 2016] and to evaluate non-referring expressions and cover singletons [Poesio et al, 2018],
- [Universal Anaphora scorer](https://github.com/juntaoy/universal-anaphora-scorer), which is an adaptation of the previous two scorers to the Universal Anaphora guidelines mostly implemented by Juntao Yu [Khosla et al, 2021], extended to evaluate also bridging, discourse deixis and split antecedents.

Unlike any of the previous scorers, CorefUD scorer is adjusted to process and correctly evaluate also non-contiguous mentions.

It supports both exact match and partial match of mentions. Partial match is an alternative to minimum span evaluation by the UA scorer. In addition, the evaluation can be run with singletons taken into account.

For the time being, the scorer is able to evaluate coreference only, excluding split antecedents, bridging and other relations.

## Installation

CorefUD scorer uses [Udapi](https://github.com/udapi/udapi-python) (>=0.3.0) for working with the [CorefUD 1.0 format](https://ufal.mff.cuni.cz/~zeman/2022/docs/corefud-1.0-format.pdf).
You can install it from PyPI together with the remaining dependencies in a standard way by running pip:

`pip3 install -r requirements.txt`

## Usage

Scorer can be run with the following command:

`python corefud-scorer.py [OPTIONS...] [key] [system]`

where `key` and `system` are the location of the key/reference and system/response files.

Options:

- `-m, --metrics METRIC[ METRIC]*`: select specific metrics to be evaluated; default: `all`; possible values: `[muc|bcub|ceafe|ceafm|blanc|lea|all]`
- `-s, --keep-singletons`: evaluate also singletons; otherwise any singletons in the key or system files are ignored
- `-x, --exact-match`: mentions in the key and sys files are matched only if they are exactly the same; otherwise the partial match is applied

## Details

By default, the CorefUD scorer calculates all evaluation metrics using partial match and ignoring all singletons.

### <a name="input_files"></a>Input Files

Both the key and system files must be [well-formed CoNLL-U files](https://universaldependencies.org/format.html) with the coreference information stored in the `MISC` field.
The coreference information must be formatted in the [CorefUD 1.0 style](https://ufal.mff.cuni.cz/~zeman/2022/docs/corefud-1.0-format.pdf).
(WARNING: It completely differs from the format used in CorefUD 0.\*).

The scorer does not check most of the morpho-syntactic features required by the CoNLL-U format.
For most fields, `_` symbol may be used instead of the true values, `0` value for the `HEAD` field.

However, the two input files must be aligned.
Otherwise, the evaluation fails.
Specifically, the evaluation scripts checks if the following requirements are fulfilled:
1. both files must contain the same number of sentences with exactly the same IDs (`# sent_id`);
2. each pair of sentences must contain the same words/tokens, i.e. both their count and forms (the `FORM` field) must be the same;
3. document separators (`# newdoc`) must be exactly at the same places.

The easiest way to satisfy all the requirements above is to ensure that the key and response files differ only in the coreference annotation in the `MISC` field.

### Evaluation Metrics

Evaluation using any of the following metrics is supported:
- MUC [Vilain et al, 1995]
- B-cubed [Bagga and Baldwin, 1998]
- CEAF in the entity (CEAFe) and mention (CEAFm) variant [Luo, 2005]
- BLANC [Recasens and Hovy, 2011]
- LEA [Moosavi and Strube, 2016]
- the averaged CoNLL score (the average of the F1 values of MUC, B-cubed and CEAFe) [Denis and Baldridge, 2009a; Pradhan et al., 2014].

You can also select only specific metrics by including one or some of the `muc`, `bcub`, `ceafe`, `ceafm`, `blanc` and `lea` values as parameters of the option `-m, --metrics`.
CoNLL score is reported automatically if all MUC, B-cubed and CEAFe are calculated.
For instance, the following command only reports the CEAFe and LEA scores:

`python corefud-scorer.py -m ceafe lea -- key sys`

The symbol `--` needs to be used to delimit the two required positional arguments (`key` and `sys`) from a list of metrics to be calculated.
Alternatively, potentially unlimited list of metrics may be passed as the last argument:

`python corefud-scorer.py key sys -m ceafe lea`

### Mention Matching

A fundamental element of all the metrics above is whether there is a correspondence between a key mention and a response mention.
In other words, if the two mentions, each from one of the two input files, are matching.
CorefUD scorer distinguishes between two types of mention matching:
1. exact
2. partial/fuzzy
This can be controlled by the `-x, --exact-match` option, which switches on exact matching.
Otherwise, mentions are compared with partial matching.

#### Exact Matching

In *exact matching*, the two mentions are considered matching if and only if they consist of the same set of words.
A word is defined here only by its position within the sentence and by position of the sentence within the whole file.
This is sufficient as one-to-one alignment of word forms has been already ensured by passing the file alignment requirements specified [above](#input_files).

#### Partial Matching

In *partial matching*, the two mentions are considered matching if and only if the key mention contains all words from the response mention and a key mention head is included among the response mention words at the same time.
As the mentions within a document may be embedded or even crossing, a mention *m* from one file may potentially match more than a single mention *n* from the other file.
To end up with a single matched mention, the following rules are obeyed:
1. pick the mention that overlaps with *m* with proportionally smallest difference
2. if still more than one *n* remain, pick the one that starts earlier in the document
3. if still more than one *n* remain, pick the one that ends earlier in the document

Data that comply with the CorefUD 1.0 format are required to have all mentions labeled with a mention head, which is one of the mention words that syntactically (but often also semantically) governs the whole mention.
(WARNING: Do not confuse with the `HEAD` field in the CoNLL-U format, which marks a dependency parent of current node)
Mention heads in CorefUD 1.0 data have been selected by [heuristics](https://github.com/udapi/udapi-python/blob/master/udapi/block/corefud/movehead.py) based on the dependency structure of the sentence the mention belongs to.
In the following example, the 3rd word of the mention `the viewing experience of art`, i.e. the word `experience`, is labeled as the mention head:
```
1   The        ...   Entity=(e27-abstract-3-
2   viewing    ...   Entity=(e28-event-1-)
3   experience ...   _
4   of         ...   _
5   art        ...   Entity=(e20-abstract-1-)e27)
6   is         ...   _
...
```

Each key mention is represented by all its words and its head, where the `--exact-match` option determines if the head is going to be taken into account or not.
On the other hand, the only information on response mentions the scorer keeps are the words that the mention consists of.
Even though marking mention head index in CorefUD 1.0 format is mandatory, unlike in the case of key mentions, heads of response mentions are simply ignored during evaluation.
A coreference resolution system producing response mentions can thus set each mention head index to value `1`, setting the first word of a mention as its head.

#### Discontinuous mentions

CorefUD scorer allows for evaluating discontinuous mentions in any of the input files.
This is why mention matching is based on set-subset relations between sets of words in mentions, instead of comparing positions of mention starts and ends, which is usual in previous scorers, e.g. in CoNLL 2012 scorer and UA scorer.

### Singletons

Singletons are entities that contain only a single mention.
Datasets often differ in the aspect whether singletons have been annotated or not.
And this does not have to be in line with a coreference resolution system.

In order to ensure fair comparison, all singletons are excluded from both key and response files.
Nevertheless, evaluation with singletons included may be turned on by the `-s, --keep-singletons` option.

### Authors

* Michal Novák, Charles University, Prague, Czech Republic, mnovak@ufal.mff.cuni.cz
* Yilun Zhu, Georgetown University, Washington D.C., USA, yz565@georgetown.edu
* Martin Popel, Charles University, Prague, Czech Republic, popel@ufal.mff.cuni.cz

The Universal Anaphora scorer has been developed by:

* Juntao Yu, Queen Mary University of London, juntao.cn@gmail.com
* Nafise Moosavi, UKP, TU Darmstadt, ns.moosavi@gmail.com
* Silviu Paun, Queen Mary University of London, spaun3691@gmail.com
* Massimo Poesio, Queen Mary University of London, poesio@gmail.com

The original reference Coreference Scorer (CoNLL 2012 scorer) was developed by:

*  Emili Sapena, Universitat Politècnica de Catalunya, http://www.lsi.upc.edu/~esapena, esapena@lsi.upc.edu
*  Sameer Pradhan, https://cemantix.org, pradhan@cemantix.org
*  Sebastian Martschat, sebastian.martschat@h-its.org
*  Xiaoqiang Luo, xql@google.com

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
