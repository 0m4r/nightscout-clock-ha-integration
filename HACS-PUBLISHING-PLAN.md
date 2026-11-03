# HACS Publishing and Compliance Plan

This plan covers HACS publishing and default-store compliance. It is separate
from the integration's feature-development plan.

Assessment checked against the HACS [publishing requirements](https://www.hacs.xyz/docs/publish/start/)
and [default-repository submission guide](https://www.hacs.xyz/docs/publish/include/)
on November 3, 2026.

## Current status

| Requirement | Status |
|---|---|
| Public, active GitHub repository | Complete |
| Repository description, topics, and issues enabled | Complete |
| README with usage instructions | Complete |
| Root `hacs.json` with a name | Complete |
| GitHub-recognized open-source license | Complete (LGPL-3.0) |
| Integration brand icon | Complete |
| HACS Action and Hassfest validation | Passed |
| Tests and lint | Passed |
| Published GitHub Release | Not complete; no release was found |
| Entry in the HACS default repository list | Not complete; PR not submitted |

The latest validation run checked was
[Validate run 41654286807](https://github.com/0m4r/nightscout-clock-ha-integration/actions/runs/41654286807).
Hassfest, HACS validation, tests, and lint all passed.

## Plan

1. **Confirm release readiness.** The README describes the integration as an
   early beta. Decide whether to publish it in that state. HACS's stated
   exclusion concerns integrations used to alpha/beta-test Home Assistant core
   integrations; an integration being beta by itself is not listed as a
   blocker.
2. **Verify release metadata.** Confirm the minimum Home Assistant version in
   [`hacs.json`](./hacs.json) is intentional and matches the integration's
   supported version. Choose a release tag consistent with the integration
   version and prepare release notes.
3. **Publish a GitHub Release.** Use the manual **Release** workflow in
   [`.github/workflows/release.yml`](./.github/workflows/release.yml). Enter
   the version without `v`; it must match the integration manifest version.
   The workflow only runs from `main`, reruns tests, lint, Hassfest, and HACS
   validation, then creates a release tagged `v<version>` on the validated
   commit. Versions containing a pre-release suffix (for example
   `0.1.0-beta.1`) are published as GitHub prereleases. This creates a full
   GitHub Release, not just a tag.
4. **Submit a PR to `hacs/default`.** As repository owner, add the repository
   to the appropriate list alphabetically and complete the PR template. Submit
   from a personal account (not an organization account) and ensure the PR is
   editable.
5. **Respond to review.** Address HACS review feedback. After merge, HACS
   includes the repository in a subsequent scheduled scan; review may take
   months.

## Remaining gates

- Publish a GitHub Release.
- Submit and obtain acceptance of the PR to `hacs/default`.
