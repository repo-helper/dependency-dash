{% set title = "Usage" %}
{% set description = "dependency-dash has two main views: 'user' and 'repository'. The repository view shows the project's dependencies, grouped by file." %}

{% macro pep(number) -%}
    [PEP {{ number }}](https://www.python.org/dev/peps/pep-{{ number }}/)
{%- endmacro %}
{% macro linked_image(alt, url) -%}
    [![{{ alt }}]({{ url }})]({{ url }})
{%- endmacro %}
{% macro status(type) -%}
    <span class="status-{{ type }}">{{ type }}</span>
{%- endmacro %}

# {{ title }}

`dependency-dash` has two main views: "user" and "repository".
The repository view shows the project's dependencies, grouped by file.
The image below gives an overview of the various elements of the repository page.


{{ linked_image("overview of the repository page", "/static/img/usage_repository.png") }}


Clicking the filename bar will collapse the table for that file, which may make navigation easier on mobile.

-----

The user page has a simpler view, showing all repositories belonging to the user and their overall status:

{{ linked_image("overview of the user page", "/static/img/usage_user.png") }}

-----

The status column on both pages has four states:

* {{ status("up-to-date") }} – The range given by the {{ pep(440) }} version specifier includes the latest, non-prerelease, version.
* {{ status("outdated") }} – A newer version of the dependency is available.
* {{ status("invalid") }} – The dependency's latest version could not be parsed because it does not conform to {{ pep(440) }}, or another error occurred when determining the latest version.
* {{ status("unsupported") }} – This is only shown on the user page, and indicates the repository did not contain any supported files from which to parse requirements.

<style>

ul span {
    padding: 2px !important;
}

</style>
