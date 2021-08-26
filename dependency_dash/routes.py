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

# 3rd party
import jinja2  # type: ignore
import markdown
from domdf_python_tools.compat import importlib_resources
from flask import redirect, render_template, request  # type: ignore
from wtforms import Form, SelectField, StringField, SubmitField  # type: ignore

# this package
from dependency_dash._app import app

__all__ = [
		"home",
		"render_markdown_page",
		"about",
		"usage",
		"configuration",
		"search",
		"page_not_found",
		"server_error",
		]


class GoToForm(Form):
	search = StringField('')


@app.route('/')
def home():
	"""
	Route for displaying the homepage.
	"""

	return render_template("home.html", form=GoToForm(request.form), home=True)


def render_markdown_page(filename: str, template: str = "page.html"):
	"""
	Render a markdown page to HTML.

	:param filename:
	:param template:
	"""

	# Expand "macros"
	raw = importlib_resources.read_text("dependency_dash.pages", filename)
	text = jinja2.Template(raw).render().splitlines()

	md = markdown.Markdown(extensions=["fenced_code", "codehilite", "toc"])

	while not text[0].strip():
		text.pop(0)
	if text[0].startswith("# "):
		title = text[0][2:].strip()
	else:
		title = ''

	body = md.convert('\n'.join(text))

	return render_template(
			template,
			form=GoToForm(request.form),
			body=body,
			title=title,
			)


@app.route("/about/")
def about():
	"""
	Route for displaying the "about" page.
	"""

	return render_markdown_page("about.md", "about.html")


@app.route("/usage/")
def usage():
	"""
	Route for displaying the "usage" page.
	"""

	return render_markdown_page("usage.md")


@app.route("/configuration/")
def configuration():
	"""
	Route for displaying the "configuration" page.
	"""

	return render_markdown_page("configuration.md")


@app.route("/search/", methods=["POST"])
@app.route("/search", methods=["POST"])
def search():
	return redirect(f"/github/{GoToForm(request.form).data['search']}", code=302)


@app.errorhandler(404)
def page_not_found(e):
	"""
	Route for HTTP 404 errors.

	:param e:
	"""

	return render_template("404.html", form=GoToForm(request.form)), 404


@app.errorhandler(500)
def server_error(e):
	"""
	Route for HTTP 500 errors.

	:param e:
	"""

	return render_template("500.html", form=GoToForm(request.form)), 500
