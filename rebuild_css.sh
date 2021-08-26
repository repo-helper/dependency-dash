#!/bin/bash

# Compile SCSS for Font Awesome
scss scss/fontawesome.scss dependency_dash/static/css/fontawesome.min.css --style compressed

# Minify other CSS
scss dependency_dash/static/css/main.css dependency_dash/static/css/main.min.css --style compressed
scss dependency_dash/static/css/pygments.css dependency_dash/static/css/pygments.min.css --style compressed
