#!/usr/bin/env python3
#
#  htmx.py
"""
Helpers for htmx_.

.. _htmx: https://htmx.org/
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
import functools
import traceback
from typing import Any, Callable
from urllib.parse import urljoin

# 3rd party
from flask import Flask, render_template

__all__ = ["htmx"]


def htmx(app: "Flask", rule: str, **options: Any) -> Callable:
	"""
	Construct a flask route at ``/htmx/<rule>`` for use with htmx_.

	:param app:
	:param rule: The URL rule string.
	:param options: Extra options passed to the flask ``app.route`` decorator.
	"""  # noqa: RST306

	rule = urljoin("/htmx/", rule.lstrip('/'))

	def decorator(f: Callable) -> Callable:
		endpoint = options.pop("endpoint", None)

		@functools.wraps(f)
		def rule_func(*args, **kwargs) -> str:
			try:
				return f(*args, **kwargs)
			except Exception as e:
				print(f"Exception in route {rule}:")
				traceback.print_exc()
				return render_template("htmx_exception.html", exception=e)

		app.add_url_rule(rule, endpoint, rule_func, **options)
		return f

	return decorator
