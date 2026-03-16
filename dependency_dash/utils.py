#!/usr/bin/env python3
#
#  utils.py
"""
General utilities.
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
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

# 3rd party
from flask import Request

# this package
from dependency_dash._app import app

__all__ = ["canonical_url_header", "get_canonical_url", "strptime", "utcnow"]

_normalize_pattern = re.compile(r"\W+")


def _normalize(name: str) -> str:
	return _normalize_pattern.sub('-', name)


def utcnow() -> datetime:
	"""
	Returns the current time in the UTC timezone.
	"""

	return datetime.now(timezone.utc)


def strptime(data_string: str, format: str) -> datetime:  # noqa: A002  # pylint: disable=redefined-builtin
	"""
	Parse a datetime string, with special handling for GMT and UTC.

	:param data_string:
	:param format:
	"""

	if "GMT" in data_string:
		data_string = data_string.replace("GMT", "+00:00")
	elif "UTC" in data_string:
		data_string = data_string.replace("UTC", "+00:00")

	return datetime.strptime(data_string, format)


def get_canonical_url(request: Request) -> str:
	"""
	Returns the canonical URL for the requested page.

	:param request: The flask request.
	"""

	return urljoin(app.config["DD_ROOT_URL"], request.path)


def canonical_url_header(request: Request) -> dict[str, str]:
	"""
	Add a header for the canonical URL to the request's response.

	:param request: The flask request.
	"""

	canonical_url = get_canonical_url(request)
	return {"Link": f'<{canonical_url}>; rel="canonical"'}
