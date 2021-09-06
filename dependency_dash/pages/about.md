{% set title = "About" %}
{% set description = "dependency-dash uses bootstrap for styling, flask for the backend, and htmx for lazy loading." %}


{% macro github_link(name) %}
	<a href="https://github.com/{{ name }}" class="github-link"><i class="fab fa-github"></i></a>
{% endmacro %}

{% macro docs_link(href) %}
	<a href="{{ href }}" class="docs-link"><i class="fas fa-book"></i></a>
{% endmacro %}


# {{ title }}

<div class="d-flex flex-row about-links">
    <div class="p-2">
        <a href="https://github.com/repo-helper/dependency-dash"><i class="fab fa-github"></i></a>
        <a href="https://github.com/repo-helper/dependency-dash">GitHub</a>
    </div>
</div>

`dependency-dash` uses [bootstrap](https://getbootstrap.com/) for styling,
[flask](https://flask.palletsprojects.com/en/2.0.x/) for the backend,
and [htmx](https://htmx.org/) for lazy loading.

Other libraries used include:

<ul>
    <li>
        <a href="/github/google/pybadges">pybadges</a>
        {{ github_link("google/pybadges") }} for generating status badges.
    </li>
    <li>
        <a href="/github//pypa/packaging">packaging</a>
        {{ github_link("pypa/packaging") }}
        {{ docs_link("https://packaging.pypa.io/en/latest/") }}
        for version parsing and comparison.
    </li>
    <li>
        <a href="/github/repo-helper/pypi-json">pypi-json</a>
        {{ github_link("repo-helper/pypi-json") }}
        {{ docs_link("https://pypi-json.readthedocs.io/en/latest/") }}
        for querying PyPI's JSON API.</li>
    <li>
        <a href="/github/sigmavirus24/github3.py">github3.py</a>
        {{ github_link("sigmavirus24/github3.py") }}
        {{ docs_link("https://github3.readthedocs.io/en/master/") }}
        for querying GitHub's REST API.</li>
</ul>

## License

`dependency-dash` is distributed under the [MIT License](https://choosealicense.com/licenses/mit/).

```
Copyright (c) 2021 Dominic Davis-Foster

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
```

<div class="vspace-15px"></div>

Icons from [Font Awesome](https://fontawesome.com).

```
Font Awesome Free License
-------------------------

Font Awesome Free is free, open source, and GPL friendly. You can use it for
commercial projects, open source projects, or really almost whatever you want.
Full Font Awesome Free license: https://fontawesome.com/license/free.

# Icons: CC BY 4.0 License (https://creativecommons.org/licenses/by/4.0/)
In the Font Awesome Free download, the CC BY 4.0 license applies to all icons
packaged as SVG and JS file types.

# Fonts: SIL OFL 1.1 License (https://scripts.sil.org/OFL)
In the Font Awesome Free download, the SIL OFL license applies to all icons
packaged as web and desktop font files.

# Code: MIT License (https://opensource.org/licenses/MIT)
In the Font Awesome Free download, the MIT license applies to all non-font and
non-icon files.

# Attribution
Attribution is required by MIT, SIL OFL, and CC BY licenses. Downloaded Font
Awesome Free files already contain embedded comments with sufficient
attribution, so you shouldn't need to do anything additional when using these
files normally.

We've kept attribution comments terse, so we ask that you do not actively work
to remove them from files, especially code. They're a great way for folks to
learn about Font Awesome.

# Brand Icons
All brand icons are trademarks of their respective owners. The use of these
trademarks does not indicate endorsement of the trademark holder by Font
Awesome, nor vice versa. **Please do not use brand logos for any purpose except
to represent the company, product, or service to which they refer.**
```
