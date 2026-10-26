# Gmail Job Application Draft Agent

A minimal reusable assistant workflow that creates personalized Gmail drafts
from a pasted job description and your Google Docs resume. All sending is manual.

## Outreach contacts

Use `emails.txt` as the single active contact list (one email per line).
New batches are appended and deduplicated. `outreach-exclusions.json` records
unreachable addresses and prevents future reimports unless explicitly reinstated.
The dated startup-outreach files preserve historical draft results only.

## Use

1. Open this project in your assistant with the Gmail plugin connected.
2. Connect Google Drive/Docs as well as Gmail. The resume source is:
   https://docs.google.com/document/d/1XYJ5nUQUbSPwiXhTmgRLVMCi5-64Cwyu0qygmwlalv8/edit?tab=t.0
3. Paste one job description, or several separated postings, and ask:
   `Create separate Gmail drafts for all these postings:`
4. The assistant tailors only existing Bounteous, RWS and XBREYINS bullets,
   appends verified missing skills in the existing Technical Skills format,
   exports a job-specific PDF, and attaches that version to the Gmail draft.
5. Review the tailored resume, draft, recipient, claims, and attachment in Gmail.
6. Send manually when satisfied.

The assistant follows `AGENTS.md`. A recruiter/application email must appear
explicitly in the job description or be separately provided by you for that
posting. When none is provided, the only response is:

Recruiter email address is not mentioned or provided in the job description.

Ambiguous or malformed recipients require clarification. Missing or unreadable
resumes stop the workflow. Unsupported qualifications are never claimed.

For multiple postings, each gets its own recipient, subject, tailored plain-text
body, PDF attachment, and Gmail draft. No recipients are combined or copied.
Validation happens for the entire batch first: postings without an explicit
application email are skipped while eligible postings continue. Single postings
without email return the exact missing-email message above. Repeated postings
and existing matching drafts are deduplicated; job-seeker advertisements are excluded.
Results are reported per draft, including partial failures, without blindly
retrying uncertain writes. Staffing advertisements require an explicit request
to contact them and are handled as candidate inquiries about opportunities.

## Gmail integration

The connected Gmail `create_draft` tool supports plain-text MIME bodies and PDF
attachments. The assistant uses the existing connection; no passwords, OAuth
code, API keys, or tokens are stored in this project. Connection availability
must be checked in the active session. Draft creation is confirmed by Gmail,
and attachment verification is reported accurately.

If attachment support is unavailable, a confirmed draft is saved without the
PDF and the assistant reports:

Draft saved successfully. Please attach your resume PDF manually before sending.

This is an assistant-operated project, not a standalone command-line application.
Run it in a session exposing the Gmail connector; shell execution alone cannot
access that connector. Project instructions constrain the workflow; they do not
remove sending tools from the overall Gmail plugin. No sending tools are used.

## Workflow

Job Description + Explicit Email -> Email Validation -> Resume Matching ->
Scoped Google Docs Resume Tailoring -> Verified PDF Export -> Email Drafting ->
Optional PDF Attachment -> Gmail Drafts -> Manual Human Review.

The linked Google Doc is edited in place. Only existing experience bullets in
Bounteous, RWS and XBREYINS may be reworded. Technical Skills is append-only:
existing text, ordering and styling are preserved. All other resume content and
formatting stay untouched. Skills absent from your verified history need your
confirmation; the agent never adds unsupported claims merely to match a JD.

Each application gets a separate verified PDF snapshot under `Resume/tailored/`.
Batch applications are processed sequentially, and the Google Doc ends with the
last tailored version. Previously attached snapshots stay unchanged. The original
`Resume/Aman-Resume.pdf` remains a reference and is never silently substituted
for a failed tailored export. Google Docs access or PDF export failures stop the
affected application with an accurate explanation.

No UI, database, background worker, scheduler, or agent framework is required.
