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

# stdlib
from collections import defaultdict
from urllib.parse import urljoin

# 3rd party
from flask_restx import fields  # type: ignore[import-untyped]
from flask_restx import Namespace, Resource
from packaging.requirements import InvalidRequirement
from pypi_json import PyPIJSON
from shippinglabel import normalize

# this package
from dependency_dash._app import api, app
from dependency_dash.pypi import get_dependency_status, get_package_requirements

__all__ = [
		"project_urls_model",
		"requirement_data_model",
		]

project_urls_model = api.model(
		"Project_URLs",
		{
				'*': fields.String(example="https://github.com/python-coincidence/coverage_pyver_pragma"),
				},
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
				"dependency_dash_url": fields.String(example="/github/python/importlib_metadata/"),
				"all_versions": fields.List(fields.String(example="1.2.3")),
				"current_version": fields.String(example="4.6.4"),
				},
		)

api = Namespace("PyPI", path="/pypi", description="API for PyPI Packages")

pypi_package_model = api.model(
		"PyPI_Package",
		{
				'*': fields.List(fields.Nested(requirement_data_model)),
				},
		)


def error404(message: str) -> tuple[dict[str, str], int]:
	"""
	Raise a HTTP 404 error, with a link to the documentation.

	:param message:
	"""

	return {
		"message": str(message),
		"documentation_url": urljoin(app.config["DD_ROOT_URL"], "/api#/PyPI/get_pypi_package"),
	}, 404


@api.route("/<package_name>/")
@api.doc(params={"package_name": "The PyPI package name."})
class PyPIPackageAPI(Resource):
	"""
	API corresponding to ``/pypi/<package_name>``.
	"""

	@api.response(200, "Success", pypi_package_model)
	@api.response(404, "Package not found or no supported files.")
	@api.doc(id="get_pypi_package")
	def get(self, package_name: str) -> tuple[dict, int]:  # noqa: PRM002
		"""
		Returns a JSON response, giving the status for each of the repository's dependencies.
		"""

		project_name = normalize(package_name)

		with PyPIJSON() as client:
			try:
				metadata = client.get_metadata(project_name)

			except InvalidRequirement:
				return error404("Package not found")

		try:
			data = get_package_requirements(metadata.name)
		except NotImplementedError:
			return error404("No supported files for package")
		else:

			output = defaultdict(list)
			overall_data = []

			for filename, requirements, invalid, counts in data:
				dependencies = list(get_dependency_status(requirements))

				if counts:
					overall_data.extend(dependencies)

				for req, status, req_data in dependencies:
					v: str = req_data.pop("version")  # type: ignore[misc]
					req_data["current_version"] = v  # type: ignore[typeddict-unknown-key]
					output[filename].append({"requirement": str(req), "status": status, **req_data})

			return output, 200
