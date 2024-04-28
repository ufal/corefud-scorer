import argparse
import importlib
uascorer = importlib.import_module("ua-scorer")

__author__ = 'michnov'

def parse_arguments():
    argparser = argparse.ArgumentParser(description="Coreference scorer for documents in CorefUD 1.0 scheme")
    argparser.add_argument('key_file', type=str, help='path to the key/reference file')
    argparser.add_argument('sys_file', type=str, help='path to the system/response file')
    argparser.add_argument('-m', '--metrics', choices=['all', 'lea', 'muc', 'bcub', 'ceafe', 'ceafm', 'blanc', 'mor', 'zero'], nargs='*', default=['all'], help='metrics to be used for evaluation')
    argparser.add_argument('-s', '--keep-singletons', action='store_true', default=False, help='evaluate also singletons; ignored otherwise')
    argparser.add_argument('-a', '--match', type=str, choices=["exact", "partial", "head"], default="head", help='choose the type of mention matching: exact, partial, head')
    argparser.add_argument('-x', '--exact-match', action='store_true', default=False, help='use exact match for matching key and system mentions; overrides the value chosen by --match|-t')
    args = argparser.parse_args()
    return vars(args)

def corefud_to_ua_args(corefud_args):
    # arguments to copy with no change
    ua_args = {k:v for k, v in corefud_args.items() if k in ["key_file", "sys_file", "metrics", "keep_singletons"]}
    # arguments to be slightly modified
    if corefud_args["exact_match"]:
        ua_args["match"] = "exact"
    elif corefud_args["match"] == "partial":
        ua_args["match"] = "partial-corefud"
    else:
        ua_args["match"] = corefud_args["match"]
    # new arguments
    ua_args["format"] = "corefud"
    ua_args["keep_split_antecedents"] = False
    ua_args["evaluate_discourse_deixis"] = False
    ua_args["only_split_antecedent"] = False
    ua_args["allow_boundary_crossing"] = False
    ua_args["np_only"] = False
    ua_args["remove_nested_mentions"] = False
    ua_args["shared_task"] = None
    return ua_args

def main():
    corefud_args = parse_arguments()
    ua_args = corefud_to_ua_args(corefud_args)
    uascorer.process_arguments(ua_args)
    uascorer.evaluate(ua_args)

if __name__ == "__main__":
    main()
