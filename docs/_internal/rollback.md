# Rollback a release (internal)

Story **6.9** — **FR50**, **NFR-R2**. Target: revert the **live** handbook site and GitHub Release state within a few minutes.

## 1. Stop serving the bad version on GitHub Pages

`mike` keeps versions on the **`gh-pages`** branch. Point **`latest`** (and default) at the last known-good semver.

```bash
pip install -r requirements.txt
git fetch origin gh-pages
git checkout gh-pages
# List deployed versions (requires mike + local clone with gh-pages)
mike list
```

From a clean machine with repo **`main`** checked out and **`SITE_URL`** set for builds if needed:

```bash
export SITE_URL="https://<owner>.github.io/<repo>/"
# Replace PRIOR with the previous semver directory (see mike list on gh-pages or GitHub Releases)
mike alias PRIOR latest --update-aliases --push
mike set-default --push PRIOR
```

If **`mike`** is not available locally, use **GitHub Actions → Deploy workflow** only after fixing **`main`** — or temporarily **re-run** a successful **`release`** workflow from the prior tag (not always possible). Prefer local **`mike`** for speed.

## 2. GitHub Release

- Open **Releases →** the faulty release → **Edit** → set to **pre-release** or **Delete** the release (requires admin).
- Optionally **delete the tag** after team agreement (rewrites history for consumers):

  ```bash
  git push origin :refs/tags/vX.Y.Z
  ```

  Recreate a corrected tag from a fixed commit when ready.

## 3. Verify

- Open the site root — it should redirect to **`/PRIOR/`** or **`/latest/`** matching the restored alias.
- Confirm the learner PDF for the prior release is still downloadable from the retained **Release** asset if you kept that release.

## 4. Screen readers / accessibility

If the rollback was due to an accessibility regression, record the SR/browser combo in the incident notes and update **`docs/_internal/accessibility.md`** when Story **6.10** cutover criteria apply.
