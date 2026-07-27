# Review of `main.tex` for Software Impacts submission

Checked against the official Software Impacts article template (v2, July 2021)
and the journal's submission requirements. Items are ordered by severity.
Line numbers refer to the current `main.tex`.

---

## 0. The red "codificação hash" note (line 181) — what it is

Nothing in the Software Impacts requirements is literally called "hash
coding/encoding". This is almost certainly a **note-to-self about the C2
metadata row**: the journal requires a *"Permanent link to code/repository
used for **this code version**"* — i.e., a link frozen to the exact code the
paper describes, which people typically satisfy with a **commit hash**, a
**git tag/release**, or (best) an **archived DOI**.

**Do you still need to do it?** Yes — the underlying requirement is real, but
you satisfy it in the metadata table, not in the Introduction:

1. Tag the reviewed version on GitHub (e.g. `git tag v1.0.1 && git push --tags`).
2. Ideally, archive that release on [Zenodo](https://zenodo.org) via its GitHub
   integration to get a DOI (Software Impacts asks you to add a software
   reference if the repository supplies a DOI — see "References" note below).
3. Put the tag URL or DOI in row C2.
4. **Delete the red text** — it must not appear in the submitted PDF.

(If the note came from a co-author and meant something else, only they can
confirm — but no journal requirement needs anything beyond the above.)

---

## 1. Blockers — must fix before submission

- [ ] **C7 says "Python 3.9" but the code cannot run on 3.9** (line 148). The
  app uses `match` statements, which require **Python ≥ 3.10** (development is
  on 3.11, and `pyproject.toml` declares `requires-python = ">=3.10"`). A
  reviewer who tries Python 3.9 gets a `SyntaxError`. Change to
  "Python ≥ 3.10" and reference `pip install .` or `requirements.txt`.
- [ ] **C7 dependency list is incomplete**: missing `matplotlib`, `pyarrow`,
  `platformdirs`, and `mapclassify` (all required). Simplest fix: "Python
  ≥ 3.10; install via `pip install streetnets` or `requirements.txt`
  (Streamlit, OSMnx, GeoPandas, NetworkX, Folium, Plotly, Matplotlib, …)".
- [ ] **C1 version "v1.01" doesn't exist anywhere** (line 136). The repo has no
  releases/tags, and the package version in `pyproject.toml` is `0.1.0`. Pick
  one scheme (e.g. `v1.0.1`), set it in `streetnets_app/__init__.py`
  (`__version__`), tag it on GitHub, and use the same string in C1.
- [ ] **C2 is a mutable link** (line 138): `https://github.com/gioguarnieri/Streetnets`
  points at whatever `main` becomes. Replace with the version-pinned link
  (release/tag URL or Zenodo DOI) — this is the "codificação hash" item.
  Also note the repo's actual casing is `gioguarnieri/streetnets`.
- [ ] **`refs.bib` and `Images/` are not in this repo** — `main.tex` cannot
  compile from here. If you edit on Overleaf that's fine, but keep the paper
  sources together (suggestion: a `paper/` folder or a separate repo, so the
  Python package stays clean). Cited keys that must exist in `refs.bib`:
  `barthelemy2011spatial`, `barthelemy2022spatial`, `boeing2017osmnx`,
  `soares2024`.
- [ ] **Delete all template instructions before submitting.** They're
  commented out (lines 34–105, 158–177, 256–266), which keeps them out of the
  PDF, but cleaning them from the source avoids any accident and the journal
  explicitly asks for their removal.

## 2. The paper is out of date with the software (important)

- [ ] **"four distinct methods" for the Input Layer** (line 208) — the app now
  has **five**: point+radius, geocoding, bounding box, drawn polygon, and
  **shapefile upload (.zip)**. The shapefile method is missing from the list.
- [ ] **The Limitations section promises what already exists** (line 243):
  "we aim to develop a downloadable version of the software that runs directly
  on the user's computer" — this is done. The tool is now a pip-installable
  package (`pip install streetnets`, launched with the `streetnets` command)
  that runs fully locally, with the 18-city dataset auto-downloaded on first
  use. Rewrite this as a delivered feature (it strengthens the paper) and
  replace the future work with what's actually next, e.g. pre-computed
  betweenness for user areas, more topological metrics, or larger-network
  handling.
- [ ] **Figure 2 (`retrievedata.png`) shows the old UI.** The interface was
  redesigned (navigation sidebar with named pages, metric cards, map sampling
  notice). Retake the screenshot from the current version — reviewers will run
  the app and compare.
- [ ] **The Database and Glossary pages are never mentioned.** The app ships
  18 pre-analyzed city networks with statistics, hierarchy maps, and
  cross-city comparisons, plus a plain-language glossary — arguably half the
  software. One or two sentences in "Software description" would cover it.
- [ ] **Group A naming is inconsistent with the app**: the paper calls it
  "Strategic" (abstract, line 199); the app's Glossary and UI call it
  "Highways". Pick one term and use it in both places.

## 3. Journal-compliance gaps (from the template / Guide for Authors)

- [ ] **C3 Reproducible Capsule: "N/A"** (line 140). Acceptable, but Software
  Impacts encourages a [CodeOcean](https://codeocean.com) capsule and
  reviewers sometimes ask for it. For a Streamlit app a capsule is awkward —
  consider writing "not applicable (interactive web application; see C2 for
  runnable package)" so it reads as a decision, not an omission.
- [ ] **C6 undersells the stack** (line 146): "Python" only. Suggested:
  "Python (Streamlit, OSMnx, GeoPandas, NetworkX, Folium, Plotly); uses the
  OpenStreetMap Overpass and Nominatim web services."
- [ ] **References section should cite the software itself** if the repository
  has a DOI ("If the software repository you used supplied a DOI, please add a
  reference for your software here") — one more reason to do the Zenodo
  archive from item 0.
- [ ] **List of scholarly publications enabled by the software**: the template
  asks for this explicitly. You cite `soares2024` in prose; consider a short
  explicit list (even if it's one item) so the editor can check the box.
- [ ] **Declaration of Competing Interest** — mandatory for Elsevier journals;
  usually entered in the submission system, but adding the standard one-line
  statement before the references avoids a revision round. Same for a
  **CRediT author contributions** statement (commonly requested).
- [ ] **Illustrative video (optional but high-value)**: a ≤150 MB MP4
  screencast (640×480 recommended) showing "type a city → see stats → download
  data" is exactly the kind of demo that lands well for a dashboard paper.
- [ ] Keywords: you use 3 of the allowed 6 (line 123). Consider adding e.g.
  "Urban planning", "GIS", "Interactive dashboard".
- [ ] Abstract is ~85 words — fine ("ca. 100 words"). Fix the grammar slip:
  "computes key topological characteristics **values**" → "computes key
  topological metrics".

## 4. Minor / style

- [ ] Title: "Streetnets" vs "StreetNets" — the abstract, body, and app all
  use "StreetNets"; make the title match (line 108).
- [ ] Impact overview repeats itself: the 2nd and 3rd paragraphs of Section 4
  both say StreetNets "bridges the gap between complex network analysis and
  …" (lines 235, 237). Merge them and use the freed space for a concrete
  impact bullet (template suggests: new research questions enabled, changes to
  users' daily practice, adoption).
- [ ] Section 2 "Graphs" is textbook background; Software Impacts articles are
  ~3 pages about *the software*. Consider compressing Sections 1–2 into a
  single short intro so the space goes to description + impact.
- [ ] `\includesvg` (line 219) needs Inkscape + `--shell-escape` at compile
  time. Works on Overleaf, but converting the flowchart to PDF once and using
  `\includegraphics` is more portable.
- [ ] `\bibliographystyle{plain}` produces "G. Guarnieri Soares" style
  initials-last; the journal generally uses numbered styles — `plain` is
  numbered and acceptable, just check the rendered reference list.
- [ ] C8: write the full clickable URL
  (`https://github.com/gioguarnieri/streetnets/blob/main/README.md`), and
  note the README now documents both install paths (pip package and source).

---

### Suggested pre-submission sequence

1. Commit the current code, tag it (`v1.0.1`), publish the GitHub release
   (including the `data-v1` asset), and archive on Zenodo → DOI.
2. Update the metadata table (C1, C2, C6, C7, C8) and delete the red note.
3. Update body text: 5 input methods, local package as delivered feature,
   mention Database/Glossary, new screenshot.
4. Add competing-interest + CRediT statements; expand keywords.
5. Delete every commented template instruction; compile; check body ≤ 3 pages
   excluding metadata/figures/references.
6. (Optional) record the 1-minute screencast MP4.
