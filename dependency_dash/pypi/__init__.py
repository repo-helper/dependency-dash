#!/usr/bin/env python3
#
#  pypi.py
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
from collections import Counter
from operator import itemgetter
from typing import Any, Dict, Iterable, Iterator, List, Tuple
from urllib.parse import urlparse

# 3rd party
import platformdirs
from domdf_python_tools.paths import PathPlus
from flask import render_template
from packaging.version import InvalidVersion, Version
from pybadges import badge
from pypi_json import PyPIJSON
from shippinglabel import normalize
from shippinglabel.requirements import ComparableRequirement

__all__ = ["format_project_links", "get_data", "get_dependency_status", "make_badge"]

CACHE_DIR = PathPlus(platformdirs.user_cache_dir("dependency_dash")) / "pypi"


def format_project_links(project_urls: Dict[str, str]) -> str:
	"""
	Format the project's links (homepage, GitHub etc.) with hyperlinks and icons.

	The rules are the same as PyPI uses for its "Project links" sidebar.

	:param project_urls:
	"""

	links: Dict[str, str] = {}
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
			icon = "fas fa-book"
			continue  # TODO
		elif name.startswith(("bug", "issue", "tracker", "report")):
			icon = "fas fa-bug"
			continue  # TODO
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


def _sort_versions(*versions: str) -> List[str]:

	for_sort = []

	for version in versions:
		try:
			ver_ver = Version(version)
		except InvalidVersion:
			continue
		else:
			for_sort.append((version, ver_ver))

	return [v[0] for v in sorted(for_sort, key=itemgetter(1))]


def get_data(project_name: str) -> Dict[str, Any]:
	"""
	Obtain metadata for ``project_name`` from PyPI.

	:param project_name:
	"""

	# TODO: HEAD and check last serial to see if update needed
	project_name = normalize(project_name)

	datafile = CACHE_DIR / project_name[0] / f"{project_name}.json"
	datafile.parent.maybe_make(parents=True)

	try:
		data = datafile.load_json()
	except FileNotFoundError:
		with PyPIJSON() as client:
			metadata = client.get_metadata(project_name)

		releases = metadata.releases
		# .releases may be None if a version is passed,
		# but in our case we aren't.
		assert releases is not None

		data = {
				"name": metadata.info["name"],
				"version": metadata.info["version"],
				"home_page": metadata.info["home_page"] or '',
				"license": metadata.info["license"] or '',
				"package_url": metadata.info["package_url"],
				"project_urls": metadata.info["project_urls"],
				"all_versions": _sort_versions(*releases.keys()),
				}

		datafile.dump_json(data)

	return data


def get_dependency_status(
		requirements: Iterable[ComparableRequirement],
		) -> Iterator[Tuple[ComparableRequirement, str, Dict[str, Any]]]:
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
		data = get_data(req.name)
		latest_version = data["version"]
		version_specifier = req.specifier

		if latest_version in version_specifier:
			status = "up-to-date"
		else:
			status = "outdated"
		# TODO: check against safety's DB. Probably need to enumerate releases from PyPI

		yield req, status, data


def make_badge(dependency_data: Iterator[Tuple[ComparableRequirement, str, Dict[str, Any]]]) -> str:
	"""
	Construct a badge from the given dependency data.

	:param dependency_data: An iterator over ``(requirement, status, metadata)`` tuples.

	:returns: The SVG badge.
	"""

	status_counts = Counter(map(itemgetter(1), list(dependency_data)))

	if not status_counts or set(status_counts.keys()) == {"up-to-date"}:
		return badge(left_text="dependencies", right_text="up-to-date", right_color="#82B805")
	# TODO: insecure
	else:
		return badge(
				left_text="dependencies",
				right_text=f'{status_counts["outdated"]} outdated',
				right_color="orange",
				)
