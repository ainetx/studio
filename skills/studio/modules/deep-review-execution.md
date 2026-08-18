# Deep Review Execution

This PDSL module executes approved thematic phases and maintains persistent findings, comment/fix queues, reports, monitoring state, and append-only history in the canonical plan.

```pdsl
UNIT DeepReviewExecutionStart
PURPOSE: Select the next unclosed thematic phase and resume from its persisted stage.
DO:
  - RUN read plan metadata, selected checks, phase/group settings, explicit checklist records, execution-settings hash, queues, and progress; re-resolve/hash cited checklist sources
  - REQUIRE phases contain 1..10 checks, form an exact partition of approved active checks, groups partition each phase, and execution settings match EXECUTION_SETTINGS_HASH
  - RUN before selecting each PR phase refresh PR state, head SHA, new commits, current diff/files, CI/check statuses, all comments/threads/replies, resolved/outdated state, and anchor validity; atomically persist monitoring changes/events without treating replies as proof
  - CONTINUE DeepReviewExistingPlanMenu WHEN TARGET_KIND == pull-request AND PR state is merged or closed
  - RUN resolve current immutable target version after the refresh
  - CONTINUE DeepReviewTargetDrift WHEN current version != approved target version
  - SET CURRENT_PHASE_ID = next phase not closed; SET current phase status from persisted progress
  - CONTINUE DeepReviewFinalConsolidation WHEN CURRENT_PHASE_ID == unset
  - CONTINUE DeepReviewExecutionCommandGate WHEN current phase status == pending
  - CONTINUE DeepReviewReviewerDispatch WHEN current phase status == commands-decided
  - CONTINUE DeepReviewVerifierDispatch WHEN current phase status == reviewed
  - CONTINUE DeepReviewPhaseReport WHEN current phase status == verified
  - CONTINUE DeepReviewPRFindingPrepare WHEN current phase status == reported AND TARGET_KIND == pull-request AND an unprocessed verified finding exists
  - CONTINUE DeepReviewLocalFindingQueue WHEN current phase status == reported AND TARGET_KIND == local-changes AND an unprocessed verified finding exists
  - CONTINUE DeepReviewPhaseActionOffer WHEN current phase status == reported AND no unprocessed verified finding exists
RULES:
  - NEVER repeat reviewer or verifier work represented by immutable persisted progress
ON_ERROR:
  execution-settings mismatch or non-partition -> CONTINUE DeepReviewGranularityApply
  plan/check/checklist mismatch -> CONTINUE DeepReviewPlanDrift
```

```pdsl
UNIT DeepReviewExecutionCommandGate
PURPOSE: Gate exact commands attached to current-phase checks.
DO:
  - RUN collect exact planned commands attached to current-phase checks
  - RUN mark phase status = commands-decided WHEN no command exists OR all commands have a recorded decision
  - CONTINUE DeepReviewReviewerDispatch WHEN phase status == commands-decided
  - EMIT phase, dependent checks, exact commands, side effects, and expected evidence
  - EMIT_MENU DeepReviewCommandMenu
  - WAIT user.reply
  - STOP_TURN
MENU DeepReviewCommandMenu:
  TITLE: "Choose how to handle commands attached to this phase."
  OPTIONS:
    1 run displayed commands -> RUN execute only displayed commands and persist command/version/exit/stdout/stderr evidence; RUN mark phase status = commands-decided; CONTINUE DeepReviewReviewerDispatch
    2 skip commands -> RUN persist denied decisions and mark dependent runtime claims evidence-limited; RUN mark phase status = commands-decided; CONTINUE DeepReviewReviewerDispatch
    3 replan -> CONTINUE DeepReviewPlanDrift
    4 cancel -> RETURN status = cancelled with REVIEW_PLAN_PATH
  INVALID:
    EMIT_MENU DeepReviewCommandMenu
    WAIT user.reply
    STOP_TURN
```

```pdsl
UNIT DeepReviewReviewerDispatch
PURPOSE: Run every approved reviewer group in the current phase and account for all phase checks.
DO:
  - RUN immediately before reviewer launch refresh complete PR evidence: state, head, commits, current diff/files, CI/check statuses, all comments/threads/replies, resolved/outdated state, and anchor validity; for local changes resolve current version; atomically persist the pre-reviewer snapshot/digest/timestamp and monitoring events
  - CONTINUE DeepReviewTargetDrift WHEN current version != approved target version
  - CONTINUE DeepReviewExistingPlanMenu WHEN TARGET_KIND == pull-request AND PR state is merged or closed
  - REQUIRE no immutable reviewer result exists for the current attempt of any current-phase check
  - SET selected dispatch group = all reviewer roles/groups assigned to CURRENT_PHASE_ID with only approved checks, target slices, cited checklist excerpts, command evidence, version, and result contract
  - RUN SubAgentDispatch
  - RUN validate returns and persist exactly one immutable `PASS`, `FINDING`, or `INSUFFICIENT_EVIDENCE` result for every current-phase check; persist explicit failure results for missing/invalid returns
  - REQUIRE every current-phase check has exactly one reviewer result
  - SET PHASE_RESULTS = current-phase results
  - RUN mark phase status = reviewed
  - CONTINUE DeepReviewVerifierDispatch
RULES:
  - NEVER let reviewers post, modify target files, or mutate controller state
```

```pdsl
UNIT DeepReviewVerifierDispatch
PURPOSE: Run one independent verifier subagent for the complete phase.
DO:
  - RUN immediately before verification refresh PR state, head SHA, commits, current diff/files, CI/check statuses, and all comments/threads/replies/resolved/outdated state from every participant; for local changes resolve current immutable version
  - RUN atomically persist the verifier-time monitoring snapshot and compare it with the phase-start/reviewer target version
  - CONTINUE DeepReviewExistingPlanMenu WHEN TARGET_KIND == pull-request AND PR state is merged or closed
  - CONTINUE DeepReviewTargetDrift WHEN current version != approved target version
  - REQUIRE no verifier outcome exists for the current attempt of any current-phase check
  - RUN normalize current comments into the duplicate corpus and current head/diff/files into verifier evidence
  - SET selected dispatch group = one independent verifier with all phase checks, immutable reviewer results, current target evidence, cited checklist excerpts, command evidence, and the complete normalized existing-comment corpus
  - RUN SubAgentDispatch
  - RUN immediately after verifier return refresh complete PR evidence again: state, head, commits, current diff/files, CI/check statuses, all comments/threads/replies, resolved/outdated state, and anchor validity; atomically persist the post-verifier snapshot/digest/timestamp and monitoring events; when target evidence changed during verification mark reviewer/verifier outputs stale before routing
  - CONTINUE DeepReviewExistingPlanMenu WHEN TARGET_KIND == pull-request AND PR state is merged or closed
  - CONTINUE DeepReviewTargetDrift WHEN current version != approved target version
  - RUN against current refreshed evidence re-read every candidate location and reject/record `fixed-by-new-commit` when the failure no longer reproduces, with fixing/current commit references; then produce exactly one outcome per check: `confirmed-pass`, `accepted-finding`, `duplicate-existing-comment`, `fixed-by-new-commit`, `rejected-finding`, `merged-finding`, or `retained-insufficient-evidence`; identify duplicates by root cause/surface/failure/correction; for every accepted or duplicate finding render and persist one canonical reportable Markdown body plus digest containing severity, a natural title, evidence/problem, reproduction, expected/actual, ASCII diagram, impact, correction, verification, and duplicate source link when applicable; keep finding/check/phase IDs, provenance, status, digests, workflow/skill/model metadata, and orchestration history only in the internal plan record outside the reportable body; accepted PR findings also require a current inline anchor
  - REQUIRE every current-phase check has exactly one verifier outcome and every duplicate-existing-comment has a non-empty source comment reference
  - SET VERIFIED_FINDINGS = accepted findings plus terminal duplicate records with stable IDs and source check IDs
  - RUN atomically persist reviewer results, verifier outcomes, accepted findings, duplicate records/links, and phase status = verified
  - CONTINUE DeepReviewPhaseReport
RULES:
  - NEVER use author replies/comments as proof without current target evidence
  - NEVER accept a finding that no longer reproduces on the current head; record the fixing/current commit when identifiable
  - NEVER accept runtime claims without executed evidence
```

```pdsl
UNIT DeepReviewPhaseReport
PURPOSE: Persist and show the complete phase report before finding actions.
DO:
  - SET phase report = phase/theme/version/checks, result/outcome counts, commands, accepted findings, duplicate-existing-comment records with source links, evidence gaps, and limitations
  - RUN atomically write phase report and status = reported
  - EMIT phase report
  - CONTINUE DeepReviewFindingReport WHEN an unreported accepted or duplicate finding exists
  - CONTINUE DeepReviewPRFindingPrepare WHEN TARGET_KIND == pull-request AND no unreported finding remains AND an unprocessed actionable finding exists
  - CONTINUE DeepReviewLocalFindingQueue WHEN TARGET_KIND == local-changes AND no unreported finding remains AND an unprocessed actionable finding exists
  - CONTINUE DeepReviewPhaseActionOffer WHEN no unreported or unprocessed actionable finding exists
```

```pdsl
UNIT DeepReviewFindingReport
PURPOSE: Report every stored phase finding to the user exactly as persisted in the plan.
DO:
  - SET CURRENT_FINDING = next accepted or duplicate finding without a presented event
  - CONTINUE DeepReviewPRFindingPrepare WHEN CURRENT_FINDING == unset AND TARGET_KIND == pull-request
  - CONTINUE DeepReviewLocalFindingQueue WHEN CURRENT_FINDING == unset AND TARGET_KIND == local-changes
  - RUN fresh-read CURRENT_FINDING canonical reportable Markdown body and body digest directly from REVIEW_PLAN_PATH
  - EMIT the complete stored reportable body verbatim, preserving severity, its natural review-comment structure, reproduction, expected/actual behavior, ASCII diagram, evidence, impact, correction, verification, and duplicate source link while exposing no internal identifiers or orchestration metadata
  - RUN append a presented event containing finding ID/body digest/timestamp without modifying the stored reportable body
  - CONTINUE DeepReviewFindingReport
RULES:
  - NEVER summarize, compress, paraphrase, reorder, truncate, or regenerate a stored finding during presentation
  - NEVER expose internal IDs, provenance, status/digests, or skill/agent/workflow/model attribution in the reportable body
```

```pdsl
UNIT DeepReviewPRFindingPrepare
PURPOSE: Persist and present a complete inline comment draft for one verified PR finding.
DO:
  - RUN refresh current PR state/head/commits/comments and revalidate finding evidence plus inline commit/path/side/line anchor
  - CONTINUE DeepReviewExistingPlanMenu WHEN PR state is merged or closed
  - CONTINUE DeepReviewTargetDrift WHEN current head != approved target version
  - SET CURRENT_FINDING = next accepted nonduplicate phase finding without terminal/queued comment action; skip terminal duplicate-existing-comment records
  - CONTINUE DeepReviewPhaseActionOffer WHEN CURRENT_FINDING == unset
  - RUN fresh-read the canonical reportable finding body from REVIEW_PLAN_PATH; when no user-edited draft exists initialize the inline payload byte-for-byte from that body, otherwise reuse the exact latest stored draft revision; never regenerate or shorten either
  - RUN atomically persist finding, anchor, exact draft revision/payload digest, queue status = draft, and event before presentation
  - EMIT the exact stored draft body verbatim with its anchor and digest
  - EMIT_MENU DeepReviewPRFindingMenu
  - WAIT user.reply
  - STOP_TURN
MENU DeepReviewPRFindingMenu:
  TITLE: "Prepare this finding for the phase comment queue. Posting happens only after all phase findings are processed."
  OPTIONS:
    1 edit or ask: <text> -> RUN revise/answer, increment draft revision, atomically persist payload/history; CONTINUE DeepReviewPRFindingPrepare
    2 approve and queue -> RUN atomically persist status = approved-queued and event; CONTINUE DeepReviewPRFindingPrepare
    3 decline: <optional reason> -> RUN atomically persist declined status/reason/event; CONTINUE DeepReviewPRFindingPrepare
  INVALID:
    EMIT_MENU DeepReviewPRFindingMenu
    WAIT user.reply
    STOP_TURN
RULES:
  - NEVER summarize, compress, paraphrase, reorder, or truncate a finding/comment body automatically
  - NEVER include internal finding/check/phase/comment IDs, provenance/digests/status, or any skill/agent/workflow/model attribution in a comment payload
  - ALWAYS persist an explicit user edit as a new exact draft revision before later posting
  - ALWAYS block and request an explicit user edit when a provider size limit rejects the full body; never auto-shorten it
  - NEVER post while individual findings are being processed
  - NEVER create a top-level PR comment or add PR findings to the fix queue
```

```pdsl
UNIT DeepReviewLocalFindingQueue
PURPOSE: Automatically queue every verified local finding for fixing.
DO:
  - REQUIRE TARGET_KIND == local-changes
  - RUN mark every unprocessed finding = marked-to-fix and create queued fix entries with finding/check/phase IDs, target files, correction, verification, and events
  - RUN atomically persist findings, fix queue, and history
  - CONTINUE DeepReviewPhaseActionOffer
```

```pdsl
UNIT DeepReviewPhaseActionOffer
PURPOSE: Offer persistent phase-end queue actions.
DO:
  - EMIT current phase and queued comment/fix summaries
  - CONTINUE DeepReviewPhaseClose WHEN (TARGET_KIND == pull-request AND no approved-queued comment exists for CURRENT_PHASE_ID) OR (TARGET_KIND == local-changes AND no queued fix exists for CURRENT_PHASE_ID)
  - EMIT_MENU DeepReviewPRPhaseActions WHEN TARGET_KIND == pull-request
  - EMIT_MENU DeepReviewLocalPhaseActions WHEN TARGET_KIND == local-changes
  - WAIT user.reply
  - STOP_TURN
MENU DeepReviewPRPhaseActions:
  TITLE: "All phase findings are processed. Post this phase's approved inline comments now?"
  OPTIONS:
    1 review and post exact batch -> SET QUEUE_ACTION_RETURN = phase; CONTINUE DeepReviewBatchCommentPost
    2 keep queued and continue -> CONTINUE DeepReviewPhaseClose
    3 inspect queue -> EMIT queue details; CONTINUE DeepReviewPhaseActionOffer
  INVALID:
    EMIT_MENU DeepReviewPRPhaseActions
    WAIT user.reply
    STOP_TURN
MENU DeepReviewLocalPhaseActions:
  TITLE: "All phase findings are processed. Run this phase's queued fixes now?"
  OPTIONS:
    1 review and run exact fix batch -> SET QUEUE_ACTION_RETURN = phase; CONTINUE DeepReviewFixQueueOffer
    2 keep queued and continue -> CONTINUE DeepReviewPhaseClose
    3 inspect queue -> EMIT fix details; CONTINUE DeepReviewPhaseActionOffer
  INVALID:
    EMIT_MENU DeepReviewLocalPhaseActions
    WAIT user.reply
    STOP_TURN
```

```pdsl
UNIT DeepReviewBatchCommentPost
PURPOSE: Validate and post an exact batch of approved queued inline comments.
DO:
  - REQUIRE TARGET_KIND == pull-request
  - RUN select approved-queued comments from CURRENT_PHASE_ID WHEN QUEUE_ACTION_RETURN == phase, otherwise all approved-queued comments
  - RUN refresh current PR state/head/commits and all external inline comments/threads from every participant; revalidate selected anchors/payloads; compare each selected draft against external comments and other batch drafts by root cause, affected surface, failure path, and correction
  - CONTINUE DeepReviewExistingPlanMenu WHEN PR state is merged or closed
  - CONTINUE DeepReviewTargetDrift WHEN current head != approved target version
  - RUN for every duplicate mark comment/finding = duplicate-existing-comment-before-post, store source URL/ID/thread/author/anchor/state, append event, and exclude it; mark invalid anchors stale/blocked
  - EMIT exact remaining valid batch plus stale/blocked/duplicate exclusions with source links
  - CONTINUE DeepReviewBatchActionReturn WHEN no valid nonduplicate comment remains
  - EMIT_MENU DeepReviewBatchCommentMenu
  - WAIT user.reply
  - STOP_TURN
MENU DeepReviewBatchCommentMenu:
  TITLE: "Post this exact nonduplicate inline-comment batch?"
  OPTIONS:
    1 post displayed batch -> RUN immediately refresh PR state/head/commits/comments again and before each post repeat duplicate comparison against all external participant comments; when PR is merged/closed or head changed persist blocked/stale statuses and skip external writes; persist newly detected duplicates with source links and skip them; RUN atomically persist posting intents for still-valid items; RUN post each exact still-valid payload; RUN persist each success/failure independently and append events; CONTINUE DeepReviewBatchActionReturn
    2 keep queued -> CONTINUE DeepReviewBatchActionReturn
    3 cancel -> RETURN queue status
  INVALID:
    EMIT_MENU DeepReviewBatchCommentMenu
    WAIT user.reply
    STOP_TURN
RULES:
  - ALWAYS post the exact latest stored user-visible draft revision whose payload digest was displayed; never wrap it with internal IDs, attribution, provenance, or workflow metadata
  - NEVER post when PR is merged/closed, head differs from approved target version, or an equivalent external comment exists at preflight/immediate pre-write recheck
  - NEVER truncate or summarize a payload automatically
  - NEVER treat partial batch success as complete success
```

```pdsl
UNIT DeepReviewFixQueueOffer
PURPOSE: Approve or defer queued local fixes.
DO:
  - REQUIRE TARGET_KIND == local-changes
  - RUN select queued fixes from CURRENT_PHASE_ID WHEN QUEUE_ACTION_RETURN == phase, otherwise all queued fixes
  - EMIT exact selected fix IDs, findings, target files, corrections, and verification
  - EMIT_MENU DeepReviewFixQueueMenu
  - WAIT user.reply
  - STOP_TURN
MENU DeepReviewFixQueueMenu:
  TITLE: "Run the displayed queued fixes now?"
  OPTIONS:
    1 run fixes -> CONTINUE DeepReviewFixQueueRun
    2 keep queued -> CONTINUE DeepReviewBatchActionReturn
    3 cancel -> RETURN fix queue status
  INVALID:
    EMIT_MENU DeepReviewFixQueueMenu
    WAIT user.reply
    STOP_TURN
```

```pdsl
UNIT DeepReviewFixQueueRun
PURPOSE: Execute approved local fixes through the coding-fix workflow.
DO:
  - RUN atomically persist selected fix tasks = running and intent events
  - RUN approved coding-fix workflow for displayed tasks only
  - RUN atomically persist fixed/failed results, verification evidence, and events per task
  - CONTINUE DeepReviewBatchActionReturn
RULES:
  - NEVER remove source findings or history after fixing
```

```pdsl
UNIT DeepReviewBatchActionReturn
PURPOSE: Return a phase/final/existing queue action to its exact continuation.
DO:
  - CONTINUE DeepReviewPhaseClose WHEN QUEUE_ACTION_RETURN == phase
  - CONTINUE DeepReviewFinalReport WHEN QUEUE_ACTION_RETURN == final
  - CONTINUE DeepReviewExistingPlanMenu WHEN QUEUE_ACTION_RETURN == existing-menu
```

```pdsl
UNIT DeepReviewPhaseClose
PURPOSE: Close one thematic phase after complete result and queue accounting.
DO:
  - REQUIRE every phase check has exactly one reviewer result and verifier outcome
  - REQUIRE (TARGET_KIND == pull-request AND every phase finding has posted/approved-queued/declined/stale-blocked comment status or terminal duplicate-existing-comment or duplicate-existing-comment-before-post status with a source link) OR (TARGET_KIND == local-changes AND every phase finding has a fix-queue entry)
  - RUN atomically mark CURRENT_PHASE_ID closed with version, results, findings, queue refs, and event
  - SET CURRENT_PHASE_ID = unset; SET PHASE_RESULTS = unset; SET VERIFIED_FINDINGS = unset; SET CURRENT_FINDING = unset
  - CONTINUE DeepReviewExecutionStart
```

```pdsl
UNIT DeepReviewCommentReverify
PURPOSE: Verify author-addressed PR comments against the current target and update monitoring history.
DO:
  - REQUIRE TARGET_KIND == pull-request
  - RUN refresh current head, replies, resolved/outdated state, and select comments marked replied/resolved/outdated/stale that require content verification
  - SET selected dispatch group = independent follow-up verifiers with original finding/comment/anchor plus current target evidence, one comment root per task
  - RUN SubAgentDispatch
  - RUN classify each as fixed, still-present, partially-addressed, superseded, or insufficient-evidence; never trust reply/resolution state alone
  - RUN atomically update finding/comment/monitoring statuses and append events
  - EMIT compact re-verification report
  - CONTINUE DeepReviewExistingPlanMenu
RULES:
  - NEVER post replies or resolve threads without a separate explicit action design
```

```pdsl
UNIT DeepReviewFinalConsolidation
PURPOSE: Consolidate all closed phases and offer one final remaining-queue decision.
DO:
  - RUN resolve current immutable target version
  - CONTINUE DeepReviewTargetDrift WHEN current version != approved target version
  - REQUIRE every approved active check has one reviewer result/verifier outcome and every phase is closed
  - RUN compute verdict: BLOCKED for Critical/evidence blocker; CHANGES_REQUIRED for Major; READY_WITH_NOTES for only Minor/nonblocking limitations; READY otherwise
  - SET final report = context, no-discovery limitation, config/check/phase/results/findings, comment/fix queues, command evidence, monitoring state, limitations, and verdict
  - RUN atomically persist final report draft and final-action-pending event
  - CONTINUE DeepReviewFinalActionOffer WHEN approved-queued PR comments or queued local fixes remain
  - CONTINUE DeepReviewFinalReport WHEN no actionable queue entry remains
```

```pdsl
UNIT DeepReviewFinalActionOffer
PURPOSE: Offer posting/fixing once more after all phases, without requiring action.
DO:
  - EMIT final verdict summary and remaining actionable queue entries
  - EMIT_MENU DeepReviewFinalPRActions WHEN TARGET_KIND == pull-request
  - EMIT_MENU DeepReviewFinalLocalActions WHEN TARGET_KIND == local-changes
  - WAIT user.reply
  - STOP_TURN
MENU DeepReviewFinalPRActions:
  TITLE: "All phases are complete. Post the remaining approved inline comments now?"
  OPTIONS:
    1 review and post exact batch -> SET QUEUE_ACTION_RETURN = final; CONTINUE DeepReviewBatchCommentPost
    2 leave comments queued and finish -> CONTINUE DeepReviewFinalReport
    3 inspect queue -> EMIT queue details; CONTINUE DeepReviewFinalActionOffer
  INVALID:
    EMIT_MENU DeepReviewFinalPRActions
    WAIT user.reply
    STOP_TURN
MENU DeepReviewFinalLocalActions:
  TITLE: "All phases are complete. Run the remaining queued fixes now?"
  OPTIONS:
    1 review and run exact fix batch -> SET QUEUE_ACTION_RETURN = final; CONTINUE DeepReviewFixQueueOffer
    2 leave fixes queued and finish -> CONTINUE DeepReviewFinalReport
    3 inspect queue -> EMIT fix details; CONTINUE DeepReviewFinalActionOffer
  INVALID:
    EMIT_MENU DeepReviewFinalLocalActions
    WAIT user.reply
    STOP_TURN
```

```pdsl
UNIT DeepReviewFinalReport
PURPOSE: Persist the final report after the final queue decision and enter monitoring/resume state.
DO:
  - RUN atomically write final report, PLAN_STATUS = monitoring for PR or completed for local, monitoring snapshot, remaining queues, and event
  - EMIT final report with remaining queued comment/fix counts
  - CONTINUE DeepReviewExistingPlanMenu
RULES:
  - NEVER offer top-level or non-inline PR comment submission
```
