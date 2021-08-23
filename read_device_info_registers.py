#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Read Modbus device register informations based on JSON registers file"""
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         read_device_info_registers.py
#  @date         July, 2021
#  @version      0.4.0
#  @brief        Read all registers via RTU modbus or external IP
#
#  @required     pymodbus 2.3.0 or higher
#
#  @usage
#  python3 read_device_info_registers.py \
#   --file=example/modbusRegisters.json \
#   --connection=rtu \
#   --address=/dev/tty.wchusbserial1420 \
#   --unit=10 \
#   --baudrate=19200 \
#   --print \
#   --pretty \
#   --save \
#   --output info.json \
#   -v4 -d
#
#  python3 read_device_info_registers.py \
#   --file=example/modbusRegisters-phoenix.json \
#   --connection=tcp \
#   --address=192.168.0.8 \
#   --port=180 \
#   --print \
#   --pretty \
#   --save \
#   --output info.json \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   -a, --address   Address to connect to, like 192.168.0.8 or
#                   /dev/tty.SLAB_USBtoUART
#   --baudrate      Baudrate of RTU connection
#   -c, --connection    Type of Modbus connection, ['tcp', 'rtu']
#   -f, --file      Path to Modbus registers file
#   -o, --output    Path to output file containing info
#   -p, --port      Port of connection, not required for RTU Serial
#   --pretty        Print collected info to stdout in human readable format
#   --print         Print collected (JSON) info to stdout
#   -s, --save      Save collected informations to file specified with
#                   '--output' or '-o'
#   -u, --unit      Unit of connection
#                   Tobi Test 1, Serial 10, Phoenix 180, ESP 255
#   --validate      Validate received data with expected data
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
__status__ = "Beta"

import argparse
import json

# custom imports
from modbus_wrapper.modbus_wrapper import ModbusWrapper
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
            # do not increment here, so '-v' will use highest log level
            pass
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
    Read Modbus register
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
    parser.add_argument('-a',
                        '--address',
                        help=('Address of connection, like 192.168.0.8 or '
                              '/dev/tty.SLAB_USBtoUART'),
                        nargs='?',
                        required=True)

    parser.add_argument('--baudrate',
                        help='Baudrate of RTU connection',
                        default=9600,
                        type=int,
                        required=False)

    parser.add_argument('-c',
                        '--connection',
                        help='Type of Modbus connection',
                        nargs='?',
                        default="tcp",
                        choices=['tcp', 'rtu'],
                        required=True)

    parser.add_argument('-f',
                        '--file',
                        help='Path to Modbus registers file',
                        nargs='?',
                        default="modbusRegisters.json",
                        type=lambda x: ModuleHelper.parser_valid_file(parser,
                                                                      x),
                        required=True)

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

    parser.add_argument('-p',
                        '--port',
                        help='Port of connection, not required for RTU Serial',
                        default=502,
                        type=int,
                        required=False)

    parser.add_argument('-s', '--save',
                        dest='save_info',
                        action='store_true',
                        help='Save collected informations to file specified '
                        'with --output or -o')

    parser.add_argument('-u',
                        '--unit',
                        help=('Unit of connection, '
                              'Phoenix 180, Tobi Test 1, ESP 255, Serial 10'),
                        default=180,
                        type=int,
                        required=False)

    parser.add_argument('--validate',
                        help='Validate received data with expected data',
                        required=False,
                        action='store_true')

    parsed_args = parser.parse_args()

    return parsed_args


if __name__ == "__main__":
    helper = ModuleHelper(quiet=True)

    logger = helper.create_logger(__name__)
    register_logger = helper.create_logger("Register Logger")

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    helper.set_logger_verbose_level(logger=logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)
    helper.set_logger_verbose_level(logger=register_logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)

    # log the provided arguments
    logger.debug(args)

    # take CLI parameters
    port = args.port
    unit = args.unit
    baudrate = args.baudrate
    output_file = args.output_file
    save_info = args.save_info
    print_result = args.print_result
    print_pretty = args.print_pretty

    # create objects
    mb = ModbusWrapper(logger=register_logger, quiet=not args.debug)

    # create and get the info dict
    read_content = mb.read_all_registers(device_type=args.connection,
                                         address=args.address,
                                         port=port,
                                         unit=unit,
                                         baudrate=baudrate,
                                         check_expectation=args.validate,
                                         file=args.file)

    now = helper.get_unix_timestamp()
    timestring = helper.format_timestamp(timestamp=now,
                                         format="%m-%d-%Y %H:%M:%S")
    read_content['TIMESTAMP'] = timestring
    logger.debug('Register content: {}'.format(read_content))

    if save_info:
        if output_file is not None:
            # do not sort keys to get JSON file in same order as input file
            result = mb.save_json_file(path=output_file,
                                       content=read_content,
                                       pretty=print_pretty,
                                       sort_keys=False)
            logger.debug('Result of saving info as JSON: {}'.format(result))
        else:
            logger.warning('Can not save to not specified file')

    # do print as last step
    if print_result:
        # do not sort keys to get JSON file in same order as input file
        if print_pretty:
            print(json.dumps(read_content, indent=4))
        else:
            print(json.dumps(read_content))
