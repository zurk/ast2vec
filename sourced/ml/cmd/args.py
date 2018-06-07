import argparse
import json
import logging
from pathlib import Path
from typing import Optional
import sys


from sourced.ml import extractors
from sourced.ml.transformers import BOWWriter, Moder
from sourced.ml.utils import add_engine_args


DEFAULT_FILTER_ARG = "**/*.asdf"


class ArgumentDefaultsHelpFormatterNoNone(argparse.ArgumentDefaultsHelpFormatter):
    """
    Pretty formatter of help message for arguments.
    It adds default value to the end if it is not None.
    """
    def _get_help_string(self, action):
        if action.default is None:
            return action.help
        return super()._get_help_string(action)


def handle_input_arg(input_arg: str,
                     filter_arg: Optional[str] = DEFAULT_FILTER_ARG,
                     log: Optional[logging.Logger] = None):
    """
    Process input arguments and return an iterator over input files.

    :param input_arg: Directory path to scan or `-` to get file paths from stdin
    :param filter_arg: File name glob selector for input directory. Ignored if `input_arg` is \
        equal to `-`.
    :param log: Logger if you want to log handling process.
    :return: an iterator over input files.
    """
    log = log.info if log else (lambda *x: None)
    if input_arg == "-":
        log("Reading file paths from stdin.")
        for line in sys.stdin:
            yield line.strip()
    else:
        log("Scanning %s", input_arg)
        if filter_arg:
            for path in Path(input_arg).glob(filter_arg):
                yield str(path)


def add_repartitioner_arg(my_parser: argparse.ArgumentParser):
    my_parser.add_argument(
        "--partitions", required=False, default=None, type=int,
        help="Performs data repartition to specified number of partitions. "
             "Nothing happens if parameter is unset.")
    my_parser.add_argument(
        "--shuffle", action="store_true",
        help="Use RDD.repartition() instead of RDD.coalesce().")


def add_split_stem_arg(my_parser: argparse.ArgumentParser):
    my_parser.add_argument(
        "--split", action="store_true",
        help="Split identifiers based on special characters or case changes. For example split "
             "'ThisIs_token' to ['this', 'is', 'token'].")


def add_vocabulary_size_arg(my_parser: argparse.ArgumentParser):
    my_parser.add_argument(
        "-v", "--vocabulary-size", default=10000000, type=int,
        help="The maximum vocabulary size.")


def add_min_docfreq(my_parser: argparse.ArgumentParser):
    my_parser.add_argument(
        "--min-docfreq", default=1, type=int,
        help="The minimum document frequency of each feature.")


def add_repo2_args(my_parser: argparse.ArgumentParser, default_packages=None):
    my_parser.add_argument(
        "-r", "--repositories", required=True,
        help="The path to the repositories.")
    my_parser.add_argument(
        "--parquet", action="store_true", help="Use Parquet files as input.")
    my_parser.add_argument(
        "--graph", help="Write the tree in Graphviz format to this file.")
    # TODO(zurk): get languages from bblfsh directly as soon as
    # https://github.com/bblfsh/client-scala/issues/98 resolved
    languages = ["Java", "Python", "Go", "JavaScript", "TypeScript", "Ruby", "Bash", "Php"]
    my_parser.add_argument(
        "-l", "--languages", nargs="+", choices=languages, default=languages,
        help="The programming languages to analyse.")
    add_engine_args(my_parser, default_packages)


def add_df_args(my_parser: argparse.ArgumentParser, required=True):
    my_parser.add_argument(
        "--min-docfreq", default=1, type=int,
        help="The minimum document frequency of each feature.")
    df_group = my_parser.add_mutually_exclusive_group(required=required)
    df_group.add_argument(
        "--docfreq-out", help="Path to save generated DocumentFrequencies model.")
    df_group.add_argument(
        "--docfreq-in", help="Path to load pre-generated DocumentFrequencies model.")
    add_vocabulary_size_arg(my_parser)


def add_feature_args(my_parser: argparse.ArgumentParser, required=True):
    my_parser.add_argument("-x", "--mode", choices=Moder.Options.__all__,
                           default="file", help="What to select for analysis.")
    my_parser.add_argument(
        "--quant", help="[OUT] The path to the QuantizationLevels model.")
    my_parser.add_argument(
        "-f", "--feature", nargs="+",
        choices=[ex.NAME for ex in extractors.__extractors__.values()],
        required=required, help="The feature extraction scheme to apply.")
    for ex in extractors.__extractors__.values():
        for opt, val in ex.OPTS.items():
            my_parser.add_argument(
                "--%s-%s" % (ex.NAME, opt), default=val, type=json.loads,
                help="%s's kwarg" % ex.__name__)


def add_bow_args(my_parser: argparse.ArgumentParser):
    my_parser.add_argument(
        "--bow", required=True, help="[OUT] The path to the Bag-Of-Words model.")
    my_parser.add_argument(
        "--batch", default=BOWWriter.DEFAULT_CHUNK_SIZE, type=int,
        help="The maximum size of a single BOW file in bytes.")


def add_filter_arg(my_parser: argparse.ArgumentParser):
    my_parser.add_argument(
        "--filter", default=DEFAULT_FILTER_ARG, help="File name glob selector.")
