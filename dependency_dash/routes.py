#!/usr/bin/env python3
#
#  routes.py
"""
Flask HTTP routes.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
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
from typing import cast

# 3rd party
from flask import Response, render_template, request

# this package
from dependency_dash._app import GoToForm, app
from dependency_dash.markdown import render_markdown_page
from dependency_dash.utils import canonical_url_header

__all__ = [
		"home",
		"about",
		"usage",
		"configuration",
		"search",
		"page_not_found",
		"security_txt",
		"server_error",
		]


@app.route('/')
def home() -> Response:
	"""
	Route for displaying the homepage.
	"""

	return Response(render_template("home.html", home=True), headers=canonical_url_header(request))


@app.route("/.well-known/security.txt")
def security_txt() -> Response:
	"""
	Route for displaying the security.txt file.
	"""

	content = """\
Contact: https://github.com/repo-helper/dependency-dash/security/advisories
Last-Updated: 2023-11-16T14:00:00.000+00:00
Expires: 2024-02-16T14:00:00.000+00:00
"""

	return Response(content, headers={"Content-Type": "text/plain; charset=utf-8"})


@app.route("/about/")
def about() -> Response:
	"""
	Route for displaying the "about" page.
	"""

	return render_markdown_page("about.md", "about.html")


@app.route("/usage/")
def usage() -> Response:
	"""
	Route for displaying the "usage" page.
	"""

	return render_markdown_page("usage.md")


@app.route("/configuration/")
def configuration() -> Response:
	"""
	Route for displaying the "configuration" page.
	"""

	return render_markdown_page("configuration.md")


def search_pypi(query: str) -> Response:
	return app.redirect(f"/pypi/{query}", code=302)


def search_github(query: str) -> Response:
	return app.redirect(f"/github/{query}", code=302)


search_domains = {"github": search_github, "pypi": search_pypi}


@app.route("/search/", methods=["POST"])
@app.route("/search/<domain>/", methods=["POST"])
def search(domain: str = "github") -> Response:  # noqa: PRM002
	"""
	Route for the search page.

	Only accepts POST requests.
	"""

	# TODO: way to indicate from PyPI pages to search without pypi: by default

	query = cast(str, GoToForm(request.form).data["search"]).lower().strip()

	for domain_string, search_fn in search_domains.items():
		domain_prefix = f"{domain_string}:"

		if query.startswith(domain_prefix):
			# Search within specified domain
			query = query.removeprefix(domain_prefix).strip()
			return search_fn(query)

	else:
		# Default domain
		return search_domains[domain](query)


@app.errorhandler(404)
def page_not_found(e: Exception) -> tuple[str, int]:  # noqa: PRM002
	"""
	Route for HTTP 404 errors.
	"""

	return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e: Exception) -> tuple[str, int]:  # noqa: PRM002
	"""
	Route for HTTP 500 errors.
	"""

	return render_template("500.html"), 500
