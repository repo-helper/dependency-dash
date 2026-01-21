#!/bin/bash

RETV=0

compile () {
  INFILE=$1
  OUTFILE=$2
  OUTFILE_MAP="$OUTFILE.map"

  if [[ -f "$OUTFILE" ]]; then
    CURRENT_SHA=$(sha256sum "$OUTFILE")
  else
    CURRENT_SHA=''
  fi

  if [[ -f "$OUTFILE_MAP" ]]; then
    CURRENT_MAP_SHA=$(sha256sum "$OUTFILE_MAP")
  else
    CURRENT_MAP_SHA=''
  fi

  npx sass "$INFILE" "$OUTFILE" --style compressed

  for file in $OUTFILE $OUTFILE_MAP; do
    sed -i '1s/^\xEF\xBB\xBF//' "$file"
    sed -i -e '$a\' "$file"
  done

  if [[ "$CURRENT_SHA" != "$(sha256sum "$OUTFILE")" ]]; then
    echo "$OUTFILE changed"
    git stage "$OUTFILE"
    RETV=1
  fi

  if [[ "$CURRENT_MAP_SHA" != "$(sha256sum "$OUTFILE_MAP")" ]]; then
    echo "$OUTFILE_MAP changed"
    git stage "$OUTFILE_MAP"
    RETV=1
  fi

  return 0
}

# Compile SCSS for Font Awesome
compile "scss/fontawesome.scss" "dependency_dash/static/css/fontawesome.min.css"

# Minify other files
compile "dependency_dash/static/css/main.css" "dependency_dash/static/css/main.min.css"
compile "dependency_dash/static/css/pygments.css" "dependency_dash/static/css/pygments.min.css"

exit $RETV
