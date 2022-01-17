#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Log read Modbus device register informations to database"""
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         log_modbus_to_database.py.py
#  @date         January, 2022
#  @version      0.2.0
#  @brief        Read all registers via RTU modbus or external IP into database
#
#  @required     pymodbus>=2.3.0,<3, pyserial>=3.5,<4
#
#  @usage
#  python3 log_modbus_to_database.py \
#   --file=example/modbusRegisters.json \
#   --connection=rtu \
#   --address=/dev/tty.SLAB_USBtoUART \
#   --unit=10 \
#   --baudrate=19200 \
#   --iterations=5 \
#   --interval=15 \
#   --backup=hour \
#   --print \
#   --pretty \
#   --save \
#   --output=some_folder \
#   --database_type=sqlite \
#   --database=modbus_db \
#   --table=modbus_data \
#   -v4 -d
#
#  python3 log_modbus_to_database.py \
#   --file=example/modbusRegisters-phoenix.json \
#   --connection=tcp \
#   --address=192.168.0.8 \
#   --port=180 \
#   --iterations=5 \
#   --interval=15 \
#   --backup=minute \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   -a, --address   Address to connect, 192.168.0.8 or /dev/tty.SLAB_USBtoUART
#   -b, --backup    Interval of backup, ['minute', 'hour', 'day', 'month',
#                   'year']
#   --baudrate      Baudrate of RTU connection
#   -c, --connection    Type of Modbus connection, ['tcp', 'rtu']
#   --database      Name of database
#   --database_type Type of database, ['sqlite', 'mysql']
#   -f, --file      Path to Modbus registers file
#   --interval      Interval of requesting data from modbus device given in sec
#   --iterations    Iterations of requesting data and storing in database
#   -o, --output    Path to output file containing info
#   -p, --port      Port of connection, not required for RTU Serial
#   --password      Password of the database user
#   --pretty        Print collected info to stdout in human readable format
#   --print         Print JSON to stdout
#   --raw           Print raw collected info to stdout
#   -s, --save      Save collected informations to file
#   --table         Name of table
#   -u, --unit      Unit of connection
#                   Tobi Test 1, Serial 10, Phoenix 180, ESP 255
#   --url           URL of the database instance
#   --user          Username of database interactions
#
#   -d, --debug     Flag, Output logger messages to stderr (default: False)
#   -v, --verbose   Verbosity level (default: None), sets debug flag to True
#                   '-v3' or '-vvvv' == INFO
#
# ----------------------------------------------------------------------------

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright by brainelectronics, ALL RIGHTS RESERVED"
__credits__ = ["Jonas Scharpf"]
__version__ = "0.2.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "info@brainelectronics.de"
__status__ = "Beta"

import argparse
import datetime
import json
import logging
import time
import sqlite3
from typing import Tuple, Union

# custom imports
from db_wrapper import DBWrapper, MySQLWrapper, SQLiteWrapper
from modbus_wrapper import ModbusWrapper
from module_helper import ModuleHelper, VAction


def setup_database(wrapper: Union[SQLiteWrapper, MySQLWrapper],
                   db_type: str,
                   db_name: str,
                   table_name: str,
                   column_dict: dict,
                   logger: logging.Logger) -> Union[sqlite3.Connection, str]:
    """
    Setup database and table for logging

    :param      wrapper:      The database wrapper
    :type       wrapper:      Union[SQLiteWrapper, MySQLWrapper]
    :param      db_type:      The database type
    :type       db_type:      str
    :param      db_name:      The database name
    :type       db_name:      str
    :param      table_name:   The table name
    :type       table_name:   str
    :param      column_dict:  The column dictionary
    :type       column_dict:  dict
    :param      logger:      The logger
    :type       logger:      logging.Logger

    :returns:   Active SQLite3 connection or database name if MySQL is used
    :rtype:     Union[sqlite3.Connection, str]
    """
    if db_type.lower() == 'sqlite':
        db = wrapper.create_db(db_name=db_name, in_memory=True)
        wrapper.create_table(db=db,
                             table_name=table_name,
                             column_dict=column_dict)
        return db
    elif db_type.lower() == 'mysql':
        wrapper.create_db(db_name=db_name)
        wrapper.create_table(table_name=table_name,
                             column_dict=column_dict,
                             db_name=db_name)
        return db_name
    else:
        logger.warning('{} is an unsupported database type, choose from {}'.
                       format(db_type, ['sqlite', 'mysql']))


def print_table_content(wrapper: Union[SQLiteWrapper, MySQLWrapper],
                        db_type: str,
                        db: Union[sqlite3.Connection, str],
                        table_name: str,
                        logger: logging.Logger) -> None:
    """
    Print all table rows content with logger on INFO level.

    :param      wrapper:     The database wrapper
    :type       wrapper:     Union[SQLiteWrapper, MySQLWrapper]
    :param      db_type:     The database type
    :type       db_type:     str
    :param      db:          The database connection or name
    :type       db:          Union[sqlite3.Connection, str]
    :param      table_name:  The table name
    :type       table_name:  str
    :param      logger:      The logger
    :type       logger:      logging.Logger
    """
    if db_type.lower() == 'sqlite':
        read_content = wrapper.read_table_completly(db=db,
                                                    table_name=table_name)
        size = wrapper.get_table_size(db=db, table_name=table_name)
    elif db_type.lower() == 'mysql':
        read_content = wrapper.read_table_completly(table_name=table_name,
                                                    db_name=db)
        size = wrapper.get_table_size(table_name=table_name, db_name=db)
    else:
        logger.warning('{} is an unsupported database type, choose from {}'.
                       format(db_type, ['sqlite', 'mysql']))

    for idx, ele in enumerate(read_content):
        logger.info('Row {}/{}: {}'.format(idx+1, size, ele))


def request_modbus_data(logger: logging.Logger,
                        mb: ModbusWrapper,
                        args: argparse.Namespace) -> Tuple[dict, dict]:
    """
    Request modbus data from specified device

    :param      logger: The logger
    :type       logger: logging.Logger
    :param      mb:     The modbus device object
    :type       mb:     ModbusWrapper
    :param      args:   The parsed arguments
    :type       args:   argparse object

    :returns:   Dictionary of returned modbus data and raw modbus data
    :rtype:     tuple
    """
    # get the info dict of modbus data
    read_content = mb.read_all_registers(check_expectation=False,
                                         file=args.file)
    logger.debug('Received register content: {}'.format(read_content))

    # remove additional '*_HUMAN' elements and restore them as default
    cleared_dict = dict()
    raw_read_content = dict()
    for key, val in read_content.items():
        if not key.endswith('_HUMAN'):
            restored = mb.restore_human_readable_content(key=key,
                                                         value=val)

            if restored != '':
                value = restored
            else:
                # nothing to be restored for humans
                # all content needs to be string for database insertion
                if not isinstance(val, str):
                    if isinstance(val, dict):
                        value = json.dumps(val)
                    else:
                        value = str(val)
                else:
                    value = val

            cleared_dict[key] = value
            raw_read_content[key] = val

    logger.debug('cleared dict content: {}'.format(cleared_dict))
    logger.debug('raw dict content: {}'.format(raw_read_content))

    return cleared_dict, raw_read_content


def backup_and_create_new_db(logger: logging.Logger,
                             slw: SQLiteWrapper,
                             table_name: str,
                             db_name: str,
                             db: sqlite3.Connection,
                             column_dict: dict,
                             output_folder: str) -> sqlite3.Connection:
    """
    Backup in memory database to file and create new and emptry database.

    :param      logger:         The logger
    :type       logger:         logging.Logger
    :param      slw:            The sqlite wrapper
    :type       slw:            SQLiteWrapper
    :param      table_name:     The table name
    :type       table_name:     str
    :param      db_name:        The database name
    :type       db_name:        str
    :param      db:             The database connection
    :type       db:             sqlite3.Connection
    :param      column_dict:    The column dictionary
    :type       column_dict:    dict
    :param      output_folder:  The output folder
    :type       output_folder:  str

    :returns:   New and empty databas
    :rtype:     sqlite3.Connection
    """
    table_size = slw.get_table_size(db=db, table_name=table_name)

    # create new table only if "old" has some content (rows)
    if table_size and (output_folder is not None):
        now = ModuleHelper.get_unix_timestamp()
        timestring = ModuleHelper.format_timestamp(timestamp=now,
                                                   format="%Y-%m-%d %H:%M:%S")
        file_db_name = '{}/{}-{}'.format(output_folder, table_name, timestring)
        file_db_name = file_db_name.replace(' ', '-').replace(':', '')

        logger.info('Save (backup) content of DB "{}" as "{}"'.
                    format(db_name, file_db_name))

        slw.backup_db_to_file(backup_name=file_db_name, db=db)
        slw.close_connection(db=db)

        db = slw.create_db(db_name=db_name, in_memory=True)
        slw.create_table(db=db, table_name=table_name, column_dict=column_dict)
    else:
        logger.info('Given table {} has no content, will not backup this'.
                    format(table_name))

    return db


def get_backup_time(backup_interval: str) -> int:
    """
    Get timestamp based on backup interval.

    :param      backup_interval:  The backup interval
    :type       backup_interval:  str

    :returns:   The backup time.
    :rtype:     int
    """
    if backup_interval == 'minute':
        this_time = datetime.datetime.now().minute
    elif backup_interval == 'hour':
        this_time = datetime.datetime.now().hour
    elif backup_interval == 'day':
        this_time = datetime.datetime.now().day
    elif backup_interval == 'month':
        this_time = datetime.datetime.now().month
    elif backup_interval == 'year':
        this_time = datetime.datetime.now().year
    else:
        raise ValueError("Unsupported backup interval")

    return this_time


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.

    :raise  argparse.ArgumentError
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Log read Modbus device register informations to SQLite database
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
                        help=('Address of modbus connection, like 192.168.0.8 '
                              'or /dev/tty.SLAB_USBtoUART'),
                        nargs='?',
                        required=True)

    parser.add_argument('-b',
                        '--backup',
                        help='Interval of backup',
                        nargs='?',
                        default="hour",
                        choices=['minute', 'hour', 'day', 'month', 'year'],
                        required=False)

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

    parser.add_argument('--database',
                        help='Name of database',
                        nargs='?',
                        default="modbus_db",
                        required=False)

    parser.add_argument('--database_type',
                        help='Type of database',
                        nargs='?',
                        default="sqlite",
                        choices=['sqlite', 'mysql'],
                        required=False)

    parser.add_argument('-f',
                        '--file',
                        help='Path to Modbus registers file',
                        nargs='?',
                        default="modbusRegisters.json",
                        type=lambda x: ModuleHelper.parser_valid_file(parser,
                                                                      x),
                        required=True)

    parser.add_argument('--interval',
                        help='Interval of requesting data from modbus device '
                             'given in seconds',
                        nargs='?',
                        const=5,
                        type=int,
                        required=False)

    parser.add_argument('--iterations',
                        help='Iterations of requesting data and storing in '
                             'database',
                        nargs='?',
                        const=5,
                        type=int,
                        required=False)

    parser.add_argument('-o', '--output',
                        dest='output_folder',
                        required=False,
                        type=lambda x: ModuleHelper.parser_valid_dir(parser,
                                                                     x),
                        help='Path to output folder of database backup')

    parser.add_argument('-p',
                        '--port',
                        help='Port of connection, not required for RTU Serial',
                        default=502,
                        type=int,
                        required=False)

    parser.add_argument('--password',
                        help='Password of the database user',
                        required=False)

    parser.add_argument('--pretty',
                        dest='print_pretty',
                        action='store_true',
                        help='Print collected info to stdout in human readable'
                        'format')

    parser.add_argument('--print',
                        dest='print_result',
                        action='store_true',
                        help='Print collected (JSON) info to stdout')

    parser.add_argument('--raw',
                        dest='print_raw',
                        action='store_true',
                        help='Print raw collected info to stdout')

    parser.add_argument('-s', '--save',
                        dest='save_info',
                        action='store_true',
                        help='Save database with collected informations to '
                        ' folder specified with --output or -o')

    parser.add_argument('--table',
                        help='Name of table',
                        nargs='?',
                        default="modbus_data",
                        required=False)

    parser.add_argument('-u',
                        '--unit',
                        help=('Unit of connection, '
                              'Phoenix 180, Tobi Test 1, ESP 255, Serial 10'),
                        default=180,
                        type=int,
                        required=False)

    parser.add_argument('--url',
                        help='URL of the database instance',
                        required=False)

    parser.add_argument('--user',
                        help='Username of database interactions',
                        required=False)

    parsed_args = parser.parse_args()

    return parsed_args


def main() -> None:
    helper = ModuleHelper(quiet=True)

    logger = helper.create_logger(__name__)
    db_logger = helper.create_logger("DBWrapper")
    mb_logger = helper.create_logger("ModbusWrapper")

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    helper.set_logger_verbose_level(logger=logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)
    helper.set_logger_verbose_level(logger=db_logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)
    helper.set_logger_verbose_level(logger=mb_logger,
                                    verbose_level=args.verbose,
                                    debug_output=args.debug)

    # log the provided arguments
    logger.debug(args)

    # take CLI parameters
    quiet_mode = not args.debug
    backup_interval = args.backup
    database_type = args.database_type
    db_name = args.database
    modbus_file = args.file
    output_folder = args.output_folder
    print_raw = args.print_raw
    print_result = args.print_result
    print_pretty = args.print_pretty
    request_interval = args.interval
    request_iterations = args.iterations
    save_info = args.save_info
    table_name = args.table

    iteration = 0
    last_backup_time = 0

    if database_type.lower() == 'sqlite':
        dbw = SQLiteWrapper(logger=db_logger, quiet=quiet_mode)
    elif database_type.lower() == 'mysql':
        dbw = MySQLWrapper(user=args.user,
                           password=args.password,
                           host=args.url,
                           logger=db_logger,
                           quiet=quiet_mode)

        # connect to complete MySQL server
        # database and table name are required on all calls
        dbw.connect = True

    mb = ModbusWrapper(logger=mb_logger, quiet=quiet_mode)

    # create table with rows of available modbus registers
    modbus_registers = mb.load_modbus_registers_file(file_path=modbus_file)
    logger.debug('Available Modbus registers: {}'.format(modbus_registers))

    column_dict = DBWrapper.generate_columns_names(registers=modbus_registers,
                                                   field_type='text')
    column_dict['TIMESTAMP'] = 'DATETIME'
    column_dict['DEVICE_UUID_IREG'] = 'text'
    column_dict['COMMIT_SHA_IREG'] = 'text'
    logger.debug('Column dict: {}'.format(column_dict))

    db = setup_database(wrapper=dbw,
                        db_type=database_type,
                        db_name=db_name,
                        table_name=table_name,
                        column_dict=column_dict,
                        logger=db_logger)
    # db and db_name are the same in case the wrapper is for MySQL

    this_time = get_backup_time(backup_interval=backup_interval)
    last_backup_time = this_time

    # setup connection to modbus device
    result = mb.setup_connection(device_type=args.connection,
                                 address=args.address,
                                 port=args.port,
                                 unit=args.unit,
                                 baudrate=args.baudrate)
    if result is False:
        logger.error('Failed to setup connection with {device_type} device '
                     'with bus ID {unit} at {address}:{port}'.
                     format(device_type=args.connection,
                            unit=args.unit,
                            address=args.address,
                            port=args.port))
        exit(-1)

    # open connection to device
    mb.connect = True

    try:
        # run until given amount of iterations are reached
        while iteration < request_iterations:
            iteration += 1
            start_time = ModuleHelper.get_unix_timestamp()
            this_time = get_backup_time(backup_interval=backup_interval)
            timestring = ModuleHelper.format_timestamp(
                timestamp=start_time,
                format="%Y-%m-%d %H:%M:%S")
            logger.info('#{iteration}/{iterations} ({percent:.0%}) at {time}'.
                        format(iteration=iteration,
                               iterations=request_iterations,
                               percent=iteration/request_iterations,
                               time=timestring))

            modbus_data, modbus_data_raw = request_modbus_data(logger=logger,
                                                               mb=mb,
                                                               args=args)
            modbus_data['TIMESTAMP'] = timestring
            modbus_data_raw['TIMESTAMP'] = timestring

            if len(modbus_data) == len(column_dict):
                if database_type.lower() == 'sqlite':
                    dbw.insert_content_into_table(db=db,
                                                  content_dict=modbus_data,
                                                  table_name=table_name)
                elif database_type.lower() == 'mysql':
                    dbw.insert_content_into_table(table_name=table_name,
                                                  content_dict=modbus_data_raw,
                                                  db_name=db)
                else:
                    logger.warning('{} is an unsupported database type, choose'
                                   ' from {}'.format(db_type,
                                                     ['sqlite', 'mysql']))
            else:
                missing_modbus_keys = set(column_dict) - set(modbus_data)
                logger.error('Received different amount of modbus data than '
                             'configured table columns. Missing: {}'.
                             format(missing_modbus_keys))

            # print table content to console with logger
            # print_table_content(wrapper=dbw,
            #                     db_type=database_type,
            #                     db=db,
            #                     table_name=table_name,
            #                     logger=logger)

            # do print as last step
            if print_result:
                if print_pretty:
                    if print_raw:
                        print(json.dumps(modbus_data_raw,
                                         indent=4,
                                         sort_keys=False))
                    else:
                        print(json.dumps(modbus_data,
                                         indent=4,
                                         sort_keys=True))
                else:
                    if print_raw:
                        print(json.dumps(modbus_data_raw, sort_keys=False))
                    else:
                        print(json.dumps(modbus_data, sort_keys=True))

            # dump the database from memory to file
            if (((last_backup_time + 1) == this_time) and
               (save_info and output_folder is not None)):
                logger.info('Time to save memory database to file')
                last_backup_time = this_time

                if database_type.lower() == 'sqlite':
                    db = backup_and_create_new_db(logger=logger,
                                                  slw=dbw,
                                                  table_name=table_name,
                                                  db_name=db_name,
                                                  db=db,
                                                  column_dict=column_dict,
                                                  output_folder=output_folder)
                    logger.info('Backup and new database created')
                elif database_type.lower() == 'mysql':
                    logger.info('MySQL backup not yet implemented')

            # do not wait if this was the last iteration
            if iteration == request_iterations:
                logger.debug('Leaving while loop after last request')
                break

            finish_time = ModuleHelper.get_unix_timestamp()
            next_sleep_time = request_interval - (finish_time - start_time)
            logger.info('Data inserted, sleep now for {} seconds'.
                        format(next_sleep_time))
            if next_sleep_time >= 0.0:
                time.sleep(next_sleep_time)

    except KeyboardInterrupt:
        logger.info('Iteration loop interruped by user')

    if save_info and (output_folder is not None):
        logger.debug('Backup latest data')

        if database_type.lower() == 'sqlite':
            # backup latest data of database to file
            db = backup_and_create_new_db(logger=logger,
                                          slw=dbw,
                                          table_name=table_name,
                                          db_name=db_name,
                                          db=db,
                                          column_dict=column_dict,
                                          output_folder=output_folder)
        elif database_type.lower() == 'mysql':
            logger.info('MySQL backup not yet implemented')

    if database_type.lower() == 'sqlite':
        dbw.close_connection(db=db)
    elif database_type.lower() == 'mysql':
        dbw.close_connection()

    logger.info('Connection to database closed, see you next time again.')


if __name__ == '__main__':
    main()
