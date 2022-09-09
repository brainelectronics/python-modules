#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Modbus register helper module

Collection of modbus related functions
"""

import datetime
# from pymodbus.compat import iteritems
# from pymodbus.constants import Endian
# from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusTcpClient        # as ModbusClient
# from pymodbus.client.sync import ModbusUdpClient      # as ModbusClient
from pymodbus.client.sync import ModbusSerialClient     # as ModbusClient
import logging
from typing import Tuple
from typing import Union

# custom imports
from be_helpers import ModuleHelper


class ModbusWrapper(ModuleHelper):
    """docstring for ModbusWrapper"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(ModbusWrapper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self._connection = None
        self._client = None
        self._unit = None
        self._read_content = dict()

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
        if key == 'CHARGING_STATE_IREG':
            # MyEVSE
            # value corresponds to the position in the list
            possible_states = ['A', 'B', 'C', 'D', 'E', 'F', 'unknown']
            return possible_states[value]
        if key == 'COMMIT_SHA_IREG':
            # MyEVSE
            unicode_chars_list = list()
            for ele in value:
                unicode_chars_list.append((ele >> 8) & 0xFF)
                unicode_chars_list.append(ele & 0xFF)
            return ''.join(chr(x) for x in unicode_chars_list)
        elif key == 'CREATION_DATE_IREG':
            # MyEVSE
            epoch_datetime = datetime.datetime(year=1970, month=1, day=1)
            creation_day = datetime.timedelta(days=value)
            # use MySQL TIMESTAMP compatible format, see ISO 8601
            return (epoch_datetime + creation_day).strftime("%Y-%m-%d")
        elif key == 'DEVICE_MAC_IREG':
            # MyEVSE
            return ':'.join(format(x, 'x') for x in value)
        elif key == 'DEVICE_NAME_HREG':
            # Phoenix EVSE
            # ASCII, character hex coded
            # e.g. STATION123
            # 0X5354 0X4154 0X494F 0X4E31 0X3233
            # First character shall not be a number
            # DEVICE_NAME_HREG: [17750, 17219, 24369, 0, 0]
            hex_str = ''.join(format(ele, 'x') for ele in value if ele != 0)
            return bytes.fromhex(hex_str).decode("ASCII")
        elif key == 'DEVICE_UUID_IREG':
            # MyEVSE
            it = iter(value)
            tupleList = zip(it, it)
            device_uuid_list = list()
            for ele in tupleList:
                device_uuid_list.append(ele[0] << 16 | ele[1])
            return ', '.join(hex(x) for x in device_uuid_list)
        elif key == 'DIP_CONFIG_IREG':
            # Phoenix EVSE
            # binary
            # DIP 1 = LSB
            # each switch is represented by one bit.
            return "{0:010b}".format(value)[::-1]
        elif key == 'EV_STATUS_IREG':
            # Phoenix EVSE
            # ASCII (8 Bit), A ... F
            return chr(value)
        elif key == 'FIRMWARE_VERSION_IREG':
            # Phoenix EVSE
            # decimal
            # e.g. 0.4.30 = 430
            # FW[0] = 0; FW[1] = 4; FW[2] = 22;
            # FW[2]+FW[1]*100+FW[0]*10.000
            # FIRMWARE_VERSION_IREG: 1323892736 = [20201, 0]
            # a uint32 is created from the list, but not necessary this time
            fw = value >> 16
            fw_0 = int(fw / 10000)
            fw_1 = int((fw - (fw_0 * 10000)) / 100)
            fw_2 = int(fw - (fw_0 * 10000) - (fw_1 * 100))
            return '.'.join(str(ele) for ele in [fw_0, fw_1, fw_2])
        elif key == 'MAC_ADDRESS_HREG':
            # Phoenix EVSE
            # hex
            # e.g. 00:A0:45:66:4F:40 0X00A0 0X4566 0X4F40
            # MAC_ADDRESS_HREG: [43124, 7576, 976]
            val_str = ''.join(format(x, 'X') for x in value)
            return ':'.join(val_str[i:i+2] for i in range(0, len(val_str), 2))
        elif ((key == 'CHARGING_BEGIN_TIME_IREG') or
              (key == 'CHARGING_DURATION_IREG') or
              (key == 'CHARGING_END_TIME_IREG') or
              (key == 'UPTIME_MS_IREG')):
            # MyEVSE
            d = datetime.timedelta(milliseconds=value)
            return str(d)
        elif key == 'SERIAL_NUMBER_HREG':
            # Phoenix EVSE
            # ASCII, character hex coded
            # z.B. EVCC10000041 0X4556 0X4343 0X3130 0X3030 0X3030 0X3431
            # E == 0x45 == d69
            # SERIAL_NUMBER_HREG: [17750, 17219, 12848, 12337, 13880, 13621]
            hex_str = ''.join(format(ele, 'x') for ele in value)
            return bytes.fromhex(hex_str).decode("ASCII")
        else:
            return ''

    def setup_connection(self,
                         device_type: str = "tcp",
                         address: str = "",
                         port: int = 502,
                         unit: int = 180,
                         baudrate: int = 9600,
                         timeout: int = 10,
                         retries: int = 3) -> bool:
        """
        Setup a connection to a Modbus device.

        :param      device_type:  The device type, "tcp" or "rtu"
        :type       device_type:  str
        :param      address:      Address of the modbus device
        :type       address:      str
        :param      port:         The port
        :type       port:         int, optional
        :param      unit:         Unit of the modbus device on the bus
        :type       unit:         int, optional
        :param      baudrate:     Baudrate of the modbus RTU connection
        :type       baudrate:     int, optional

        :param      timeout:      The timeout before the conntection fails
        :type       timeout:      int
        :param      retries:      Amount of connection retries
        :type       retries:      int

        :returns:   Result of connection setup
        :rtype:     bool
        """
        result = False

        if device_type == "tcp":
            # TCP/IP Client
            # default value in src/ModbusSettings.h or src/ModbusIP_ESP8266.h
            client = ModbusTcpClient(host=address,
                                     retries=retries,
                                     # retry_on_empty=True,
                                     timeout=timeout,
                                     port=port)
            result = True
        elif device_type == "rtu":
            # Serial RTU Client
            client = ModbusSerialClient(method="rtu",
                                        port=address,
                                        stopbits=1,
                                        bytesize=8,
                                        parity="N",
                                        baudrate=baudrate,
                                        timeout=timeout,
                                        retries=retries)
            result = True
        else:
            self.logger.error('Device type unknown')

        if result:
            self.client = client
            self.unit = unit

        return result

    @property
    def connection(self) -> bool:
        """
        Get status of connection with device

        :returns:   Flag whether connection is active or not
        :rtype:     bool
        """
        return self._connection

    @connection.setter
    def connect(self, value: bool) -> None:
        """
        Open or close connection to device

        :param      value:  The value
        :type       value:  bool
        """
        if value:
            if self.client:
                self.connection = self.client.connect()
            else:
                self.logger.error('No client, call "setup_connection" first')
        else:
            if self.client:
                self.connection = self.client.close()
            else:
                self.logger.error('No client, call "setup_connection" first')

    @connection.setter
    def connection(self, value: bool) -> None:
        """
        Set connection status

        :param      value:  The connection status
        :type       value:  bool
        """
        self._connection = value

    def disconnect(self) -> None:
        """
        Disconnect from modbus device, wrapper around @see connect.
        """
        self.connect = False
        if self.connection is False:
            self.logger.debug('Connection closed')

    @property
    def client(self) -> Union[ModbusSerialClient, ModbusTcpClient]:
        """
        Get modbus client instance

        :returns:   Modbus client instance
        :rtype:     Union[ModbusSerialClient, ModbusTcpClient]
        """
        return self._client

    @client.setter
    def client(self,
               value: Union[ModbusSerialClient, ModbusTcpClient]) -> None:
        """
        Set modbus client instance

        :param      value:  The modbus client
        :type       value:  Union[ModbusSerialClient, ModbusTcpClient]
        """
        self._client = value

    @property
    def unit(self) -> int:
        """
        Get modbus bus device ID

        :returns:   Modbus device ID
        :rtype:     int
        """
        return self._unit

    @unit.setter
    def unit(self, value: int) -> None:
        """
        Set modbus bus device ID

        :param      value:  The bus device ID
        :type       value:  int
        """
        self._unit = value

    def read_all_registers(self,
                           check_expectation: bool = False,
                           file: str = 'modbusRegisters.json') -> dict:
        """
        Read all modbus registers.

        :param      check_expectation:  Flag to check expectation
        :type       check_expectation:  bool, optional
        :param      file:               The modbus register json file
        :type       file:               str, optional

        :returns:   Dictionary with read register data
        :rtype:     dict
        """
        invalid_reg_content = 0
        read_content = dict()

        # exit if no connection is established
        if self.connection is False:
            self.logger.info('Connection not yet established')
            if self.client is None:
                self.logger.error('Modbus client unavailable')
                return read_content
            else:
                self.logger.warning('Connect to device beforehand')
                self.connect = True
                if self.connection is False:
                    self.logger.error('Failed to open connection to device')
                    return read_content

        modbus_registers = self.load_modbus_registers_file(file_path=file)

        # Coils (setter+getter) [0, 1]
        self.logger.info('Coils:')
        if 'COILS' in modbus_registers:
            invalid_counter, coil_register_content = self.read_coil_registers(
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
                modbus_registers=modbus_registers['IREGS'],
                check_expectation=check_expectation)
            self.logger.debug('ireg_register_content: {}'.
                              format(ireg_register_content))

            invalid_reg_content += invalid_counter
            read_content.update(ireg_register_content)
        else:
            self.logger.info('No IREGS defined, skipping')

        self.disconnect()

        if check_expectation and invalid_reg_content:
            self.logger.warning('Mismatch of expected register values: {}'.
                                format(invalid_reg_content))

        self.logger.debug(read_content)
        self.read_content = read_content

        return self.read_content

    @property
    def read_content(self) -> dict:
        """
        Get latest read content from devie

        :returns:   Read resgister content
        :rtype:     dict
        """
        return self._read_content

    @read_content.setter
    def read_content(self, value: dict) -> None:
        """
        Set latest read content from device

        :param      value:  The content
        :type       value:  dict
        """
        self._read_content = value

    def write_all_registers(self, file: str = 'modbusRegisters.json') -> dict:
        """
        Write all modbus registers.

        :param      file:  The modbus register json file
        :type       file:  str, optional

        :returns:   Dictionary with failed register write operations
        :rtype:     dict
        """
        failed_reg_counter = 0
        failed_reg_log = dict()

        # exit if no connection is established
        if self.connection is False:
            self.logger.info('Connection not yet established')
            if self.client is None:
                self.logger.error('Modbus client unavailable')
                return failed_reg_log
            else:
                self.logger.error('Connect to device beforehand')
                self.connect = True
                if self.connection is False:
                    self.logger.error('Failed to open connection to device')
                    return failed_reg_log

        modbus_registers = self.load_modbus_registers_file(file_path=file)

        # Coils (setter+getter) [0, 1]
        self.logger.info('Coils:')
        if 'COILS' in modbus_registers:
            failed_counter, coil_register_log = self.write_coil_registers(
                modbus_registers=modbus_registers['COILS'])
            self.logger.debug('coil_register_log: {}'.
                              format(coil_register_log))

            failed_reg_counter += failed_counter
            failed_reg_log.update(coil_register_log)
        else:
            self.logger.info('No COILS defined, skipping')

        # Hregs (setter+getter) [0, 65535]
        self.logger.info('Hregs:')
        if 'HREGS' in modbus_registers:
            failed_counter, hreg_register_log = self.write_hregs_registers(
                modbus_registers=modbus_registers['HREGS'])
            self.logger.debug('hreg_register_log: {}'.
                              format(hreg_register_log))

            failed_reg_counter += failed_counter
            failed_reg_log.update(hreg_register_log)
        else:
            self.logger.info('No HREGS defined, skipping')

        # Ists (only getter) [0, 1]
        if 'ISTS' in modbus_registers:
            self.logger.info('ISTS can only be read, skipping')

        # Iregs (only getter) [0, 65535]
        if 'IREGS' in modbus_registers:
            self.logger.info('IREGS can only be read, skipping')

        self.disconnect()

        if failed_reg_counter:
            self.logger.warning('Failed to set {} register values: {}'.
                                format(failed_reg_counter, failed_reg_log))

        self.logger.debug(failed_reg_log)

        return failed_reg_log

    def read_coil_registers(self,
                            modbus_registers: dict,
                            check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all coil registers.

        Coils (setter+getter) [0, 1], function 01 - read single register

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

            response = self.client.read_coils(address=register_address,
                                              count=count,
                                              unit=self.unit)
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

    def write_coil_registers(self,
                             modbus_registers: dict) -> Tuple[int, dict]:
        """
        Write all coil registers.

        Coils (setter+getter) [0, 1], function 05 - write single register

        :param      modbus_registers:   The modbus registers
        :type       modbus_registers:   dict

        :returns:   Amount of failed content and failed registers as dict
        :rtype:     tuple
        """
        failed_reg_counter = 0
        failed_reg_log = dict()

        for key, val in modbus_registers.items():
            self.logger.debug('\tkey: {}'.format(key))
            self.logger.debug('\t\tval: {}'.format(val))

            register_address = val['register']
            set_val = val['val']

            response = self.client.write_coil(address=register_address,
                                              value=set_val,
                                              unit=self.unit)

            if response.isError():
                failed_reg_counter += 1
                failed_reg_log[key] = False
                self.logger.warning('\tFailed to set {} to {}'.
                                    format(key, set_val))
            else:
                self.logger.debug('\tSuccessfully set {} to {}'.
                                  format(key, set_val))

        return failed_reg_counter, failed_reg_log

    def read_hregs_registers(self,
                             modbus_registers: dict,
                             check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all holding registers.

        Hregs (setter+getter) [0, 65535], function 03 - read holding register

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

            response = self.client.read_holding_registers(
                address=register_address,
                count=count,
                unit=self.unit)

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

                try:
                    restored = self.restore_human_readable_content(
                                        key=key,
                                        value=register_val)
                except Exception:
                    restored = ''

                if restored != '':
                    self.logger.info('\t[{}]\t{}'.format(restored,
                                                         register_description))
                    self.logger.debug('\t{}\t{}'.format(register_val,
                                                        register_description))
                    register_content[key+'_HUMAN'] = restored
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

    def write_hregs_registers(self,
                              modbus_registers: dict) -> Tuple[int, dict]:
        """
        Write all holding registers.

        Hregs (setter+getter) [0, 65535], function 06 - write holding register

        :param      modbus_registers:   The modbus registers
        :type       modbus_registers:   dict

        :returns:   Amount of failed content and failed registers as dict
        :rtype:     tuple
        """
        failed_reg_counter = 0
        failed_reg_log = dict()

        for key, val in modbus_registers.items():
            self.logger.debug('\tkey: {}'.format(key))
            self.logger.debug('\t\tval: {}'.format(val))

            register_address = val['register']
            set_val = val['val']
            count = val['len']

            # @TODO fix me for larger numbers than 4294967296
            if set_val > 65535 and count > 1:
                c, f = divmod(set_val, 65535)

                response = self.client.write_register(
                    address=register_address,
                    value=c,
                    unit=self.unit)

                response = self.client.write_register(
                    address=register_address + 1,
                    value=f,
                    unit=self.unit)
            else:
                response = self.client.write_register(address=register_address,
                                                      value=set_val,
                                                      unit=self.unit)

            if response.isError():
                failed_reg_counter += 1
                failed_reg_log[key] = False
                self.logger.warning('Failed to set {} to {}'.
                                    format(register_address, set_val))
            else:
                self.logger.debug('Successfully set {} to {}'.
                                  format(register_address, set_val))

        return failed_reg_counter, failed_reg_log

    def read_ists_registers(self,
                            modbus_registers: dict,
                            check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all discrete input registers.

        Ists (only getter) [0, 1], function 02 - read input status (discrete
        inputs/digital input)

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

            response = self.client.read_discrete_inputs(
                address=register_address,
                count=count,
                unit=self.unit)

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
                             modbus_registers: dict,
                             check_expectation: bool) -> Tuple[int, dict]:
        """
        Read all input registers.

        Iregs (only getter) [0, 65535], function 04 - read input registers

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

            response = self.client.read_input_registers(
                address=register_address,
                count=count,
                unit=self.unit)

            if response.isError():
                register_content[key] = False
                invalid_reg_counter += 1
            else:
                self.logger.debug('\t\tregisters: {}'.format(response))
                registers = response.registers
                self.logger.debug('\t\tregisters: {}'.format(registers))

                if count == 1:
                    register_val = registers[0]
                elif count == 2 and len(registers) == 2:
                    # actual a uint32_t value, reconstruct it
                    register_val = registers[0] << 16 | registers[1]
                else:
                    # using a higher range than available is save and will just
                    # return all available content of the list
                    register_val = registers[0:count]

                try:
                    restored = self.restore_human_readable_content(
                        key=key,
                        value=register_val)
                except Exception:
                    restored = ''

                if restored != '':
                    self.logger.info('\t[{}]\t{}'.format(restored,
                                                         register_description))
                    self.logger.debug('\t{}\t{}'.format(register_val,
                                                        register_description))
                    register_content[key+'_HUMAN'] = restored
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
