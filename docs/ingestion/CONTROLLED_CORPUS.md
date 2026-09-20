# Controlled corpus — Phase 7 (bundle `2026-09-20-corpus-01`)

The first real records of `KSC-BC-2020-06` held by the platform: **22 public
records** selected by the operator as a representative sample, captured in an
ordinary browser session on the official Public Court Records repository on
2026-09-20, matched to their downloaded PDFs by exact SHA-256, ingested once and
verified record by record. This is a controlled sample. It is **not** the case
corpus (the capture notes report 1,150+ public decision-type filings alone) and
nothing below claims completeness for any category.

Provenance chain for every record: official detail page URL → official PDF URL
→ capture-time SHA-256 / byte count (in the operator's manifest and snapshot)
→ downloaded bytes matched by that hash → re-hashed after copy → stored in
MinIO under a hash-addressed key → re-hashed from MinIO at the quality gate.

## Machine-readable record

[`manifests/phase7-controlled-corpus.json`](manifests/phase7-controlled-corpus.json)
is the tracked, machine-readable reproducibility record of this corpus,
exported from the verified database state with
`ksc-ingest export-corpus data/captures/2026-09-20-corpus-01 --out …` and
validated by `tests/unit/ingestion/test_corpus_manifest.py` (schema
`ksc_ingestion.corpus_manifest.CorpusManifest`). It holds metadata only —
identifiers, official URLs, SHA-256, sizes, page counts, hearing identity and
gate results. The PDFs and the browser-captured pages are intentionally **not**
committed (`data/captures/` is git-ignored); the artifact bytes live in object
storage under the listed `object_key`, identified by `sha256`; the official KSC
URLs remain the canonical provenance. This page is the human-readable
companion.

## Records

| #   | official version ref                | type            | language | published status          | party (as published)              | court level             | date (as published) | pages | bytes      | SHA-256 (first 12) | gate       |
| --- | ----------------------------------- | --------------- | -------- | ------------------------- | --------------------------------- | ----------------------- | ------------------- | ----- | ---------- | ------------------ | ---------- |
| r01 | `KSC-BC-2020-06/F00045/A03`         | public_redacted | eng      | public_redacted           | — → —                             | Basic Court Chamber     | —                   | 68    | 1,019,458  | `08cfad70e731`     | PASS 32/32 |
| r02 | `KSC-BC-2020-06/F00045/A03/sqi`     | translation     | sqi      | public_redacted           | — → —                             | Basic Court Chamber     | —                   | 71    | 1,088,564  | `8cf509c7b3ab`     | PASS 32/32 |
| r03 | `KSC-BC-2020-06/F00001`             | reclassified    | eng      | public                    | President → court                 | Basic Court Chamber     | 23/04/2020          | 3     | 136,710    | `3fcef62d3b7f`     | PASS 32/32 |
| r04 | `KSC-BC-2020-06/F00004/RED`         | public_redacted | eng      | public_redacted           | Specialist Chambers → court       | Basic Court Chamber     | 27/05/2020          | 4     | 125,856    | `bed7c45b4ed8`     | PASS 32/32 |
| r05 | `KSC-BC-2020-06/F00004/RED/sqi`     | translation     | sqi      | public_redacted           | Specialist Chambers → court       | Basic Court Chamber     | 27/05/2020          | 4     | 113,807    | `0ab83210ea57`     | PASS 32/32 |
| r06 | `KSC-BC-2020-06/F03752`             | original        | eng      | public                    | Specialist Chambers → court       | Basic Court Chamber     | 24/06/2026          | 7     | 203,746    | `01d74237df33`     | PASS 32/32 |
| r07 | `KSC-BC-2020-06/F03780`             | original        | eng      | public                    | Specialist Chambers → court       | Basic Court Chamber     | 15/09/2026          | 16    | 334,465    | `51d603790791`     | PASS 32/32 |
| r08 | `KSC-BC-2020-06/IA042/F00005/RED`   | public_redacted | eng      | public_redacted           | Specialist Chambers → court       | Court of Appeal Chamber | 28/05/2026          | 41    | 614,654    | `64445be3ce6f`     | PASS 32/32 |
| r09 | `KSC-BC-2020-06/IA042/F00002`       | reclassified    | eng      | public                    | President → court                 | Court of Appeal Chamber | 30/03/2026          | 3     | 223,184    | `d65f967b9d35`     | PASS 32/32 |
| r10 | `KSC-BC-2020-06/F03776`             | original        | eng      | public                    | Specialist Prosecutor → spo       | Basic Court Chamber     | 21/08/2026          | 12    | 344,665    | `e10e4917da7d`     | PASS 32/32 |
| r11 | `KSC-BC-2020-06/F03667/COR/RED`     | public_redacted | eng      | public_redacted_corrected | Specialist Prosecutor → spo       | Basic Court Chamber     | 19/01/2026          | 716   | 10,119,923 | `ac6accc77483`     | PASS 32/32 |
| r12 | `KSC-BC-2020-06/F03777`             | original        | eng      | public                    | Specialist Counsel → defence      | Basic Court Chamber     | 01/09/2026          | 3     | 133,367    | `8a909ef401da`     | PASS 32/32 |
| r13 | `KSC-BC-2020-06/F03762/RED`         | public_redacted | eng      | public_redacted           | Specialist Counsel → defence      | Basic Court Chamber     | 08/07/2026          | 14    | 267,841    | `3388133808c5`     | PASS 32/32 |
| r14 | `KSC-BC-2020-06/F03774`             | reclassified    | eng      | public                    | Specialist Counsel → defence      | Basic Court Chamber     | 21/08/2026          | 3     | 174,276    | `410e3c8e010e`     | PASS 32/32 |
| r15 | `KSC-BC-2020-06/F03664/RED2`        | public_redacted | eng      | public_redacted_v2        | Specialist Counsel → defence      | Basic Court Chamber     | 19/01/2026          | 308   | 3,513,842  | `b2f56aec3262`     | PASS 32/32 |
| r16 | `KSC-BC-2020-06/F03668/RED/A01/RED` | public_redacted | eng      | public_redacted           | — → —                             | Basic Court Chamber     | —                   | 14    | 325,209    | `56c1abfb2bd4`     | PASS 32/32 |
| r17 | `KSC-BC-2020-06/F03668/RED2`        | public_redacted | eng      | public_redacted_v2        | Specialist Counsel → defence      | Basic Court Chamber     | 11/05/2026          | 346   | 3,812,810  | `70abbee36376`     | PASS 32/32 |
| r18 | `KSC-BC-2020-06/F03744/RED`         | public_redacted | eng      | public_redacted           | Victims Counsel → victims_counsel | Basic Court Chamber     | 08/06/2026          | 5     | 151,665    | `a545e1767af3`     | PASS 32/32 |
| r19 | `KSC-BC-2020-06/F00267/RED`         | public_redacted | eng      | public_redacted           | Registrar → other                 | Basic Court Chamber     | 28/07/2026          | 7     | 174,934    | `d7f10383e7d4`     | PASS 32/32 |
| r20 | `KSC-BC-2020-06/T/2026-02-18`       | original        | eng      | public                    | — → —                             | —                       | 18/02/2026          | 91    | 436,537    | `17f8a2ece162`     | PASS 35/35 |
| r21 | `KSC-BC-2020-06/T/2026-02-18/sqi`   | translation     | sqi      | public                    | — → —                             | —                       | 18/02/2026          | 103   | 449,585    | `79f53534fe64`     | PASS 35/35 |
| r22 | `KSC-BC-2020-06/T/2026-02-16`       | original        | eng      | public                    | — → —                             | Basic Court Chamber     | 16/02/2026          | 140   | 663,996    | `0d03ed82b9b0`     | PASS 35/35 |

## Titles and selection reasons (as published / as captured)

- **r01** — ANNEX 3 to Submission of corrected and public redacted versions of confirmed Indictment and related requests  
  _Confirmed indictment (corrected + public redacted) - the core charging instrument of the case; anchors every downstream filing._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180227f65&doc_type=stl_filing_annex&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e98037f0e4/ANNEX%203%20to%20Submission%20of%20corrected%20and%20public%20redacted%20versions%20of%20confirmed%20Indictment%20and%20related%20requests.pdf>  
  reference source: published_id_confirmed_by_pdf_header; court stamp: “reclassified as Public.”
- **r02** — SHTOJCË 3 e parashtrimit të versioneve të korrigjuara dhe të redaktuara publike të Aktakuzës së konfirmuar dhe kërkesave lidhur  
  _Official Albanian public translation of r01 - same filing number F00045, different language; gives a verified EN/SQ translation pair._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180228458&doc_type=stl_filing_annex&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e18005e7ac/SHTOJC%C3%8B%203%20e%20parashtrimit%20t%C3%AB%20versioneve%20t%C3%AB%20korrigjuara%20dhe%20t%C3%AB%20redaktuara%20publike%20t%C3%AB%20Aktakuz%C3%ABs%20s%C3%AB%20konfirmuar%20dhe%20k%C3%ABrkesave%20lidhur.pdf>  
  reference source: published_id_confirmed_by_pdf_header; court stamp: “reclassified as Public.”
- **r03** — Decision Assigning a Pre-Trial Judge  
  _F00001 - first filing in the case file; establishes the Pre-Trial Judge and the start of the record sequence._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180227ce6&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e9802ba591/Decision%20Assigning%20a%20Pre-Trial%20Judge.pdf>  
  reference source: published_id_confirmed_by_pdf_header; page-1 classification line: “Confidential”; court stamp: “this filing is reclassified as: Reclassification date: 27/04/2020”
- **r04** — Public Redacted Version of Decision on Specialist Prosecutor's Request for Extension of the Word Limit  
  _Early Pre-Trial Judge decision issued as a public redacted version - sample of the RED suffix convention at the earliest stage of the case._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180228910&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e980398e3f/Public%20Redacted%20Version%20of%20Decision%20on%20Specialist%20Prosecutor%E2%80%99s%20Request%20for%20Extension%20of%20the%20Word%20Limit.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r05** — Version i redaktuar publik i Vendimit mbi kërkesën e Prokurorit të Specializuar për tejkalimin e numrit të lejuar të fjalëve  
  _Albanian public translation of r04 - shares the same artifact directory as the English version, demonstrating multi-language artifacts under one filing ID._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e18022ad05&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b1ec6e980398e3f/Version%20i%20redaktuar%20publik%20i%20Vendimit%20mbi%20k%C3%ABrkes%C3%ABn%20e%20Prokurorit%20t%C3%AB%20Specializuar%20%20p%C3%ABr%20tejkalimin%20e%20numrit%20t%C3%AB%20lejuar%20t%C3%AB%20fjal%C3%ABve.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r06** — Decision on the Joint Defence Submissions Regarding the Corrected Version of the SPO Final Trial Brief  
  _Trial Panel decision resolving a dispute about a corrected filing - documents the versioning/correction event that produced r11._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805bed0b&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805bed41/Decision%20on%20the%20Joint%20Defence%20Submissions%20Regarding%20the%20Corrected%20Version%20of%20the%20SPO%20Final%20Trial%20Brief.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r07** — Decision on Periodic Review of Detention of Kadri Veseli  
  _Most recent fully public Trial Panel decision in the case at capture time - the recurring periodic detention review genre._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e18060eb4c&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e18060ed97/Decision%20on%20Periodic%20Review%20of%20Detention%20of%20Kadri%20Veseli.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r08** — Public Redacted Version of Decision on Rexhep Selimi's Appeal Against Decision on Periodic Review of Detention  
  _Court of Appeals Panel decision - the IA (interlocutory appeal) sub-series numbering, distinct from the main F-series._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805a997d&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805a996a/Public%20Redacted%20Version%20of%20Decision%20on%20Rexhep%20Selimi%E2%80%99s%20Appeal%20Against%20Decision%20on%20Periodic%20Review%20of%20Detention.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r09** — Decision Assigning a Court of Appeals Panel  
  _Opening decision of the IA042 appeal sub-file - pairs with r08 to show a complete public appeal thread._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180570605&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e180570517/Decision%20Assigning%20a%20Court%20of%20Appeals%20Panel.pdf>  
  reference source: derived_from_published_id; page-1 classification line: “Strictly Confidential”; court stamp: “PUBLIC Reclassified as Public pursuant to instructions contained in CRSPD983 of 7 May 2026”
- **r10** — Prosecution submission pertaining to periodic detention review of Jakup Krasniqi  
  _Fully public SPO filing (no redaction suffix, no confidential annex) - clean baseline sample of prosecution submissions._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805f75e8&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805f775e/Prosecution%20submission%20pertaining%20to%20periodic%20detention%20review%20of%20Jakup%20Krasniqi.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r11** — Public Redacted Version of 'Corrected Version of "Prosecution Final Trial Brief"' with public redacted Annexes 1-3  
  _SPO Final Trial Brief - the single most substantive public prosecution document; CORRED suffix marks a corrected AND redacted version._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805a3f12&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805a3ff6/Public%20Redacted%20Version%20of%20%E2%80%98Corrected%20Version%20of%20%E2%80%9CProsecution%20Final%20Trial%20Brief%E2%80%9D%E2%80%99%20with%20public%20redacted%20Annexes%201-3.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r12** — Krasniqi Defence Notification in Relation to Prosecution Submission Pertaining to Periodic Detention Review of Jakup Krasniqi (F03776)  
  _Defence filing for accused KRASNIQI - and a direct public reply to r10, giving a linked SPO/Defence exchange._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180601fec&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805fe9df/Krasniqi%20Defence%20Notification%20in%20Relation%20to%20Prosecution%20Submission%20Pertaining%20to%20Periodic%20Detention%20Review%20of%20Jakup%20Krasniqi%20%28F03776%29.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r13** — Public Redacted Version of Veseli Defence Renewed Request for Provisional Release  
  _Defence filing for accused VESELI - second accused, different Defence team, redacted request genre._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805cb221&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805cb1e1/Public%20Redacted%20Version%20of%20Veseli%20Defence%20Renewed%20Request%20for%20Provisional%20Release.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r14** — Selimi Defence Request for Reclassification of F03720  
  _Defence filing for accused SELIMI - third accused; reclassification requests are the mechanism by which confidential filings become public._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805f75e6&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805f5b18/Selimi%20Defence%20Request%20for%20Reclassification%20of%20F03720.pdf>  
  reference source: derived_from_published_id; page-1 classification line: “Strictly Confidential”; court stamp: “Reclassified as Public pursuant to instructions contained in CRSPD989 of 8 September 2026 PUBLIC”
- **r15** — Further Public Redacted Version of 'Thaçi Defence Final Trial Brief with Confidential Annexes 1 and 2'  
  _Defence filing for accused THAÇI - fourth accused; RED2 shows a second-generation public redaction of the same filing ID._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805b71d6&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805b7022/Further%20Public%20Redacted%20Version%20of%20%E2%80%98Tha%C3%A7i%20Defence%20Final%20Trial%20Brief%20with%20Confidential%20Annexes%201%20and%202%E2%80%99.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r16** — ANNEX 1 to Public Redacted Version of 'Krasniqi Defence Final Trial Brief'  
  _VERSION PAIR (part 1 of 2): the first public redacted generation of filing F03668._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e18057b079&doc_type=stl_filing_annex&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e18057b118/ANNEX%201%20to%20Public%20Redacted%20Version%20of%20%E2%80%98Krasniqi%20Defence%20Final%20Trial%20Brief%E2%80%99.pdf>  
  reference source: pdf_header
- **r17** — Further Public Redacted Version of 'Krasniqi Defence Final Trial Brief with Confidential Annexes 1-3 and Confidential and Ex-Parte Annex 4'  
  _VERSION PAIR (part 2 of 2): same filing number F03668, later and less redacted public generation - the RED/RED2 pair requested._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180596a11&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e18059698e/Further%20Public%20Redacted%20Version%20of%20%E2%80%98Krasniqi%20Defence%20Final%20Trial%20Brief%20with%20Confidential%20Annexes%201-3%20and%20Confidential%20and%20Ex-Parte%20Annex%204%E2%80%99.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r18** — Public Redacted Version of Victims' Counsel's Request for resumption of action of V02-06 with one strictly confidential and ex parte Annex  
  _Victims' Counsel filing - the victim-participation track; only the public redacted parent is captured, its confidential annex is NOT included._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805b0bcc&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805b0b45/Public%20Redacted%20Version%20of%20Victims%E2%80%99%20Counsel%E2%80%99s%20Request%20for%20resumption%20of%20action%20of%20V02-06%20with%20one%20strictly%20confidential%20and%20ex%20parte%20Annex.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r19** — Public Redacted Version of Registrar's Submissions on Veseli Defence Request for Temporary Release on Compassionate Grounds (F00267)  
  _Registry filing - the administrative/Registrar track, distinct from SPO, Defence and Chambers._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805dc7e1&doc_type=stl_filing&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Filing/0b10c8e1805dc7c3/Public%20Redacted%20Version%20of%20Registrar%E2%80%99s%20Submissions%20on%20Veseli%20Defence%20Request%20for%20Temporary%20Release%20on%20Compassionate%20Grounds%20%28F00267%29.pdf>  
  reference source: published_id_confirmed_by_pdf_header
- **r20** — Closing Statements - 18 February 2026  
  _Public hearing transcript - final day of closing statements, the most significant oral proceeding in the public record._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180548bf2&doc_type=stl_transcript&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/Closing%20Statements%20-%2018%20February%202026.pdf>  
  reference source: derived_transcript_key
- **r21** — Deklaratat përmbyllëse - 18 shkurt 2026  
  _Albanian public transcript of the same 18/02/2026 hearing as r20 - verified same-hearing EN/SQ transcript pair._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e1805552d0&doc_type=stl_transcript&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/Deklaratat%20p%C3%ABrmbyll%C3%ABse%20-%2018%20shkurt%202026.pdf>  
  reference source: derived_transcript_key
- **r22** — Closing Statements - 16 February 2026  
  _Second public transcript, earlier closing-statements day - gives a multi-day transcript sample rather than a single isolated hearing._  
  detail: <https://repository.scp-ks.org/details.php?doc_id=0910c8e180547470&doc_type=stl_transcript&lang=eng>  
  pdf: <https://repository.scp-ks.org/LW/Published/Transcript/KSC-BC-2020-06/Closing%20Statements%20-%2016%20February%202026.pdf>  
  reference source: derived_transcript_key

Party column: label as published → `filing_party` enum stored (`—` = not
published; nothing inferred). Dates are the repository's single "Date" field as
published and are stored as `document_date`; `filing_date` / `public_date` stay
NULL because the source does not publish them separately. Court level is kept on
the source record's metadata snapshot (no column on `documents`).

## Coverage of the sample

| Category                                            | Records                                                              | Note                                                                                                                                                                             |
| --------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Indictment / core charging material                 | r01, r02                                                             | Annex 3 to the submission of the corrected and public-redacted confirmed indictment, EN + SQ                                                                                     |
| SPO filings                                         | r10, r11                                                             | r11 = Prosecution Final Trial Brief, corrected + public redacted, 716 pages — the largest substantive filing in the sample                                                       |
| Defence filings (four accused)                      | r12, r16, r17 (Krasniqi) · r13 (Veseli) · r14 (Selimi) · r15 (Thaçi) | filing party published as "Specialist Counsel"                                                                                                                                   |
| Trial Panel / Pre-Trial Judge / President decisions | r03, r04, r05, r06, r07                                              | r03 = first filing of the case (assignment of the Pre-Trial Judge)                                                                                                               |
| Court of Appeals material                           | r08, r09                                                             | sub-proceeding `IA042`; r09 = President's assignment of the appeals panel                                                                                                        |
| Registry / Victims' Counsel                         | r19 (Registrar) · r18 (Victims' Counsel)                             | both public redacted                                                                                                                                                             |
| Transcripts                                         | r20, r21, r22                                                        | closing statements 16 and 18 Feb 2026; 18 Feb in EN + SQ; two hearings, three transcript rows                                                                                    |
| English / Albanian variants                         | r01↔r02 · r04↔r05 · r20↔r21                                          | one document, two language versions; the court's own `/sqi` suffix is the version reference                                                                                      |
| Successive public-redaction generations             | r15 (`RED2`), r17 (`RED2`), r16 (`RED/A01/RED`)                      | see "version relationships"                                                                                                                                                      |
| Corrected + redacted                                | r11 (`COR/RED`) and r06, the decision about that correction          |                                                                                                                                                                                  |
| Reclassified to public                              | r03, r09, r14                                                        | page 1 prints the filing-time classification and the court's "reclassified as Public" stamp                                                                                      |
| Trial judgment                                      | none                                                                 | not found in this controlled capture or the operator's observed query (`filing_type=Judgement` returned nothing on 2026-09-20 per CAPTURE_NOTES.md) — not independently verified |
| Original (unredacted) + redacted pair               | none                                                                 | the operator observed that unredacted originals of redacted filings are not public; not independently verified                                                                   |

## Version relationships as stored

- **Same document, language versions** — `F00045/A03` (r01 eng, r02 sqi),
  `F00004` (r04 `RED`, r05 `RED/sqi`), `T/2026-02-18` (r20 eng, r21 sqi). The
  document keeps the original-language identity (title, language, detail URL);
  each translation is a `translation` version with its own detail page recorded
  on its source record.
- **r16 / r17 are not a RED → RED2 pair of one document.** The PDF header of r16
  reads `KSC-BC-2020-06/F03668/RED/A01/RED`: it is _Annex 1_ to the public
  redacted brief, itself redacted. r17 is the further public redacted brief
  (`F03668/RED2`). They are stored as two documents (`F03668/A01`, `F03668`);
  no `supersedes` link is set because the earlier generation of the brief
  itself (`F03668/RED`) is not in the sample. The capture notes' description of
  the pair was corrected by the artifact itself.
- **r15** (`F03664/RED2`) and **r11** (`F03667/COR/RED`) are single generations
  in the sample; no predecessor is held, so no `supersedes` link is set.
- No redacted content was compared, inferred or reconstructed.

## Reference scheme (ADR-012)

Version references are the strings the court prints in the filing header
(`KSC-BC-2020-06/F00004/RED`, `…/F00045/A03/sqi`, `…/IA042/F00005/RED`,
`…/F03667/COR/RED`, `…/F03668/RED/A01/RED`). 19 of 22 were confirmed from the
PDF text layer; r16 adopted the header's more specific spelling; r09 and r14
fall back to the published id (their footers did not extract) and the
transcripts use the derived key `KSC-BC-2020-06/T/<hearing date>[/sqi]` because
the repository publishes no filing number for them. Every derivation is recorded
in `source_records.raw_metadata.metadata.extra.reference`.

## Quality gate (2026-09-20)

`ksc-ingest gate data/captures/2026-09-20-corpus-01` — **22 / 22 PASS**,
32 checks per filing and 35 per transcript: case; official reference; title
(document title stays in the original language for translations); type;
language; visibility public / public_redacted only; official detail URL on the
source record; official PDF URL on the version; declared SHA-256 = stored
SHA-256 = hash of the local file = hash of the bytes read back from MinIO;
declared byte count = stored; PDF valid; page count; source record, document,
version, hearing and transcript rows and their links; job item `downloaded`
linked to the version; SHA-256 unique across the bundle. Full report:
`data/captures/2026-09-20-corpus-01/quality_gate_report.json` (git-ignored with
the bundle).

The gate found one real defect on its first run — translation records had
overwritten the shared document's `source_url` — which was fixed in the
pipeline, converged by a re-run (three `document.metadata_updated` audit rows
restoring the original-language URL) and covered by a test.

## Idempotency (2026-09-20)

Running the same bundle again: `source_records` (22), `documents` (19),
`document_versions` (22), `hearings` (2), `transcripts` (3) and the 22 MinIO
objects byte-for-byte identical including `updated_at`; one new
`capture_bundle` job with 22 `skipped_duplicate` items; 0 downloads; 0 document
metadata updates.

## Counts

|                                                                 |                                            |
| --------------------------------------------------------------- | ------------------------------------------ |
| Real source records captured                                    | 22                                         |
| Real records validated (source manifest ↔ snapshot cross-check) | 22                                         |
| PDF files matched by SHA-256                                    | 22 / 22                                    |
| PDF files hash-verified after copy and from MinIO               | 22                                         |
| PDF files stored in MinIO                                       | 22                                         |
| Metadata-only records                                           | 0                                          |
| Documents created                                               | 19                                         |
| Document versions created                                       | 22 (fetched 22 · not_fetched 0 · failed 0) |
| Hearings created                                                | 2                                          |
| Transcripts created                                             | 3                                          |
| MinIO objects created                                           | 22 (24,429,094 bytes)                      |
| Duplicates skipped (re-runs)                                    | 22 per re-run; 0 within the first run      |
| Ambiguous mappings                                              | 0                                          |
| Failed records                                                  | 0                                          |
| Missing PDFs                                                    | 0                                          |
| Hash mismatches                                                 | 0                                          |

## What the operator's capture notes say that is _not_ independently verified

`CAPTURE_NOTES.md` (copied into the bundle) describes the repository's search
filters (`record_type_short`, `filing_court_level`, `filing_type`,
`filing_submitter`, …), the absence of a public trial judgment and of public
unredacted originals, and a corpus size of 1,150+ public decisions. These are
the operator's observations from the session and are recorded as such; only
the 22 records above were verified by this pipeline.
