# T015数据范围隔离实施裁定

按实际执行顺序保留每项裁定、原因及判断错误的代价。P01目前仅为内部类型/目录验证；P02—P07、共享采用和整卡验收另列。

1. Task 1: Ruling: internal invalid scope data raises existing AUTHORITY_SCOPE_INVALID503; client request validation still precedes it — these are server trust bindings, not a new public request schema — cost if wrong: clients must never see internal structures or raw exceptions, and negative tests gate integration.

2. Task 1: Ruling: HTTP Principal has no mapping_version field; bind its real issuer/subject/actor, target and policy/generation, while T014 independently rechecks directory mappings. Work subjects bind actual identity_id/mapping_version — do not invent an authenticated field — cost if wrong: a mapping change cannot be detected by DataScope alone and must continue to fail T014 root revalidation.

3. Task 1: Ruling: constructor validates registered mounted/work operations using lazily read existing internal catalogs, with no database connection; do not copy an independent operation whitelist — cost if wrong: circular imports must be caught by actual module-import tests and later DB integration.

4. Task 1: Ruling: follow the user-approved per-task targeted verification and retain full original module regression/engineering gates at integration and P07, rather than rerun unchanged whole product services for each unused type file — this phase adds no imports to old application entrypoints — cost if wrong: no full-product PASS is claimed for P01 and any later full-suite failure remains a named blocker.

5. Task 1: Ruling: first multi-target harness invocation passed the test list as one argument, so pytest exit4 ran zero tests; discard it as test evidence and re-run with individual argv entries. Its mypy failure exposed a variable-length tuple annotation, now corrected without changing behavior — cost if wrong: no completion/RED claim may use those zero-test reports.

6. Task 1: Ruling: source_ids are a set for scope identity, so sort their canonical UUID values before hashing; reject malformed work targets before attribute access — three actual RED failures prove both defects — cost if wrong: initial canonical binding affects only new internal DataScope, and T014 exact target/version/source revalidation remains mandatory.
