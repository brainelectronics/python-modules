#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Generate structure information data JSON file"""
#
#  @author       Jonas Scharpf (jonas.scharpf@hilti.com) SCHAJONAS
#  @file         generate_structure_info.py
#  @date         June, 2021
#  @version      0.1.1
#  @brief        Generate structure information data JSON file
#
#  This script ...
#
#  @usage
#  python generate_structure_info.py \
#   --root path-to-root-of-structure \
#   --print \
#   --pretty \
#   --save \
#   --output info.json \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   -o, --output    Path to output file containing info
#   --pretty        Print collected info to stdout in human readable format
#   -p, --print     Print JSON to stdout
#   -r, --root      Path to root of folder to create structure for
#   -s, --save      Save collected informations to file
#
#   -d, --debug     Flag, Output logger messages to stderr (default: False)
#   -v, --verbose   Verbosity level (default: None), sets debug flag to True
#                   '-v3' or '-vvvv' == INFO
#
# ----------------------------------------------------------------------------

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright by brainelectronics, ALL RIGHTS RESERVED"
__credits__ = ["Jonas Scharpf"]
__version__ = "0.1.1"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Beta"

import argparse
import json
import logging
import os
from pathlib import Path
import sys

# custom imports
from structure_info_generator.structure_info_generator import StructureInfoGenerator


class VAction(argparse.Action):
    """docstring for VAction"""
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(VAction, self).__init__(option_strings, dest, nargs, const,
                                      default, type, choices, required,
                                      help, metavar)
        self.values = 0

    def __call__(self, parser, args, values, option_string=None):
        """Actual call or action to perform"""
        # print('values: {v!r}'.format(v=values))
        if values is None:
            pass
            # do not increment here, so '-v' will use highest log level
            # self.values += 1
        else:
            try:
                self.values = int(values)
            except ValueError:
                # self.values = values.count('v')+1
                self.values = values.count('v')  # do not count the first '-v'
        setattr(args, self.dest, self.values)


def create_logger(logger_name: str = None) -> logging.Logger:
    """
    Create a logger.

    :param      logger_name:  The logger name
    :type       logger_name:  str, optional

    :returns:   Configured logger
    :rtype:     logging.Logger
    """
    custom_format = '[%(asctime)s] [%(levelname)-8s] [%(filename)-15s @'\
                    ' %(funcName)-15s:%(lineno)4s] %(message)s'

    # configure logging
    logging.basicConfig(level=logging.INFO,
                        format=custom_format,
                        stream=sys.stdout)

    if logger_name and (isinstance(logger_name, str)):
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(__name__)

    # set the logger level to DEBUG if specified differently
    logger.setLevel(logging.DEBUG)

    return logger


def is_valid_file(parser: argparse.ArgumentParser, arg: str) -> str:
    """
    Determine whether file exists.

    :param      parser:                 The parser
    :type       parser:                 parser object
    :param      arg:                    The file to check
    :type       arg:                    str
    :raise      argparse.ArgumentError: Argument is not a file

    :returns:   Input file path, parser error is thrown otherwise.
    :rtype:     str
    """
    if not Path(arg).is_file():
        parser.error("The file {} does not exist!".format(arg))
    else:
        return arg


def is_valid_dir(parser: argparse.ArgumentParser, arg: str) -> str:
    """
    Determine whether directory exists.

    :param      parser:                 The parser
    :type       parser:                 parser object
    :param      arg:                    The directory to check
    :type       arg:                    str
    :raise      argparse.ArgumentError: Argument is not a directory

    :returns:   Input directory path, parser error is thrown otherwise.
    :rtype:     str
    """
    if not Path(arg).is_dir():
        parser.error("The directory {} does not exist!".format(arg))
    else:
        return arg


def parse_arguments():
    """
    Parse CLI arguments.

    :raise      argparse.ArgumentError  asdf
    :return:    argparse object
    """
    parser = argparse.ArgumentParser(description="Generate informations",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # default arguments
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Output logger messages to stderr')
    parser.add_argument('-v', '--verbose',
                        nargs='?',
                        action=VAction,
                        dest='verbose',
                        help='Set level of verbosity')

    # specific arguments
    parser.add_argument('-r', '--root',
                        dest='root_path',
                        required=True,
                        help='Path to root dir for structure generation',
                        type=lambda x: is_valid_dir(parser, x))

    parser.add_argument('-o', '--output',
                        dest='output_file',
                        required=False,
                        help='Path to output file containing info')

    parser.add_argument('--pretty',
                        dest='print_pretty',
                        action='store_true',
                        help='Print collected info to stdout in human readable'
                        'format')

    parser.add_argument('-p', '--print',
                        dest='print_result',
                        action='store_true',
                        help='Print collected info to stdout')

    parser.add_argument('-s', '--save',
                        dest='save_info',
                        action='store_true',
                        help='Save collected informations to file specified'
                        'Specified with --output or -o')

    parsed_args = parser.parse_args()

    return parsed_args


if __name__ == '__main__':
    logger = create_logger(__name__)
    sig_logger = create_logger("StructureInfoGenerator")

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    verbose_level = args.verbose
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_LEVELS = LOG_LEVELS[::-1]

    if verbose_level is None:
        if not args.debug:
            # disable the logger of this file and the ReleaseInfoGenerator
            logger.disabled = True
            sig_logger.disabled = True
    else:
        log_level = min(len(LOG_LEVELS) - 1, max(verbose_level, 0))
        log_level_name = LOG_LEVELS[log_level]

        # set the level of the logger of this file and the ReleaseInfoGenerator
        logger.setLevel(log_level_name)
        sig_logger.setLevel(log_level_name)

    # take CLI parameters
    root_path = args.root_path
    output_file = args.output_file
    save_info = args.save_info
    print_result = args.print_result
    print_pretty = args.print_pretty

    # create objects
    sig = StructureInfoGenerator(logger=sig_logger, quiet=not args.debug)

    # create and get the info dict
    sig.create_info_dict(root_path=root_path)
    info_dict = sig.get_info_dict()
    logger.debug('Info dict: {}'.format(info_dict))

    if save_info:
        if output_file is not None:
            result = sig.save_json_file(path=output_file,
                                        content=info_dict,
                                        pretty=print_pretty)
            logger.debug('Result of saving info as JSON: {}'.format(result))
        else:
            logger.warning('Can not save to not specified file')

    # do print as last step
    if print_result:
        if print_pretty:
            print(json.dumps(info_dict, indent=4, sort_keys=True))
        else:
            print(json.dumps(info_dict, sort_keys=True))
