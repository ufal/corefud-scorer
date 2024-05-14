# CorefUD scorer

## About

CorefUD scorer is a scorer for coreference relations represented in the CorefUD 1.0 format.
It is an official scorer for the CRAC Shared Tasks on Multilingual Coreference Resolution.
The shared task is one of the activities of the [CorefUD](https://ufal.mff.cuni.cz/corefud) project, which collects coreference and anaphora datasets of various languages and aims to harmonize them under the same scheme.

The scorer builds on top of the [Universal Anaphora scorer (UA scorer)](https://github.com/juntaoy/universal-anaphora-scorer), currently on its version 2.0 <a href="https://aclanthology.org/2023.iwcs-1.19/">[Yu et al, 2023]</a>.
At the same time, the CorefUD scorer is one of the sources for the new features in the UA scorer.

It supports exact, partial and head match of mentions.
Whereas partial match is an alternative to minimum span evaluation by the UA scorer, head match compares whether the mention heads are represented by identical tokens.
The scorer is also able to evaluate zero anaphora, using two alternative strategies to match key zero mentions to response zero mentions: linear and dependency.

The CorefUD scorer supports all standard metrics used for coreference, e.g. MUC, B-cubed, CEAF, BLANC and LEA.
In addition, is is able to compute the Mention Overlap Ratio and Anaphor-decomposable score, introduced for the CRAC 2022 Shared Task.
Optionally, the evaluation can be run with singletons taken into account.

The scorer is limited to evaluate coreference only, excluding split antecedents, bridging and other relations, as the latter relations are currently irrelevant for the shared task.

## Installation

CorefUD scorer uses [Udapi](https://github.com/udapi/udapi-python) (>=0.3.0) for working with the [CorefUD 1.0 format](https://ufal.mff.cuni.cz/~zeman/2022/docs/corefud-1.0-format.pdf).
You can install it from PyPI together with the remaining dependencies in a standard way by running pip:

`pip3 install -r requirements.txt`

## Usage

Scorer can be run with the following command:

`python corefud-scorer.py [OPTIONS...] [key] [system]`

where `key` and `system` are the location of the key/reference and system/response files.

Options:

- `-m, --metrics METRIC[ METRIC]*`: select specific metrics to be evaluated; default: `all`; possible values: `[muc|bcub|ceafe|ceafm|blanc|lea|mor|zero|all]`
- `-s, --keep-singletons`: evaluate also singletons; otherwise any singletons in the key or system files are ignored
- `-a, --match`: select the way of mention matching; default: `head`; possible values: `[exact|partial|head]`
- `-x, --exact-match`: a shortcut for enabling exact matching; corresponds to `-a exact`
- `-z, --zero-match-method`: choose the method for matching zero mentions; default: `dependent`; possible values: `[dependent|linear]`

## Details

By default, the CorefUD scorer calculates all evaluation metrics using head match and ignoring all singletons.

### <a name="input_files"></a>Input Files

Both the key and system files must be [well-formed CoNLL-U files](https://universaldependencies.org/format.html) with the coreference information stored in the `MISC` field.
The coreference information must be formatted in the [CorefUD 1.0 style](https://ufal.mff.cuni.cz/~zeman/2022/docs/corefud-1.0-format.pdf).
(WARNING: It completely differs from the format used in CorefUD 0.\*).

The scorer does not check most of the morpho-syntactic features required by the CoNLL-U format.
For most fields, `_` symbol may be used instead of the true values, `0` value for the `HEAD` field.

However, the two input files must be aligned, besides the empty tokens.
Otherwise, the evaluation fails.
Specifically, the evaluation scripts checks if the following requirements are fulfilled:
1. both files must contain the same number of sentences with exactly the same IDs (`# sent_id`);
2. each pair of sentences must consist of the same sequences of non-empty words/tokens, i.e. sequences of forms (the `FORM` field) must be the same; note that empty nodes are excluded from this alignment check
3. document separators (`# newdoc`) must be exactly at the same places.

The easiest way to satisfy all the requirements above is to ensure that the key and response files differ only in coreference annotation in the `MISC` field, and possibly in empty token.

*Changed in version 1.2: Empty tokens are excluded from the alignment tests of the key and response file tokens.*

### Evaluation Metrics

Evaluation using any of the standard following metrics is supported:
- MUC [Vilain et al, 1995]
- B-cubed [Bagga and Baldwin, 1998]
- CEAF in the entity (CEAFe) and mention (CEAFm) variant [Luo, 2005]
- BLANC [Recasens and Hovy, 2011]
- LEA [Moosavi and Strube, 2016]
- the averaged CoNLL score (the average of the F1 values of MUC, B-cubed and CEAFe) [Denis and Baldridge, 2009a; Pradhan et al., 2014].

Also two supplementary measures introduced for CRAC 2022 shared task are supported:
- MOR -- Mention Overlap Ratio [Žabokrtský et al., 2022]
- Anaphor-decomposable score for zeros [Žabokrtský et al., 2022]

You can also select only specific metrics by including one or some of the `muc`, `bcub`, `ceafe`, `ceafm`, `blanc`, `lea`, `mor`, `zero` values as parameters of the option `-m, --metrics`.
CoNLL score is reported automatically if all MUC, B-cubed and CEAFe are calculated.
For instance, the following command only reports the CEAFe and LEA scores:

`python corefud-scorer.py -m ceafe lea -- key sys`

The symbol `--` needs to be used to delimit the two required positional arguments (`key` and `sys`) from a list of metrics to be calculated.
Alternatively, potentially unlimited list of metrics may be passed as the last argument:

`python corefud-scorer.py key sys -m ceafe lea`

### Mention Matching

A fundamental element of all the metrics above is whether there is a correspondence between a key mention and a response mention.
In other words, if the two mentions, each from one of the two input files, are matching.
CorefUD scorer distinguishes between three types of mention matching:
1. exact
2. partial/fuzzy
3. head
This can be controlled by the `-a, --match [exact|partial|head]` option.
As a shortcut, the `-x, --exact-match` option switches on exact matching and is thus equivalent to `-a exact`.
By default, mentions are compared with head matching.

All three methods seek for 1-to-1 correspondence between key and response mentions.
That is, no key mention is allowed to match multiple response mentions, and vice versa.
On the other hand, it is absolutely valid if some key or response mentions remain unmatched.

*Changed in version 1.1: default matching changed from partial to head.*
*Changed in version 1.2: a bug that allowed for 1-to-n matching between the response and key mentions has been fixed by adopting the implementation of matching from the UA scorer 2.0.*

#### Exact Matching

In *exact matching*, the two mentions are considered matching if and only if they consist of the same set of words.
A word is defined here only by its position within the sentence and by position of the sentence within the whole file.
This is sufficient as one-to-one alignment of word forms has been already ensured by passing the file alignment requirements specified [above](#input_files).

Setting of mention heads in both key and response files is ignored in this setup.

#### Partial Matching

In *partial matching*, the two mentions are considered matching if and only if the key mention contains all words from the response mention and a key mention head is included among the response mention words at the same time.
As the mentions within a document may be embedded or even crossing, a mention *m* from one file may potentially match more than a single mention *n* from the other file.
To end up with a single matched mention, the following disambiguation rules are obeyed:
1. pick the mention that overlaps with *m* with proportionally smallest difference
2. if still more than one *n* remain, pick the one that starts earlier in the document
3. if still more than one *n* remain, pick the one that ends earlier in the document

Data that comply with the CorefUD 1.0 format are required to have all mentions labeled with a mention head, which is one of the mention words that syntactically (but often also semantically) governs the whole mention.
(WARNING: Do not confuse with the `HEAD` field in the CoNLL-U format, which marks a dependency parent of current node)
Mention heads in CorefUD data have been selected by [heuristics](https://github.com/udapi/udapi-python/blob/master/udapi/block/corefud/movehead.py) based on the dependency structure of the sentence the mention belongs to.
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

In partial matching, each key mention is represented by all its words and its head (unlike in exact matching, where heads of key mentions are ignored).
On the other hand, the only information on response mentions the scorer takes into account in the partial matching strategy are the words that the mention consists of.
Even though marking mention head index in CorefUD 1.0 format is mandatory, heads of response mentions are simply ignored during evaluation with partial matching.

#### Head Matching

In *head matching*, the two mentions are considered matching if their heads correspond to identical tokens.
If there are multiple key or response mentions with the same head, the same disambiguation rules as in the partial matching are used.
In other words, as long as there are no mentions in either the key or the response file that share the same head, only mention heads are used to match key and response mentions.
Full mention spans are ignored in such case.
However, full spans can be taken into account but only to disambiguate between multiple mentions with the same head.

In order for a coreference resolver to succeed with respect to head matching, it should focus on predicting not only the mention span but also its head.
If the resolver is able to predict mention spans only (and, for instance, sets each mention head index to value `1`, selecting always the first word of a mention as its head), mention heads can be estimated using the dependency tree obtained by a parser (the CorefUD data already contain annotation of dependency syntax) and some heuristics, e.g. [the one provided by Udapi](https://github.com/udapi/udapi-python/blob/master/udapi/block/corefud/movehead.py).

### Matching of Zero Mentions

Zero mention referes to a mention whose head token is an empty token.
Most commonly, the empty token comprises the entire mention, as in the case of dropped pronouns.
However, it can also consist of multiple tokens, particularly with elided verbs or nouns.

Starting from version 1.2, the CorefUD scorer relaxes the rules for empty token alignment.
Empty tokens are no longer subjected to strict checks for alignment between the tokens in the key and response files.
This means that empty tokens present in one file may be missing from the other, or they may appear at different surface positions within the sentence, yet play the same role.
If two zero mentions are governed by such empty tokens, they are still expected to be matched.

The CorefUD scorer implements two alternative methods for matching key and response zeros: linear and dependency (enabled by the `linear` and `dependent` value of the `--zero-match-method` option, respectively).

The linear method treats zero mentions similarly to other mentions.
Regardless of the selected matching method (exact, partial or head), the candidate mentions are compared based on the token ord numbers represented by the values in the `ID` field.
However, this simplistic strategy can lead to incorrect alignments.
For example, consider a sentence with both subject and object pronouns dropped.
The key file represent them as empty nodes with IDs `x.1` and `x.2`, respectively.
If a coreference resolver reconstructs them in a reversed order or reconstructs just the object pronoun with ID `x.1`, the linear method produces an incorrect matching of zero mentions, affecting the reliability of coreference scores.

The dependency-based method adresses this issue by looking for the matching of zeros within the same sentence that maximizes the F-score of predicting dependencies in the `DEPS` field that the zeros are involved in.
Specifically, the task is cast as searching for a 1-to-1 matching in a weighted bipartite graph (with key mentions and sys mentions as partitions) to maximize the total sum of weights in the matching.
Each candidate pair (key zero, sys zero) is weighed with a non-zero score only if the two zeros belong to the same sentence.
The score is then calculated as a weighted sum of two features:
- the F-score of the key zero dependencies (in the `DEPS` field) predicted in the response zero, considering both parent and dependency type assignments (weighted by a factor of 10);
- the F-score of the key zero dependencies (in the `DEPS` field) predicted in the response zero, considering only parent assignments (weighed by a factor of 1).
The scoring system prioritizes exact assignment of both parents and types, while parent assignments without considering dependency types should only serve to break ties.

Note that matching zero mentions by their dependencies is applied first, preceding the other matching strategies.
Zeros that have not been matched to other zeros may then be matched to non-zero mentions.
Although such matching may seem counterintuitive, it can be valid in cases where a zero response mention is incorrectly labeled as non-zero, or vice versa, often due to the wrong choice of the head in multi-token mentions involving empty tokens.

### Discontinuous mentions

CorefUD scorer allows for evaluating discontinuous mentions in any of the input files.
This is why mention matching is based on set-subset relations between sets of words in mentions, instead of comparing positions of mention starts and ends, which is usual in previous scorers, e.g. in CoNLL 2012 scorer and UA scorer 1.0.

### Singletons

Singletons are entities that contain only a single mention.
Datasets often differ in the aspect whether singletons have been annotated or not.
And this does not have to be in line with a coreference resolution system.

In order to ensure fair comparison, all singletons are excluded from both key and response files by default.
Nevertheless, evaluation with singletons included may be turned on by the `-s, --keep-singletons` option.

## Shared Tasks

### CRAC 2022

[CRAC 2022 Shared Task on Multilingual Coreference Resolution](https://ufal.mff.cuni.cz/corefud/crac22) used this scorer in version 1.0 (and some features of the version 1.1 for the Findings paper) as an official scorer to evaluate the submissions.
The primary score to rank the submissions was the macro-average of the CoNLL F1 of identity coreference calculated for each dataset.
It was computed without singletons using partial matching.
Split antecedents, bridging and other anaphoric relations were not included into the evaluation.

### CRAC 2023

[CRAC 2023 Shared Task on Multilingual Coreference Resolution](https://ufal.mff.cuni.cz/corefud/crac23) uses this scorer in version 1.1 as an official scorer to evaluate the submissions.
The primary score to rank the submissions is the macro-average of the CoNLL F1 of identity coreference calculated for each dataset, computed without singletons using head matching.
Split antecedents, bridging and other anaphoric relations are not included into the evaluation.

### CRAC 2024

[CRAC 2024 Shared Task on Multilingual Coreference Resolution](https://ufal.mff.cuni.cz/corefud/crac24) uses this scorer in version 1.2 as an official scorer to evaluate the submissions.
The primary score to rank the submissions is the macro-average of the CoNLL F1 of identity coreference calculated for each dataset, computed without singletons using head matching and aligning zero by their dependency.
Split antecedents, bridging and other anaphoric relations are not included into the evaluation.

## Change Log

* 2024-05-10 v1.2
  * using a modified version of the UA scorer 2.0 as the backbone
  * key and response zeros don't have to be present at the same positions; instead the `linear` and `dependent` strategy can be alternatively used to align zeros
* 2023-02-15 v1.1
  * mention overlap score added
  * anaphor-decomposable score for zeros added
  * head match added
* 2022-05-03 v1.0
  * initial version

## Authors

* Michal Novák, Charles University, Prague, Czech Republic, mnovak@ufal.mff.cuni.cz
* Juntao Yu, Queen Mary University of London, juntao.cn@gmail.com
* Martin Popel, Charles University, Prague, Czech Republic, popel@ufal.mff.cuni.cz
* Yilun Zhu, Georgetown University, Washington D.C., USA, yz565@georgetown.edu

The Universal Anaphora scorer has been developed by:

* Juntao Yu, Queen Mary University of London, juntao.cn@gmail.com
* Nafise Moosavi, UKP, TU Darmstadt, ns.moosavi@gmail.com
* Silviu Paun, Queen Mary University of London, spaun3691@gmail.com
* Massimo Poesio, Queen Mary University of London, poesio@gmail.com
* Michal Novák, Charles University, Prague, Czech Republic, mnovak@ufal.mff.cuni.cz
* Martin Popel, Charles University, Prague, Czech Republic, popel@ufal.mff.cuni.cz
* Yilun Zhu, Georgetown University, Washington D.C., USA, yz565@georgetown.edu

The original reference Coreference Scorer (CoNLL 2012 scorer) was developed by:

*  Emili Sapena, Universitat Politècnica de Catalunya, http://www.lsi.upc.edu/~esapena, esapena@lsi.upc.edu
*  Sameer Pradhan, https://cemantix.org, pradhan@cemantix.org
*  Sebastian Martschat, sebastian.martschat@h-its.org
*  Xiaoqiang Luo, xql@google.com

## References
  
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

  Juntao Yu, Michal Novák, Abdulrahman Aloraini, Nafise Sadat Moosavi, Silviu Paun, Sameer Pradhan, and Massimo Poesio. 2023.
  The Universal Anaphora Scorer 2.0.
  In Proceedings of the 15th International Conference on Computational Semantics, pages 183–194.

  Zdeněk Žabokrtský, Miloslav Konopík, Anna Nedoluzhko, Michal Novák, Maciej Ogrodniczuk, Martin Popel, Ondřej Pražák, Jakub Sido, Daniel Zeman, and Yilun Zhu. 2022.
  Findings of the Shared Task on Multilingual Coreference Resolution.
  In Proceedings of the CRAC 2022 Shared Task on Multilingual Coreference Resolution, pages 1–17.
