#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Generate structure information data JSON file"""
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         generate_structure_info.py
#  @date         July, 2021
#  @version      0.2.1
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
#   --output structure-info.json \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   -o, --output    Path to output file containing info
#   --pretty        Print collected info to stdout in human readable format
#   --print         Print collected (JSON) info to stdout
#   -r, --root      Path to root of folder to create structure for
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
from module_helper.module_helper import ModuleHelper
from structure_info_generator.structure_info_generator \
    import StructureInfoGenerator


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
        if values is None:
            pass
            # do not increment here, so '-v' will use highest log level
        else:
            try:
                self.values = int(values)
            except ValueError:
                self.values = values.count('v')  # do not count the first '-v'
        setattr(args, self.dest, self.values)


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.

    :raise      argparse.ArgumentError  asdf
    :return:    argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Generate structure informations
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
    parser.add_argument('-r', '--root',
                        dest='root_path',
                        required=True,
                        type=lambda x: ModuleHelper.parser_valid_dir(parser,
                                                                     x),
                        help='Path to root dir for structure generation')

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
    sig_logger = helper.create_logger("StructureInfoGenerator")

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    helper.set_logger_verbose_level(logger=logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)
    helper.set_logger_verbose_level(logger=sig_logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)

    # log the provided arguments
    logger.debug(args)

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
