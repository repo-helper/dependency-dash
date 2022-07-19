#!/usr/bin/env python3
#
#  github.py
"""
GitHub backend.
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
import ast
import hashlib
import re
from collections import Counter
from configparser import ConfigParser
from contextlib import suppress
from datetime import datetime, timedelta
from http import HTTPStatus
from operator import itemgetter
from typing import Any, Callable, Dict, Iterator, List, Set, Tuple, Union

# 3rd party
import dom_toml
import github3
import github3.repos.contents
import platformdirs
import requests
import setup_py_upgrade  # type: ignore[import]
from domdf_python_tools.paths import PathPlus
from flask import Response, render_template, request
from github3.orgs import Organization
from github3.repos import ShortRepository
from github3.users import User
from packaging.requirements import InvalidRequirement
from packaging.version import InvalidVersion
from shippinglabel.requirements import ComparableRequirement, parse_requirements

# this package
from dependency_dash._app import app
from dependency_dash.github._env import GITHUB
from dependency_dash.github.api import GitHubProjectAPI  # noqa: F401
from dependency_dash.htmx import htmx
from dependency_dash.pypi import format_project_links, get_dependency_status, make_badge

__all__ = [
		"SkipFile",
		"badge_github_project",
		"get_requirements_from_github",
		"get_repo_requirements",
		"github_project",
		"github_user",
		"htmx_github_project",
		"htmx_github_user",
		"iter_repos_for_user",
		"parse_pyproject_toml",
		"parse_requirements_txt",
		"parse_setup_cfg",
		"parse_setup_py"
		]

CACHE_DIR = PathPlus(platformdirs.user_cache_dir("dependency_dash")) / "github"


class SkipFile(Exception):
	"""
	Indicate that a file should be skipped when searching for the file containing the project's requirements.
	"""


class SetupPyNodeVisitor(setup_py_upgrade.Visitor):

	def __init__(self):
		super().__init__()
		self._variables: Dict[str, Any] = {}

	def visit_Assign(self, node: ast.Assign) -> Any:
		# Can't understand updates to the variable after assignment.

		try:
			value = ast.literal_eval(node.value)
		except ValueError:
			self.generic_visit(node)
		else:
			for target in node.targets:
				if isinstance(target, ast.Name):
					self._variables[target.id] = value

	def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
		# Can't understand updates to the variable after assignment.

		if node.value is None:
			self.generic_visit(node)
		else:
			try:
				value = ast.literal_eval(node.value)
			except ValueError:
				self.generic_visit(node)
			else:
				if isinstance(node.target, ast.Name):
					self._variables[node.target.id] = value

	def visit_Call(self, node: ast.Call) -> None:
		if setup_py_upgrade.is_setuptools_attr_call(node, "setup"):
			for kwd in node.keywords:
				if kwd.arg not in {"install_requires", "extras_require"}:
					continue

				if isinstance(kwd.value, ast.Name) and kwd.value.id in self._files:
					self.sections["options"][kwd.arg] = f'file: {self._files[kwd.value.id]}'
				elif isinstance(kwd.value, ast.Name) and kwd.value.id in self._variables:
					self.sections["options"][kwd.arg] = self._variables[kwd.value.id]
				else:
					with suppress(ValueError):
						self.sections["options"][kwd.arg] = ast.literal_eval(kwd.value)

		self.generic_visit(node)


def parse_requirements_txt(content: bytes) -> Tuple[Set[ComparableRequirement], List[str]]:
	"""
	Parse the given ``requirements.txt`` content.

	:param content:

	:returns: A set of requirements listed in the file, and a list of syntactically invalid lines.
	"""

	if not content:
		return set(), []  # We assume the presence of an empty file indicates "no requirements"

	requirements, comments, invalid = parse_requirements(
		content.decode("UTF-8").splitlines(),
		include_invalid=True,
		normalize_func=str,
		)

	return requirements, invalid


def parse_pyproject_toml(content: bytes) -> Tuple[Set[ComparableRequirement], List[str]]:
	"""
	Parse the given ``pyproject.toml`` content.

	:param content:

	:returns: A set of requirements listed in the file, and a list of syntactically invalid lines.
	:raises: :exc:`~.SkipFile` if the file has no content,
		or is missing the ``project.dependencies`` or ``tool.flit.metadata.requires`` key.
	"""

	if not content:
		raise SkipFile

	config = dom_toml.loads(content.decode("UTF-8"))

	if "project" in config:
		if "dependencies" not in config["project"]:
			raise SkipFile
		dependencies = config["project"]["dependencies"]
	elif "flit" in config.get("tool", {}):
		if "requires" not in config["tool"].get("flit", {}).get("metadata", {}):
			raise SkipFile
		dependencies = config["tool"]["flit"]["metadata"]["requires"]
	else:
		raise SkipFile

	requirements, comments, invalid_lines = parse_requirements(
		dependencies,
		include_invalid=True,
		normalize_func=str,
		)
	return requirements, invalid_lines


def parse_setup_cfg(content: bytes) -> Tuple[Set[ComparableRequirement], List[str]]:
	"""
	Parse the given ``setup.cfg`` content.

	:param content:

	:returns: A set of requirements listed in the file, and a list of syntactically invalid lines.
	:raises: :exc:`~.SkipFile` if the file has no content, or is missing the ``options.install_requires``.
	"""

	if not content:
		raise SkipFile

	parser = ConfigParser()
	parser.read_string(content.decode("UTF-8"))

	if "options" not in parser.sections():
		raise SkipFile

	options_section = parser["options"]

	if "install_requires" in options_section:
		dependencies = map(str.strip, options_section.get("install_requires").splitlines())
	else:
		raise SkipFile

	requirements, comments, invalid_lines = parse_requirements(
		dependencies,
		include_invalid=True,
		normalize_func=str,
		)
	return requirements, invalid_lines


def parse_setup_py(content: bytes) -> Tuple[Set[ComparableRequirement], List[str]]:
	"""
	Parse the given ``setup.cfg`` content.

	:param content:

	:returns: A set of requirements listed in the file, and a list of syntactically invalid lines.
	:raises: :exc:`~.SkipFile` if the file has no content,
		or is missing the ``install_requires`` argument to ``setup``.
	"""

	if not content:
		raise SkipFile

	try:
		tree = ast.parse(content, filename="setup.py")
	except SyntaxError:
		raise SkipFile

	visitor = SetupPyNodeVisitor()

	try:
		visitor.visit(tree)
	except Exception:
		raise SkipFile

	options_section = visitor.sections["options"]

	if "install_requires" in options_section:
		dependencies = options_section["install_requires"]
	else:
		raise SkipFile

	requirements, comments, invalid_lines = parse_requirements(
		dependencies,
		include_invalid=True,
		normalize_func=str,
		)
	return requirements, invalid_lines


def get_repo_requirements(
		repository_name: str,
		default_branch: str = "master",
		) -> List[Tuple[str, Set[ComparableRequirement], List[str], bool]]:
	"""
	Returns the requirements specified for the given repository.

	The following files are searched, in order:

	* ``requirements.txt``
	* ``pyproject.toml``
	* ``setup.cfg``
	* ``setup.py``

	:param repository_name: The repository's full name.
	:param default_branch: The repository's default branch name.

	:returns: An iterator of tuples containing:

	* The filename containing the requirements,
	* a set of requirements listed in the file,
	* a list of syntactically invalid lines,
	* and whether the file's requirements should count towards the overall status.
	"""

	try:
		files = get_our_config(repository_name, default_branch)
	except (requests.HTTPError, KeyError):
		lookup_map = [
				(parse_requirements_txt, "requirements.txt", True),
				(parse_pyproject_toml, "pyproject.toml", True),
				(parse_setup_cfg, "setup.cfg", True),
				(parse_setup_py, "setup.py", True),
				]

	else:
		lookup_map = []

		# sort by "order" attribute
		for filename, file_config in sorted(files.items(), key=lambda i: i[1].get("order", 0)):
			counts = file_config.get("include", True)

			if "format" in file_config:
				file_format = file_config["format"]
			elif filename == "pyproject.toml":
				file_format = "pyproject.toml"
			elif filename == "setup.cfg":
				file_format = "setup.cfg"
			elif filename == "setup.py":
				file_format = "setup.py"
			else:
				file_format = "requirements.txt"

			if file_format == "pyproject.toml":
				lookup_map.append((parse_pyproject_toml, filename, counts))
			elif file_format == "setup.cfg":
				lookup_map.append((parse_setup_cfg, filename, counts))
			elif file_format == "setup.py":
				lookup_map.append((parse_setup_py, filename, counts))
			else:
				lookup_map.append((parse_requirements_txt, filename, counts))
			# TODO: error on unrecognised format?

	output = []

	for function, filename, counts in lookup_map:
		try:
			requirements, invalid_lines = get_requirements_from_github(
				repository_name, default_branch, file=filename, parse_func=function,
				)
		except (requests.HTTPError, SkipFile):
			continue
		else:
			output.append((filename, requirements, invalid_lines, counts))

	if output:
		return output
	else:
		raise NotImplementedError


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
						),
				404
				)

	return Response(
			render_template(
					"project.html",
					project_name=repo.full_name,
					data_url=f"/htmx/github/{repo.full_name}/{repo.default_branch}",
					description=f"Dependency status for https://github.com/{repo.full_name}",
					)
			)


_normalize_pattern = re.compile(r"\W+")


def _normalize(name: str) -> str:
	return _normalize_pattern.sub('-', name)


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
		return Response("Repository not found.", 404)

	try:
		data = get_repo_requirements(repo.full_name, repo.default_branch)
	except NotImplementedError:
		return Response(render_template("no_supported_files.html"), 404)
	else:
		all_requirements: List[ComparableRequirement] = []
		for filename, requirements, invalid, include in data:
			if include:
				all_requirements.extend(requirements)

		badge_svg = make_badge(get_dependency_status(all_requirements))
		etag = hashlib.sha256(badge_svg.encode("UTF-8")).hexdigest()

		if request.headers.get("If-None-Match") == etag:
			resp = Response(status=HTTPStatus.NOT_MODIFIED)
		else:
			resp = Response(
					make_badge(get_dependency_status(all_requirements)),
					content_type="image/svg+xml;charset=utf-8"
					)

		resp.headers["ETag"] = etag
		resp.headers["Cache-Control"] = "max-age=30"
		resp.headers["Expires"] = (datetime.utcnow() + timedelta(seconds=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
		return resp


@app.route("/github/<username>/")
def github_user(username: str) -> str:
	"""
	Route for displaying information about a all repositories owned by ``username``.

	:param username: The user or organization to display information for.
	"""

	return render_template(
			"user.html",
			username=username,
			data_url=f"/htmx/github/{username}",
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
			return render_template("repository_status.html", status="unsupported")

		try:
			all_requirements: List[ComparableRequirement] = []
			for filename, requirements, invalid, include in data:
				if include:
					all_requirements.extend(requirements)

			dependencies = list(get_dependency_status(all_requirements))
			status_counts = Counter(map(itemgetter(1), dependencies))

			if not status_counts or set(status_counts.keys()) == {"up-to-date"}:
				return render_template("repository_status.html", status="up-to-date")
			# TODO: insecure
			else:
				return render_template(
						"repository_status.html",
						status=f'{status_counts["outdated"]} outdated',
						status_class="status-outdated"
						)
		except (InvalidRequirement, InvalidVersion):
			return render_template("repository_status.html", status="invalid")

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
			data_url=f"/htmx/github/{username}",
			page=int(page) + 1,
			)


def iter_repos_for_user(
		user_or_org: Union[User, Organization],
		page: int,
		) -> Iterator[ShortRepository]:
	"""
	Returns an iterator over all repositories owned py ``user_or_org``.

	:param user_or_org:
	:param page: The page of the repositories (30 repositories per page) to return.
	"""

	url = user_or_org._build_url("users", user_or_org.login, "repos")
	params = {"type": "owner", "sort": "full_name", "direction": "asc", "per_page": 30, "page": int(page)}

	yield from user_or_org._iter(30, url, ShortRepository, params)


def get_requirements_from_github(
		repository: str,
		default_branch: str,
		file: str,
		parse_func: Callable[[bytes], Tuple[Set[ComparableRequirement], List[str]]],
		) -> Tuple[Set[ComparableRequirement], List[str]]:
	"""
	Download a file from GitHub, and parse requirements from it.

	:param repository: The repository to obtain the file from (in the form ``<user>/<repo>``).
	:param default_branch: The repository's default branch (e.g. ``'master'``).
	:param file: The file to download (as a full path relative to the repository root).
	:param parse_func: The function used for parsing the requirements.

	:returns: A set of requirements listed in the file, and a list of syntactically invalid lines.
	"""

	datafile = CACHE_DIR / repository / f"{file}.dat"
	datafile.parent.maybe_make(parents=True)
	url = f"https://raw.githubusercontent.com/{repository}/{default_branch}/{file}"

	etag: str
	expires: datetime

	try:
		data: List[str] = datafile.read_lines()
	except FileNotFoundError:
		response = requests.get(url, timeout=10)
		if response.status_code != 200:
			raise requests.HTTPError  # TODO: better error

		etag = response.headers["etag"]
		expires = datetime.strptime(response.headers["expires"], "%a, %d %b %Y %H:%M:%S %Z")
		content = response.content
		requirements, invalid_lines = parse_func(content)
	else:
		etag = data[0]
		expires = datetime.fromisoformat(data[1])
		requirements_block = data[2:]
		marker = requirements_block.index('\ue000')
		requirements = set(map(ComparableRequirement, requirements_block[:marker]))
		invalid_lines = requirements_block[marker + 1:]

		if expires > datetime.utcnow():
			# Nothing changed
			return requirements, invalid_lines
		else:
			response = requests.get(url, timeout=10, headers={"If-None-Match": etag})
			if response.status_code not in (200, 304):
				raise requests.HTTPError  # TODO: better error

			if response.status_code == 200:
				content = response.content
				requirements, invalid_lines = parse_func(content)

			etag = response.headers["etag"]
			expires = datetime.strptime(response.headers["expires"], "%a, %d %b %Y %H:%M:%S %Z")

	data = [
			etag,
			expires.isoformat(),
			*map(str, requirements),
			'\ue000',
			*invalid_lines,
			]
	datafile.write_lines(data)
	return requirements, invalid_lines


def get_our_config(
		repository: str,
		default_branch: str,
		) -> Dict[str, Dict[str, Any]]:
	"""
	Parse our config from the ``pyproject.toml`` file from GitHub.

	:param repository: The repository to obtain the file from (in the form ``<user>/<repo>``).
	:param default_branch: The repository's default branch (e.g. ``'master'``).

	:returns: The file's contents, parsed as a dictionary.
	"""

	# This makes another request, but I can't find a better way to lay everything out.

	datafile = CACHE_DIR / repository / "dependency-dash.dat"
	datafile.parent.maybe_make(parents=True)
	url = f"https://raw.githubusercontent.com/{repository}/{default_branch}/pyproject.toml"

	etag: str
	expires: datetime

	try:
		data: Dict[str, Any] = datafile.load_json()
	except FileNotFoundError:
		response = requests.get(url, timeout=10)
		if response.status_code != 200:
			raise requests.HTTPError  # TODO: better error

		etag = response.headers["etag"]
		expires = datetime.strptime(response.headers["expires"], "%a, %d %b %Y %H:%M:%S %Z")
		config = dom_toml.loads(response.text)
		if "dependency-dash" not in config.get("tool", {}):
			raise KeyError

		files = config["tool"]["dependency-dash"]

	else:
		etag = data["etag"]
		expires = datetime.fromisoformat(data["expires"])
		files = data["files"]

		if expires > datetime.utcnow():
			# Nothing changed
			return files
		else:
			response = requests.get(url, timeout=10, headers={"If-None-Match": etag})
			if response.status_code not in (200, 304):
				raise requests.HTTPError  # TODO: better error

			if response.status_code == 200:
				config = dom_toml.loads(response.text)
				if "dependency-dash" not in config.get("tool", {}):
					raise KeyError
				files = config["tool"]["dependency-dash"]

			etag = response.headers["etag"]
			expires = datetime.strptime(response.headers["expires"], "%a, %d %b %Y %H:%M:%S %Z")

	data = {
			"etag": etag,
			"expires": expires.isoformat(),
			"files": files,
			}
	datafile.dump_json(data)
	return files


#
# def parse_config():
# 	"""
#
# 	Possible syntax:
#
# 	* Filename to ``requirements.txt``-style.
# 	* ``setup.cfg`` -- to consider the library requirements
# 	# * ``setup.cfg[extra1, extra2]`` -- to consider the extras with the given name
# 	* ``pyproject.toml`` -- to consider the library requirements
# 	# * ``pyproject.toml[extra1, extra2]`` -- to consider the extras with the given name
#
# 	:return:
# 	"""
