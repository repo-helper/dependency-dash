#!/usr/bin/env python3
#
#  _env.py
"""
Environment variable helper.
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
import os

# 3rd party
import github3.repos.contents
import platformdirs
import setup_py_upgrade  # type: ignore
from domdf_python_tools.paths import PathPlus
from flask import render_template, request  # type: ignore

try:
	# 3rd party
	from dotenv import load_dotenv
except ImportError:
	pass
else:
	load_dotenv()  # take environment variables from .env.

if "GITHUB_TOKEN" not in os.environ:
	raise ValueError("'GITHUB_TOKEN' environment variable not found.")

GITHUB = github3.GitHub(token=os.getenv("GITHUB_TOKEN"))
CACHE_DIR = PathPlus(platformdirs.user_cache_dir("dependency_dash")) / "github"