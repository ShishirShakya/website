# Website (Shishir Shakya)

Personal academic site: CV, publications lists, projects, paper-facing explainers, and Grain of Salt essays built with MyST.

## Language

**Publication**:
A bibliographic record of a research output, maintained in the CV publications list (`book/cv/publications.md` and generated themed pages). This is the work that title-search and Google Scholar should treat as the article, via a DOI and/or a crawlable PDF.
_Avoid_: Paper note, Grain of Salt essay, blog post, explainer

**Paper note**:
A short, policy-facing explainer page tied to one Publication; paraphrases findings for non-specialist readers and links to the Canonical PDF or DOI. It is not the journal article and must not be marked or titled as if it were. A Publication list entry may link to its Paper note.
_Avoid_: Grain of Salt essay, blog post, full paper, abstract dump, publication list entry

**Canonical PDF or DOI**:
The Publication's full text or persistent identifier (a same-origin or repository `.pdf`, a publisher page, or `https://doi.org/...`). A Dropbox `/scl/` share is a human download convenience, not this.
_Avoid_: Paper note URL, Dropbox share as scholarly full text

**Free PDF**:
The public label for a Dropbox `/scl/` share that gives a free copy of a Publication. It is not Canonical.
_Avoid_: Download, Download PDF as if it were Canonical, scholarly full text

**Grain of Salt essay**:
A first-person reflective page on this site (memoir, meaning, craft of a life), not tied to a Publication, with no Facts block. The salt is that it is the author's view, not a research claim.
_Avoid_: Blog post, Paper note, Publication, op-ed list entry

**Facts block**:
The fixed, human-verified claim fields on a Paper note (main finding, one caveat, policy hook, data and setting, plain-language design, Canonical PDF or DOI then Free PDF) that substantive narrative may rely on.
_Avoid_: Abstract paste, unverified AI summary

**Verified**:
A Paper note whose Facts block has been checked against the Canonical PDF or DOI, marked `status: verified` in page source (YAML frontmatter), not in the visible body.
_Avoid_: Stub, draft, Facts filled, Status in the public page body

**Stub**:
A Paper note with citation and link only, marked `status: stub` in page source, whose Facts block is not yet verified against the Canonical PDF or DOI.
_Avoid_: Verified, published claim
