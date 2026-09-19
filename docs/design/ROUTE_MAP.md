# ROUTE_MAP.md
### KSC Public Record Intelligence — route structure

Case: KSC-BC-2020-06. 21 artboards. All routes are client-side; the case is a deployment constant, not a path segment.

---

## 1. Principles

**Every meaningful view state is addressable.** A researcher must be able to paste a URL that reopens the same document at the same page with the same paragraph highlighted, or the same table with the same filters. Anything a user can reach by clicking, they can reach by link.

**Tabs are route state, not component state.** `?tab=testimony` is part of the URL on every tabbed screen.

**Filters are query params.** Table filters, network depth, timeline layers and search facets all serialise. Back and forward behave as expected.

**Identifiers in routes are the record's own.** `W01234`, `P00441`, `F00482`, `I-0042` are used verbatim. They are never re-keyed to internal IDs in the URL, because researchers cite URLs.

**The case prefix is omitted.** Every route is scoped to KSC-BC-2020-06. If a second case is ever added, the prefix becomes `/case/:caseId/…` and everything below nests unchanged.

---

## 2. Route table

| Route | Artboard | Notes |
|---|---|---|
| `/` | **02** Homepage | Entry point |
| `/search` | **06** Global Search | `?q=` required; empty `q` renders the empty state |
| — (modal) | **06b** ⌘K Overlay | Opens over any route; does not change the URL until a result is chosen |
| `/people` | *not designed* | Directory — reuse table pattern from 10 |
| `/people/:slug` | **07** Person Dossier | |
| `/witnesses` | *not designed* | Directory — protection state column |
| `/witnesses/:code` | **08** Witness Dossier | `:code` is the W-code, e.g. `W01234` |
| `/witnesses/:code/compare` | **09** Statement Comparison | |
| `/documents` | *not designed* | Directory |
| `/documents/:id` | **04** Document Reader | Light mode |
| `/exhibits` | **10** Evidence Explorer | Detail is panel state on the same route |
| `/incidents` | *not designed* | Directory |
| `/incidents/:id` | **11** Incident Detail | |
| `/timeline` | **12** Research Timeline | |
| `/findings` | *not designed* | Findings matrix — reuse table from 07 at full page |
| `/findings/:id` | **05** Finding Detail | |
| `/network` | **03** Network Explorer | |
| `/network/path` | **20** Evidence Path | |
| `/appeal` | **13** Appeal Research | |
| `/appeal/argument/:id` | **14** Argument Lab + Red Team | |
| `/ai` | **15** AI Research | New session |
| `/ai/:sessionId` | **15** AI Research | Saved session |
| `/public` | **16** Public / Simple Mode | Light mode |
| `/public/:topic` | **16** Public / Simple Mode | e.g. `/public/what-the-court-decided` |

---

## 3. Query parameters by route

### `/search`
```
q          string    required. Raw query as typed, URL-encoded.
cat        csv       people,witnesses,documents,transcripts,exhibits,
                     incidents,findings,locations
from,to    YYYY      event-date range (not filing date)
src        csv       court,witness,spo,defence,exhibit
verif      csv       verified,unreviewed,unresolved
avail      csv       public,redacted
sort       enum      relevance | date-asc | date-desc
```

### `/people/:slug` · `/witnesses/:code` · `/incidents/:id` · `/findings/:id`
```
tab        enum      see §4 for the per-screen tab set
```

### `/witnesses/:code/compare`
```
segment    string    comparison segment id
label      enum      consistent | possible-contradiction | qualification
                     | timeline-difference | not-comparable   (filter)
```

### `/documents/:id`
```
page       int       1-based page number
highlight  string    paragraph anchor, e.g. "8422" or "8421-8427"
panel      enum      summary | mentions | people | exhibits | findings | citations
```

### `/exhibits`
```
q          string
type       csv       order,report,memo,log,imagery,photo,forensic,
                     intercept,statement,chart,record,expert
party      csv       spo,defence
cited      bool      only exhibits cited in the judgment
from,to    YYYY-MM-DD   document date
verif      csv       verified,unreviewed,unresolved,needs-evidence
density    enum      compact | comfortable
sort       string    column key, prefix "-" for descending
sel        string    exhibit id — opens the detail panel
```

### `/network`
```
focus      string    entity id to centre on
depth      1|2|3
layers     csv       accused,witness,protected,document,incident,
                     finding,location,organisation
edge       csv       edge types to show
from,to    YYYY      date range
verif      csv
sel        string    selected node id
seledge    string    selected edge id
```

### `/network/path`
```
from       string    required — entity id A
to         string    required — entity id B
maxhops    1|2|3     default 3
alt        int       index into the alternate-path list; 0 = shortest
hop        int       expanded hop in the inspector
```

### `/timeline`
```
layers     csv       events,documents,hearings,testimony,decisions,
                     judgment,appeal
from,to    YYYY-MM-DD   applied per era
person     csv
witness    csv
incident   csv
doc        csv
card       string    selected card id
```

### `/appeal`
```
category   csv       error-of-law,error-of-fact,sentencing,
                     evidence-assessment,procedural-fairness,
                     reasoning,mode-of-liability,other
state      csv       kept,dismissed,awaiting
issue      string    expanded issue id
```

### `/appeal/argument/:id`
```
stage      1|2|3     which red-team stage is displayed
```

### `/ai/:sessionId`
```
q          string    the question (also stored server-side on the session)
cite       string    citation id whose preview popover is open
```

---

## 4. Tab sets

| Route | Tabs (`?tab=`) |
|---|---|
| `/people/:slug` | `overview` · `documents` · `testimony` · `exhibits` · `incidents` · `timeline` · `findings` · `arguments` · `network` · `appeal` |
| `/witnesses/:code` | `overview` · `testimony` · `cross` · `prior-statements` · `exhibits` · `findings` · `comparison` · `timeline` · `network` · `ai` |
| `/incidents/:id` | `overview` · `findings` · `witnesses` · `evidence` · `spo` · `defence` · `timeline` · `network` · `issues` |
| `/findings/:id` | `chain` · `quotes` · `arguments` · `annotations` |

Default tab is the first in each set. An unknown `tab` value falls back to the default without an error.

---

## 5. Cross-screen navigation contract

These are the links the audited flows depend on. Each is a hard requirement, not a convenience.

| From | To | Carries |
|---|---|---|
| Any citation chip | `/documents/:id?page=&highlight=` | page **and** paragraph anchor |
| Search result row | the entity's own route | — |
| Person quick action | `/network?focus=:id&depth=2` | focus + depth |
| Person quick action | `/network/path?from=:id` | A pre-filled, B empty |
| Network edge inspector | the source that created the edge | exact citation |
| Evidence Path hop | the document behind that hop | citation |
| Document `Cited in Finding` banner | `/findings/:id` | — |
| Finding evidence row | the source of that item | citation |
| Finding direction count | `/incidents/:id?tab=evidence&direction=` | filtered matrix |
| Finding → Argument Lab | `/appeal/argument/new?finding=:id` | finding id |
| Appeal issue → Argument Lab | `/appeal/argument/new?issue=:id` | issue id |
| Witness flagged testimony | `/witnesses/:code/compare?segment=` | segment |
| AI citation chip | preview popover, **then** the document | citation |
| AI answer → graph | `/network?nodes=<source set>` | the answer's source set |
| Timeline card | the record behind it | — |
| Public mode term | `/public/glossary#:term` | — |

---

## 6. Mode and language

Neither is a route prefix.

**Mode** — Simple / Research is a user setting. `/public` is the simple-mode landing page; from there, entity links resolve to the same canonical routes and render in whichever mode is active. Switching mode preserves the route and, where possible, the scroll position.

**Language** — EN / SQ is a user setting persisted per user, surfaced as `Accept-Language` on API calls. It does not appear in the URL. Document language is independent of interface language and is a property of the document, never of the route.

---

## 7. Deep-link guarantees

These must survive a cold load from a pasted URL:

1. `/documents/:id?page=894&highlight=8422` opens page 894 with ¶8422 highlighted and scrolled into view.
2. `/findings/:id` opens with the chain in order and the left rail scroll-spy at step 01.
3. `/network?focus=X&depth=2&sel=Y` renders the graph and opens Y's inspector.
4. `/network/path?from=A&to=B` recomputes the path — paths are not cached by URL, because the record can change under them.
5. `/exhibits?...&sel=P00441` opens the table with filters applied and the panel open.
6. `/witnesses/:code/compare?segment=7` opens that segment in all three columns.

---

## 8. Error routes

| Condition | Behaviour |
|---|---|
| Unknown entity id | 404 view naming the identifier that was not found, with a search field pre-filled with it |
| Identifier exists but is not public | Explicit "this record is not in the public set" — **never** a generic 404, because the distinction matters to a researcher |
| Protected witness code, protection state unresolvable | Renders the protected treatment. Fails closed. |
| Path request with no route found | "No source-backed path within N hops" plus a control to raise the hop limit |
| AI answer with an unresolvable citation | Answer withheld; the gap is reported. Not a route error — a render refusal. |

---

## 9. Not yet designed

Five directory routes are referenced by designed screens but have no artboard. None needs new components or new semantics.

| Route | Build from |
|---|---|
| `/people` | Evidence Explorer table (10) with person columns |
| `/witnesses` | Table (10) plus the protected treatment from 08 |
| `/documents` | Table (10) with document columns |
| `/incidents` | Table (10) or cards using the header pattern from 11 |
| `/findings` | The findings table from 07, promoted to full page |
