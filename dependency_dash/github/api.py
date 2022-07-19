#!/usr/bin/env python3
#
#  api.py
"""
REST API for GitHub backend.
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
from typing import Dict, Tuple
from urllib.parse import urljoin

# 3rd party
import github3
import github3.repos.contents
from flask_restx import Namespace, Resource, fields  # type: ignore[import]

# this package
from dependency_dash._app import app
from dependency_dash.github._env import GITHUB
from dependency_dash.pypi import get_dependency_status
from dependency_dash.pypi.api import requirement_data_model

__all__ = ["GitHubProjectAPI", "api", "github_project_model"]

api = Namespace("GitHub", path="/github", description="API for GitHub Repositories")

github_project_model = api.model("GitHub_Project", {
		'*': fields.List(fields.Nested(requirement_data_model)),
		})


def error404(message: str) -> Tuple[Dict[str, str], int]:
	"""
	Raise a HTTP 404 error, with a link to the documentation.

	:param message:
	"""

	return {
		"message": str(message),
		"documentation_url": urljoin(app.config["DD_ROOT_URL"], "/api#/GitHub/get_github_project"),
		}, 404


@api.route("/<username>/<repository>/")
@api.doc(
		params={
				"username": "The GitHub user / organization which owns the repository.",
				"repository": "The GitHub repository.",
				}
		)
class GitHubProjectAPI(Resource):
	"""
	API corresponding to ``/github/<username>/<repository>``.
	"""

	@api.response(200, "Success", github_project_model)
	@api.response(404, "Repository not found or no supported files in repository.")
	@api.doc(id="get_github_project")
	def get(self, username: str, repository: str) -> Tuple[Dict, int]:
		"""
		Returns a JSON response, giving the status for each of the repository's dependencies.
		"""

		try:
			repo = GITHUB.repository(username, repository)
		except github3.exceptions.NotFoundError:
			return error404("Repository not found")

		# this package
		from dependency_dash.github import get_repo_requirements

		try:
			data = get_repo_requirements(repo.full_name, repo.default_branch)
		except NotImplementedError:
			return error404("No supported files in repository")
		else:

			output = defaultdict(list)
			overall_data = []

			for filename, requirements, invalid, counts in data:
				dependencies = list(get_dependency_status(requirements))

				if counts:
					overall_data.extend(dependencies)

				for req, status, req_data in dependencies:
					req_data["current_version"] = req_data.pop("version")
					output[filename].append({"requirement": str(req), "status": status, **req_data})

			return output, 200


@app.route("/api/<path:path>")
def api_error_404(path: str) -> Tuple[Dict[str, str], int]:
	return {
		"message": "Not Found",
		"documentation_url": urljoin(app.config["DD_ROOT_URL"], "/api"),
		}, 404
