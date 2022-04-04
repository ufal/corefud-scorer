# CorefUD scorer

## About

CorefUD scorer is a scorer for coreference and anaphoric relations that are harmonized under the same scheme defined by the CorefUD 1.0 project.

The scorer builds on the following projects:

- original Coreference scorer [Pradhan et al, 2014] developed for scoring the CoNLL 2011 and 2012 shared tasks using the OntoNotes corpus [Pradhan et al, 2011; Pradhan et al, 2012]: https://github.com/conll/reference-coreference-scorers
- its reimplementation in Python by Moosavi, also extended to compute the LEA score [Moosavi and Strube, 2016] and to evaluate non-referring expressions evaluation and cover singletons [Poesio et al, 2018]: https://github.com/ns-moosavi/LEA-coreference-scorer
- UA scorer, which is an adaptation of the previous two scorers to the Universal Anaphora guidelines by Juntao Yu (see TODO), extended to evaluate also bridging, discourse deixis and split antecedents

Unlike any of the previous scorers, CorefUD scorer is adjusted to process and correctly evaluate also non-contiguous mentions.

It supports both exact match and partial match of mentions. Partial match is an alternative to minimum span evaluation by the UA scorer. In addtion, the evaluation can be run with singletons taken into account.

For the time being, the scorer is able to evaluate coreference only, excluding split antecedents, bridging and other relations.

## Usage

Scorer can be run with the following command:

`python corefud-scorer.py` \[OPTIONS...\] \[key\] \[system\]`

where `key` and `system` are the location of the key (gold) and system (predicted) files.

Options:

- `-m, --metrics METRIC[ METRIC]\*`: select specific metrics to be evaluated; default: `all`; possible values: `[muc|bcub|ceafe|ceafm|blanc|lea|all]`
- `-s, --keep-singletons`: evaluate also singletons; otherwise any singletons in the key or system files are ignored
- `-x, --exact-match`: mentions in the key and sys files are matched only if they are exactly the same; otherwise the partial match is applied

## Details on Evaluation Metrics and Evaluation Modes

By default, the CorefUD scorer calculates all evaluation metrics using partial match and ignoring all singletons.

### Evaluation Metrics

Evaluation using any of the following metrics is supported:
- `The above command reports MUC [Vilain et al, 1995], B-cubed [Bagga and Baldwin, 1998], CEAF [Luo et al., 2005], BLANC [Recasens and Hovy, 2011], LEA [Moosavi and Strube, 2016] and the averaged CoNLL score (the average of the F1 values of MUC, B-cubed and CEAFe) [Denis and Baldridge, 2009a; Pradhan et al., 2014].

You can also only select specific metrics by including one or some of the `muc`, `bcub`, `ceafe`, `ceafm`, `blanc` and `lea` options in the input arguments.
For instance, the following command only reports the CEAFe and LEA scores:

`python ua-scorer.py key system ceafe lea`

The first and second arguments after `ua-scorer.py` have to be 'key' and 'system', respectively. The order of the other options is arbitrary.

