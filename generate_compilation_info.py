#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Generate information data JSON file"""
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         generate_info.py
#  @date         July, 2021
#  @version      0.2.1
#  @brief        Generate information data JSON file
#
#  This script ...
#
#  @usage
#  python generate_info.py \
#   --file README.md \
#   --git ./ \
#   --print \
#   --pretty \
#   --save \
#   --output compilation-info.json \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   -f, --file      Path to file for binary section
#   -g, --git       Path to git repo
#   -o, --output    Path to output file containing info
#   --pretty        Print collected info to stdout in human readable format
#   --print         Print collected (JSON) info to stdout
#   -s, --save      Save collected informations to file specified with
#                   '--output' or '-o'
#
#   -d, --debug     Flag, Output logger messages to stderr (default: False)
#   -v, --verbose   Verbosity level (default: None), sets debug flag to True
#                   '-v3' or '-vvvv' == INFO
#
# ----------------------------------------------------------------------------

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright by brainelectronics, ALL RIGHTS RESERVED"
__credits__ = ["Jonas Scharpf"]
__version__ = "0.2.1"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Beta"

import argparse
import json

# custom imports
from compilation_info_generator import CompilationInfoGenerator
from module_helper import ModuleHelper, VAction


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.

    :raise      argparse.ArgumentError  asdf
    :return:    argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Generate compilation informations
    """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

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
    parser.add_argument('-g', '--git',
                        dest='git_path',
                        required=True,
                        type=lambda x: ModuleHelper.parser_valid_dir(parser,
                                                                     x),
                        help='Path to local git repo')

    parser.add_argument('-f', '--file',
                        dest='file_path',
                        required=True,
                        type=lambda x: ModuleHelper.parser_valid_file(parser,
                                                                      x),
                        help='Path to file')

    parser.add_argument('-o', '--output',
                        dest='output_file',
                        required=False,
                        help='Path to output file containing info')

    parser.add_argument('--pretty',
                        dest='print_pretty',
                        action='store_true',
                        help='Print collected info to stdout in human readable'
                        'format')

    parser.add_argument('--print',
                        dest='print_result',
                        action='store_true',
                        help='Print collected (JSON) info to stdout')

    parser.add_argument('-s', '--save',
                        dest='save_info',
                        action='store_true',
                        help='Save collected informations to file specified '
                        'with --output or -o')

    parsed_args = parser.parse_args()

    return parsed_args


if __name__ == '__main__':
    helper = ModuleHelper(quiet=True)

    logger = helper.create_logger(__name__)
    cig_logger = helper.create_logger("CompilationInfoGenerator")

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    helper.set_logger_verbose_level(logger=logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)
    helper.set_logger_verbose_level(logger=cig_logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)

    # log the provided arguments
    logger.debug(args)

    # take CLI parameters
    git_path = args.git_path
    file_path = args.file_path
    output_file = args.output_file
    save_info = args.save_info
    print_result = args.print_result
    print_pretty = args.print_pretty

    # create objects
    cig = CompilationInfoGenerator(logger=cig_logger, quiet=not args.debug)

    # create and get the info dict
    cig.create_info_dict(git_path=git_path, file_path=file_path)
    info_dict = cig.get_info_dict()
    logger.debug('Info dict: {}'.format(info_dict))

    if save_info:
        if output_file is not None:
            result = cig.save_json_file(path=output_file,
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
