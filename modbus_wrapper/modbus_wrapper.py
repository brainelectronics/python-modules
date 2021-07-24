#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Modbus register helper module

Collection of modbus related functions
"""

# from pymodbus.compat import iteritems
# from pymodbus.constants import Endian
# from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient        # as ModbusClient
# from pymodbus.client.sync import ModbusUdpClient      # as ModbusClient
from pymodbus.client.sync import ModbusSerialClient     # as ModbusClient
import logging
from typing import Tuple

# custom imports
from module_helper.module_helper import ModuleHelper


class ModbusWrapper(ModuleHelper):
    """docstring for ModbusWrapper"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(ModbusWrapper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self.repo = None
        self.git_dict = dict()

        self.logger.debug('ModbusWrapper init finished')

    def load_modbus_registers_file(self, file_path: str) -> dict:
        """
        Get the modbus registers from a json file.

        :param      file_path:  The file path
        :type       file_path:  str

        :returns:   The modbus registers.
        :rtype:     dict
        """
        return self.load_json_file(path=file_path)

    def restore_human_readable_content(self, key: str, value: list) -> str:
        """
        Restore received response to human readable content

        :param      key:    The key
        :type       key:    str
        :param      value:  The value
        :type       value:  list

        :returns:   Human readable content
        :rtype:     str
        """
        if key == 'DEVICE_UUID_IREG':
            it = iter(value)
            tupleList = zip(it, it)
            device_uuid_list = list()
            for ele in tupleList:
                device_uuid_list.append(ele[0] << 16 | ele[1])
            return ', '.join(hex(x) for x in device_uuid_list)
        elif key == 'DEVICE_MAC_IREG':
            return ':'.join(format(x, 'x') for x in value)
        elif key == 'COMMIT_SHA_IREG':
            unicode_chars_list = list()
            for ele in value:
                unicode_chars_list.append((ele >> 8) & 0xFF)
                unicode_chars_list.append(ele & 0xFF)
            return ''.join(chr(x) for x in unicode_chars_list)
        else:
            return ''

    def read_all_registers(self,
                           device_type: str = "tcp",
                           address: str = "",
                           port: int = 502,
                           unit: int = 180,
                           check_expectation: bool = False,
                           file: str = 'modbusRegisters.json') -> dict:
        """
        Read all modbus registers.

        :param      device_type:        The device type, "tcp" or "rtu"
        :type       device_type:        str
        :param      address:            Address of the modbus device
        :type       address:            str
        :param      port:               The port
        :type       port:               int
        :param      unit:               Unit of the modbus device on the bus
        :type       unit:               int
        :param      check_expectation:  Flag to check expectation
        :type       check_expectation:  bool
        :param      file:               The modbus register json file
        :type       file:               str
        """
        invalid_reg_content = 0
        connection = False
        read_content = dict()
        modbus_registers = self.load_modbus_registers_file(file_path=file)

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
        else:
            self.logger.error('Device type unknown')
            return read_content

        connection = client.connect()
        self.logger.debug('Connection result: {}'.format(connection))

        # exit if no connection is established
        if connection is False:
            self.logger.error('Connection failed')
            return read_content

        # Coils (only getter) [0, 1]
        self.logger.info('Coils:')
        if 'COILS' in modbus_registers:
            invalid_counter, coil_register_content = self.read_coil_registers(
                client=client,
                unit=unit,
                modbus_registers=modbus_registers['COILS'],
                check_expectation=check_expectation)
            self.logger.debug('coil_register_content: {}'.
                              format(coil_register_content))

            invalid_reg_content += invalid_counter
            read_content.update(coil_register_content)
        else:
            self.logger.info('No COILS defined, skipping')

        # Hregs (setter+getter) [0, 65535]
        self.logger.info('Hregs:')
        if 'HREGS' in modbus_registers:
            invalid_counter, hreg_register_content = self.read_hregs_registers(
                client=client,
                unit=unit,
                modbus_registers=modbus_registers['HREGS'],
                check_expectation=check_expectation)
            self.logger.debug('hreg_register_content: {}'.
                              format(hreg_register_content))

            invalid_reg_content += invalid_counter
            read_content.update(hreg_register_content)
        else:
            self.logger.info('No HREGS defined, skipping')

        # Ists (only getter) [0, 1]
        self.logger.info('Ists:')
        if 'ISTS' in modbus_registers:
            invalid_counter, ists_register_content = self.read_ists_registers(
                client=client,
                unit=unit,
                modbus_registers=modbus_registers['ISTS'],
                check_expectation=check_expectation)
            self.logger.debug('ists_register_content: {}'.
                              format(ists_register_content))

            invalid_reg_content += invalid_counter
            read_content.update(ists_register_content)
        else:
            self.logger.info('No ISTS defined, skipping')

        # Iregs (only getter) [0, 65535]
        self.logger.info('Iregs:')
        if 'IREGS' in modbus_registers:
            invalid_counter, ireg_register_content = self.read_iregs_registers(
                client=client,
                unit=unit,
                modbus_registers=modbus_registers['IREGS'],
                check_expectation=check_expectation)
            self.logger.debug('ireg_register_content: {}'.
                              format(ireg_register_content))

            invalid_reg_content += invalid_counter
            read_content.update(ireg_register_content)
        else:
            self.logger.info('No IREGS defined, skipping')

        client.close()
        self.logger.debug('Connection closed')

        if check_expectation and invalid_reg_content:
            self.logger.warning('Mismatch of expected register values: {}'.
                                format(invalid_reg_content))

        self.logger.debug(read_content)

        return read_content

    def read_coil_registers(self,
                            client,
                            unit: int,
                            modbus_registers: dict,
                            check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all coil registers.

        Coils (only getter) [0, 1], function 01 - read single register

        :param      client:             The client
        :type       client:             ModbusTcpClient or ModbusSerialClient
        :param      unit:               Unit of the modbus device on the bus
        :type       unit:               int
        :param      modbus_registers:   The modbus registers
        :type       modbus_registers:   dict
        :param      check_expectation:  Flag to check expectation
        :type       check_expectation:  bool

        :returns:   Amount of mismatching content and read content as dict
        :rtype:     tuple
        """
        invalid_reg_counter = 0
        register_content = dict()

        for key, val in modbus_registers.items():
            self.logger.debug('\tkey: {}'.format(key))
            self.logger.debug('\t\tval: {}'.format(val))

            register_address = val['register']
            count = val['len']
            register_description = val['description']
            expected_val = 0

            if 'test' in val:
                expected_val = val['test']

            response = client.read_coils(address=register_address,
                                         count=count,
                                         unit=unit)
            if response.isError():
                register_content[key] = False
                invalid_reg_counter += 1
            else:
                self.logger.debug('\t\tbits: {}'.format(response))
                bits = response.bits
                self.logger.debug('\t\tbits: {}'.format(bits))

                if count == 1:
                    bit_val = bits[0]
                else:
                    bit_val = bits[0:count]

                self.logger.info('\t{:<5}\t{}'.format(bit_val,
                                                      register_description))

                register_content[key] = bit_val

                if (check_expectation and
                    (expected_val != bit_val) and
                        (expected_val != -1)):
                    self.logger.error('\tValue {} not matching expectation {}'.
                                      format(bit_val, expected_val))
                    invalid_reg_counter += 1

        return invalid_reg_counter, register_content

    def read_hregs_registers(self,
                             client,
                             unit: int,
                             modbus_registers: dict,
                             check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all holding registers.

        Hregs (setter+getter) [0, 65535], function 03 - read holding register

        :param      client:             The client
        :type       client:             ModbusTcpClient or ModbusSerialClient
        :param      unit:               Unit of the modbus device on the bus
        :type       unit:               int
        :param      modbus_registers:   The modbus registers
        :type       modbus_registers:   dict
        :param      check_expectation:  Flag to check expectation
        :type       check_expectation:  bool

        :returns:   Amount of mismatching content and read content as dict
        :rtype:     tuple
        """
        invalid_reg_counter = 0
        register_content = dict()

        for key, val in modbus_registers.items():
            self.logger.debug('\t\tkey: {}'.format(key))
            self.logger.debug('\t\tval: {}'.format(val))

            register_address = val['register']
            count = val['len']
            register_description = val['description']
            expected_val = 0

            if 'test' in val:
                expected_val = val['test']

            response = client.read_holding_registers(address=register_address,
                                                     count=count,
                                                     unit=unit)

            if response.isError():
                register_content[key] = -1
                invalid_reg_counter += 1
            else:
                self.logger.debug('\t\tregisters: {}'.format(response))
                registers = response.registers
                self.logger.debug('\t\tregisters: {}'.format(registers))

                # decoder = BinaryPayloadDecoder.fromRegisters(registers)
                # decoded = []

                if count == 1:
                    register_val = registers[0]
                else:
                    register_val = registers[0:count]

                self.logger.info('\t{}\t{}'.format(register_val,
                                                   register_description))

                register_content[key] = register_val

                if (check_expectation and
                    (expected_val != register_val) and
                        (expected_val != -1)):
                    self.logger.error('\tValue {} not matching expectation {}'.
                                      format(register_val, expected_val))
                    invalid_reg_counter += 1

        return invalid_reg_counter, register_content

    def read_ists_registers(self,
                            client,
                            unit: int,
                            modbus_registers: dict,
                            check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all discrete input registers.

        Ists (only getter) [0, 1], function 02 - read input status (discrete
        inputs/digital input)

        :param      client:             The client
        :type       client:             ModbusTcpClient or ModbusSerialClient
        :param      unit:               Unit of the modbus device on the bus
        :type       unit:               int
        :param      modbus_registers:   The modbus registers
        :type       modbus_registers:   dict
        :param      check_expectation:  Flag to check expectation
        :type       check_expectation:  bool

        :returns:   Amount of mismatching content and read content as dict
        :rtype:     tuple
        """
        invalid_reg_counter = 0
        register_content = dict()

        for key, val in modbus_registers.items():
            self.logger.debug('\t\tkey: {}'.format(key))
            self.logger.debug('\t\tval: {}'.format(val))

            register_address = val['register']
            count = val['len']
            register_description = val['description']
            expected_val = 0

            if 'test' in val:
                expected_val = val['test']

            response = client.read_discrete_inputs(address=register_address,
                                                   count=count,
                                                   unit=unit)
            if response.isError():
                register_content[key] = -1
                invalid_reg_counter += 1
            else:
                self.logger.debug('\t\tbits: {}'.format(response))
                bits = response.bits
                self.logger.debug('\t\tbits: {}'.format(bits))

                if count == 1:
                    bit_val = bits[0]
                else:
                    bit_val = bits[0:count]

                self.logger.info('\t{:<5}\t{}'.
                                 format(bit_val, register_description))

                register_content[key] = bit_val

                if (check_expectation and
                    (expected_val != bit_val) and
                        (expected_val != -1)):
                    self.logger.error('\tValue {} not matching expectation {}'.
                                      format(bit_val, expected_val))
                    invalid_reg_counter += 1

        return invalid_reg_counter, register_content

    def read_iregs_registers(self,
                             client,
                             unit: int,
                             modbus_registers: dict,
                             check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all input registers.

        Iregs (only getter) [0, 65535], function 04 - read input registers

        :param      client:             The client
        :type       client:             ModbusTcpClient or ModbusSerialClient
        :param      unit:               Unit of the modbus device on the bus
        :type       unit:               int
        :param      modbus_registers:   The modbus registers
        :type       modbus_registers:   dict
        :param      check_expectation:  Flag to check expectation
        :type       check_expectation:  bool

        :returns:   Amount of mismatching content and read content as dict
        :rtype:     tuple
        """
        invalid_reg_counter = 0
        register_content = dict()

        for key, val in modbus_registers.items():
            self.logger.debug('\t\tkey: {}'.format(key))
            self.logger.debug('\t\tval: {}'.format(val))

            register_address = val['register']
            count = val['len']
            register_description = val['description']
            expected_val = 0

            if 'test' in val:
                expected_val = val['test']

            response = client.read_input_registers(address=register_address,
                                                   count=count,
                                                   unit=unit)
            if response.isError():
                register_content[key] = False
                invalid_reg_counter += 1
            else:
                self.logger.debug('\t\tregisters: {}'.format(response))
                registers = response.registers
                self.logger.debug('\t\tregisters: {}'.format(registers))

                if count == 1:
                    register_val = registers[0]
                elif count == 2:
                    # actual a uint32_t value, reconstruct it
                    register_val = registers[0] << 16 | registers[1]
                else:
                    register_val = registers[0:count]

                restored = self.restore_human_readable_content(
                    key=key,
                    value=register_val)

                if restored != '':
                    self.logger.info('\t[{}]\t{}'.format(restored,
                                                         register_description))
                    self.logger.debug('\t{}\t{}'.format(register_val,
                                                        register_description))
                    register_content['HUMAN_'+key] = restored
                else:
                    self.logger.info('\t{}\t{}'.format(register_val,
                                                       register_description))

                register_content[key] = register_val

                if (check_expectation and
                    (expected_val != register_val) and
                        (expected_val != -1)):
                    self.logger.error('\tValue {} not matching expectation {}'.
                                      format(register_val, expected_val))
                    invalid_reg_counter += 1

        return invalid_reg_counter, register_content
