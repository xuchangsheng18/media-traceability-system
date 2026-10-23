# T014隔离实施裁定与适用边界

2026-10-20；P01—P07批准范围。下列裁定依执行顺序完整保存，每条包括原因及判断错误的影响。它们不是正式业务制度、共享采用或整卡验收；人员/分类/委托、现场负载、T013真实恢复与31个未挂载操作仍另列。

独立最终复核发现7项重要问题、0项严重/单列次要问题，已在同一次测试先失败后通过的修复批次处理；详见[复核与修复](t014-isolated-review-disposition.md)。没有第二轮评审来替代实际回归。

本次导出的执行记录SHA256：`c16b355233831a336c7cc999536e13dff17ddf0b018583af5468a14c555014bd`；共有38条裁定。

1. Ruling: Plan headings now use Task 1..7 with P01..P07 labels for the skill's brief extractor; no scope or technical change.

2. Task 1: Ruling: ActiveRole expiry uses finite float epoch seconds instead of integer truncation, preserving PostgreSQL subsecond expiry and exact now>=expiry rejection; no external field changes. Cost if wrong: conservative unavailability rather than extended access.

3. Task 3: Ruling: RuleTarget adds optional immutable source_ids and request_digest to bind every import source and exact path/query/body; seven original positional fields preserved. A single-source target would miss entries in ImportRequest. Cost if wrong: internal adapter compatibility; public API/SQL unchanged.

4. Task 3: Ruling: create_app accepts structural ConditionalPort implemented by the production authority and explicit test-only adapters. Default remains None/503; no fixture is imported by application code. Cost if wrong: adapter validation must be enforced at the guard and fence.

5. Task 4: Ruling: retain the planned DutyFacts six fields and add internal immutable BoundDutyFacts for exact object, current assignment and verified person bindings; store proof only in existing decision evidence_refs JSON — this binds old votes without an external API/schema change — cost if wrong: old unbound votes conservatively invalidate and need reapproval.

6. Task 4: Ruling: explicit trusted DutyAssignmentReader is required because current SQL has no authoritative executor/evaluator/person registry; only test fixtures provide synthetic people — no identity-by-user-id or invented formal assignment — cost if wrong: missing providers return503.

7. Task 5: Ruling: independent GenerationProof binds database name/OID, epoch floor, immutable policy digest and recovery generation; metadata starts NULL, with no automatic activation — a restored old database cannot self-certify a new generation — cost if wrong: unavailable authority blocks actions until independently confirmed.

8. Task 5: Ruling: initial exact object version and retained row locks are followed by full current-condition reauthorization without requiring the pre-write object version after our own legitimate update — otherwise every version-changing operation rejects itself — cost if wrong: adapters must retain immutable request/source/object scope and all actual conditions.

9. Task 5: Ruling: append-only review_record/evidence_package reads omit FOR SHARE because runtime lacks UPDATE and database triggers already reject mutation; mutable object/source rows are locked in epoch-first order — cost if wrong: throughput/deadlock behavior still needs explicit isolated measurement, not a production guarantee.

10. Task 5: Ruling: HTTP authorization context binds one actor, one root transaction and precommit checks; absent fence rejects writes. Background work is closed separately by P06 using real execution subjects, never fabricated JWTs — cost if wrong: P05 alone is not the whole runtime acceptance.

11. Task 6: Ruling: prepare RED tests while Task 5 repeats verification of its already committed,99-test-passing snapshot; no P06 production change or concurrent SQL suite until Task 5 task-done succeeds — independent test preparation avoids idle time without changing the validated snapshot — cost if wrong: task boundaries must be checked against exact commits and saved runner tags.

12. Task 6: Ruling: additive0009 resolves only exact work identity/map through a runtime-only SECURITY DEFINER function; real job ownership stays in an actor-bound RLS query — no fabricated JWT or new table grants — cost if wrong: migration/function ACL and identity rebinding must remain covered.

13. Task 6: Ruling: RoleDirectory implements read_roles and read_for_work through structurally separate HTTP/work protocols; WorkRoleFacts retains fractional deadlines capped at5seconds and actual identity expiry — HTTP-only readers cannot accidentally impersonate work support — cost if wrong: absent work support returns503.

14. Task 6: Ruling: internal task work consumes existing task.create/TASK_CREATE plus actual creator, analysis source purpose and explicit model/version/capability facts; cancellation uses task.cancel — no task.execute permission seed or new HTTP route — cost if wrong: missing authoritative model/delegation facts deny work rather than silently expanding the41 public permissions.

15. Task 6: Ruling: retain existing pagination/receipt storage, protect its real transaction boundaries through the common context and fresh per-request guard, and run the existing named cursor/receipt revocation cases instead of duplicating them solely for a new test name — cost if wrong: future mounted or worker entrypoints must use the same fence and regression gate.

16. Task 7: Ruling: prepare parser RED cases and documentation while Task 6 repeats its exact committed-source work/runtime verification; no gate production changes until its success and observed RED — same bounded overlap as Task 5/6 — cost if wrong: completion evidence must stay pinned to the recorded source commit.

17. Task 7: Ruling: normalize only this batch's changed text to the repository's LF policy before regenerating the candidate manifest —19 current text files had CRLF while Git stores LF, which otherwise makes byte-hash claims differ between Windows and Linux — cost if wrong: current candidate and final committed bytes must be compared, and historical protected originals/locks/0001—0006 must remain exact.

18. Task 7: Ruling: delivery manifest binds all2097 staged Git blobs; raw worktree equality is additionally required for this batch's changed files, not unrelated unchanged historical text — existing stage-two-supplement-report.json has preexisting Windows CRLF while Git stores LF; it is left untouched — cost if wrong: final Linux exact-manifest audit and original source/lock preservation still gate delivery.

19. Task 7: Ruling: the979-test runtime binding covers backend/tests, the executed permission verifier and confirmed rule JSON; the navigation generator changed during that long run and is verified separately by committed-source documentation checks and hosted CI — no claim that the old full snapshot ran the newer generator — cost if wrong: exact-source/hash audits must reject a mismatched runtime file or current generator/check failure.

20. Task 7: Ruling: run the single final read-only code review once all P01—P07 implementation and current full/extended-gate tests are green, while hosted legacy CI and delivery receipts finish independently — avoids an idle serial wait and does not record P07 complete early — cost if wrong: any later CI/code defect belongs to the same one TDD fix pass, and no completion is claimed until actual CI is verified.

21. Final review: Ruling: review the entire approved plan change range b9770b2..c89e75b and its integration with the baseline, rather than unrelated earlier native-migration/history work already on this reused feature branch — b9770b2 is the recorded plan execution baseline — cost if wrong: pre-baseline behavior outside the inspected integration paths is not newly certified.

22. Task 7: Ruling: a refresh interval cannot be a hard job timeout; retain the root transaction, original subject/operation/target and epoch, then freshly reauthorize at commit, including current token, delegation, service, source, rule and generation expiry — approved PR04 expressly excludes killing every long job after five seconds — cost if wrong: fresh exact-object/expiry and rollback regressions must fail delivery; global-lock throughput remains unproven.

23. Task 7: Ruling: generation semantic identity excludes its freshly read confirmed_at/valid_until, but fixes database name/OID, policy version/hash, recovery generation and a nondecreasing applicable epoch floor; each new interval is independently checked — cost if wrong: true retirement, expired proof, epoch/policy rollback and actual clock reversal remain rejection tests.

24. Task 7: Ruling: bind approval votes to stable actor/person/mapping and duty/object versions, with current proof freshness checked separately. Proof version2 preserves historical person_valid_until for audit; old version1 votes conservatively need reapproval and are never rewritten/deleted — cost if wrong: test unchanged renewal, true mapping/duty change and the fixed1800-second approval boundary; no automatic TTL renewal.

25. Task 7: Ruling: only SQL-unresolved delegation predicates may be filled by the exact trusted adapter; owner/same_org/case/source and other SQL predicates remain protected, including False — cost if wrong: missing/revoked/mismatched delegation must deny, no client-supplied authority.

26. Task 7: Ruling: explicitly resolve imports through import_item, reviews through task/asset, clusters through cluster_member/asset; canonical propagation argument is cluster_id. Collection eligibility is not item authorization: source/purpose/classification must constrain case-scoped SQL results before page/count/cursor, including empty pages — cost if wrong: real positive HTTP plus per-source revocation, filtering and cursor regressions must block closure.

27. Task 7: Ruling: clock sampling, finite validation and high-water update share one lock, not just assignment — cost if wrong: deterministic earlier/later request interleaving and true backward time must remain covered.

28. Task 7: Ruling: publish a reversible feature-source checkpoint only after all7 finding regressions and quality/doc gates have actual scoped green results, while the complete1009-case run continues and hosted exact-source CI starts independently — neither P07 nor whole-task completion is claimed and no main merge/runtime adoption occurs — cost if wrong: the checkpoint remains an unaccepted feature candidate; a failed full run or CI must be fixed before task-done or acceptance.

29. Task 7: Ruling: preserve all previous planning-evidence rows/scopes rather than deduplicating by path; append only the new owner MFA negative attestation — repeated paths can carry different historical scope — cost if wrong: final current-document validation and source manifests must reject any evidence-set inconsistency.

30. Final: Ruling: formal PR03/05/06 and authority providers remain unavailable because this approved batch supplies isolated rules, not official classification, purpose, personnel, delegation or service registries — cost if wrong: real deployment remains denied until authoritative adapters and policy adoption are independently verified.

31. Final: Ruling: unchanged database name/OID after uncontrolled restore is outside the demonstrated generation boundary; retain the external retirement requirement rather than claiming automatic detection — cost if wrong: bypassing the controlled recovery process can reuse stale authority and cannot be accepted.

32. Final: Ruling: T013 private USB, actual identity restore, old-session/key invalidation and bootstrap retirement are independent of the T014 test verdict — owner control and precise maintenance approval remain required — cost if wrong: a successful permission suite could otherwise conceal untested recovery or premature credential retirement.

33. Final: Ruling:31 unmounted operations, actual algorithm result production and organization model release remain with their original tasks; no placeholder success is added to satisfy coverage counts — cost if wrong: full product delivery remains incomplete until those tasks are implemented and tested.

34. Final: Ruling: getForensics is CASE_READ under the existing contract; do not add CASE_ANALYSIS-purpose checks merely because the reviewer declined to judge that policy — cost if wrong: any future purpose-policy change requires its own explicit scope and regression review.

35. Final: Ruling: isolated timing measurements do not certify global-lock capacity, WAN/Keycloak revocation SLA or shared runtime adoption — no benchmark or deployment is invented — cost if wrong: production sizing and remote authority behavior require their own tests.

36. Final: Ruling: final CI and staged/server manifest audits remain separate gates, while unrelated pre-b977 history is context rather than newly certified work — cost if wrong: absent exact-source/digest verification would make old success look current.

37. Task 7: Ruling: completion uses the actual current hosted PostgreSQL permission gate and actual expected-failure probe once their exact commit/artifact digests pass, without repeating an equivalent native SQL suite; the fresh11 committed-source data/navigation checks combine with4 earlier unchanged-code engineering/model checks and the current32 hosted gates — all original command scopes remain required, only redundant reruns are avoided — cost if wrong: task-done rejects any failed gate, missing proof, changed runtime byte or mismatched source commit.

38. Final: Ruling: retain the existing feature branch and worktree for the user-authorized T001—T123 continuation, applying only already authorized GitHub source pushes and Linux fast-forwards; do not ask another integration menu or merge main — cost if wrong: the work remains an unmerged candidate and shared runtime adoption is still outstanding.
