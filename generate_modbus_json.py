#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# ----------------------------------------------------------------------------
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         generate_modbus_json.py
#  @date         December, 2021
#  @version      0.4.0
#  @brief        Generate a JSON file from a modbus register header file
#
#  @note         No numbers are allowed in the register name
#
#  @usage
#  python3 generate_modbus_json.py \
#   --input example/modbusRegisters.h \
#   --print \
#   --pretty \
#   --save \
#   --output modbusRegisters.json \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   --input         Header file of modbus registers
#   --output        Path to output folder or file for JSON file, default name
#                   is set as 'registers.json' if path to folder is provided
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
__version__ = "0.4.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "info@brainelectronics.de"
__status__ = "Development"

import argparse
import json
import logging
from pathlib import Path
import re

# custom imports
from module_helper.module_helper import ModuleHelper


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

    :raise  argparse.ArgumentError
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Generate JSON of modbus register header file
    """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # default arguments
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Output logger messages to stderr')
    parser.add_argument('-v', "--verbose",
                        nargs='?',
                        action=VAction,
                        dest='verbose',
                        help='Set level of verbosity')

    # specific arguments
    parser.add_argument('--input',
                        required=True,
                        type=lambda x: ModuleHelper.parser_valid_file(parser,
                                                                      x),
                        help='Header file of modbus registers')

    parser.add_argument('--output',
                        required=False,
                        help='Path to output folder or file for JSON file, '
                        'default name is set as "registers.json" if path is '
                        'provided')

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


def extract_defined_registers(file_path: str, logger: logging.Logger) -> dict:
    """
    Extract all registers, their unit, description, length and range from the
    header file and return a dict of that informations

    :param      file_path:  The path to the input modbus register file
    :type       file_path:  string
    :param      logger:     The logger
    :type       logger:     logger object

    :returns:   Dictionary of extracted informations
    :rtype:     dictionary
    """
    # create dict of register names
    registers_dict = dict()
    registers_dict['COILS'] = dict()
    registers_dict['HREGS'] = dict()
    registers_dict['ISTS'] = dict()
    registers_dict['IREGS'] = dict()
    registers_dict['META'] = dict()

    # read all lines of the file
    file_lines = []
    with open(str(file_path), 'r') as file:
        file_lines = file.read().splitlines()

    # extract lines of register definition or addtional comment only
    definition_lines = []
    for idx, line in enumerate(file_lines):
        if idx < 10:
            if 'Modified on ' in line:
                modified_date = line.split('Modified on ')[1]
                logger.debug('Modified: {}'.format(modified_date))
                registers_dict['META']['modified'] = modified_date

            if ('Created ' in line) and (' on ' in line):
                creation_date = line.split(' on ')[1]
                logger.debug('Created: {}'.format(creation_date))
                registers_dict['META']['created'] = creation_date

        # use only lines with a comment for register extraction
        if '//<' in line:
            definition_lines.append(line)

    # iterate all register lines
    for idx, line in enumerate(definition_lines):
        # take only line of register definiton
        if line.startswith('#define '):
            # get the register name which must be given in capital letters and
            # must be more or equal to 3 characters, maybe with numbers in it
            register_name = re.findall(r'[A-Z_0-9]{3,}', line)[0]

            # get the part without the register name
            tmp_part = line.split(register_name)[-1]
            # get the first number with any length, which shall be the register
            register_register = re.findall(r'\d+', tmp_part)[0]

            # loop over all additional registers if any available in the next
            # line
            i = 1
            nextelem = definition_lines[(idx + i) % len(definition_lines)]
            while not nextelem.startswith('#define '):
                i += 1
                nextelem = definition_lines[(idx + i) % len(definition_lines)]

            # do not count the start register itself as it is repeated
            if i > 1:
                i -= 1

            # get the description of that register after the doxygen comment
            try:
                register_description = line.split('//<')[1].lstrip()
            except IndexError:
                register_description = ''

            # try to get unit of register description provided as '[something]'
            register_unit_list = re.findall(r'\[(.*?)\]', register_description)
            register_range = ''
            register_unit = ''
            # check for any matches
            if register_unit_list:
                # check for range info, like [0, 4095]
                if ',' in register_unit_list[0]:
                    register_range = register_unit_list[0]
                else:
                    # take it as unit
                    register_unit = register_unit_list[0]

            # fill this registers dictionaly with content
            this_register_dict = dict()
            this_register_dict['register'] = int(register_register)
            this_register_dict['len'] = int(i)
            this_register_dict['description'] = register_description
            this_register_dict['range'] = register_range
            this_register_dict['unit'] = register_unit

            # add this register dict to the proper section of the overall dict
            if register_name.endswith('_COIL'):
                registers_dict['COILS'][register_name] = this_register_dict
            elif register_name.endswith('_HREG'):
                registers_dict['HREGS'][register_name] = this_register_dict
            elif register_name.endswith('_ISTS'):
                registers_dict['ISTS'][register_name] = this_register_dict
            elif register_name.endswith('_IREG'):
                registers_dict['IREGS'][register_name] = this_register_dict

    # logger.debug(json.dumps(registers_dict, indent=4, sort_keys=False))
    return registers_dict


if __name__ == '__main__':
    helper = ModuleHelper(quiet=True)

    logger = helper.create_logger(__name__)

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    helper.set_logger_verbose_level(logger=logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)

    # log the provided arguments
    logger.debug(args)

    # take CLI parameters
    input_file_path = Path(args.input)
    output_arg = args.output
    save_info = args.save_info
    print_result = args.print_result
    print_pretty = args.print_pretty

    # set fallback name of output file
    file_name = 'registers.json'
    output_path = None

    file_check_result = ModuleHelper.check_file(input_file_path, '.h')
    logger.debug('Input file check result: {}'.format(file_check_result))

    if output_arg:
        if ModuleHelper.check_folder(output_arg):
            output_path = Path(output_arg) / file_name
        else:
            if output_arg.endswith('.json'):
                output_path = Path(output_arg)
            else:
                logger.warning('Unsupported file type, using default')
                output_path = Path(output_arg).with_suffix('.json')

    if output_path is None:
        logger.info('No output specified, using same directory as input file')
        output_path = input_file_path.parent / file_name

    logger.debug('Save output to {}'.format(output_path))
    registers_dict = dict()

    if file_check_result:
        registers_dict = extract_defined_registers(file_path=input_file_path,
                                                   logger=logger)

        if save_info:
            # do not sort keys to get JSON file in same order as input file
            result = helper.save_json_file(path=output_path,
                                           content=registers_dict,
                                           pretty=print_pretty,
                                           sort_keys=False)

            logger.debug('Result of saving info as JSON: {}'.format(result))

        # do print as last step
        if print_result:
            # do not sort keys to get JSON file in same order as input file
            if print_pretty:
                print(json.dumps(registers_dict, indent=4))
            else:
                print(json.dumps(registers_dict))
