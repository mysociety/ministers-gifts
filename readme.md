
# ministers-gifts

[![badge](https://mybinder.org/badge.svg)](https://mybinder.org/v2/gh/mysociety/ministers-gifts/HEAD)

Republishing ministers gifts and hospitality register

This repository is available online at https://github.com/mysociety/ministers-gifts

If Github Pages are enabled, the URL is: https://pages.mysociety.org/ministers-gifts/

Instructions on using the features of this notebook (data publishing, notebook rendering, Github Pages) are available in [https://github.com/mysociety/data_common/blob/main/data-repo-readme.md](Data Common readme file).

Use Python 3.11–3.14 and a current version of uv. Run `uv sync` and
`script/test` to install dependencies and check the project. `script/server`
serves the Flask site at `http://127.0.0.1:5000/ministers-gifts/`.

Published downloads live in `data/packages/_published`; `uv run dataset site build`
builds the website into `_site`. Both directories are ignored. On a fresh checkout,
`uv run dataset publish --all` generates local downloads from the existing packages.
The daily workflow rebuilds and publishes downloads before building the site.

Notebook settings remain in `notebooks/_render_config/default.yaml`. The site
loads analysis bundles from `_render/site/analysis`; the existing example only
has a placeholder Google Drive target. Configure a `site` upload target to export
an analysis bundle, and use `uv sync --group google` for Google Drive support.

See [MIGRATION.md](MIGRATION.md) for the template migration baseline and verification.
