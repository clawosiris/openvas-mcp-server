# Releasing

This repository releases from in-repo GitHub Actions workflows, following the
same model as [rust-gvm](https://github.com/greenbone-hive/rust-gvm) and
[rust-gvm-api](https://github.com/greenbone-hive/rust-gvm-api): release file
changes land through a normal PR, release tags are created from merged PRs that
carry the `release` label, and publishing runs only from pushed `v*` tags.

## Release Model

The release flow has three phases:

1. **Prepare**: `Prepare Release` updates the `[package]` version in
   `Cargo.toml`, refreshes `Cargo.lock`, and opens a release-preparation PR
   against `main`.
2. **Tag**: `Create Release Tag` runs when a PR into `main` closes. If the PR
   was merged, has the `release` label, and changed the package version, it
   creates annotated tag `v<version>` at the merge commit.
3. **Publish**: `Publish Release` runs on pushed tags matching `v*`, validates
   the tag against `Cargo.toml`, tests, and publishes release assets.

The `Cargo.toml` package version on `main` represents the last released version
or the current release candidate. Do not bump to a synthetic next-dev version
after a release.

Versions are semantic (`MAJOR.MINOR.PATCH`, optionally with a pre-release
suffix). Tags are always `v<version>`.

## Creating a Release

1. Open the `Prepare Release` workflow in GitHub Actions.
2. Run it with the target semantic version without a leading `v`, for example
   `0.2.0` or `0.2.0-alpha.1`.
3. Review the generated PR. It should update the package version and
   `Cargo.lock` only.
4. Apply the exact PR label `release`.
5. Merge the PR into `main` after required checks pass.
6. Confirm that `Create Release Tag` created tag `v<version>`.
7. Confirm that `Publish Release` completed for that tag.

`Publish Release` builds and uploads:

- Cross-platform `gvm-mcp` binaries (linux/macOS, x86_64 + aarch64) as
  `.tar.gz` archives
- matching `.sha256` checksum files
- a CycloneDX SBOM archive (`.tar.gz` + `.sha256`)
- a distroless Docker image pushed to
  `ghcr.io/greenbone-hive/openvas-mcp-server` (tags `latest` and `<version>`)

GitHub release notes are auto-generated from merged PRs.

## Secrets

- `RELEASE_TOKEN` (optional): a PAT used by `Prepare Release` and
  `Create Release Tag` so that the pushed branch/tag re-triggers downstream
  workflows. If unset, the workflows fall back to `GITHUB_TOKEN`; note that a
  tag pushed with `GITHUB_TOKEN` does **not** trigger `Publish Release`, so in
  that case publish must be re-run manually against the tag.

## Retry and Recovery

- If preparation fails before opening a PR, rerun `Prepare Release` with the
  same version.
- If the preparation PR needs changes, edit its branch. Keep all release-version
  file changes in the PR.
- If the PR merged without the `release` label, add a new release-preparation PR
  or create the tag manually only after verifying `Cargo.toml` matches the
  intended version.
- If tag creation failed after a labeled merge, rerun `Create Release Tag`.
- If publishing failed, rerun `Publish Release` for the existing `v<version>`
  tag.
- Do not force-push release tags as part of normal recovery. If a tag points at
  the wrong commit, stop and resolve that deliberately.
