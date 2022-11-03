================
dependency-dash
================

.. start short_desc

**A fully Open Source dependency dashboard.**

.. end short_desc


.. start shields

.. list-table::
	:stub-columns: 1
	:widths: 10 90

	* - Tests
	  - |actions_linux| |actions_macos|
	* - PyPI
	  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
	* - Activity
	  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
	* - QA
	  - |codefactor| |actions_flake8| |actions_mypy|
	* - Other
	  - |license| |language| |requires|

.. |actions_linux| image:: https://github.com/repo-helper/dependency-dash/workflows/Linux/badge.svg
	:target: https://github.com/repo-helper/dependency-dash/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_macos| image:: https://github.com/repo-helper/dependency-dash/workflows/macOS/badge.svg
	:target: https://github.com/repo-helper/dependency-dash/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/repo-helper/dependency-dash/workflows/Flake8/badge.svg
	:target: https://github.com/repo-helper/dependency-dash/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/repo-helper/dependency-dash/workflows/mypy/badge.svg
	:target: https://github.com/repo-helper/dependency-dash/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://dependency-dash.repo-helper.uk/github/repo-helper/dependency-dash/badge.svg
	:target: https://dependency-dash.repo-helper.uk/github/repo-helper/dependency-dash/
	:alt: Requirements Status

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/repo-helper/dependency-dash?logo=codefactor
	:target: https://www.codefactor.io/repository/github/repo-helper/dependency-dash
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/dependency-dash
	:target: https://pypi.org/project/dependency-dash/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/dependency-dash?logo=python&logoColor=white
	:target: https://pypi.org/project/dependency-dash/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/dependency-dash
	:target: https://pypi.org/project/dependency-dash/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/dependency-dash
	:target: https://pypi.org/project/dependency-dash/
	:alt: PyPI - Wheel

.. |license| image:: https://img.shields.io/github/license/repo-helper/dependency-dash
	:target: https://github.com/repo-helper/dependency-dash/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/repo-helper/dependency-dash
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/repo-helper/dependency-dash/v0.1.0b1
	:target: https://github.com/repo-helper/dependency-dash/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/repo-helper/dependency-dash
	:target: https://github.com/repo-helper/dependency-dash/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2022
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/dependency-dash
	:target: https://pypi.org/project/dependency-dash/
	:alt: PyPI - Downloads

.. end shields

Installation
--------------

.. start installation

``dependency-dash`` can be installed from PyPI.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install dependency-dash

.. end installation


Usage
--------

Before starting you'll need to `create a personal access token`_.
The token doesn't need access to any additional scopes.

Then set the ``GITHUB_TOKEN`` environment variable to the token.
``dependency-dash`` supports ``.env`` files is you wish to place the token in there instead.

You'll also need to set the ``DD_ROOT_URL`` to the root URL of the web server,
including the scheme.
This defaults to ``http://localhost:5000``.

Then run the app using a `WSGI server`_ such as Gunicorn:

.. code-block:: bash

	$ gunicorn dependency_dash:app -w 4 -b 127.0.0.1

.. _create a personal access token: https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token
.. _WSGI server: https://flask.palletsprojects.com/en/2.0.x/deploying/wsgi-standalone/


About
------


.. image:: https://web-platforms.sfo2.digitaloceanspaces.com/WWW/Badge%203.svg
	:target: https://www.digitalocean.com/?refcode=10ebc51ba008&utm_campaign=Referral_Invite&utm_medium=Referral_Program&utm_source=badge
	:alt: DigitalOcean Referral Badge


The deployed version of this app runs in a dokku_ instance hosted on DigitalOcean. It was previously hosted on Heroku.

.. _dokku: https://dokku.com/
