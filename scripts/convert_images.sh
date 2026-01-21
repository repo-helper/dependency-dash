#!/bin/bash
# update alternative image formats

set -e

RETV=0
echo "$@"

for filename in "$@"
do

  WEBP_FILENAME=$(echo "$filename" | sed -r 's/(.jpg|.png)/.webp/')
  AVIF_FILENAME=$(echo "$filename" | sed -r 's/(.jpg|.png)/.avif/')

  if [[ -f "$WEBP_FILENAME" ]]; then
    CURRENT_WEBP_SHA=$(sha256sum "$WEBP_FILENAME")
  else
    CURRENT_WEBP_SHA=''
  fi

  if [[ -f "$AVIF_FILENAME" ]]; then
    CURRENT_AVIF_SHA=$(sha256sum "$AVIF_FILENAME")
  else
    CURRENT_AVIF_SHA=''
  fi

  npx squoosh-cli "$filename" --avif "{near_lossless: 0}" --webp "{near_lossless: 0}" -d $(dirname "$filename")
  NEW_WEBP_SHA=$(sha256sum "$WEBP_FILENAME")
  NEW_AVIF_SHA=$(sha256sum "$AVIF_FILENAME")

  git stage "$AVIF_FILENAME"
  git stage "$WEBP_FILENAME"

  if [[ "$CURRENT_WEBP_SHA" != "$NEW_WEBP_SHA" ]]; then
    RETV=1
  fi

  if [[ "$CURRENT_AVIF_SHA" != "$NEW_AVIF_SHA" ]]; then
    RETV=1
  fi
done

exit $RETV
