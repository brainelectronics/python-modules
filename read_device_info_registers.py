#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# ----------------------------------------------------------------------------
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         read_device_info_registers.py
#  @date         June, 2021
#  @version      0.1.0
#  @brief        Read all registers via RTU modbus or external IP
#
#  @required     pymodbus 2.3.0 or higher
#
#  @usage
#  python3 read_device_info_registers.py \
#   --file=../application/config/modbusRegisters.json \
#   --connection=rtu \
#   --address=/dev/tty.wchusbserial1420 \
#   --unit=10 \
#   -d -v4
#
#  python3 read_device_info_registers.py \
#   --file=../application/config/modbusRegisters.json \
#   --connection=tcp \
#   --address=192.168.4.1 \
#   --unit=255 \
#   -d -v4
#
#
#  optional arguments:
#   -h, --help
#
#   -a, --address   Address to connect, 192.168.0.8 or /dev/tty.SLAB_USBtoUART
#   -c, --connection    Type of Modbus connection, ['tcp', 'rtu']
#   -f, --file      Path to Modbus registers file
#   -p, --port      Port of connection, not required for RTU Serial
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
__version__ = "0.1.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "info@brainelectronics.de"
__status__ = "Development"

# from pymodbus.compat import iteritems
# from pymodbus.constants import Endian
# from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient        # as ModbusClient
# from pymodbus.client.sync import ModbusUdpClient      # as ModbusClient
from pymodbus.client.sync import ModbusSerialClient     # as ModbusClient

import argparse
import json
import logging
# import os
import sys
# import time


class VAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(VAction, self).__init__(option_strings, dest, nargs, const,
                                      default, type, choices, required,
                                      help, metavar)
        self.values = 0

    def __call__(self, parser, args, values, option_string=None):
        if values is None:
            # do not increment here, so '-v' will use highest log level
            pass
        else:
            try:
                self.values = int(values)
            except ValueError:
                self.values = values.count('v')  # do not count the first '-v'
        setattr(args, self.dest, self.values)


def create_logger(logger_name: str = None) -> logging:
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


def get_modbus_registers(file_path: str) -> dict:
    """
    Get the modbus registers for json file.

    :param      file_path:  The file path
    :type       file_path:  str

    :returns:   The modbus registers.
    :rtype:     dict
    """
    data = dict()

    with open(file_path) as json_file:
        data = json.load(json_file)

    return data


def read_all_registers(device_type: str = "tcp",
                       address: str = "",
                       port: int = 502,
                       unit: int = 180,
                       check_expectation: bool = False,
                       file: str = 'modbusRegisters.json',
                       logger: logging = None):
    """
    Read all registers.

    :param      device_type:        The device type, "tcp" or "rtu"
    :type       device_type:        str
    :param      address:            The address
    :type       address:            str
    :param      port:               The port
    :type       port:               int
    :param      unit:               The unit
    :type       unit:               int
    :param      check_expectation:  Flag to check expectation
    :type       check_expectation:  bool
    :param      file:               The file
    :type       file:               str
    :param      logger:             The logger
    :type       logger:             logging
    """
    if logger is None:
        logger = create_logger()
        logger.setLevel(logging.INFO)

    available_modbus_registers = get_modbus_registers(file)

    invalid_reg_content = 0
    connection = False

    if device_type == "tcp":
        # TCP/IP Client
        # default value in src/ModbusSettings.h or src/ModbusIP_ESP8266.h
        client = ModbusTcpClient(host=address,
                                 retries=3,
                                 # retry_on_empty=True,
                                 timeout=10,
                                 port=port)
    elif device_type == "rtu":
        # Serial RTU Client
        client = ModbusSerialClient(method="rtu",
                                    port=address,
                                    stopbits=1,
                                    bytesize=8,
                                    parity="N",
                                    baudrate=9600,
                                    timeout=10,
                                    retries=3)

    connection = client.connect()
    logger.info('Connection result: {}'.format(connection))

    # exit if no connection is established
    if connection is False:
        logger.error('Connection failed')
        exit(-1)

    # Coils (only getter) [0, 1]
    logger.info('Coils coil:')
    # function 01 - read single register
    # address=0, count=4, unit=12
    for key, val in available_modbus_registers['COILS'].items():
        logger.debug('\tkey: {}'.format(key))
        logger.debug('\t\tval: {}'.format(val))

        register_address = val['register']
        count = val['len']
        register_description = val['description']
        expected_val = 0
        if 'test' in val:
            expected_val = val['test']

        bits = client.read_coils(address=register_address,
                                 count=count,
                                 unit=unit)

        logger.debug('\t\tbits: {}'.format(bits))
        bits = bits.bits
        logger.debug('\t\tbits: {}'.format(bits))

        if count == 1:
            bit_val = bits[0]
        else:
            bit_val = bits[0:count]

        logger.info('\t{:<5}\t{}'.format(bit_val, register_description))

        if (check_expectation and
            (expected_val != bit_val) and
            (expected_val != -1)):
            logger.error('\tValue {} not matching expectation {}'.
                         format(bit_val, expected_val))
            invalid_reg_content += 1

    # Hregs (setter+getter) [0, 65535]
    logger.info('Holding Hregs:')
    # function 03 - read holding register
    # address=0, count=1, unit=12
    for key, val in available_modbus_registers['HREGS'].items():
        logger.debug('\t\tkey: {}'.format(key))
        logger.debug('\t\tval: {}'.format(val))

        register_address = val['register']
        count = val['len']
        register_description = val['description']
        expected_val = 0
        if 'test' in val:
            expected_val = val['test']

        registers = client.read_holding_registers(address=register_address,
                                                  count=count,
                                                  unit=unit)

        logger.debug('\t\tregisters: {}'.format(registers))
        registers = registers.registers
        logger.debug('\t\tregisters: {}'.format(registers))

        # decoder = BinaryPayloadDecoder.fromRegisters(registers)
        # decoded = []

        if count == 1:
            register_val = registers[0]
        else:
            register_val = registers[0:count]

        logger.info('\t{:<5}\t{}'.format(register_val, register_description))

        if (check_expectation and
            (expected_val != register_val) and
            (expected_val != -1)):
            logger.error('\tValue {} does not match expectation {}'.
                         format(register_val, expected_val))
            invalid_reg_content += 1

    # Ists (only getter) [0, 1]
    logger.info('Discrete Ists:')
    # function 02 - read input status (discrete inputs/digital input)
    # address=0, count=1, unit=12
    for key, val in available_modbus_registers['ISTS'].items():
        logger.debug('\t\tkey: {}'.format(key))
        logger.debug('\t\tval: {}'.format(val))

        register_address = val['register']
        count = val['len']
        register_description = val['description']
        expected_val = 0
        if 'test' in val:
            expected_val = val['test']

        bits = client.read_discrete_inputs(address=register_address,
                                           count=count,
                                           unit=unit)

        logger.debug('\t\tbits: {}'.format(bits))
        bits = bits.bits
        logger.debug('\t\tbits: {}'.format(bits))

        if count == 1:
            bit_val = bits[0]
        else:
            bit_val = bits[0:count]

        logger.info('\t{:<5}\t{}'.format(bit_val, register_description))

        if (check_expectation and
            (expected_val != bit_val) and
            (expected_val != -1)):
            logger.error('\tValue {} does not match expectation {}'.
                         format(bit_val, expected_val))
            invalid_reg_content += 1

    # Iregs (only getter) [0, 65535]
    logger.info('Input Iregs:')
    # function 04 - read input registers
    # address=0, count=1, unit=12
    for key, val in available_modbus_registers['IREGS'].items():
        logger.debug('\t\tkey: {}'.format(key))
        logger.debug('\t\tval: {}'.format(val))

        register_address = val['register']
        count = val['len']
        register_description = val['description']
        expected_val = 0
        if 'test' in val:
            expected_val = val['test']

        registers = client.read_input_registers(address=register_address,
                                                count=count,
                                                unit=unit)

        logger.debug('\t\tregisters: {}'.format(registers))
        registers = registers.registers
        logger.debug('\t\tregisters: {}'.format(registers))

        if count == 1:
            register_val = registers[0]
        elif count == 2:
            # actual a uint32_t value, reconstruct it
            register_val = registers[0] << 16 | registers[1]
        else:
            register_val = registers[0:count]

        if key == 'DEVICE_UUID_IREG':
            it = iter(register_val)
            tupleList = zip(it, it)
            device_uuid_list = list()
            for ele in tupleList:
                device_uuid_list.append(ele[0] << 16 | ele[1])
            device_uuid_str = ', '.join(hex(x) for x in device_uuid_list)
            logger.info('\t[{:<5}]\t{}'.
                        format(device_uuid_str, register_description))
            logger.debug('\t{}\t{}'.format(register_val, register_description))
        elif key == 'DEVICE_MAC_IREG':
            device_mac_str = ':'.join(format(x, 'x') for x in register_val)
            logger.info('\t{:<5}\t{}'.
                        format(device_mac_str, register_description))
            logger.info('\t{}\t{}'.format(register_val, register_description))
        elif key == 'COMMIT_SHA_IREG':
            unicode_chars_list = list()
            for ele in register_val:
                unicode_chars_list.append((ele >> 8) & 0xFF)
                unicode_chars_list.append(ele & 0xFF)
            commit_sha_str = ''.join(chr(x) for x in unicode_chars_list)
            logger.debug('\t{}\t{}'.format(register_val, register_description))
            logger.debug('\t{}\t{}'.
                         format(unicode_chars_list, register_description))
            logger.info('\t{}\t{}'.
                        format(commit_sha_str, register_description))
        else:
            logger.info('\t{}\t{}'.format(register_val, register_description))

            if (check_expectation and
                (expected_val != register_val) and
                (expected_val != -1)):
                logger.error('\tValue {} does not match expectation {}'.
                             format(register_val, expected_val))
                invalid_reg_content += 1

    client.close()
    logger.debug('Connection closed')

    if check_expectation and invalid_reg_content:
        logger.warning('Mismatch of expected register values: {}'.
                       format(invalid_reg_content))


if __name__ == "__main__":
    logger = create_logger(__name__)
    register_logger = create_logger("Register Logger")

    parser = argparse.ArgumentParser()

    parser.add_argument('-a',
                        '--address',
                        help=('Address of connection, like 192.168.0.8 or '
                              '/dev/tty.SLAB_USBtoUART'),
                        nargs='?',
                        required=True)
    parser.add_argument('-c',
                        '--connection',
                        help='Type of Modbus connection',
                        nargs='?',
                        default="tcp",
                        choices=['tcp', 'rtu'],
                        required=False)
    parser.add_argument('-f',
                        '--file',
                        help='Path to Modbus registers file',
                        nargs='?',
                        default="modbusRegisters.json",
                        required=False)
    parser.add_argument('-p',
                        '--port',
                        help='Port of connection, not required for RTU Serial',
                        default=502,
                        required=False)
    parser.add_argument('-u',
                        '--unit',
                        help=('Unit of connection, '
                              'Phoenix 180, Tobi Test 1, ESP 255, Serial 10'),
                        default=180,
                        required=False)
    parser.add_argument('--validate',
                        help='Validate received data with expected data',
                        required=False,
                        action='store_true')

    parser.add_argument('-d',
                        '--debug',
                        help='Output logger messages to stderr',
                        action='store_true')
    parser.add_argument('-v',
                        '--verbosity',
                        help='Set level of verbosity',
                        nargs='?',
                        default=1,
                        required=False)

    # parse the args
    args = parser.parse_args()

    # listing the levels in ascending order is easier
    verbosity = int(args.verbosity)
    log_levels_list = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_levels_list = log_levels_list[::-1]
    log_level = min(len(log_levels_list) - 1, verbosity)
    log_level_name = log_levels_list[log_level]

    logger.setLevel(log_level_name)
    register_logger.setLevel(log_level_name)

    if not args.debug:
        print("Disabled loggers")
        logger.disabled = True
        register_logger.disabled = True

    logger.debug(args)

    try:
        port = int(args.port)
        unit = int(args.unit)
    except Exception as e:
        raise e

    read_all_registers(device_type=args.connection,
                       address=args.address,
                       port=port,
                       unit=unit,
                       check_expectation=args.validate,
                       file=args.file,
                       logger=register_logger)
