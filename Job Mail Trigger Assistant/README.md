# Gmail Job Application Draft Agent

A minimal reusable assistant workflow that creates personalized Gmail drafts
from a pasted job description and your saved PDF resume. All sending is manual.

## Use

1. Open this project in your assistant with the Gmail plugin connected.
2. Keep your current resume at `Resume/Aman-Resume.pdf`.
3. Paste one job description, or several separated postings, and ask:
   `Create separate Gmail drafts for all these postings:`
4. Review the resulting draft, recipient, claims, and attachment in Gmail.
5. Send manually when satisfied.

The assistant follows `AGENTS.md`. A recruiter/application email must appear
explicitly in the job description. When none is provided, the only response is:

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

Job Description -> Email Validation -> Resume Matching -> Email Drafting ->
Optional PDF Attachment -> Gmail Drafts -> Manual Human Review.

No UI, database, background worker, scheduler, or agent framework is required.
