{% set title = "Configuration" %}
{% set description = "dependency-dash doesn't require any configuration for basic usage. However, it can be customised to check requirements in additional/different files." %}

{% macro pep(number) -%}
    [PEP {{ number }}](https://www.python.org/dev/peps/pep-{{ number }}/)
{%- endmacro %}
{% macro toml(type) -%}
    [{{ type }}](https://toml.io/en/v0.5.0#{{ type }}/)
{%- endmacro %}

# {{ title }}

`dependency-dash` doesn't require any configuration for basic usage.
However, it can be customised to check requirements in additional/different files.

Customisation is placed in a `tool.dependency-dash` table within the
`pyproject.toml` file in the repository root.
See [PEP 518](https://www.python.org/dev/peps/pep-0518/)
for more details about `pyproject.toml`.

Configuration for a single file would look like this:

```toml

[tool.dependency-dash."setup.py"]
format = "setup.py"
order = 30
include = false
```

The final part of the table name, ``"setup.py"``, is the name of the file the configuration is for.
This can include a forward slash path separator, for example ``"doc-source/requirements.txt``.

The table understands the following keys:

#### format

**Type**: {{ toml("String") }}

The format of the file. Supported formats are:

* `pyproject.toml` – a [TOML](https://toml.io/en/)-format file structured per {{ pep(518) }}. The requirements may either be in `project.dependencies` (per {{ pep(621) }}) or in `tool.flit.metadata.requires` (for [flit](https://flit.readthedocs.io/en/latest/)).
* `setup.cfg` – a setuptools [`setup.cfg`](https://setuptools.readthedocs.io/en/latest/userguide/declarative_config.html)) file.
* `setup.py` – a distutils/setuptools `setup.py` file.
* `requirements.txt` – a file containing a list of {{ pep(508) }} requirements, one per line.

If no format is given it will be inferred from the filename, falling back to `requirements.txt`.

#### order

**Type**: {{ toml("Integer") }}

The order the file should appear when displayed on the dashboard.
If you don't care about the order, or if you only have one file, you can ignore this field.


#### include

**Type**: {{ toml("Boolean") }}

Whether the requirements in the file should be included in the overall repository score.

-----

After you've made changes to your ``pyproject.toml`` file and pushed to GitHub, it may take a few minutes for the changes to show up. Please be patient; it shouldn't be more than 5 minutes.
