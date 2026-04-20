# Deploy & versioning (internal)

Story **6.8** — private org-scoped GitHub Pages + **`mike`** versioned docs.

## GitHub Pages source

- **Branch:** **`gh-pages`** at repository root (standard **`mike`** layout).
- **Not** “GitHub Actions” static artifact deploy: **`deploy.yml`** uses **`mike deploy --push`**, which commits to **`gh-pages`**.

After the first successful **`Deploy`** workflow, confirm **Settings → Pages → Build and deployment → Source: Deploy from a branch → `gh-pages` / `(root)`**.

## Visibility (FR33, NFR-S2)

For **GitHub Enterprise Cloud** or repos that support **private Pages**, set site visibility so only the org can read the handbook. Unauthenticated visitors should **not** receive a normal **200** HTML document for the full site.

The **`deploy.yml`** job performs a **smoke check**: if an unauthenticated **`curl`** to the public site URL returns **200**, it emits a **warning** so maintainers can verify visibility settings.

## Version aliases

| Alias | Meaning |
|-------|---------|
| **`main`** | Built from **`main`** — version id = NSO version from **`scripts/read_nso_version.py`** (e.g. `6.3`). Updated on every green **`Build`** on `main`. |
| **`latest`** | Points at the **semver** from the most recent **`v*`** tag deploy (**`release.yml`**). Also **`mike set-default`** so the site root redirects to that build. |

Until the first **`v*`** release, **`/latest/`** may be missing; **`/main/`** (or the NSO version path **`mike`** emits) still serves rolling docs.

## Local **`mike`** (optional)

```bash
export SITE_URL=http://127.0.0.1:8000/
mike deploy "$(python3 scripts/read_nso_version.py)" main --update-aliases
# Preview: mike serve
```

Do not push **`gh-pages`** from local unless you intend to — prefer CI.
