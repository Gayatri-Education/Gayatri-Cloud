# Phase Log Template — PXX: <phase name>

**Status:** `NOT_STARTED`  
**Started:** YYYY-MM-DD HH:MM TZ  
**Finished:** Not finished  
**Owner approvals:** None recorded  
**Branch/commit:** Verify at start/end

## 1. `/plan` — goal and scope

- Master-plan section:
- Requirements IDs:
- Prerequisite phases and verified statuses:
- Explicit in-scope work:
- Explicit out-of-scope work:
- Files/modules inspected:
- Proposed files to add/change:
- Relevant open/approved decision IDs:
- Risks and failure modes:
- Migration/data compatibility concerns:
- Test commands to run:
- Acceptance criteria (objective and measurable):
  - [ ] AC-1 ...
  - [ ] AC-2 ...
- Blockers requiring owner action:

## 2. Implementation record

| Item | Details |
|---|---|
| File/change | ... |
| Requirement | `RQ-...` |
| Reason | ... |
| Trade-off | ... |
| Tests added/adjusted | ... |

## 3. Test run evidence

| Stage | Exact command | Exit/result | Evidence path | Notes |
|---|---|---|---|---|
| Format/lint/type | `...` | Not run | `...` | Do not mark pass unless executed |
| Targeted unit | `...` | Not run | `...` | ... |
| Integration | `...` | Not run | `...` | ... |
| Regression | `...` | Not run | `...` | ... |
| Security/negative | `...` | Not run | `...` | ... |
| End-to-end/manual | `...` | Not run | `...` | ... |

## 4. Debugging log

For each failure, preserve:
- failure ID and first observed behavior;
- root-cause evidence;
- change made to resolve it;
- focused retest command/result;
- full regression command/result;
- remaining limitations.

Never delete a failing test or weaken its assertion just to get a pass. If evidence shows the test expectation itself is wrong, document why and get approval for the change.

## 5. Diff and safety review

- [ ] No credentials/private keys/student production data added.
- [ ] Tenant boundary and role checks verified for new access paths.
- [ ] Inputs validated and errors are not swallowed.
- [ ] Logging redacts secrets and follows event/privacy policy.
- [ ] Migration/rollback/backward compatibility reviewed.
- [ ] Dependency/license changes reviewed.
- [ ] Out-of-scope modifications reviewed and removed or documented.

## 6. Acceptance and status

- Passed criteria: `0 / N`
- Blocked criteria: `0`
- Failed criteria: `0`
- Unexplained test failures: `0`
- Required tests skipped: `0` (or list approved reason and owner evidence)
- Phase result: `NOT_STARTED` / `PLANNED` / `IN_PROGRESS` / `TESTING` / `DEBUGGING` / `BLOCKED` / `GREEN` / `AWAITING_OWNER` / `DEFERRED`
- Reason for non-GREEN status, if any:

## 7. Context-resume checkpoint

- What is now true, with evidence:
- What remains incomplete:
- Open decision IDs:
- Known defect IDs:
- Last known passing test command:
- Git status and commit/hash:
- Exact one next action:
- Files a resumed agent must read first:

## 8. Closeout message

Summarize scope, changed files, actual tests and results, unresolved issues, decision IDs, security/migration concerns and next action. Stop at this boundary; do not begin the next phase automatically.
