# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
## [x.y.z] - yyyy-mm-dd
### Added
### Changed
### Removed
### Fixed
-->
<!--
RegEx for release version from file
r"^\#\# \[\d{1,}[.]\d{1,}[.]\d{1,}\] \- \d{4}\-\d{2}-\d{2}$"
-->

## Released
## [1.3.0] - 2022-10-23
### Changed
- `modbus_wrapper` folder replaced by [`be-modbus-wrapper`][ref-modbus-wrapper]
  package, see [#7][ref-issue-7]
- Module imports of `log_modbus_to_database`, `read_device_info_registers` and
  `write_device_info_registers` scripts updated

## [1.2.0] - 2022-09-09
### Added
- Install `be-helpers` package with [`requirements.txt`](requirements.txt)
- Badges and TOC in `README`

### Changed
- Import `be_helpers` instead of `module_helper` in all modules and scripts
- Action performed by `VAction` replaced with `count` action of argparse
  argument `--verbose, -v`

### Removed
- Remove `module_helper`
- Import of `VAction` from all scripts

## Fixed
- `get_available_ref()` of `GitWrapper` takes also not annotated tags into
  account, see [#8][ref-issue-8]

## [1.1.0] - 2022-02-20
### Added
- `mysql_wrapper.py` added to `db_wrapper`
- Description for converting `sqlite3` to `sql` in `README`
- Usage example for Modbus logging to MySQL database in `README`
- Modbus register map of MyEVSE added to [example](example) folder
- `mysql-connector-python` added to `requirements.txt`

### Changed
- Timestamp is saved as `YYYY-MM-DD HH:MM:SS` in `modbus_wrapper` for ISO 8601
- Update modbus data files in [example](example) with new timestamp format
- `log_modbus_to_database` script can be used with SQlite or MySQL
- `requirements.txt` updated with info about modules using specific package

### Fixed
- `log_modbus_to_database` script uses new Modbus request API and opens a
  connection before a request
- Add missing length definitions in example modbus register setting file
- Some typos in comments

## [1.0.0] - 2022-01-11
### Added
- First breaking change since 9 releases :)
- Provide property for latest read register data, bus ID unit, client and
   connection in `ModbusWrapper` class
- Connection to device can be setup once with `setup_connection` function
- Connection status can be set with `connect` and checked with `connection`
  property

### Changed
- `read_all_registers` and `write_all_registers` require setup and opened
  connection beforehand
- All register operation functions use setup connection and unit instead of
  function call arguments for client and unit
- Import level decreased by adjusting content of module `__init__.py` file
- `F401` is ignored for all `__init__.py` files

### Fixed
- Shebang of `log_modbus_to_database.py`, `read_device_info_registers.py` and
  `write_device_info_registers.py` is `python3` instead of unspecific `python`
- Yet another set of flake8 warnings removed

## [0.9.0] - 2021-12-17
### Added
- Modbus register name defines can contain numbers
- `.gitignore` file added with default python ignores

### Changed
- Set register description to `""` if no description is provided in input
  modbus register header file
- Set semver informations to `0.1.0` in case no semver version could be parsed

## [0.8.0] - 2021-10-04
### Added
- Holding registers and coils can be set via functions or based on input JSON
- Example script to set registers with JSON file

### Changed
- Update README with example usage of register setting script

### Fixed
- Usage example for modbus requests on TCP use correct `port` instead of `unit`
- Catch error on restoring data to human readable content and skip restoring
- Reconstruct possible uint32_t only if length of response allows access to
  required list position

## [0.7.0] - 2021-07-31
### Added
- `log_modbus_to_database` module added
- `get_table_size` functions added to `sqlite_wrapper.py`
- Database wrapper documented
- Unix timestamp in JSON of requested modbus data results
- Modbus connection info added to example register JSON files
- Holding registers can be decoded to human readable content
- Decode response of Phoenix EVSE to human readable content
- Decode response of MyEVSE to human readable content
- Baudrate of RTU connection can be specified for `modbus_wrapper.py`
- Flake8 ignore file

### Changed
- `execute_sql_query` returns result of sql execution
- Connection to backuped database is not automatically closed
- Backup progress can be printed on `backup_db_to_file`

### Fixed
- Usage examples use same CLI parameter style
- Help info text corrected on all modules
- Check existance of output file/folder path of modules scripts
- Treat argparse arguments as int if int is expected
- Human readable restored register content keywords are sorted alphabetically
- No more unused imports and other flake8 warnings

## [0.6.0] - 2021-07-24
### Added
- requirements file with all used python packages of the python module folder
  inside modules
- `set_logger_verbose_level` and `convert_string_to_uint16t` functions added
  to `module_helper.py`
- `parser_valid_file`, `parser_valid_dir`, `check_file` and `check_folder` are
  class methods of `module_helper.py`
- `restore_human_readable_content` function added to `modbus_wrapper.py`
- Example folder with output files of all python modules
- Filename in vcs info file header is filled with filename or `vcsInfo.h` as
  default
- Provided usage description of all python modules inside [modules](modules)

### Changed
- List of lines can now be saved with a linebreak `\n` after each line
- requirements file split into general buildsystem packages and python module
  folder specific packages
- All loggers are created and configured by `module_helper.py` functions
- Moved `generate_modbus_json.py` from [scripts](scripts) to [modules](modules)

### Fixed
- Request registers only if defined in the register input file
- Response of modbus request is only processed if not an error

## [0.5.0] - 2021-06-15
### Added
- `modbus_wrapper` module added
- JSON content can be sorted before saving in `save_json_file` function

### Fixed
- Added missing docstring of `get_random_string`

## [0.4.0] - 2021-06-14
### Added
- `get_unix_timestamp` and `get_random_string` functions added to
  `module_helper.py`

### Fixed
- Use correct author mail address for python modules and scripts
- No flake8 warnings for all python modules and scripts

## [0.3.0] - 2021-06-09
### Changed
- `generate_modbus_json.py` uses given output file name or defines the file
  name as `registers.json` if a path is given as output argument

## [0.2.0] - 2021-06-04
### Added
- Commit SHA is added as comment before the commit SHA as numbers to vcs info
  file
- VCS informations can be generated by `generate_vcs.py`
- All tags, all tags sorted by date and described commit added to git dict
- Described commit can be returned by function of git wrapper module
- JSON file of modbus registers header file can be generated
- Modbus data from remote RTU or TCP devices can be collected based on modbus
  register JSON file content

## [0.1.0] - 2021-05-17
### Added
- This changelog file
- Compilation info generator module and script
- Structure info generator module and script
- requirements file with all used python packages

<!-- Links -->
[Unreleased]: https://github.com/brainelectronics/python-modules/compare/1.3.0...develop

[1.3.0]: https://github.com/brainelectronics/python-modules/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/brainelectronics/python-modules/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/brainelectronics/python-modules/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/brainelectronics/python-modules/compare/0.9.0...1.0.0
[0.9.0]: https://github.com/brainelectronics/python-modules/compare/0.8.0...0.9.0
[0.8.0]: https://github.com/brainelectronics/python-modules/compare/0.7.0...0.8.0
[0.7.0]: https://github.com/brainelectronics/python-modules/compare/0.6.0...0.7.0
[0.6.0]: https://github.com/brainelectronics/python-modules/compare/0.5.0...0.6.0
[0.5.0]: https://github.com/brainelectronics/python-modules/compare/0.4.0...0.5.0
[0.4.0]: https://github.com/brainelectronics/python-modules/compare/0.3.0...0.4.0
[0.3.0]: https://github.com/brainelectronics/python-modules/compare/0.2.0...0.3.0
[0.2.0]: https://github.com/brainelectronics/python-modules/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/brainelectronics/python-modules/tree/0.1.0

[ref-issue-7]: https://github.com/brainelectronics/python-modules/issues/7
[ref-issue-8]: https://github.com/brainelectronics/python-modules/issues/8

[ref-modbus-wrapper]: https://pypi.org/project/be-modbus-wrapper/
