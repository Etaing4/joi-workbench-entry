# Portable follow-up contract v1

## What is live, and what is not

The public page is static. Its registration, progress list, readiness marker, browser auto-save and same-origin tab refresh work locally. Nothing is submitted, shared across computers, scored, or accepted automatically. Return the downloaded JSON/ZIP using the task owner's existing attachment channel. No max4 connection is required. A reviewer imports it and runs independent checks before any findings are changed.

A participant must obtain the owner-approved task packet separately. This package intentionally excludes baseline source packets, golden answers, grading materials, personal records and all credentials. A reference is not the full study assignment.

## Quick start (Python 3.9+ standard library)

Unzip the package in your own empty working directory. No install or account is required.

```sh
python3 entry.py register --label cloud-example --model unknown --harness "Cloud Bot" --output entry.json
# Optional, only if you want to probe a known executable with --version:
python3 entry.py detect python
# For a baseline access-blocked retry, add --retry-of E04 at registration.
python3 entry.py event entry.json --kind started --message "Received participant packet"
python3 entry.py track entry.json A --state partial --summary "Initial analysis ready" --check-command "your actual check command" --observed-result "actual output, not invented"
python3 entry.py event entry.json --kind checkpoint --track A --message "First useful artifact"
python3 entry.py event entry.json --kind submitted --message "Ready for independent review"
python3 entry.py export entry.json --output result.zip --artifact answer.txt
python3 entry.py validate result.zip
```

`--artifact` can be repeated for explicitly chosen files. Export reads only those named files. ZIP attachments are opaque untrusted bytes, never executed by the tool. JSON alone transports metadata and must not claim bundled artifact payloads. Files over 128 MiB / total 256 MiB exceed v1 limits; use an owner-approved external attachment transport for larger media and record the limitation. Existing ZIP targets are never overwritten. Protect your working JSON and retain exports as immutable checkpoints. `event` and `track` accept only working `.json` records and refuse ZIP inputs. Track summaries/state are current projections that can be revised by appending a new progress event; they are not independently authenticated immutable test evidence. Import archives every received snapshot. A same-event-history change to tracks/state/limitations is rejected. Identity/cohort and existing event prefixes cannot be revised through import.

## Cloud / bot adapter

A bot without shell access can use the web form, or return the JSON contract in a single `json` fenced code block. Start from a genuine registration JSON created by the page or CLI: preserve its identity, cohort and event history. Do not invent observations or accepted findings. The model/harness fields are your own claims unless a separate runner can verify them. The browser cannot read your CLI or detect your runtime model.

```sh
python3 entry.py adapt bot-response.txt --source cloud-bot --output adapted.json
python3 entry.py validate adapted.json
python3 entry.py import adapted.json --inbox reviewer-inbox
python3 entry.py import result.zip --inbox reviewer-inbox
```

`adapt` accepts raw JSON or one fenced JSON response. It preserves the contract; receipt records adapter source and source SHA-256. Import preserves original source bytes plus normalized immutable snapshots by content hash. Re-import is idempotent. Changed cohort/identity or divergent event history is a conflict, not an overwrite. Out-of-order earlier checkpoints remain archived and must not supersede newer progress. A ZIP is validated in memory, never extracted. Import never executes artifacts, sends messages, modifies baseline records or awards acceptance. Review an imported JSON in the UI separately if desired.

## Contract semantics

* `schema_version`: `joi-portable-entry/1`.
* `entry_id`: random `FU-<UUID>`; frozen E01–E10 IDs are prohibited here.
* `baseline_ref`: `JOI-WORKBENCH-20261017-01` is a reference only.
* `cohort`: immutable random `FOLLOWUP-<UUID>`, `kind: follow-up`, nullable `retry_of: E01` … `E10`. Each attempt is a distinct follow-up arm; do not combine these with the frozen 10-route/70-cell baseline.
* Identity: immutable model/harness/provider/session claims, each with `value` and `provenance: self_reported` or `unknown`. Optional installed CLI records have `observed_executable` or `unknown`: this proves only that the executable answered `--version`, not its model, account, actual run or author. Imported observations are unverified claims to the reviewer. Hashes are integrity checks, NOT signatures/authentication.
* `state`: registered/running/blocked/submitted. `review_state` must be `pending`. Entrants cannot certify acceptance.
* All A–G tracks: state, summary, checks (command and actual observed result), relative artifact references and limitations. No commands are executed.
* Append-only `events`: consecutive one-based sequence, timestamp (untrusted producer clock), kind started/checkpoint/blocked/artifact/submitted, nullable track, message and self_reported provenance. The producer preserves earlier events unchanged.
* ZIP root: `manifest.json`, `submission.json`, and exactly the declared `artifacts/...` members. Manifest includes version, exact member paths, byte counts and SHA-256. No undeclared or duplicate members, traversal, absolute/backslash paths, symlinks, encrypted members, high compression ratios or oversized files.
* Do not put private filesystem paths, secrets, account information or personal records in messages, commands, labels or artifacts. This tool cannot automatically determine whether chosen artifact content is safe. Review before sharing. The public UI never uploads it.

## Deployment boundary / remaining integration

GitHub Pages can host this safe static package under an existing authorized account. It cannot run a database, accept POST submissions or provide cross-machine live progress. A real shared live service still needs an approved backend resource, authentication/abuse controls, retention rules, public-data consent and reviewer integration. No such backend is implied or silently provisioned here. Frozen baseline and findings remain outside this package.
