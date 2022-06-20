#!/usr/bin/env python3
#
#  api.py
"""
Common API Models.
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
from flask_restx import fields  # type: ignore[import]

# this package
from dependency_dash._app import api

__all__ = [
		"project_urls_model",
		"requirement_data_model",
		]

project_urls_model = api.model(
		"Project_URLs", {
				'*': fields.String(example="https://github.com/python-coincidence/coverage_pyver_pragma"),
				}
		)

requirement_data_model = api.model(
		"Requirement_Data",
		{
				"requirement": fields.String(example='importlib-metadata>=3.6.0; python_version < "3.9"'),
				"status": fields.String(example="up-to-date"),
				"name": fields.String(example="importlib-metadata"),
				"home_page": fields.Url(example="https://github.com/python/importlib_metadata"),
				"license": fields.String(example="MIT"),
				"package_url": fields.Url(example="https://pypi.org/project/importlib-metadata/"),
				"project_urls": fields.Nested(project_urls_model),
				"all_versions": fields.List(fields.String(example="1.2.3")),
				"current_version": fields.String(example="4.6.4"),
				}
		)
