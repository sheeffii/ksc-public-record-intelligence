# Lawyer/researcher beta protocol

Status: prepared; real external participants and completed feedback are an
external dependency. Do not claim that a beta occurred until signed session
records exist.

Recruit a small set of legal/research users without collecting unnecessary
personal data. Obtain consent for notes; identify participants only by random
session code. Explain that this is an independent research tool, not a KSC
product or legal advice, and that public sources exclude confidential, ex parte
and private material. AI is analysis, not court record.

Each 60-minute moderated session uses staging and asks the participant to:

1. locate a filing by exact reference and verify it at the original source;
2. trace a citation and inspect an evidence path;
3. inspect a finding and the Court/party separation;
4. compare two source-backed statements and inspect appeal research;
5. verify or reject an AI answer using its cited sources;
6. distinguish external public material from court evidence.

Record task completion, citation/source trust, navigation, labels, missing
workflow, accessibility/device issue and observed latency. Never record court
document text, protected identity guesses or private legal strategy. Classify
feedback as bug, data/provenance, UX, missing feature, performance,
legal-language clarity, security/privacy or AI quality. Integrity/provenance
issues rank ahead of convenience. Critical/high security or provenance defects
pause beta; every item needs disposition, owner and evidence before closeout.

The final evidence-only gate is `scripts/phase16_gate.py <evidence-directory>`.
It never performs or invents a test. All live readiness evidence must pass; the
beta item alone may contain `{"status":"external_dependency"}`.
