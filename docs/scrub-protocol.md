---
classification: "Cisco Confidential"
---

# Screenshot and diagram scrub protocol

Follow this protocol **before you merge** any image that could show customer networks, identities, or operational data. Use second-person, imperative steps (UX-DR27).

---

## Scope

This protocol applies to:

1. **Screenshots** — PNG/JPEG/WebP captures of terminals, browsers, NSO Web UI, device CLIs, or OS windows.
2. **Diagrams that embed text** — Exported images (PNG/SVG) where hostnames, IPs, or labels are baked into pixels or paths.
3. **PDF images** — Any raster copied into the workbook PDF pipeline from the same sources as (1) and (2).

It does **not** replace **alt text** or **Mermaid source** hygiene: you still satisfy authoring lint rule 5 and pre-rendered diagram alt files as described in `docs/authoring.md`.

---

## Identifiers to remove

For each category below, scrub **before** commit. Pair each category with a practical check and a safe replacement.

| Identifier | Detection heuristic | Replace with |
|------------|---------------------|--------------|
| **Customer hostnames** | FQDNs not in the approved list (see next section); host labels that match a customer naming convention visible in the shot | Use names from the approved list (`xr-1`, `nso-server`, `linux-host`, …) or generic placeholders (`router-a`, `nms-host`) consistent with UX-DR11 topology naming. |
| **Real public IPs** | IPv4/IPv6 that are not in RFC 5737 documentation ranges; addresses that match your organization’s live allocation | **RFC 5737** documentation ranges only: `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/64` (IPv4 examples); for IPv6 use `2001:db8::/32` per RFC 3849. |
| **MAC addresses** | Six octet patterns (`xx:xx:xx:xx:xx:xx`, vendor OUIs that identify customer gear) | Fixed lab values such as `00:1a:2b:3c:4d:5e` (document that they are synthetic in the chapter if needed). |
| **Serial numbers / PIDs** | Long alphanumeric strings on chassis labels, `show inventory`, license dialogs | Redact to `SN-REDACTED` or a short synthetic token (`CHASSIS-001`). |
| **IGP / LDAP user identifiers** | Real usernames in prompts, `whoami`, directory UIs | Replace with lab accounts (`admin`, `cisco`, `learner`) already used in the workbook narrative. |
| **Customer organization names** | Logos, banners, email domains, “Company X” in titles | Use **Example Org** or **Lab Org**; remove logos. |
| **License key fragments** | Long hex/base64 strings in entitlement or install dialogs | Crop or blur the region; do not transcribe. |
| **Clearly internal Cisco project codenames** | Non-public program names visible in slides or tickets | Replace with a neutral label (**Internal project**) or remove the line. |

---

## Identifiers permitted

Use these consistently so learners and screenshots stay aligned with the lab topology (UX-DR11):

- **Device names:** `xr-1`, `xr-2`, `nso-server`, `linux-host` (and names listed in your chapter’s topology macro).
- **Documentation IPv4:** Any address inside **192.0.2.0/24**, **198.51.100.0/24**, or **203.0.113.0/24** (RFC 5737).
- **Documentation IPv6:** **2001:db8::/32** (RFC 3849) unless your lab file specifies another documented range.
- **Lab accounts** explicitly taught in the workbook (e.g. `admin` / documented passwords in fenced blocks only when required by the lab).

If you are unsure whether a string is permitted, **scrub it**.

---

## Scrub tools

1. **In-image editing** — Crop sensitive regions; use solid fills or blur for small areas; redraw simple UI chrome if needed.
2. **OS-level redaction** — macOS Preview, Snipping Tool + editor, or GIMP for redact boxes before export.
3. **Re-capture** — Prefer a clean capture from a sanitized lab VM over heavy editing when time allows.

Re-export to **PNG** (or WebP for web-only) and keep file sizes within NFR-P6 budgets in `docs/authoring.md`.

---

## Worked example

**Scenario:** A terminal screenshot showed a customer hostname and a routable public IP in a `ping` line.

| Asset | Role |
|-------|------|
| `docs/assets/images/scrub-example/before.png` | Stand-in “before” image (synthetic 1×1 pixel — replace with a real before/only example in your branch when illustrating the guide). |
| `docs/assets/images/scrub-example/after.png` | Stand-in “after” scrub (documentation-safe palette). |

**Diff narrative:** Remove the customer FQDN and public IP from the visible line; replace with `xr-1` and an address from `198.51.100.0/24`; re-run `ping` in the lab VM if needed so the capture matches the story. Crop scrollback if unrelated sessions leak identifiers.

---

## Author self-review

Before you open a PR that adds or changes images in chapter **NN**:

1. List every raster under `docs/assets/images/` referenced from `docs/NN-*.md` (and any Mermaid PNG/SVG used by that chapter).
2. Walk the **Identifiers to remove** table above for each file.
3. Confirm **alt text** is present and describes the scrubbed content (lint rule 5).
4. Add or update a **dated** row in `docs/scrub-logs/NN.md` with your name, date, and “pass — protocol 4.1”.

---

## Second-pair review (NFR-S6)

At **v0.9** (pre-release cohort readiness):

1. A **second CX engineer** (not the chapter author) selects **10% of chapters at random**, **rounding up** — for **9** labs, review **at least 1** chapter (if 10 chapters, review 2).
2. For each selected chapter, open **every** image referenced from that chapter’s Markdown and verify compliance with **Identifiers to remove** and **Identifiers permitted**.
3. Record a **dated** sign-off in **`docs/scrub-logs/second-pair-review.md`**: reviewer name, chapter(s), date, pass/fail, and short notes on any fix-ups required.

Random selection can be a simple spreadsheet draw or `shuf -n 1` on the list `01`–`09` — document the method in the log entry.

---

## Related documents

- **`docs/authoring.md`** — Screenshots, alt text, image budgets, voice (UX-DR27).
- **`docs/scrub-logs/`** — Per-chapter and second-pair logs referenced above.
