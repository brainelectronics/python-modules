# Information generator

Generate SCM and directory informations

---------------

## About

This package can generate JSON info files with details about the SCM, directory
and other things.

## Available generators

For the individual usage of a generator, use the brief description and usage
instructions on each generator file.

#### Compilation info generator

Create information file with content of the currently running CI/CD job.

This example call extracts informations about the file `README.md` of the git
repository at `./` and saves the result as `compilation-info.json` in human
readable, formatted and sorted style. An example output can be found at
[example/compilation-info.json](example/compilation-info.json)

```bash
.venv/bin/python3 \
generate_compilation_info.py \
--file README.md \
--git ./ \
--print \
--pretty \
--save \
--output compilation-info.json \
-d -v4
```

#### Structure info generator

Create information file with the available info and target files in all
subdirectories in a specified path.

This example call creates a info about the folder structure at `tests/data`
and saves the result as `structure-info.json` in human readable, formatted and
sorted style. An example output can be found at
[example/structure-info.json](example/structure-info.json)

```bash
.venv/bin/python3 \
generate_structure_info.py \
--root ../modules \
--print \
--pretty \
--save \
--output structure-info.json \
-d -v4
```
