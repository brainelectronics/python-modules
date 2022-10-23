#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Set Modbus device register informations based on JSON registers file"""
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         write_device_info_registers.py
#  @date         October, 2022
#  @version      0.3.0
#  @brief        Set all registers via RTU modbus or external IP
#
#  @required     be-modbus-wrapper>=0.1.0,<1
#
#  @usage
#  python3 write_device_info_registers.py \
#   --file=example/set-modbusRegisters-MyEVSE.json \
#   --connection=rtu \
#   --address=/dev/tty.wchusbserial1420 \
#   --unit=10 \
#   --baudrate=19200 \
#   --print \
#   --pretty \
#   -v4 -d
#
#  python3 write_device_info_registers.py \
#   --file=example/set-modbusRegisters-MyEVSE.json \
#   --connection=tcp \
#   --address=192.168.0.8 \
#   --port=180 \
#   --print \
#   --pretty \
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
#   -p, --port      Port of connection, not required for RTU Serial
#   --pretty        Print collected info to stdout in human readable format
#   --print         Print collected (JSON) info to stdout
#   -u, --unit      Unit of connection
#                   Tobi Test 1, Serial 10, Phoenix 180, ESP 255
#
#   -d, --debug     Flag, Output logger messages to stderr (default: False)
#   -v, --verbose   Verbosity level (default: None), sets debug flag to True
#                   '-v3' or '-vvvv' == INFO
#
# ----------------------------------------------------------------------------

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright by brainelectronics, ALL RIGHTS RESERVED"
__credits__ = ["Jonas Scharpf"]
__version__ = "0.3.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "info@brainelectronics.de"
__status__ = "Beta"

import argparse
import json

# custom imports
from be_helpers import ModuleHelper
from be_modbus_wrapper import ModbusWrapper


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
    parser.add_argument('-v',
                        default=0,
                        action='count',
                        dest='verbose',
                        help='Set level of verbosity')
    parser.add_argument('--verbose',
                        nargs='?',
                        type=int,
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

    parser.add_argument('-u',
                        '--unit',
                        help=('Unit of connection, '
                              'Phoenix 180, Tobi Test 1, ESP 255, Serial 10'),
                        default=180,
                        type=int,
                        required=False)

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
    print_result = args.print_result
    print_pretty = args.print_pretty

    # create objects
    mb = ModbusWrapper(logger=register_logger, quiet=not args.debug)

    # open connection to device
    result = mb.setup_connection(device_type=args.connection,
                                 address=args.address,
                                 port=port,
                                 unit=unit,
                                 baudrate=baudrate)
    if result is False:
        logger.error('Failed to setup connection with {device_type} device '
                     'with bus ID {unit} at {address}:{port}'.
                     format(device_type=args.connection,
                            unit=unit,
                            address=args.address,
                            port=port))
        exit(-1)

    # open connection to device
    mb.connect = True

    # create and get the info dict
    failed_registers = mb.write_all_registers(file=args.file)

    if len(failed_registers):
        now = helper.get_unix_timestamp()
        timestring = helper.format_timestamp(timestamp=now,
                                             format="%m-%d-%Y %H:%M:%S")
        failed_registers['TIMESTAMP'] = timestring
        logger.debug('Failed registers: {}'.format(failed_registers))

        # do print as last step
        if print_result:
            # do not sort keys to get JSON file in same order as input file
            if print_pretty:
                print(json.dumps(failed_registers, indent=4))
            else:
                print(json.dumps(failed_registers))
    else:
        logger.info('No failed registers')
