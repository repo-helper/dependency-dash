#!/usr/bin/env python3
#
#  badges.py
"""
Badge generation and serving.
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
import hashlib
from collections import Counter
from collections.abc import Iterator
from datetime import timedelta
from http import HTTPStatus
from operator import itemgetter

# 3rd party
from flask import Response, request
from pybadges import badge
from shippinglabel.requirements import ComparableRequirement

# this package
from dependency_dash.pypi import DependencyMetadata
from dependency_dash.utils import utcnow

__all__ = ["make_badge", "serve_badge"]


def make_badge(dependency_data: Iterator[tuple[ComparableRequirement, str, DependencyMetadata]]) -> str:
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


def serve_badge(badge_svg: str) -> Response:
	"""
	Serve the given badge with flask.

	:param badge_svg:
	"""

	etag = hashlib.sha256(badge_svg.encode("UTF-8")).hexdigest()

	if request.headers.get("If-None-Match") == etag:
		resp = Response(status=HTTPStatus.NOT_MODIFIED)
	else:
		resp = Response(badge_svg, content_type="image/svg+xml;charset=utf-8")

	resp.headers["ETag"] = etag
	cache_duration = 1200
	resp.headers["Cache-Control"] = f"max-age={cache_duration}"
	expires = (utcnow() + timedelta(seconds=cache_duration)).strftime("%a, %d %b %Y %H:%M:%S GMT")
	resp.headers["Expires"] = expires
	return resp
