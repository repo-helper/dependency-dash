#!/usr/bin/env python3
#
#  github/routes.py
"""
Routes for the GitHub frontend.
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
from collections import Counter
from operator import itemgetter
from sys import intern

# 3rd party
import github3
from flask import Response, render_template, request
from packaging.requirements import InvalidRequirement
from packaging.version import InvalidVersion
from shippinglabel.requirements import ComparableRequirement

# this package
from dependency_dash._app import app
from dependency_dash.badges import make_badge, serve_badge
from dependency_dash.github import _bad_repo_badge, get_repo_requirements, iter_repos_for_user
from dependency_dash.github._env import GITHUB
from dependency_dash.github.api import GitHubProjectAPI  # noqa: F401
from dependency_dash.htmx import htmx
from dependency_dash.pypi import _format_internal_link, format_project_links, get_dependency_status
from dependency_dash.utils import _normalize

__all__ = [
		"badge_github_project",
		"github",
		"github_project",
		"github_user",
		"htmx_github_project",
		"htmx_github_user",
		]

STATUS_TEMPLATE_FILE = intern("repository_status.html")


@app.route("/github/")
def github() -> Response:
	"""
	Route for displaying the GitHub frontend landing page.
	"""

	return Response(render_template("github_search.html"))


@app.route("/github/<username>/<repository>/")
def github_project(username: str, repository: str) -> Response:
	"""
	Route for displaying information about a single github repository.

	:param username: The user or organization that owns the repository.
	:param repository: The repository name.
	"""

	project_name = f"{username}/{repository}"

	try:
		repo = GITHUB.repository(username, repository)
	except github3.exceptions.NotFoundError:
		return Response(
				render_template(
						"project_404.html",
						project_name=project_name,
						description=f"Dependency status for https://github.com/{project_name}",
						search_url="/search/github/",
						),
				404,
				)

	return Response(
			render_template(
					"project.html",
					project_name=repo.full_name,
					data_url=f"/htmx/github/{repo.full_name}/{repo.default_branch}/",
					description=f"Dependency status for https://github.com/{repo.full_name}",
					search_url="/search/github/",
					),
			)


@htmx(app, "/github/<username>/<repository>/<branch>/")
def htmx_github_project(username: str, repository: str, branch: str) -> str:
	"""
	HTMX callback for obtaining the requirements table for the given repository.

	:param username: The user or organization that owns the repository.
	:param repository: The repository name.
	:param branch: The repository's default branch name.
	"""

	try:
		data = get_repo_requirements(f"{username}/{repository}", branch)
	except NotImplementedError:
		return render_template("no_supported_files.html")
	else:

		# TODO: list invalid requirements
		return render_template(
				"dependency_table.html",
				data=data,
				get_dependency_status=get_dependency_status,
				format_project_links=format_project_links,
				make_badge=make_badge,
				normalize=_normalize,
				format_internal_link=_format_internal_link,
				)


@app.route("/github/<username>/<repository>/badge.svg")
def badge_github_project(username: str, repository: str) -> Response:
	"""
	Route for displaying the status badge for the given project.

	:param username: The user or organization that owns the repository.
	:param repository: The repository name.
	"""

	# TODO: etag caching

	try:
		repo = GITHUB.repository(username, repository)
	except github3.exceptions.NotFoundError:
		return _bad_repo_badge("not found")

	try:
		data = get_repo_requirements(repo.full_name, repo.default_branch)
	except NotImplementedError:
		return _bad_repo_badge("unsupported")

	else:
		all_requirements: list[ComparableRequirement] = []
		for filename, requirements, invalid, include in data:
			if include:
				all_requirements.extend(requirements)

		badge_svg = make_badge(get_dependency_status(all_requirements))

		return serve_badge(badge_svg)


@app.route("/github/<username>/")
def github_user(username: str) -> str:
	"""
	Route for displaying information about a all repositories owned by ``username``.

	:param username: The user or organization to display information for.
	"""

	return render_template(
			"user.html",
			username=username,
			data_url=f"/htmx/github/{username}/",
			search_url="/search/github/",
			)


@htmx(app, "/github/<username>/")
def htmx_github_user(username: str) -> str:
	"""
	HTMX callback for obtaining the projects table for the given user.

	:param username: The user or organization to display information for.
	"""

	if "repo" in request.args:
		repo = GITHUB.repository(*request.args["repo"].split('/'))

		try:
			data = get_repo_requirements(repo.full_name, repo.default_branch)
		except NotImplementedError:
			return render_template(STATUS_TEMPLATE_FILE, status="unsupported")

		try:
			all_requirements: list[ComparableRequirement] = []
			for filename, requirements, invalid, include in data:
				if include:
					all_requirements.extend(requirements)

			dependencies = list(get_dependency_status(all_requirements))
			status_counts = Counter(map(itemgetter(1), dependencies))

			if status_counts.get("insecure", 0):
				return render_template(
						STATUS_TEMPLATE_FILE,
						status=f'{status_counts["insecure"]} insecure',
						status_class="status-insecure",
						)
			elif status_counts.get("outdated", 0):
				return render_template(
						STATUS_TEMPLATE_FILE,
						status=f'{status_counts["outdated"]} outdated',
						status_class="status-outdated",
						)
			elif status_counts.get("prerelease", 0):
				return render_template(
						STATUS_TEMPLATE_FILE,
						status=f'{status_counts["prerelease"]} prerelease',
						status_class="status-prerelease",
						)
			else:
				return render_template(STATUS_TEMPLATE_FILE, status="up-to-date")

		except (InvalidRequirement, InvalidVersion):
			return render_template(STATUS_TEMPLATE_FILE, status="invalid")

	page = int(request.args.get("page", 1))

	try:
		user = GITHUB.user(username)
	except github3.exceptions.NotFoundError:
		try:
			user = GITHUB.organization(username)
		except github3.exceptions.NotFoundError:
			return "<h6>User not found.</h6>"

	repositories = {}

	for repo in iter_repos_for_user(user, page):
		repositories[repo.full_name] = ("loading...", "status-unsupported")

	return render_template(
			"repositories_table.html",
			repositories=repositories,
			data_url=f"/htmx/github/{username}/",
			page=int(page) + 1,
			)
