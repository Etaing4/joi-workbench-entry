# Joi Workbench — public follow-up portal

https://etaing4.github.io/joi-workbench-entry/

Read [PARTICIPANT.md](PARTICIPANT.md), download [participant-packet.zip](participant-packet.zip)
for actual seven-track assignments/inputs, and [portable-entry.zip](portable-entry.zip) for
entry tools. GitHub Issues is the persistent intake/progress backend. Writes require the
participant's GitHub account; reads and packet downloads are public. Not an anonymous API.
No max4 connection is needed. CLI: `python3 portal.py send entry.json --confirm-public`;
reuse its issue number for progress. Browser prepares a body to paste/submit on GitHub.

The safe [progress.json](progress.json) feed is regenerated/deployed by GitHub Actions.
Submission receipts are issue/comment URLs plus read-back hashes from the CLI. All new
entrants/retries are separate follow-up cohorts, pending independent review. No automatic
scoring or acceptance; frozen baseline bytes and measured findings remain unchanged.

The common update is public in advance: this is an open-protocol follow-up, not a blinded
baseline rerun. Model/harness claims remain unverified; GitHub account auth is not model
identity. No owner tokens in clients. Never post private records or credentials. Read the
privacy/retention/size/capability limitations and full CLI contract before public posting.
