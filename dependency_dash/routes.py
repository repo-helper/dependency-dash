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
from flask import redirect, render_template, request  # type: ignore
from wtforms import Form, SelectField, StringField, SubmitField  # type: ignore

# this package
from dependency_dash._app import app

__all__ = ["home"]


class GoToForm(Form):
	search = StringField('')


@app.route('/')
def home():
	"""
	Route for displaying the homepage.
	"""

	return render_template(
			"home.html",
			form=GoToForm(request.form),
			)


@app.route("/about/")
def about():
	"""
	Route for displaying the "about" page.
	"""

	return render_template(
			"about.html",
			form=GoToForm(request.form),
			)


@app.route("/search/", methods=["POST"])
@app.route("/search", methods=["POST"])
def search():
	return redirect(f"/github/{GoToForm(request.form).data['search']}", code=302)
