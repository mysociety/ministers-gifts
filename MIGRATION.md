# Template and Flask publication migration

This migration was prepared and verified as an uncommitted merge on `main`,
then committed at the maintainer's request to finish the pending merge. No push,
history rewrite, non-dry-run version command, or dataset publish command was run.

## Baseline

- Repository HEAD: `85f1ef5317c519a9dff9d36876c7398929b7339c`.
- Fetched `template/main`: `fa596e34c7a756bd9a4de4989ff07629ee102843`.
- Template remote: `https://github.com/mysociety/template_data_repo`.
- Original pinned data_common: `8538c2f090fda29386c613fc6943a9a36173491c`.
- Merged template's pinned data_common: `afecc75feab845838c0cd362982e04d6ac2a94f7`.
  The submodule is clean and was not advanced independently.
- Python project version and dataset `ministers_gifts_and_hospitality`: `0.1.0`.
  The only stored dataset version remains `0.1.0`.
- `data/raw`, `data/private`, and `data/interim` contained only placeholders.
  The build downloads GOV.UK CSVs directly; there was no local raw-data cache.
- Published downloads were ignored at `docs/data`; none were present locally.
  The migrated policy ignores `data/packages/_published/` and `_site/`.
  The template's tracked `.gitinclude` is only a directory placeholder.

The first inspection stopped on different submodule checkouts: theme
`9d8328fd1e96d6c534d78733e9d9cc1a99f4bbd3` and data_common
`44646d8959d7e7322079fc9495fbb0a9251380f6`. After continuation, the migration
was prepared in `/tmp/ministers_gifts-migration`. Before applying it to the
original workspace, its HEAD was checked against the baseline and its working
tree, including submodules, was confirmed clean. Both merges used
`--no-commit --no-ff`; the final merge preserves both parents.

## Resolution decisions

- Used upstream infrastructure for composite actions, Pages workflows, container
  plumbing, standard scripts, uv groups, and removal of Ruby/Jekyll/theme files.
- Structurally converted Poetry configuration to `[project]`, preserving the
  project name, description, entry point and `mysoc-validator` constraint. Made
  the downloader's HTTP/HTML dependencies explicit; included rendering and chart
  dependencies needed by notebook code. Regenerated `uv.lock` with current uv.
- Preserved daily scheduling, user-agent secret setup, Slack notification
  configuration, the container image name, and workspace paths. No notification
  workflow was executed. Kept explicit publication in the daily workflow so
  ignored downloads are rebuilt even when the dataset version does not change.
  The test workflow now uses the automatic version rule in dry-run mode.
- Removed the template-only meta-test workflow, which this repository had already
  deleted. Removed `poetry.lock`; it was not merged by hand.
- Resolved the data_common gitlink to the template's exact commit. Retained the
  upstream safer `script/update-from-template` without alteration.
- Preserved site title `UK Gov Ministers gifts and hospitality`, description,
  homepage title `Download ministers_gifts`, base path `/ministers-gifts`, host
  `https://pages.mysociety.org`, soft download gate, survey
  `6876792/Data-usage`, form header, and credit text/URL.
- Preserved the existing publication URL
  `https://pages.mysociety.org/ministers_gifts/`. Its underscore differs from the
  site's hyphenated base path; review this existing discrepancy before deployment.
- Notebook settings and the default render configuration are unchanged. The
  example has only a placeholder Google Drive upload, with both IDs set to
  `blank`; no site bundle was configured or present. The Flask site discovers
  bundles at `_render/site/analysis` when a `site` upload is configured.
- Legacy theme-only settings included the `@mysociety` Twitter card, the theme
  logo, and DataTables CSS/JS for analysis layouts. Those old layout hooks have
  no direct settings in the shared Flask renderer and are recorded here for
  reference; the former configuration remains available in Git history.

The migration preview proposed removal of the recognised legacy `docs` files
and the ignored-publication policy. It was applied with `--ignore-published`,
without `--force`. The subsequent preview with the same policy reports
`Repository is already migrated.`

## Data and metadata verification

The first live build exposed parser drift from pandas 1.4.2 to 2.3.3: 53 gift
dates and 445 hospitality dates changed, including day/month swaps and lost
values. All other values and the row counts were identical. Explicit mixed-date
parsing restores the existing ISO/UK interpretation. A Parquet writer now compares
round-tripped dataframes and retains existing bytes when only serialization would
change; genuinely changed values are written. Regression tests cover both cases.

Final rebuilt resources are byte-for-byte identical to the originals and their
stored `0.1.0` copies:

| Resource | Rows | SHA-256 |
| --- | ---: | --- |
| gifts.parquet | 3332 | `304b20c630fe08b04fa47136c48e2cd23a366e9a5996a856f9fb545803591b55` |
| hospitality.parquet | 3899 | `4f46d646d7f3b63260063cfac272b561c6c7d6b7816b49962a0460e945e0983f` |

Two metadata corrections were necessary:

1. The configured test module did not exist. The current package now points to
   `tests/test_ministers_gifts.py`, retaining its original test and adding migration
   regressions. The stored package descriptor is unchanged.
2. The existing `Date` schemas said `string`, although the unchanged Parquet files
   contain native dates. Frictionless 5 rejected these descriptors. `Date.type`
   is now `date` in both current and stored resource YAML, describing the existing
   bytes correctly. No examples, hashes, row counts, or data values were changed.
   Historical resource descriptors therefore have this explicit one-line correction;
   they are not claimed to be byte-identical. Formatting-only YAML churn was removed
   after checking semantic equality.

The final `dataset version auto --auto-ban major --all --dry-run` reports
`No changes detected, not bumping`. No new package version was created.

## Checks completed

- `uv lock`, `uv sync`: pass; 189 locked packages.
- `script/test`: 40 tests pass, including shared notebook tests; Ruff check,
  Ruff formatting and Pyright all pass.
- `dataset build --all`: live-source build passes in the final workspace.
- `dataset version auto --auto-ban major --all --dry-run`: no bump.
- `dataset validate --all`: passes.
- Rendered the existing stored `0.1.0` using `DataPackage.build_package()` into
  ignored local output; integrity validation and composite generation pass.
  No version/publish CLI command was used for this step.
- `dataset site check` and `dataset site build`: 11 pages, 8 data files;
  the build includes 9 assets under `_site`.
- `script/server`: HTTP 200 at `/ministers-gifts/`, with the dataset listed.
- Migration preview after application: idempotent with `--ignore-published`.
- Infrastructure scan: no active Ruby/Jekyll/theme dependency or malformed
  `$/.github` action path. Historical migration fixtures inside data_common are
  intentional and were not edited.
- Reviewed the final diff, lockfile structure and local action targets;
  staged and unstaged `git diff --check` pass.

Verification used Python 3.12.5, uv 0.12.10 and Node 22.23.2. The existing global
uv 0.3.0 does not support dependency groups, and Node 14 cannot parse this Pyright
configuration. Current tools were installed under `/tmp`, without replacing
system installations. For this session, prepend
`/tmp/ministers_gifts-node/node_modules/.bin:/tmp/ministers_gifts-tools/bin`
to `PATH`, or rebuild the updated devcontainer. Docker and hosted Actions were
not run because Docker is unavailable here.

## Remaining configuration and commit plan

Confirm GitHub Pages uses **GitHub Actions**, the `github-pages` environment is
available, workflow writes are permitted, and the existing user-agent/Slack
secrets remain configured. Review the preserved publication URL discrepancy.
Rebuild the devcontainer or install current local uv/Node tooling.

The migration is recorded as one merge commit preserving the template ancestry,
including configuration, compatibility fixes, tests, and this record. No additional
data-version commit is needed. Pushing is left to the maintainer.

Detailed command logs and the initial drift artifacts are retained at
`/tmp/ministers_gifts-migration-audit`; the preparation worktree is retained at
`/tmp/ministers_gifts-migration`. Neither is needed to run the migrated repository.
