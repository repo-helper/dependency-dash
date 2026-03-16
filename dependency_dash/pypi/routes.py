#!/usr/bin/env python3
#
#  pypi/routes.py
"""
Routes for PyPI frontend.
"""
#
#  Copyright © 2026 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# stdlib

# 3rd party
from flask import Response, render_template
from packaging.requirements import InvalidRequirement
from pypi_json import PyPIJSON
from shippinglabel import normalize
from shippinglabel.requirements import ComparableRequirement

# this package
from dependency_dash._app import app
from dependency_dash.badges import make_badge, serve_badge
from dependency_dash.htmx import htmx
from dependency_dash.pypi import (
		_bad_package_badge,
		_format_internal_link,
		format_project_links,
		get_dependency_status,
		get_package_requirements
		)

__all__ = ["badge_pypi_package", "htmx_pypi_package", "pypi", "pypi_package"]


@app.route("/pypi/")
def pypi() -> Response:
	"""
	Route for displaying the PyPI frontend landing page.
	"""

	return Response(render_template("pypi_search.html"))


@app.route("/pypi/<name>")
def pypi_package(name: str) -> Response:
	"""
	Route for displaying information about a single pypi package.

	:param name: The name of the package.
	"""

	project_name = normalize(name)

	with PyPIJSON() as client:
		try:
			metadata = client.get_metadata(project_name)

		except InvalidRequirement:
			return Response(
					render_template(
							"pypi_package_404.html",
							project_name=project_name,
							description=f"Dependency status for https://pypi.org/project/{project_name}",
							search_url="/search/pypi/",
							),
					404,
					)

	return Response(
			render_template(
					"pypi_package.html",
					project_name=metadata.name,
					data_url=f"/htmx/pypi/{metadata.name}/",
					description=f"Dependency status for https://pypi.org/project/{metadata.name}",
					search_url="/search/pypi/",
					),
			)


@htmx(app, "/pypi/<name>/")
def htmx_pypi_package(name: str) -> str:
	"""
	HTMX callback for obtaining the requirements table for the given PyPI package.

	:param name: The package name.
	"""

	try:
		data = get_package_requirements(name)
	except NotImplementedError:
		return render_template("no_supported_files.html")
	else:
		return render_template(
				"dependency_table.html",
				data=data,
				get_dependency_status=get_dependency_status,
				format_project_links=format_project_links,
				make_badge=make_badge,
				normalize=normalize,
				format_internal_link=_format_internal_link,
				)


@app.route("/pypi/<name>/badge.svg")
def badge_pypi_package(name: str) -> Response:
	"""
	Route for displaying the status badge for the given package.

	:param name: The package name.
	"""

	# TODO: etag caching

	try:
		data = get_package_requirements(name)
	except InvalidRequirement:
		return _bad_package_badge("not found")
	except NotImplementedError:
		return _bad_package_badge("unsupported")

	else:
		all_requirements: list[ComparableRequirement] = []
		for filename, requirements, invalid, include in data:
			if include:
				all_requirements.extend(requirements)

		badge_svg = make_badge(get_dependency_status(all_requirements))

		return serve_badge(badge_svg)
