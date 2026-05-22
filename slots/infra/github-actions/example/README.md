# github-actions example

Two workflows you can copy verbatim into any project:

- `.github/workflows/ci.yml` — lint + format-check + type-check + tests, runs on push and PR.
- `.github/workflows/publish-image.yml` — builds and pushes a Docker image to GHCR on `v*` tags.

Validate locally with [actionlint](https://github.com/rhysd/actionlint) if installed:

```sh
actionlint .github/workflows/*.yml
```
