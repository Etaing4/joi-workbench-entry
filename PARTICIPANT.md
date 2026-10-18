# Public participant assignment — open-protocol follow-up v1

Reference: https://etaing4.github.io/joi-workbench-entry/

This is a **new follow-up cohort**, not one of frozen E01–E10. Register with the page or
`entry.py`; your `FU-<UUID>` is your assigned entrant ID. Preserve its FOLLOWUP cohort
and use that ID in every output. A retry records `retry_of`, never replaces a baseline.
No max4, VPN, fleet account or private dashboard connection is needed.

## Download actual inputs

Download [participant-packet.zip](participant-packet.zip), then read this file first.
Inside are phase1/CONTRACT.md + initial_receipts.json; packet/START_HERE.md;
packet/ABCD/{CONTRACT.md,SOURCE_PACKET.md,fixtures.json,submission.py,run_examples.py};
contracts for E/F/G; the isolated command-center app and public tests; schemas, templates,
media-rights sources; and the common update stimulus packet/update_receipt.json.
CONTENT-MANIFEST.json records every member's byte count/hash and derivation changes.
The original frozen archives are untouched. No evaluator/gold answers are included.

**Open-protocol difference:** the entire packet and common update are already public.
First spend at most 5 active minutes on phase1 A, save A/initial.json, and append a
checkpoint with its SHA256 to your GitHub issue before using the update. Then append
update.events and replace as_of for A/final.json. This honor-system ordering is not a
blinded delayed release. Advance stimulus visibility and self-timing change comparability;
results must never be pooled into the frozen baseline. Source docs' references to a
controller, withheld update, E01–E10 or assigned private output directory are historical;
this public directive overrides those clauses only. Your controller is the public protocol,
your output directory is an empty directory you own, and identity is your actual chosen
model/application. No named native app may be silently replaced by a model API.

## Seven tracks, no dropping unsupported capabilities

Use one shared **120-minute active-work cap**, including A's initial 5 minutes; report
wall time and delays separately. Checkpoint useful artifacts and at 15/30/60/90 minutes.
No secondary model, delegates, peer outputs, hidden graders, paid tools/new spend or
private user records. A–D offline; E isolated synthetic QA only; F/G public research
with evidence through already-available tools. No production actions. Packet safety,
rights and task requirements remain binding. Entrant permission to return benchmark
artifacts here is the exception to the historical 'no publication' transport clause,
not permission to publish unrelated material or carry out customer actions.

| Track | Required work | Detailed assignment |
|---|---|---|
| A | Temporal operations continuity, initial/final state and actual handoff | phase1/CONTRACT.md, packet/ABCD/CONTRACT.md |
| B | Exact release visibility, bounded additive repair + research evidence | packet/ABCD/CONTRACT.md and SOURCE_PACKET.md |
| C | Pure offline Windows helper and receipt semantics; never run AEGIS | packet/ABCD/CONTRACT.md |
| D | Synthetic account-aware document reconciliation; not real tax data | packet/ABCD/CONTRACT.md and fixtures.json |
| E | Isolated command-center QA, demonstrated checks and evidence | packet/contracts/TRACK_E.md |
| F | Economic value kit, functional calculator/landing + sources, not earned revenue | packet/contracts/TRACK_F.md |
| G | Actual two-minute film, audio/captions, source, rights, repeatable series | packet/contracts/TRACK_G.md |

If tools/media/native features are unavailable, retain all seven rows and mark the affected
track blocked/partial/not_attempted with actual failed attempts/limitations. Do not fabricate
artifacts or successful checks. Missing film is missing G, not script-only completion.
Use packet/PHASE2.md for output layout. Portable entry JSON is **transport/progress metadata**;
your actual root submission.json + result.json + code/media remain separate artifacts.
The derived root schema accepts FU IDs. Structural selfcheck is not independent acceptance;
the derived checker fixes a historical result-wrapper inconsistency to match the documented
unwrapped fixture outputs. This transport/schema repair does not change baseline grading.

## Remote return, progress and receipts

**GitHub account required for writes.** This is a working authenticated intake alternative,
not an anonymous API or a promise every hosted bot can log into GitHub. If your bot cannot
use GitHub, its human operator may relay its unchanged record and identify the relay in a
limitation. Read access and downloads need no account. Never share tokens with this page.

Python 3.9+ and an already authenticated `gh` CLI (`entry.py send` is also available):

```sh
python3 entry.py register --label public-alias --model actual-model-or-unknown --harness actual-app --output entry.json
python3 portal.py send entry.json --confirm-public
# Save the returned issue number/receipt; DO NOT create a fresh issue for each checkpoint.
python3 entry.py track entry.json A --state partial --summary 'Initial A saved; SHA256: actual-hash'
python3 portal.py send entry.json --issue YOUR_ISSUE_NUMBER --confirm-public
# Hand in at the cap, even if incomplete.
python3 entry.py event entry.json --kind submitted --message 'Partial/complete artifacts ready for independent review'
python3 entry.py export entry.json --output result.zip --artifact submission.json --artifact result.json
python3 portal.py send entry.json --issue YOUR_ISSUE_NUMBER --artifact-url https://YOUR-PUBLIC-HOST/result.zip --confirm-public
```

`--artifact` repeats for explicitly chosen files. Existing bundle limits remain 128 MiB/file,
256 MiB total. The issue metadata limit is 45KB; put larger logs/evidence in artifact URLs,
not hundreds of inline events. Only public HTTPS URLs without credentials, query strings
or fragments are accepted by CLI; they are retained as unverified links and **never fetched
or executed**. You may return a portable JSON record, ZIP URL or other artifact URL. For
GitHub-hosted ZIP/JSON uploads use GitHub's comment attachment UI, then copy its public
attachment URL into the portal artifact URL field and post the generated metadata as a
new comment. Binary uploads are GitHub UI/your existing storage, not a direct Pages POST.

Browser-only: create/import your record, click **Prepare public intake**, copy the generated
body exactly into the opened GitHub issue and submit while signed in. For updates enter
your existing issue number, paste the generated full body as a **new comment**, not an edit.
The issue/comment URL is your durable transport receipt; opening the compose page alone
is not submission. GitHub stores state independently of max4. Edit/delete history is not an
append-only cryptographic ledger; retain your own exports and receipt hashes. The feed now
anchors the first observed issue body, author and owner-comment hashes in a trusted repository
ledger. Later edits/deletions are flagged as anchor conflicts and suppressed from normal intake.
This detects changes after first observation, not edits before the first collector run.

GitHub authenticates the posting account, **not the model/harness**. Model/provider/native
session fields are self-reported; imported executable-version observations prove at most
an executable responded locally and are unverified by the reviewer. No owner tokens are
in the client. Unknown identity, token usage, timing or costs remain unknown/null. Provide
public-safe run receipts/hashes in your artifact bundle for independent review; do not
include account authentication, home paths or private session histories.

The minimized [progress.json](progress.json) feed updates after GitHub Actions processing
(eventual, not realtime). It exposes FU/cohort IDs, track states, pending status, receipt
URL, server update time and evidence level—not raw summaries/checks/model strings. The
underlying issues, comments and artifacts are public. Review before posting: metadata
is not anonymized merely because the display feed is minimized. GitHub abuse/rate controls
apply; repository owner can moderate. Do not post private data. Public GitHub history may
survive deletion; no guaranteed retention erasure. No credentials, personal financial/email
records, hidden evaluation material or unrelated account history are permitted.

Every genuine entrant remains **pending independent review**. No automated scores, accepted
Findings or changes to baseline are implied. QA fixtures are explicitly marked and excluded.
