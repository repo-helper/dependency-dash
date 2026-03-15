#!/usr/bin/env python3
#
#  pypi/__init__.py
"""
Retrieve and cache data from PyPI.
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
import datetime
import os
from collections import Counter
from collections.abc import Iterable, Iterator
from email.utils import parsedate_to_datetime
from operator import itemgetter
from typing import Any, Optional
from urllib.parse import urlparse

# 3rd party
import platformdirs
import requests
from domdf_python_tools.paths import PathPlus
from flask import Response, render_template
from packaging.requirements import InvalidRequirement
from packaging.tags import generic_tags
from packaging.version import InvalidVersion, Version
from pybadges import badge
from pypi_json import ProjectMetadata, PyPIJSON
from remote_wheel import RemoteWheelDistribution
from shippinglabel import normalize
from shippinglabel.requirements import ComparableRequirement

# this package
from dependency_dash._app import app
from dependency_dash.htmx import htmx

__all__ = [
		"format_project_links",
		"get_data",
		"get_dependency_dash_url",
		"get_dependency_status",
		"get_package_requirements",
		"htmx_pypi_package",
		"make_badge",
		"pypi_package",
		]

CACHE_DIR = PathPlus(platformdirs.user_cache_dir("dependency_dash")) / "pypi"


def format_project_links(project_urls: dict[str, str]) -> str:
	"""
	Format the project's links (homepage, GitHub etc.) with hyperlinks and icons.

	The rules are the same as PyPI uses for its "Project links" sidebar.

	:param project_urls:
	"""

	links: dict[str, str] = {}
	if project_urls is None:
		return ''

	for name, url in project_urls.items():
		orig_name = name
		name = name.lower()
		parsed = urlparse(url)

		if name in ["home", "homepage", "home page"]:
			icon = "fas fa-home"
		elif name in ["changelog", "change log", "changes", "release notes", "news", "what's new", "history"]:
			icon = "fas fa-scroll"
		elif (
				name.startswith(("docs", "documentation"))
				or parsed.netloc in ["readthedocs.io", "readthedocs.org", "rtfd.io", "rtfd.org"]
				or parsed.netloc.endswith((".readthedocs.io", ".readthedocs.org", ".rtfd.io", ".rtfd.org"))
				or parsed.netloc.startswith(("docs.", "documentation."))
				):
			continue  # TODO: icon = "fas fa-book"
		elif name.startswith(("bug", "issue", "tracker", "report")):
			continue  # TODO: icon = "fas fa-bug"
		elif parsed.netloc in ["github.com", "github.io"] or parsed.netloc.endswith((".github.com", ".github.io")):
			icon = "fab fa-github"
		elif parsed.netloc == "gitlab.com" or parsed.netloc.endswith(".gitlab.com"):
			icon = "fab fa-gitlab"
		elif parsed.netloc == "bitbucket.org" or parsed.netloc.endswith(".bitbucket.org"):
			icon = "fab fa-bitbucket"
		else:
			continue

		links[icon] = render_template("single_project_link.html", name=orig_name, url=url, icon=icon)

	return ''.join(map(itemgetter(1), sorted(links.items(), key=lambda t: t[0].split()[1])))


def _sort_versions(*versions: str) -> list[str]:

	for_sort = []

	for version in versions:
		try:
			ver_ver = Version(version)
		except InvalidVersion:
			continue
		else:
			for_sort.append((version, ver_ver))

	return [v[0] for v in sorted(for_sort, key=itemgetter(1))]


def get_dependency_dash_url(project_urls: dict[str, str]) -> Optional[str]:
	"""
	Returns the internal dependency-dash URL determined from the given project URLs.

	If no URL can be inferred (because a GitHub URL isn't listed, for instance) an empty string will be returned.

	:param project_urls:
	"""

	# this package
	from dependency_dash.github import parse_repo_url

	if project_urls is None:
		return ''

	for url in project_urls.values():
		parsed = urlparse(url)

		if parsed.netloc in ["github.com"]:
			try:
				username, repo_name = parse_repo_url(url)
			except ValueError:
				continue
			else:
				return f"/github/{username}/{repo_name}/"

	return ''


def get_data(project_name: str) -> dict[str, Any]:
	"""
	Obtain metadata for ``project_name`` from PyPI.

	:param project_name:
	"""

	# TODO: HEAD and check last serial to see if update needed
	project_name = normalize(project_name)

	datafile = CACHE_DIR / project_name[0] / f"{project_name}.json"
	datafile.parent.maybe_make(parents=True)

	def get_updated_data(
			etag: Optional[str] = None,
			stale_data: Optional[dict[str, Any]] = None,
			) -> dict[str, Any]:
		with PyPIJSON() as client:
			query_url = client.endpoint / project_name / "json"

			if etag is None:
				headers = {}
			else:
				headers = {"If-None-Match": str(etag)}

			response: requests.Response = query_url.get(timeout=client.timeout, headers=headers)

			if response.status_code == 404:
				raise InvalidRequirement(f"No such project {project_name!r}")
			elif response.status_code == 304 and etag is not None and stale_data is not None:
				stale_data["last_modified"] = parsedate_to_datetime(response.headers["date"]).timestamp()
				return stale_data
			elif response.status_code != 200:
				raise requests.HTTPError(
						f"An error occurred when obtaining project metadata for {project_name!r}: "
						f"HTTP Status {response.status_code}",
						response=response,
						)

			metadata = ProjectMetadata(**response.json())

			releases = metadata.releases
			# .releases may be None if a version is passed, but in our case we aren't.
			assert releases is not None

			return {
					"name": metadata.info["name"],
					"version": metadata.info["version"],
					"home_page": metadata.info["home_page"] or '',
					"license": metadata.info["license"] or '',
					"package_url": metadata.info["package_url"],
					"dependency_dash_url": get_dependency_dash_url(metadata.info["project_urls"]),
					"project_urls": metadata.info["project_urls"],
					"all_versions": _sort_versions(*releases.keys()),
					"etag": response.headers["etag"],
					"last_modified": parsedate_to_datetime(response.headers["date"]).timestamp(),
					}

	try:
		data = datafile.load_json()

		last_modified = data.get("last_modified")
		if last_modified and datetime.datetime.now().timestamp() - last_modified < 300:  # 5 mins:
			return data

		old_etag = data.get("etag", None)
		if not old_etag:
			data = get_updated_data(stale_data=data)
		else:
			data = get_updated_data(etag=old_etag, stale_data=data)

	except FileNotFoundError:
		data = get_updated_data()

	datafile.dump_json(data)

	return data


def get_dependency_status(
		requirements: Iterable[ComparableRequirement],
		) -> Iterator[tuple[ComparableRequirement, str, dict[str, Any]]]:
	# TODO: TypedDict
	"""
	For the given requirements, determine whether it is up-to-date.

	:param requirements:

	:returns: An iterator over three element tuples comprising:

		* The requirement.
		* Either the string ``"up-to-date"`` or ``"outdated"``.
		* A dictionary containing metadata about the project.
	"""

	for req in sorted(requirements):

		try:
			data = get_data(req.name)
		except InvalidRequirement:
			yield req, "invalid", {
				"name": req.name,
				"version": '',
				"home_page": '',
				"license": '',
				"package_url": '',
				"project_urls": {},
				"dependency_dash_url": '',
				"all_versions": [],
				"etag": '',
				"last_modified": 0.0,
			}
			continue

		latest_version = data["version"]
		version_specifier = req.specifier
		latest_prerelease = max(map(Version, data["all_versions"]))

		if latest_version in version_specifier:
			yield req, "up-to-date", data
		elif latest_prerelease in version_specifier:
			yield req, "prerelease", data
		else:
			yield req, "outdated", data
		# TODO: check against safety's DB. Probably need to enumerate releases from PyPI


def make_badge(dependency_data: Iterator[tuple[ComparableRequirement, str, dict[str, Any]]]) -> str:
	"""
	Construct a badge from the given dependency data.

	:param dependency_data: An iterator over ``(requirement, status, metadata)`` tuples.

	:returns: The SVG badge.
	"""

	status_counts = Counter(map(itemgetter(1), list(dependency_data)))

	if status_counts.get("insecure", 0):
		return badge(
				left_text="dependencies",
				right_text=f'{status_counts["insecure"]} insecure',
				right_color="red",
				)
	elif status_counts.get("outdated", 0):
		return badge(
				left_text="dependencies",
				right_text=f'{status_counts["outdated"]} outdated',
				right_color="orange",
				)
	else:
		return badge(left_text="dependencies", right_text="up-to-date", right_color="#82B805")


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
							),
					404,
					)

	return Response(
			render_template(
					"pypi_package.html",
					project_name=metadata.name,
					data_url=f"/htmx/pypi/{metadata.name}/",
					description=f"Dependency status for https://pypi.org/project/{metadata.name}",
					),
			)


def _format_internal_link(req: ComparableRequirement, data: dict[str, Any]) -> str:
	return f'<a href="/pypi/{normalize(req.name)}" title="View Dependencies">{req.name}</a>'


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


def get_package_requirements(package_name: str) -> list[tuple[str, set[ComparableRequirement], list[str], bool]]:
	"""
	Returns the requirements specified for the given package.

	:param package_name: The package name.

	:returns: An iterator of tuples containing:

	* The (wheel) filename containing the requirements,
	* a set of requirements listed in the file,
	* a list of syntactically invalid lines,
	* and whether the file's requirements should count towards the overall status (always :py:obj:`True`).
	"""

	# TODO: handle sdist-only packages

	# TODO: caching
	# datafile = CACHE_DIR / "wheel-deps" / f"{package_name}.dat"
	# datafile.parent.maybe_make(parents=True)

	with PyPIJSON() as client:
		metadata = client.get_metadata(package_name)
		tag_mapping, non_wheel_urls = metadata.get_wheel_tag_mapping(metadata.version)
		generic_tag = next(generic_tags())
		if generic_tag in tag_mapping:
			wheel_url = tag_mapping[generic_tag]
		else:
			wheel_url = next(iter(tag_mapping.values()))

	with RemoteWheelDistribution.from_url(wheel_url) as wheel:
		wheel_metadata = wheel.get_metadata()
		# TODO: handle extra requirements (split up like separate files?)
		dependencies = set(map(ComparableRequirement, wheel_metadata.get_all("Requires-Dist", default=())))
		wheel_filename = os.path.basename(urlparse(str(wheel_url)).path)
		return [(wheel_filename, dependencies, [], True)]


@app.route("/pypi/")
def pypi() -> Response:
	"""
	Route for displaying the PyPI frontend landing page.
	"""

	return Response(render_template("pypi_search.html"))
