#!/usr/bin/env python3
#
#  _app.py
"""
The Flask app itself.

Don't import from here; import directly from ``dependency_dash`` itself.
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
import mimetypes
import os
from http import HTTPStatus
from typing import Any, Dict, Optional

# 3rd party
from domdf_python_tools.paths import PathPlus
from flask import Flask, Response, redirect, request, url_for
from flask_restx import Api  # type: ignore[import]
from wtforms import Form, StringField  # type: ignore[import]

__all__ = ["app", "api"]

try:
	# 3rd party
	from dotenv import load_dotenv
except ImportError:
	pass
else:
	load_dotenv()  # take environment variables from .env.

app = Flask("dependency_dash", template_folder=(PathPlus(__file__).parent / "templates").as_posix())
api = Api(app, prefix="/api", doc="/api/")
app.config["SWAGGER_UI_DOC_EXPANSION"] = "full"  # change to list when there's another endpoint
app.config["JSON_SORT_KEYS"] = False
app.config["DD_ROOT_URL"] = os.getenv("DD_ROOT_URL", "http://localhost:5000")


class GoToForm(Form):
	search = StringField('')


@app.context_processor
def inject_constants() -> Dict[str, Any]:
	return {
			"show_sidebar": False,
			"root_url": app.config["DD_ROOT_URL"],
			"list": list,
			"form": GoToForm(request.form),
			}


def https_redirect() -> Optional[Response]:
	# Based on https://stackoverflow.com/a/59771351
	# By Maximilian Burszley <https://stackoverflow.com/users/8188846/maximilian-burszley>
	# CC BY-SA 4.0

	if not request.endpoint:
		return None

	if request.scheme != "http":
		return None

	view_args: Dict[str, Any] = request.view_args or {}
	args: Dict[str, Any] = dict(request.args or {})

	retval = redirect(
			url_for(
					request.endpoint,
					_scheme="https",
					_external=True,
					**view_args,
					**args,
					),
			HTTPStatus.PERMANENT_REDIRECT,
			)

	return retval  # type: ignore[return-value]


if "ON_HEROKU" in os.environ:
	app.before_request(https_redirect)


@app.after_request
def add_header(response: Response) -> Response:
	response.headers["X-Clacks-Overhead"] = "GNU Terry Pratchett"
	return response


# Register image mimetypes
mimetypes.types_map[".webp"] = "image/webp"
mimetypes.types_map[".avif"] = "image/avif"
