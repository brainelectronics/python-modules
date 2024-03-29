# Python modules

<!-- [![Downloads](https://pepy.tech/badge/be-helpers)](https://pepy.tech/project/be-helpers) -->
![Release](https://img.shields.io/github/v/release/brainelectronics/python-modules?include_prereleases&color=success)
![Python](https://img.shields.io/badge/python3-Ok-green.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- [![codecov](https://codecov.io/github/brainelectronics/be-helpers/branch/main/graph/badge.svg)](https://app.codecov.io/github/brainelectronics/be-helpers) -->

Custom brainelectronics python modules and wrappers

---------------

## About

This is a collection of python modules required for MyEVSE and other
brainelectronics projects.

<!-- MarkdownTOC -->

- [Available generators](#available-generators)
- [Setup](#setup)
	- [Compilation info generator](#compilation-info-generator)
	- [DB wrapper](#db-wrapper)
		- [SQLite](#sqlite)
		- [MySQL](#mysql)
		- [Convert SQLite to MySQL dump](#convert-sqlite-to-mysql-dump)
		- [Install phpLiteAdmin \(optional\)](#install-phpliteadmin-optional)
	- [Git wrapper](#git-wrapper)
	- [Modbus JSON Generator](#modbus-json-generator)
	- [Modbus wrapper](#modbus-wrapper)
		- [Reading data](#reading-data)
			- [Modbus TCP](#modbus-tcp)
			- [Modbus RTU](#modbus-rtu)
		- [Writing data](#writing-data)
			- [Modbus TCP](#modbus-tcp-1)
			- [Modbus RTU](#modbus-rtu-1)
	- [Structure info generator](#structure-info-generator)

<!-- /MarkdownTOC -->

## Available generators

For the individual usage of a generator or wrapper read the brief description
and usage instructions of each module.

## Setup

Create a virtual environment and install the required modules of the
[requirements.txt](requirements.txt) file.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Compilation info generator

Create information file with content of the currently running CI/CD job.

This example call extracts informations about the file `README.md` of the git
repository at `./` and saves the result as `compilation-info.json` in human
readable, formatted and sorted style. An example output can be found at
[example/compilation-info.json](example/compilation-info.json)

```bash
python generate_compilation_info.py \
--file=README.md \
--git=./ \
--print \
--pretty \
--save \
--output=compilation-info.json \
--debug \
--verbose=4
```

### DB wrapper

Request modbus data with the [Modbus wrapper](#modbus-wrapper) and save the
result to a database with optional backup to file.

#### SQLite

This example requests the data of all registers defined in the file of
[example/modbusRegisters-phoenix.json](example/modbusRegisters-phoenix.json)
using `tcp` as connection type from a device with the unit (address) `180`
with an interval of 10 sec for 10 times (iterations), total runtime is 100
sec. A backup of the table `modbus_data` in the database `modbus_db` in RAM
only database is created every `minute` to the folder `backup_folder`. The
response of each request is printed in human readable, formatted and sorted
style to the console.

```bash
python log_modbus_to_database.py \
--file=example/modbusRegisters-phoenix.json \
--connection=tcp \
--address=192.168.178.188 \
--port=180 \
--iterations=10 \
--interval=10 \
--backup=minute \
--print \
--pretty \
--save \
--output=backup_folder \
--database_type=sqlite \
--database=modbus_db \
--table=modbus_data \
--debug \
--verbose=4
```

#### MySQL

This example requests the data of all registers defined in the file of
[example/modbusRegisters-MyEVSE.json](example/modbusRegisters-MyEVSE.json)
using `rtu` as connection type from a device with the unit (address) `10` on
the bus at `9600` baud, with an interval of 5 sec for 20 times (iterations),
total runtime is 100 sec. The data is inserted into the table `modbus_data` in the database `MyEVSE_DB` by the user `data_providing_user` authenticated by
its password `superSecurePassword1` in a MySQL database at `127.0.0.1`. The
response of each request is printed in human readable, formatted and sorted
style to the console.

```bash
python log_modbus_to_database.py \
--file=example/modbusRegisters-MyEVSE.json \
--connection=rtu \
--address=/dev/tty.SLAB_USBtoUART \
--baudrate=9600 \
--unit=10 \
--iterations=5 \
--interval=20 \
--print \
--pretty \
--save \
--database_type=mysql \
--database=MyEVSE_DB \
--table=modbus_data \
--user=data_providing_user \
--password=superSecurePassword1 \
--url=127.0.0.1 \
--debug \
--verbose=4
```

#### Convert SQLite to MySQL dump

To get a quick convertion between the SQLite and the MySQL format use the
following command and may import it in a MySQL instance afterwards.

*Some adjustments might be necessary on the converted SQL file before a
successful import into MySQL*

```bash
sqlite3 modbus_data-01-12-2022-191219.sqlite3 .dump > modbus_data-01-12-2022-191219.sql
```

#### Install phpLiteAdmin (optional)

```bash
# install Apache2
sudo apt-get install apache2 -y

# install PHP and required modules
sudo apt-get install php5 libapache2-mod-php5 php5-sqlite zip unzip -y

# create database folder in web directory
cd /var/www/html
sudo mkdir database
cd database

# download phpLiteAdmin
sudo wget https://bitbucket.org/phpliteadmin/public/downloads/phpLiteAdmin_v1-9-7-1.zip
sudo unzip phpLiteAdmin_v1-9-7-1.zip
sudo rm phpLiteAdmin_v1-9-7-1.zip

# copy example config as real config
sudo cp phpliteadmin.config.sample.php phpliteadmin.config.php

# may adjust username or other configs now in phpliteadmin.config.php

cd ..

# change ownership, access and execution permissions of the database directory
sudo chmod 757 database
sudo chmod 644 database/*.php
sudo chown root:root database
sudo chown root:root database/*
```

To copy all generated SQlite3 databases inside `database` to the phpLiteAdmin
installation directory `/var/www/html/database`, call the following command

```bash
scp -r database/*.sqlite3 username@ip-address:/var/www/html/database
```

At this point the copied/uploaded databases are only readable but not yet
writable/editable by phpLiteAdmin. To make them editable call this command on
the machine running phpLiteAdmin

```bash
sudo chmod 646 /var/www/html/database/*.sqlite3
```

Finally login to phpLiteAdmin with the default password `admin` at
[http://ip-address/database/phpliteadmin.php](http://ip-address/database/phpliteadmin.php)

### Git wrapper

Create a source code information file with the latest git informations.

This example call extracts informations of the git repository at `./` and
saves the result with the default name `vcsInfo.h` in `./`. The output file is
based on the [example/vcsInfo.h.template](example/vcsInfo.h.template) and
filled with the corresponding data. An example output can be found at
[example/vcsInfo.h](example/vcsInfo.h)

```bash
python generate_vcs.py \
--directory=./ \
--print \
--save \
--output=./ \
--debug \
--verbose=4
```

### Modbus JSON Generator

Generate a JSON file for the [Modbus wrapper](#modbus-wrapper) based on a
header file.

The header file, which might be included in some C project, is converted into
a JSON file which is useable by the onwards described
[Modbus wrapper](#modbus-wrapper).

A range or a unit can be given as a comment inside of squared brackets before
the actual description of this register, refer to
[example/modbusRegisters.h](example/modbusRegisters.h). The default output file name is set as `register.json` and located in the same folder as the input file if no output file is specified or a folder is given.

This example call converts the modbus register header file
`example/modbusRegisters.h` and saves the result as `modbusRegisters.json` in
human readable and formatted style. It is not sorted to keep the same order as
the input file. An example output can be found at
[example/modbusRegisters.h](example/modbusRegisters.h)

```bash
python generate_modbus_json.py \
--input=example/modbusRegisters.h \
--print \
--pretty \
--save \
--output=modbusRegisters.json \
--debug \
--verbose=4
```

### Modbus wrapper

Perform read/write requests of modbus registers on TCP or RTU devices.

The unit of the device might be different, e.g. some commercial charging
stations use `180` while ESP devices use `255` by default for TCP. The MyEVSE
is using the bus address (unit) `10` on RTU.

#### Reading data

This example call requests the data of all registers defined in the file of
`example/modbusRegisters-phoenix.json` using either `tcp` (network) or `rtu`
(serial) from a device with the unit (address) `180` (tcp case) or `10` (rtu
case) and saves the result as `result-modbusRegisters-phoenix-info.json` (tcp)
or `result-modbusRegisters-info.json` (rtu) in human readable, formatted and
sorted style. An example output can be found in the [example/](example/)
folder.

##### Modbus TCP

```bash
python read_device_info_registers.py \
--file=example/modbusRegisters-phoenix.json \
--connection=tcp \
--address=192.168.178.188 \
--port=180 \
--print \
--pretty \
--save \
--output=result-modbusRegisters-phoenix-info.json \
--debug \
--verbose=4
```

##### Modbus RTU

```bash
python read_device_info_registers.py \
--file=example/modbusRegisters.json \
--connection=rtu \
--address=/dev/tty.wchusbserial1420 \
--unit=10 \
--baudrate=19200 \
--print \
--pretty \
--save \
--output=result-modbusRegisters-info.json \
--debug \
--verbose=4
```

#### Writing data

This example call sets the data of all registers defined in the file of
`example/set-modbusRegisters-MyEVSE.json` using either `tcp` (network) or `rtu`
(serial) on a device with the unit (address) `180` (tcp case) or `10` (rtu
case) and prints the result in human readable, formatted and sorted style.

##### Modbus TCP

```bash
python3 write_device_info_registers.py \
--file=example/set-modbusRegisters-MyEVSE.json \
--connection=tcp \
--address=192.168.0.8 \
--port=180 \
--print \
--pretty \
--debug \
--verbose=4
```

##### Modbus RTU

```bash
python3 write_device_info_registers.py \
--file=example/set-modbusRegisters-MyEVSE.json \
--connection=rtu \
--address=/dev/tty.wchusbserial1420 \
--unit=10 \
--baudrate=19200 \
--print \
--pretty \
--debug \
--verbose=4
```

### Structure info generator

Create information file with the available info and target files in all
subdirectories in a specified path.

This example call creates a info about the folder structure at `./` and saves
the result as `structure-info.json` in human readable, formatted and
sorted style. An example output can be found at
[example/structure-info.json](example/structure-info.json)

```bash
python generate_structure_info.py \
--root=./ \
--print \
--pretty \
--save \
--output=structure-info.json \
--debug \
--verbose=4
```
