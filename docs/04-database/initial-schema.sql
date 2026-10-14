-- Development input candidate. Empty isolated PostgreSQL 16 database only. No business data or approved policy seeds.

BEGIN;

CREATE SCHEMA mt;

REVOKE ALL ON SCHEMA mt FROM PUBLIC;

DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='mt_runtime') THEN CREATE ROLE mt_runtime NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$;

GRANT USAGE ON SCHEMA mt TO mt_runtime;

CREATE TABLE mt.organizations (
    org_id uuid PRIMARY KEY,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid 
);

COMMENT ON TABLE mt.organizations IS '单位目录；本包待评审设计';

CREATE TABLE mt.permissions (
    permission_id uuid PRIMARY KEY,
    code text NOT NULL UNIQUE,
    description text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid 
);

COMMENT ON TABLE mt.permissions IS '权限目录；本包待评审设计';

CREATE TABLE mt.roles (
    role_id uuid PRIMARY KEY,
    code text NOT NULL UNIQUE,
    description text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid 
);

COMMENT ON TABLE mt.roles IS '角色目录；本包待评审设计';

CREATE TABLE mt.cases (
    case_id uuid PRIMARY KEY,
    org_id uuid NOT NULL REFERENCES mt.organizations(org_id),
    display_code text NOT NULL,
    status text NOT NULL CHECK(status IN ('ACTIVE','ARCHIVED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    UNIQUE(case_id,org_id),
    UNIQUE(org_id,display_code)
);

COMMENT ON TABLE mt.cases IS '案件隔离域；本包待评审设计';

CREATE TABLE mt.dataset_version (
    dataset_version_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    dataset_id text NOT NULL,
    version text NOT NULL,
    catalog_sha256 text NOT NULL CHECK(catalog_sha256 ~ '^[a-f0-9]{64}$'),
    authorization_status text NOT NULL CHECK(authorization_status IN ('pending','verified','expired','revoked')),
    split_manifest_ref text NOT NULL,
    actual_count bigint CHECK(actual_count>=0),
    status text NOT NULL CHECK(status IN ('PLANNING','DRAFT','RELEASED','FROZEN','REVOKED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    UNIQUE(org_id,dataset_id,version)
);

COMMENT ON TABLE mt.dataset_version IS '数据版本元数据不存真实样本；本包待评审设计';

CREATE INDEX dataset_version_org_created ON mt.dataset_version(org_id,created_at);

CREATE TABLE mt.index_registry (
    index_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    capability text NOT NULL,
    model_version text NOT NULL,
    dimension integer NOT NULL CHECK(dimension>0),
    normalization text NOT NULL CHECK(normalization IN ('l2','none')),
    index_version text NOT NULL,
    state text NOT NULL CHECK(state IN ('BUILDING','READY','ACTIVE','RETIRED')),
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    UNIQUE(org_id,capability,index_version)
);

COMMENT ON TABLE mt.index_registry IS '索引版本不混向量；本包待评审设计';

CREATE INDEX index_registry_org_created ON mt.index_registry(org_id,created_at);

CREATE TABLE mt.model_registry (
    model_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    name text NOT NULL,
    version text NOT NULL,
    capability text NOT NULL,
    digest text NOT NULL CHECK(digest ~ '^[a-f0-9]{64}$'),
    metric_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    dataset_version text NOT NULL,
    model_card_ref text NOT NULL,
    license_record_ref text NOT NULL,
    backend text NOT NULL,
    environment_ref text NOT NULL,
    status text NOT NULL CHECK(status IN ('REGISTERED','EVALUATED','CANDIDATE','APPROVED','ACTIVE','RETIRED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    UNIQUE(org_id,name,version),
    UNIQUE(org_id,model_id)
);

COMMENT ON TABLE mt.model_registry IS '模型版本与许可引用；本包待评审设计';

CREATE INDEX model_registry_org_created ON mt.model_registry(org_id,created_at);

CREATE TABLE mt.policy_registry (
    policy_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    kind text NOT NULL,
    version text NOT NULL,
    definition_ref text NOT NULL,
    status text NOT NULL CHECK(status IN ('DRAFT','APPROVED')),
    approval_id uuid ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    UNIQUE(org_id,kind,version)
);

COMMENT ON TABLE mt.policy_registry IS '标签阈值流程保留等策略；本包待评审设计';

CREATE INDEX policy_registry_org_created ON mt.policy_registry(org_id,created_at);

CREATE TABLE mt.role_permissions (
    role_permission_id uuid PRIMARY KEY,
    role_id uuid NOT NULL REFERENCES mt.roles(role_id),
    permission_id uuid NOT NULL REFERENCES mt.permissions(permission_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    UNIQUE(role_id,permission_id)
);

COMMENT ON TABLE mt.role_permissions IS '角色功能权限映射；本包待评审设计';

CREATE TABLE mt.users (
    user_id uuid PRIMARY KEY,
    org_id uuid NOT NULL REFERENCES mt.organizations(org_id),
    subject text NOT NULL UNIQUE,
    enabled boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid 
);

COMMENT ON TABLE mt.users IS '用户与认证主体；本包待评审设计';

CREATE TABLE mt.approval_request (
    approval_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid ,
    object_type text NOT NULL,
    object_id uuid NOT NULL,
    object_version bigint NOT NULL CHECK(object_version>0),
    purpose text NOT NULL,
    policy_version text NOT NULL,
    requested_by uuid NOT NULL REFERENCES mt.users(user_id),
    state text NOT NULL CHECK(state IN ('REQUESTED','APPROVED','REJECTED','RETURNED','REVOKED','EXPIRED','INVALIDATED')),
    expires_at timestamptz ,
    reason text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    run_version bigint CHECK(run_version>0),
    result_version bigint CHECK(result_version>0),
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    UNIQUE(case_id,approval_id),
    UNIQUE(org_id,approval_id),
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    CHECK((object_type='model_release' AND case_id IS NULL) OR (object_type<>'model_release' AND case_id IS NOT NULL)),
    CHECK(object_type<>'task' OR (run_version IS NOT NULL AND result_version IS NOT NULL))
);

COMMENT ON TABLE mt.approval_request IS '按目的独立审批申请；本包待评审设计';

CREATE INDEX approval_request_org_created ON mt.approval_request(org_id,created_at);

CREATE TABLE mt.audit_event (
    event_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid ,
    actor_id uuid NOT NULL REFERENCES mt.users(user_id),
    action text NOT NULL,
    object_type text NOT NULL,
    object_id uuid ,
    object_version bigint CHECK(object_version>0),
    outcome text NOT NULL CHECK(outcome IN ('allowed','denied','failed')),
    request_id uuid NOT NULL,
    occurred_at timestamptz NOT NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)
);

COMMENT ON TABLE mt.audit_event IS '追加式审计事实；本包待评审设计';

CREATE INDEX audit_event_org_created ON mt.audit_event(org_id,created_at);

CREATE TABLE mt.case_membership (
    membership_id uuid PRIMARY KEY,
    case_id uuid NOT NULL,
    org_id uuid NOT NULL,
    user_id uuid NOT NULL REFERENCES mt.users(user_id),
    expires_at timestamptz ,
    revoked_at timestamptz ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    UNIQUE(case_id,user_id),
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)
);

COMMENT ON TABLE mt.case_membership IS '显式案件授权；本包待评审设计';

CREATE TABLE mt.content_cluster (
    cluster_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    scope text NOT NULL,
    policy_version text NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,cluster_id)
);

COMMENT ON TABLE mt.content_cluster IS '高可信整内容簇；本包待评审设计';

CREATE INDEX content_cluster_case_created ON mt.content_cluster(case_id,created_at);

CREATE TABLE mt.event_receipt (
    receipt_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    event_id uuid NOT NULL,
    consumer text NOT NULL,
    effect_sha256 text NOT NULL CHECK(effect_sha256 ~ '^[a-f0-9]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,receipt_id),
    UNIQUE(case_id,event_id,consumer)
);

COMMENT ON TABLE mt.event_receipt IS '消费去重记录；本包待评审设计';

CREATE INDEX event_receipt_case_created ON mt.event_receipt(case_id,created_at);

CREATE TABLE mt.idempotency_record (
    idempotency_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    actor_id uuid NOT NULL REFERENCES mt.users(user_id),
    operation text NOT NULL,
    idempotency_key text NOT NULL,
    request_sha256 text NOT NULL CHECK(request_sha256 ~ '^[a-f0-9]{64}$'),
    response_ref jsonb NOT NULL DEFAULT '{}'::jsonb,
    expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,idempotency_id),
    UNIQUE(case_id,actor_id,operation,idempotency_key)
);

COMMENT ON TABLE mt.idempotency_record IS '主体请求摘要幂等；本包待评审设计';

CREATE INDEX idempotency_record_case_created ON mt.idempotency_record(case_id,created_at);

CREATE TABLE mt.import_job (
    import_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    state text NOT NULL,
    requested_count integer NOT NULL CHECK(requested_count>0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,import_id)
);

COMMENT ON TABLE mt.import_job IS '批量清单导入作业；本包待评审设计';

CREATE INDEX import_job_case_created ON mt.import_job(case_id,created_at);

CREATE TABLE mt.model_evaluation (
    evaluation_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    model_id uuid NOT NULL,
    dataset_id text NOT NULL,
    dataset_version text NOT NULL,
    protocol_id text NOT NULL,
    split text NOT NULL CHECK(split IN ('validation','calibration','holdout')),
    sample_count integer NOT NULL CHECK(sample_count>0),
    failure_count integer NOT NULL CHECK(failure_count>=0 AND failure_count<=sample_count),
    metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
    artifact_ref jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    FOREIGN KEY(org_id,model_id) REFERENCES mt.model_registry(org_id,model_id)
);

COMMENT ON TABLE mt.model_evaluation IS '不可覆盖评测记录；本包待评审设计';

CREATE INDEX model_evaluation_org_created ON mt.model_evaluation(org_id,created_at);

CREATE TABLE mt.object_version (
    object_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    bucket_alias text NOT NULL,
    object_key text NOT NULL,
    version_id text NOT NULL,
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    size_bytes bigint NOT NULL CHECK(size_bytes>0),
    retention_policy_version text ,
    retain_until timestamptz ,
    legal_hold boolean NOT NULL DEFAULT false,
    object_lock_verified boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,object_id),
    UNIQUE(bucket_alias,object_key,version_id)
);

COMMENT ON TABLE mt.object_version IS '对象版本与摘要清单；本包待评审设计';

CREATE INDEX object_version_case_created ON mt.object_version(case_id,created_at);

CREATE TABLE mt.outbox_event (
    event_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    topic text NOT NULL,
    aggregate_id uuid NOT NULL,
    aggregate_version bigint NOT NULL CHECK(aggregate_version>0),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    published_at timestamptz ,
    attempts integer NOT NULL DEFAULT 0 CHECK(attempts>=0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,event_id),
    UNIQUE(case_id,topic,aggregate_id,aggregate_version)
);

COMMENT ON TABLE mt.outbox_event IS '事务发件箱；本包待评审设计';

CREATE INDEX outbox_event_case_created ON mt.outbox_event(case_id,created_at);

CREATE TABLE mt.source_registry (
    source_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    name text NOT NULL,
    source_type text NOT NULL,
    authorization_ref text NOT NULL,
    purpose text[] NOT NULL,
    authorization_status text NOT NULL CHECK(authorization_status IN ('pending','verified','expired','revoked')),
    expires_at timestamptz ,
    authorization_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,source_id)
);

COMMENT ON TABLE mt.source_registry IS '来源与用途授权；本包待评审设计';

CREATE INDEX source_registry_case_created ON mt.source_registry(case_id,created_at);

CREATE TABLE mt.user_roles (
    user_role_id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES mt.users(user_id),
    role_id uuid NOT NULL REFERENCES mt.roles(role_id),
    expires_at timestamptz ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    UNIQUE(user_id,role_id)
);

COMMENT ON TABLE mt.user_roles IS '用户角色绑定；本包待评审设计';

CREATE TABLE mt.approval_decision (
    decision_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid ,
    approval_id uuid NOT NULL,
    decision text NOT NULL CHECK(decision IN ('approve','reject','return','revoke','invalidate')),
    decision_actor_id uuid NOT NULL REFERENCES mt.users(user_id),
    reason text NOT NULL,
    evidence_refs jsonb NOT NULL DEFAULT '{}'::jsonb,
    policy_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    FOREIGN KEY(org_id,approval_id) REFERENCES mt.approval_request(org_id,approval_id),
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)
);

COMMENT ON TABLE mt.approval_decision IS '审批历史决定；本包待评审设计';

CREATE INDEX approval_decision_org_created ON mt.approval_decision(org_id,created_at);

CREATE TABLE mt.audit_export (
    export_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    approval_id uuid NOT NULL,
    start_at timestamptz NOT NULL,
    end_at timestamptz NOT NULL,
    purpose text NOT NULL,
    state text NOT NULL,
    artifact_ref jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,export_id),
    FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id),
    CHECK(end_at>start_at)
);

COMMENT ON TABLE mt.audit_export IS '审计导出作业；本包待评审设计';

CREATE INDEX audit_export_case_created ON mt.audit_export(case_id,created_at);

CREATE TABLE mt.content_item (
    content_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    source_id uuid NOT NULL,
    platform text ,
    account_id text ,
    published_at timestamptz ,
    discovered_at timestamptz NOT NULL,
    title text ,
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,content_id),
    FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id)
);

COMMENT ON TABLE mt.content_item IS '逻辑内容对象；本包待评审设计';

CREATE INDEX content_item_case_created ON mt.content_item(case_id,created_at);

CREATE TABLE mt.model_release (
    release_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    model_id uuid NOT NULL,
    bundle_sha256 text NOT NULL CHECK(bundle_sha256 ~ '^[a-f0-9]{64}$'),
    calibration_version text ,
    backend text NOT NULL,
    index_version text ,
    approval_id uuid ,
    state text NOT NULL CHECK(state IN ('CANDIDATE','APPROVED','ACTIVE','RETIRED')),
    environment_ref text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    FOREIGN KEY(org_id,model_id) REFERENCES mt.model_registry(org_id,model_id),
    FOREIGN KEY(org_id,approval_id) REFERENCES mt.approval_request(org_id,approval_id)
);

COMMENT ON TABLE mt.model_release IS '模型发布包；本包待评审设计';

CREATE INDEX model_release_org_created ON mt.model_release(org_id,created_at);

CREATE TABLE mt.operation_token (
    token_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid ,
    approval_id uuid NOT NULL,
    actor_id uuid NOT NULL REFERENCES mt.users(user_id),
    purpose text NOT NULL,
    object_id uuid NOT NULL,
    object_version bigint NOT NULL CHECK(object_version>0),
    token_sha256 text NOT NULL CHECK(token_sha256 ~ '^[a-f0-9]{64}$'),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(org_id) REFERENCES mt.organizations(org_id),
    UNIQUE(token_sha256),
    FOREIGN KEY(org_id,approval_id) REFERENCES mt.approval_request(org_id,approval_id),
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id)
);

COMMENT ON TABLE mt.operation_token IS '一次性确认授权记录；本包待评审设计';

CREATE INDEX operation_token_org_created ON mt.operation_token(org_id,created_at);

CREATE TABLE mt.propagation_node (
    node_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    cluster_id uuid NOT NULL,
    type text NOT NULL,
    display_label text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,node_id),
    FOREIGN KEY (case_id, cluster_id) REFERENCES mt.content_cluster (case_id, cluster_id)
);

COMMENT ON TABLE mt.propagation_node IS '传播图节点；本包待评审设计';

CREATE INDEX propagation_node_case_created ON mt.propagation_node(case_id,created_at);

CREATE TABLE mt.media_asset (
    asset_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    content_id uuid NOT NULL,
    source_id uuid NOT NULL,
    object_id uuid NOT NULL,
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    mime text NOT NULL,
    size_bytes bigint NOT NULL CHECK(size_bytes>0),
    duration_ms bigint CHECK(duration_ms>=0),
    width integer CHECK(width>0),
    height integer CHECK(height>0),
    kind text NOT NULL CHECK(kind IN ('original','derived')),
    parent_asset_id uuid ,
    mapping_version text NOT NULL,
    state text NOT NULL CHECK(state IN ('VALIDATING','VALID','QUARANTINED','ARCHIVED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,asset_id),
    FOREIGN KEY (case_id, content_id) REFERENCES mt.content_item (case_id, content_id),
    FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id),
    FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id),
    FOREIGN KEY (case_id, parent_asset_id) REFERENCES mt.media_asset (case_id, asset_id)
);

COMMENT ON TABLE mt.media_asset IS '原始或派生媒体；本包待评审设计';

CREATE INDEX media_asset_case_created ON mt.media_asset(case_id,created_at);

CREATE TABLE mt.propagation_edge (
    edge_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    from_node_id uuid NOT NULL,
    to_node_id uuid NOT NULL,
    relation text NOT NULL,
    origin text NOT NULL CHECK(origin IN ('observed','inferred','human')),
    probability double precision CHECK(probability>=0 AND probability<=1),
    evidence_refs jsonb NOT NULL DEFAULT '{}'::jsonb,
    state text NOT NULL CHECK(state IN ('candidate','confirmed','rejected')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,edge_id),
    FOREIGN KEY (case_id, from_node_id) REFERENCES mt.propagation_node (case_id, node_id),
    FOREIGN KEY (case_id, to_node_id) REFERENCES mt.propagation_node (case_id, node_id),
    CHECK(from_node_id<>to_node_id)
);

COMMENT ON TABLE mt.propagation_edge IS '显式推断传播边；本包待评审设计';

CREATE INDEX propagation_edge_case_created ON mt.propagation_edge(case_id,created_at);

CREATE TABLE mt.analysis_task (
    task_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    scene text NOT NULL,
    priority text NOT NULL CHECK(priority IN ('low','normal','high')),
    state text NOT NULL CHECK(state IN ('CREATED','QUEUED','RUNNING','WAIT_REVIEW','REVIEWING','SUCCEEDED','FAILED','RETURNED','CANCEL_REQUESTED','CANCELLED','ARCHIVED')),
    progress double precision NOT NULL DEFAULT 0 CHECK(progress>=0 AND progress<=1),
    run_version bigint NOT NULL DEFAULT 1 CHECK(run_version>0),
    result_version bigint NOT NULL DEFAULT 1 CHECK(result_version>0),
    policy_version text NOT NULL,
    modules text[] NOT NULL,
    missing_modalities text[] NOT NULL DEFAULT '{}',
    report_eligibility text NOT NULL CHECK(report_eligibility IN ('draft_only','reviewable','formal_eligible')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,task_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)
);

COMMENT ON TABLE mt.analysis_task IS '分析任务当前投影；本包待评审设计';

CREATE INDEX analysis_task_case_created ON mt.analysis_task(case_id,created_at);

CREATE TABLE mt.asset_lineage (
    lineage_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    parent_asset_id uuid NOT NULL,
    child_asset_id uuid NOT NULL,
    operation text NOT NULL,
    parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
    code_digest text NOT NULL CHECK(code_digest ~ '^[a-f0-9]{64}$'),
    mapping_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,lineage_id),
    FOREIGN KEY (case_id, parent_asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY (case_id, child_asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    CHECK(parent_asset_id<>child_asset_id),
    UNIQUE(case_id,parent_asset_id,child_asset_id,operation,mapping_version)
);

COMMENT ON TABLE mt.asset_lineage IS '多父对象血缘；本包待评审设计';

CREATE INDEX asset_lineage_case_created ON mt.asset_lineage(case_id,created_at);

CREATE TABLE mt.claim (
    claim_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    subject text ,
    action text ,
    claim_time text ,
    place text ,
    result text ,
    source_segment_refs jsonb NOT NULL DEFAULT '{}'::jsonb,
    model_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,claim_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id)
);

COMMENT ON TABLE mt.claim IS '结构化主张与来源；本包待评审设计';

CREATE INDEX claim_case_created ON mt.claim(case_id,created_at);

CREATE TABLE mt.feature (
    feature_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    model_id uuid NOT NULL,
    dimension integer NOT NULL CHECK(dimension>0),
    normalization text NOT NULL,
    feature_ref jsonb NOT NULL DEFAULT '{}'::jsonb,
    index_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,feature_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY(org_id,model_id) REFERENCES mt.model_registry(org_id,model_id)
);

COMMENT ON TABLE mt.feature IS '模型特征元数据；本包待评审设计';

CREATE INDEX feature_case_created ON mt.feature(case_id,created_at);



CREATE TABLE mt.import_item (
    item_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    import_id uuid NOT NULL,
    ordinal integer NOT NULL CHECK(ordinal>=0),
    source_id uuid NOT NULL,
    asset_id uuid ,
    state text NOT NULL,
    error_code text ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,item_id),
    FOREIGN KEY (case_id, import_id) REFERENCES mt.import_job (case_id, import_id),
    FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    UNIQUE(case_id,import_id,ordinal)
);

COMMENT ON TABLE mt.import_item IS '逐条导入结果；本包待评审设计';

CREATE INDEX import_item_case_created ON mt.import_item(case_id,created_at);

CREATE TABLE mt.search_job (
    search_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    query_asset_id uuid NOT NULL,
    kind text NOT NULL CHECK(kind IN ('image','image_region','video')),
    state text NOT NULL,
    index_version text NOT NULL,
    error_code text ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,search_id),
    FOREIGN KEY (case_id, query_asset_id) REFERENCES mt.media_asset (case_id, asset_id)
);

COMMENT ON TABLE mt.search_job IS '异步检索任务；本包待评审设计';

CREATE INDEX search_job_case_created ON mt.search_job(case_id,created_at);

CREATE TABLE mt.shot (
    shot_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    start_ms bigint NOT NULL CHECK(start_ms>=0),
    end_ms bigint NOT NULL,
    score double precision CHECK(score>=0 AND score<=1),
    mapping_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,shot_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    CHECK(end_ms>start_ms)
);

COMMENT ON TABLE mt.shot IS '镜头时间区间；本包待评审设计';

CREATE INDEX shot_case_created ON mt.shot(case_id,created_at);

CREATE TABLE mt.text_segment (
    segment_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    type text NOT NULL CHECK(type IN ('OCR','ASR','SUBTITLE')),
    start_ms bigint CHECK(start_ms>=0),
    end_ms bigint ,
    text text NOT NULL,
    confidence double precision CHECK(confidence>=0 AND confidence<=1),
    bbox jsonb NOT NULL DEFAULT '{}'::jsonb,
    mapping_version text NOT NULL,
    model_name text NOT NULL,
    model_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,segment_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    CHECK((start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND end_ms>start_ms))
);

COMMENT ON TABLE mt.text_segment IS 'OCR ASR字幕原文；本包待评审设计';

CREATE INDEX text_segment_case_created ON mt.text_segment(case_id,created_at);

CREATE TABLE mt.upload_session (
    upload_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    source_id uuid NOT NULL,
    filename text NOT NULL,
    size_bytes bigint NOT NULL CHECK(size_bytes>0),
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    mime text NOT NULL,
    part_size_bytes bigint NOT NULL CHECK(part_size_bytes>0),
    state text NOT NULL CHECK(state IN ('UPLOADING','VALIDATING','COMPLETED','REJECTED','EXPIRED')),
    expires_at timestamptz NOT NULL,
    owner_id uuid NOT NULL REFERENCES mt.users(user_id),
    asset_id uuid ,
    duplicate_of uuid ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,upload_id),
    FOREIGN KEY (case_id, source_id) REFERENCES mt.source_registry (case_id, source_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY (case_id, duplicate_of) REFERENCES mt.media_asset (case_id, asset_id)
);

COMMENT ON TABLE mt.upload_session IS '上传会话；本包待评审设计';

CREATE INDEX upload_session_case_created ON mt.upload_session(case_id,created_at);

CREATE TABLE mt.keyframe (
    frame_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    shot_id uuid ,
    timestamp_ms bigint NOT NULL CHECK(timestamp_ms>=0),
    object_id uuid NOT NULL,
    quality_score double precision CHECK(quality_score>=0 AND quality_score<=1),
    mapping_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,frame_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY (case_id, shot_id) REFERENCES mt.shot (case_id, shot_id),
    FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id)
);

COMMENT ON TABLE mt.keyframe IS '关键帧；本包待评审设计';

CREATE INDEX keyframe_case_created ON mt.keyframe(case_id,created_at);

CREATE TABLE mt.source_match (
    match_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    search_id uuid NOT NULL,
    query_asset_id uuid NOT NULL,
    candidate_asset_id uuid NOT NULL,
    score double precision CHECK(score>=0 AND score<=1),
    verification_type text NOT NULL CHECK(verification_type IN ('unverified','geometry','temporal','human')),
    relation text NOT NULL CHECK(relation IN ('similar','full_copy','partial_copy','contains','segment_map','unknown')),
    query_start_ms bigint CHECK(query_start_ms>=0),
    query_end_ms bigint ,
    source_start_ms bigint CHECK(source_start_ms>=0),
    source_end_ms bigint ,
    direction text NOT NULL CHECK(direction IN ('forward','reverse','not_applicable')),
    speed_ratio double precision NOT NULL CHECK(speed_ratio>0),
    evidence_refs jsonb NOT NULL DEFAULT '{}'::jsonb,
    index_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,match_id),
    FOREIGN KEY (case_id, search_id) REFERENCES mt.search_job (case_id, search_id),
    FOREIGN KEY (case_id, query_asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY (case_id, candidate_asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    CHECK(query_asset_id<>candidate_asset_id),
    CHECK((query_start_ms IS NULL AND query_end_ms IS NULL) OR (query_start_ms IS NOT NULL AND query_end_ms IS NOT NULL AND query_end_ms>query_start_ms)),
    CHECK((source_start_ms IS NULL AND source_end_ms IS NULL) OR (source_start_ms IS NOT NULL AND source_end_ms IS NOT NULL AND source_end_ms>source_start_ms))
);

COMMENT ON TABLE mt.source_match IS '同源或片段映射候选；本包待评审设计';

CREATE INDEX source_match_case_created ON mt.source_match(case_id,created_at);

CREATE TABLE mt.task_event (
    event_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL CHECK(run_version>0),
    from_state text ,
    to_state text NOT NULL,
    reason text NOT NULL,
    request_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,event_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id)
);

COMMENT ON TABLE mt.task_event IS '任务状态事件；本包待评审设计';

CREATE INDEX task_event_case_created ON mt.task_event(case_id,created_at);

CREATE TABLE mt.task_run (
    task_run_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL CHECK(run_version>0),
    input_sha256 text NOT NULL CHECK(input_sha256 ~ '^[a-f0-9]{64}$'),
    dag_version text NOT NULL,
    policy_version text NOT NULL,
    fencing_epoch bigint NOT NULL DEFAULT 1 CHECK(fencing_epoch>0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,task_run_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    UNIQUE(case_id,task_id,run_version)
);

COMMENT ON TABLE mt.task_run IS '任务运行历史；本包待评审设计';

CREATE INDEX task_run_case_created ON mt.task_run(case_id,created_at);

CREATE TABLE mt.upload_part (
    part_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    upload_id uuid NOT NULL,
    part_no integer NOT NULL CHECK(part_no>0),
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    size_bytes bigint NOT NULL CHECK(size_bytes>0),
    object_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,part_id),
    FOREIGN KEY (case_id, upload_id) REFERENCES mt.upload_session (case_id, upload_id),
    FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id),
    UNIQUE(case_id,upload_id,part_no)
);

COMMENT ON TABLE mt.upload_part IS '分片接收与校验；本包待评审设计';

CREATE INDEX upload_part_case_created ON mt.upload_part(case_id,created_at);

CREATE TABLE mt.task_node_run (
    run_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL CHECK(run_version>0),
    node_code text NOT NULL,
    attempt integer NOT NULL CHECK(attempt>0),
    model_version text ,
    input_hash text NOT NULL CHECK(input_hash ~ '^[a-f0-9]{64}$'),
    state text NOT NULL CHECK(state IN ('PENDING','READY','RUNNING','SUCCEEDED','FAILED','SKIPPED','DEFERRED','CANCELLED','NOT_SUPPORTED')),
    required boolean NOT NULL,
    reason text ,
    lease_token text ,
    fencing_epoch bigint NOT NULL CHECK(fencing_epoch>0),
    started_at timestamptz ,
    ended_at timestamptz ,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,run_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY(case_id,task_id,run_version) REFERENCES mt.task_run(case_id,task_id,run_version),
    UNIQUE(case_id,task_id,run_version,node_code,attempt),
    CHECK(ended_at IS NULL OR started_at IS NOT NULL AND ended_at>=started_at)
);

COMMENT ON TABLE mt.task_node_run IS '节点尝试与租约；本包待评审设计';

CREATE INDEX task_node_run_case_created ON mt.task_node_run(case_id,created_at);

CREATE TABLE mt.task_result (
    result_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL CHECK(run_version>0),
    result_version bigint NOT NULL CHECK(result_version>0),
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    policy_version text NOT NULL,
    summary jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,result_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY(case_id,task_id,run_version) REFERENCES mt.task_run(case_id,task_id,run_version),
    UNIQUE(case_id,task_id,run_version,result_version)
);

COMMENT ON TABLE mt.task_result IS '结果版本快照；本包待评审设计';

CREATE INDEX task_result_case_created ON mt.task_result(case_id,created_at);

CREATE TABLE mt.evidence_item (
    evidence_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL,
    result_version bigint NOT NULL,
    asset_id uuid NOT NULL,
    type text NOT NULL,
    object_id uuid ,
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    captured_at timestamptz NOT NULL,
    model_name text ,
    model_version text ,
    mapping_version text NOT NULL,
    authorization_version text NOT NULL,
    immutable_state text NOT NULL CHECK(immutable_state IN ('RECORDED','SEALED')),
    time_range jsonb NOT NULL DEFAULT '{}'::jsonb,
    bbox jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,evidence_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version)
);

COMMENT ON TABLE mt.evidence_item IS '证据事实版本；本包待评审设计';

CREATE INDEX evidence_item_case_created ON mt.evidence_item(case_id,created_at);

CREATE TABLE mt.evidence_package (
    package_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL,
    result_version bigint NOT NULL,
    version bigint NOT NULL CHECK(version>0),
    manifest_sha256 text NOT NULL CHECK(manifest_sha256 ~ '^[a-f0-9]{64}$'),
    approval_id uuid NOT NULL,
    signature_status text NOT NULL CHECK(signature_status IN ('not_signed','mock','verified','failed')),
    retention_policy_version text NOT NULL,
    state text NOT NULL CHECK(state IN ('DRAFT','SEALED','SUPERSEDED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,package_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version),
    UNIQUE(case_id,task_id,version)
);

COMMENT ON TABLE mt.evidence_package IS '固化证据包版本；本包待评审设计';

CREATE INDEX evidence_package_case_created ON mt.evidence_package(case_id,created_at);

CREATE TABLE mt.report (
    report_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL,
    result_version bigint NOT NULL,
    version bigint NOT NULL CHECK(version>0),
    template_version text NOT NULL,
    approval_id uuid ,
    object_id uuid ,
    state text NOT NULL CHECK(state IN ('DRAFT','GENERATING','READY','FAILED','SUPERSEDED')),
    snapshot_sha256 text NOT NULL CHECK(snapshot_sha256 ~ '^[a-f0-9]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,report_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id),
    FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version),
    UNIQUE(case_id,task_id,version)
);

COMMENT ON TABLE mt.report IS '报告生成与下载状态；本包待评审设计';

CREATE INDEX report_case_created ON mt.report(case_id,created_at);

CREATE TABLE mt.review_record (
    review_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL,
    result_version bigint NOT NULL,
    reviewer_id uuid NOT NULL REFERENCES mt.users(user_id),
    decision text NOT NULL CHECK(decision IN ('confirm_candidate','reject_candidate','return_for_evidence','request_rerun')),
    comments text NOT NULL,
    review_version bigint NOT NULL CHECK(review_version>0),
    policy_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,review_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version),
    UNIQUE(case_id,task_id,review_version)
);

COMMENT ON TABLE mt.review_record IS '业务复核事实；本包待评审设计';

CREATE INDEX review_record_case_created ON mt.review_record(case_id,created_at);

CREATE TABLE mt.risk_finding (
    finding_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL,
    result_version bigint NOT NULL,
    category text NOT NULL,
    score double precision CHECK(score>=0 AND score<=1),
    calibrated_score double precision CHECK(calibrated_score>=0 AND calibrated_score<=1),
    start_ms bigint CHECK(start_ms>=0),
    end_ms bigint ,
    model_name text NOT NULL,
    model_version text NOT NULL,
    threshold_version text ,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,finding_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version),
    CHECK((start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND end_ms>start_ms))
);

COMMENT ON TABLE mt.risk_finding IS '风险候选发现；本包待评审设计';

CREATE INDEX risk_finding_case_created ON mt.risk_finding(case_id,created_at);

CREATE TABLE mt.tamper_finding (
    tamper_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL,
    result_version bigint NOT NULL,
    type text NOT NULL,
    score double precision CHECK(score>=0 AND score<=1),
    calibrated_score double precision CHECK(calibrated_score>=0 AND calibrated_score<=1),
    start_ms bigint CHECK(start_ms>=0),
    end_ms bigint ,
    model_name text NOT NULL,
    model_version text NOT NULL,
    threshold_version text ,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,tamper_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version),
    CHECK((start_ms IS NULL AND end_ms IS NULL) OR (start_ms IS NOT NULL AND end_ms IS NOT NULL AND end_ms>start_ms))
);

COMMENT ON TABLE mt.tamper_finding IS '疑似篡改发现；本包待评审设计';

CREATE INDEX tamper_finding_case_created ON mt.tamper_finding(case_id,created_at);

CREATE TABLE mt.claim_evidence_relation (
    relation_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    claim_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    relation text NOT NULL CHECK(relation IN ('supports','contradicts','partially_supports','unrelated','insufficient')),
    score double precision CHECK(score>=0 AND score<=1),
    model_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,relation_id),
    FOREIGN KEY (case_id, claim_id) REFERENCES mt.claim (case_id, claim_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)
);

COMMENT ON TABLE mt.claim_evidence_relation IS '主张证据关系；本包待评审设计';

CREATE INDEX claim_evidence_relation_case_created ON mt.claim_evidence_relation(case_id,created_at);

CREATE TABLE mt.cluster_member (
    member_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    cluster_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    relation text NOT NULL CHECK(relation IN ('full_copy')),
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,member_id),
    FOREIGN KEY (case_id, cluster_id) REFERENCES mt.content_cluster (case_id, cluster_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id),
    UNIQUE(case_id,cluster_id,asset_id)
);

COMMENT ON TABLE mt.cluster_member IS '簇成员整内容证据；本包待评审设计';

CREATE INDEX cluster_member_case_created ON mt.cluster_member(case_id,created_at);

CREATE TABLE mt.feedback_request (
    feedback_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    finding_id uuid NOT NULL,
    approval_id uuid NOT NULL,
    label_version text NOT NULL,
    label text NOT NULL,
    purpose text NOT NULL CHECK(purpose='training'),
    source_authorization_ref text NOT NULL,
    state text NOT NULL CHECK(state IN ('REQUESTED','APPROVED','REJECTED','REVOKED','APPLIED')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,feedback_id),
    FOREIGN KEY (case_id, finding_id) REFERENCES mt.risk_finding (case_id, finding_id),
    FOREIGN KEY (case_id, approval_id) REFERENCES mt.approval_request (case_id, approval_id)
);

COMMENT ON TABLE mt.feedback_request IS '纠错训练用途申请；本包待评审设计';

CREATE INDEX feedback_request_case_created ON mt.feedback_request(case_id,created_at);

CREATE TABLE mt.finding_evidence (
    link_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    risk_finding_id uuid ,
    tamper_finding_id uuid ,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,link_id),
    FOREIGN KEY (case_id, risk_finding_id) REFERENCES mt.risk_finding (case_id, finding_id),
    FOREIGN KEY (case_id, tamper_finding_id) REFERENCES mt.tamper_finding (case_id, tamper_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id),
    CHECK(num_nonnulls(risk_finding_id,tamper_finding_id)=1)
);

COMMENT ON TABLE mt.finding_evidence IS '发现与证据多对多；本包待评审设计';

CREATE INDEX finding_evidence_case_created ON mt.finding_evidence(case_id,created_at);

CREATE TABLE mt.package_item (
    package_item_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    package_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    object_id uuid NOT NULL,
    sha256 text NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,package_item_id),
    FOREIGN KEY (case_id, package_id) REFERENCES mt.evidence_package (case_id, package_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id),
    FOREIGN KEY (case_id, object_id) REFERENCES mt.object_version (case_id, object_id),
    UNIQUE(case_id,package_id,evidence_id)
);

COMMENT ON TABLE mt.package_item IS '固化包版本引用；本包待评审设计';

CREATE INDEX package_item_case_created ON mt.package_item(case_id,created_at);

CREATE TABLE mt.report_evidence (
    link_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    report_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,link_id),
    FOREIGN KEY (case_id, report_id) REFERENCES mt.report (case_id, report_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)
);

COMMENT ON TABLE mt.report_evidence IS '报告证据引用；本包待评审设计';

CREATE INDEX report_evidence_case_created ON mt.report_evidence(case_id,created_at);

CREATE TABLE mt.review_evidence (
    link_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    review_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,link_id),
    FOREIGN KEY (case_id, review_id) REFERENCES mt.review_record (case_id, review_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id)
);

COMMENT ON TABLE mt.review_evidence IS '复核证据引用；本包待评审设计';

CREATE INDEX review_evidence_case_created ON mt.review_evidence(case_id,created_at);

CREATE TABLE mt.task_evidence (
    link_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    task_id uuid NOT NULL,
    evidence_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,link_id),
    FOREIGN KEY (case_id, task_id) REFERENCES mt.analysis_task (case_id, task_id),
    FOREIGN KEY (case_id, evidence_id) REFERENCES mt.evidence_item (case_id, evidence_id),
    UNIQUE(case_id,task_id,evidence_id)
);

COMMENT ON TABLE mt.task_evidence IS '任务证据引用；本包待评审设计';

CREATE INDEX task_evidence_case_created ON mt.task_evidence(case_id,created_at);

CREATE TABLE mt.first_source_ranking (
    ranking_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    cluster_id uuid NOT NULL,
    task_id uuid NOT NULL,
    run_version bigint NOT NULL CHECK(run_version>0),
    result_version bigint NOT NULL CHECK(result_version>0),
    candidate_count integer NOT NULL CHECK(candidate_count BETWEEN 0 AND 3),
    model_version text NOT NULL,
    policy_version text NOT NULL,
    coverage_note text NOT NULL,
    status text NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,ranking_id),
    UNIQUE(case_id,ranking_id,cluster_id),
    UNIQUE(case_id,cluster_id,task_id,run_version,result_version),
    FOREIGN KEY(case_id,cluster_id) REFERENCES mt.content_cluster(case_id,cluster_id),
    FOREIGN KEY(case_id,task_id,run_version,result_version) REFERENCES mt.task_result(case_id,task_id,run_version,result_version),
    CHECK(candidate_count<>0 OR status='insufficient')
);

CREATE TABLE mt.first_source_candidate (
    candidate_id uuid PRIMARY KEY,
    org_id uuid NOT NULL,
    case_id uuid NOT NULL,
    cluster_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    rank integer NOT NULL CHECK(rank BETWEEN 1 AND 3),
    probability double precision CHECK(probability>=0 AND probability<=1),
    published_at timestamptz ,
    model_version text NOT NULL,
    evidence_refs jsonb NOT NULL,
    coverage_note text NOT NULL,
    status text NOT NULL CHECK(status IN ('candidate','insufficient','reviewed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
    created_by uuid ,
    FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
    UNIQUE(case_id,candidate_id),
    FOREIGN KEY (case_id, cluster_id) REFERENCES mt.content_cluster (case_id, cluster_id),
    FOREIGN KEY (case_id, asset_id) REFERENCES mt.media_asset (case_id, asset_id),
    ranking_id uuid NOT NULL,
    FOREIGN KEY(case_id,ranking_id,cluster_id) REFERENCES mt.first_source_ranking(case_id,ranking_id,cluster_id),
    FOREIGN KEY(case_id,cluster_id,asset_id) REFERENCES mt.cluster_member(case_id,cluster_id,asset_id),
    UNIQUE(case_id,ranking_id,rank),
    UNIQUE(case_id,ranking_id,asset_id)
);

COMMENT ON TABLE mt.first_source_candidate IS '首发候选及覆盖范围；本包待评审设计';

CREATE INDEX first_source_candidate_case_created ON mt.first_source_candidate(case_id,created_at);

CREATE FUNCTION mt.actor_id() RETURNS uuid LANGUAGE sql STABLE AS $$
SELECT NULLIF(current_setting('app.actor_id',true),'')::uuid
$$;
CREATE FUNCTION mt.org_id() RETURNS uuid LANGUAGE sql STABLE AS $$
SELECT NULLIF(current_setting('app.org_id',true),'')::uuid
$$;
CREATE FUNCTION mt.actor_in_org() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt AS $$
SELECT EXISTS(SELECT 1 FROM mt.users u WHERE u.user_id=mt.actor_id() AND u.org_id=mt.org_id() AND u.enabled)
$$;
CREATE FUNCTION mt.can_access_case(wanted uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt AS $$
 SELECT EXISTS(SELECT 1 FROM mt.case_membership m JOIN mt.users u ON u.user_id=m.user_id
WHERE m.case_id=wanted AND m.user_id=mt.actor_id() AND u.enabled
AND m.org_id=mt.org_id() AND u.org_id=m.org_id AND m.revoked_at IS NULL
AND (m.expires_at IS NULL OR m.expires_at>now()))
$$;
REVOKE ALL ON FUNCTION mt.can_access_case(uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION mt.actor_in_org() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.can_access_case(uuid),mt.actor_id(),mt.org_id(),mt.actor_in_org() TO mt_runtime;
CREATE FUNCTION mt.reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only table % rejects %',TG_TABLE_NAME,TG_OP USING ERRCODE='55000'; END $$;
CREATE FUNCTION mt.preserve_asset_original() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.object_id<>NEW.object_id OR OLD.sha256<>NEW.sha256 OR OLD.kind<>NEW.kind
 OR OLD.source_id<>NEW.source_id OR OLD.case_id<>NEW.case_id THEN
 RAISE EXCEPTION 'media provenance is immutable; append a derived asset' USING ERRCODE='55000';
 END IF; RETURN NEW;
END $$;
CREATE TRIGGER media_provenance BEFORE UPDATE ON mt.media_asset FOR EACH ROW EXECUTE FUNCTION mt.preserve_asset_original();
CREATE FUNCTION mt.validate_seal() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,mt AS $$
DECLARE a mt.approval_request; t mt.analysis_task;
BEGIN
 SELECT * INTO a FROM mt.approval_request WHERE case_id=NEW.case_id AND approval_id=NEW.approval_id;
 IF NOT FOUND OR a.state<>'APPROVED' OR a.purpose<>'seal'
 OR a.object_type<>'task' OR a.object_id<>NEW.task_id
 OR a.run_version IS DISTINCT FROM NEW.run_version OR a.result_version IS DISTINCT FROM NEW.result_version
 OR (a.expires_at IS NOT NULL AND a.expires_at<=now()) THEN
 RAISE EXCEPTION 'seal approval missing stale or unauthorized purpose' USING ERRCODE='23514';
 END IF;
 SELECT * INTO t FROM mt.analysis_task WHERE task_id=NEW.task_id AND case_id=NEW.case_id;
 IF NOT FOUND OR t.row_version<>a.object_version OR t.run_version<>NEW.run_version
 OR t.result_version<>NEW.result_version THEN
 RAISE EXCEPTION 'seal snapshot no longer current' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER package_approval BEFORE INSERT ON mt.evidence_package FOR EACH ROW EXECUTE FUNCTION mt.validate_seal();
CREATE FUNCTION mt.prevent_token_reuse() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.consumed_at IS NOT NULL THEN RAISE EXCEPTION 'token already consumed' USING ERRCODE='55000'; END IF;
 IF OLD.case_id IS DISTINCT FROM NEW.case_id OR OLD.org_id<>NEW.org_id
 OR OLD.token_sha256<>NEW.token_sha256 OR OLD.actor_id<>NEW.actor_id OR OLD.object_id<>NEW.object_id
 OR OLD.object_version<>NEW.object_version OR OLD.purpose<>NEW.purpose OR OLD.approval_id<>NEW.approval_id
 OR OLD.expires_at<>NEW.expires_at THEN RAISE EXCEPTION 'token binding is immutable' USING ERRCODE='55000'; END IF;
 IF NEW.consumed_at IS NOT NULL AND OLD.expires_at<=now() THEN RAISE EXCEPTION 'token expired' USING ERRCODE='23514'; END IF;
 RETURN NEW; END $$;
CREATE TRIGGER token_use BEFORE UPDATE ON mt.operation_token FOR EACH ROW EXECUTE FUNCTION mt.prevent_token_reuse();


GRANT SELECT ON mt.organizations TO mt_runtime;

ALTER TABLE mt.organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY directory_scope ON mt.organizations TO mt_runtime USING(org_id=mt.org_id());

GRANT SELECT ON mt.users TO mt_runtime;

ALTER TABLE mt.users ENABLE ROW LEVEL SECURITY;

CREATE POLICY directory_scope ON mt.users TO mt_runtime USING(org_id=mt.org_id());

GRANT SELECT ON mt.roles TO mt_runtime;

GRANT SELECT ON mt.permissions TO mt_runtime;

GRANT SELECT ON mt.user_roles TO mt_runtime;

ALTER TABLE mt.user_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY directory_scope ON mt.user_roles TO mt_runtime USING(user_id=mt.actor_id());

GRANT SELECT ON mt.role_permissions TO mt_runtime;

ALTER TABLE mt.cases ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.cases FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.cases TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.cases TO mt_runtime;

GRANT SELECT ON mt.case_membership TO mt_runtime;

ALTER TABLE mt.case_membership ENABLE ROW LEVEL SECURITY;

CREATE POLICY directory_scope ON mt.case_membership TO mt_runtime USING(user_id=mt.actor_id());

ALTER TABLE mt.source_registry ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.source_registry FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.source_registry TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.source_registry TO mt_runtime;

ALTER TABLE mt.content_item ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.content_item FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.content_item TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.content_item TO mt_runtime;

ALTER TABLE mt.object_version ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.object_version FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.object_version TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.object_version TO mt_runtime;

CREATE TRIGGER object_version_append_only BEFORE UPDATE OR DELETE ON mt.object_version FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER object_version_no_truncate BEFORE TRUNCATE ON mt.object_version FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.media_asset ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.media_asset FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.media_asset TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.media_asset TO mt_runtime;

ALTER TABLE mt.asset_lineage ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.asset_lineage FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.asset_lineage TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.asset_lineage TO mt_runtime;

CREATE TRIGGER asset_lineage_append_only BEFORE UPDATE OR DELETE ON mt.asset_lineage FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER asset_lineage_no_truncate BEFORE TRUNCATE ON mt.asset_lineage FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.upload_session ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.upload_session FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.upload_session TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.upload_session TO mt_runtime;

ALTER TABLE mt.upload_part ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.upload_part FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.upload_part TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.upload_part TO mt_runtime;

ALTER TABLE mt.import_job ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.import_job FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.import_job TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.import_job TO mt_runtime;

ALTER TABLE mt.import_item ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.import_item FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.import_item TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.import_item TO mt_runtime;

ALTER TABLE mt.idempotency_record ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.idempotency_record FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.idempotency_record TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.idempotency_record TO mt_runtime;

ALTER TABLE mt.policy_registry ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.policy_registry FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.policy_registry TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org()) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org());

GRANT SELECT,INSERT,UPDATE ON mt.policy_registry TO mt_runtime;

ALTER TABLE mt.analysis_task ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.analysis_task FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.analysis_task TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.analysis_task TO mt_runtime;

ALTER TABLE mt.task_run ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.task_run FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.task_run TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.task_run TO mt_runtime;

CREATE TRIGGER task_run_append_only BEFORE UPDATE OR DELETE ON mt.task_run FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER task_run_no_truncate BEFORE TRUNCATE ON mt.task_run FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.task_result ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.task_result FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.task_result TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.task_result TO mt_runtime;

CREATE TRIGGER task_result_append_only BEFORE UPDATE OR DELETE ON mt.task_result FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER task_result_no_truncate BEFORE TRUNCATE ON mt.task_result FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.task_node_run ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.task_node_run FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.task_node_run TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.task_node_run TO mt_runtime;

ALTER TABLE mt.task_event ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.task_event FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.task_event TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.task_event TO mt_runtime;

CREATE TRIGGER task_event_append_only BEFORE UPDATE OR DELETE ON mt.task_event FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER task_event_no_truncate BEFORE TRUNCATE ON mt.task_event FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.outbox_event ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.outbox_event FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.outbox_event TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.outbox_event TO mt_runtime;

ALTER TABLE mt.event_receipt ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.event_receipt FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.event_receipt TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.event_receipt TO mt_runtime;

CREATE TRIGGER event_receipt_append_only BEFORE UPDATE OR DELETE ON mt.event_receipt FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER event_receipt_no_truncate BEFORE TRUNCATE ON mt.event_receipt FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.shot ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.shot FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.shot TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.shot TO mt_runtime;

CREATE TRIGGER shot_append_only BEFORE UPDATE OR DELETE ON mt.shot FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER shot_no_truncate BEFORE TRUNCATE ON mt.shot FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.keyframe ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.keyframe FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.keyframe TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.keyframe TO mt_runtime;

CREATE TRIGGER keyframe_append_only BEFORE UPDATE OR DELETE ON mt.keyframe FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER keyframe_no_truncate BEFORE TRUNCATE ON mt.keyframe FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.text_segment ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.text_segment FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.text_segment TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.text_segment TO mt_runtime;

CREATE TRIGGER text_segment_append_only BEFORE UPDATE OR DELETE ON mt.text_segment FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER text_segment_no_truncate BEFORE TRUNCATE ON mt.text_segment FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.model_registry ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.model_registry FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.model_registry TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org()) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org());

GRANT SELECT,INSERT,UPDATE ON mt.model_registry TO mt_runtime;

ALTER TABLE mt.model_evaluation ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.model_evaluation FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.model_evaluation TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org()) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org());

GRANT SELECT,INSERT ON mt.model_evaluation TO mt_runtime;

CREATE TRIGGER model_evaluation_append_only BEFORE UPDATE OR DELETE ON mt.model_evaluation FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER model_evaluation_no_truncate BEFORE TRUNCATE ON mt.model_evaluation FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.model_release ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.model_release FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.model_release TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org()) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org());

GRANT SELECT,INSERT,UPDATE ON mt.model_release TO mt_runtime;

ALTER TABLE mt.index_registry ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.index_registry FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.index_registry TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org()) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org());

GRANT SELECT,INSERT,UPDATE ON mt.index_registry TO mt_runtime;

ALTER TABLE mt.feature ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.feature FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.feature TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.feature TO mt_runtime;

CREATE TRIGGER feature_append_only BEFORE UPDATE OR DELETE ON mt.feature FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER feature_no_truncate BEFORE TRUNCATE ON mt.feature FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.evidence_item ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.evidence_item FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.evidence_item TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.evidence_item TO mt_runtime;

CREATE TRIGGER evidence_item_append_only BEFORE UPDATE OR DELETE ON mt.evidence_item FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER evidence_item_no_truncate BEFORE TRUNCATE ON mt.evidence_item FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.risk_finding ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.risk_finding FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.risk_finding TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.risk_finding TO mt_runtime;

CREATE TRIGGER risk_finding_append_only BEFORE UPDATE OR DELETE ON mt.risk_finding FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER risk_finding_no_truncate BEFORE TRUNCATE ON mt.risk_finding FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.tamper_finding ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.tamper_finding FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.tamper_finding TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.tamper_finding TO mt_runtime;

CREATE TRIGGER tamper_finding_append_only BEFORE UPDATE OR DELETE ON mt.tamper_finding FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER tamper_finding_no_truncate BEFORE TRUNCATE ON mt.tamper_finding FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.finding_evidence ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.finding_evidence FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.finding_evidence TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.finding_evidence TO mt_runtime;

CREATE TRIGGER finding_evidence_append_only BEFORE UPDATE OR DELETE ON mt.finding_evidence FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER finding_evidence_no_truncate BEFORE TRUNCATE ON mt.finding_evidence FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.task_evidence ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.task_evidence FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.task_evidence TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.task_evidence TO mt_runtime;

CREATE TRIGGER task_evidence_append_only BEFORE UPDATE OR DELETE ON mt.task_evidence FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER task_evidence_no_truncate BEFORE TRUNCATE ON mt.task_evidence FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.search_job ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.search_job FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.search_job TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.search_job TO mt_runtime;

ALTER TABLE mt.source_match ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.source_match FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.source_match TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.source_match TO mt_runtime;

CREATE TRIGGER source_match_append_only BEFORE UPDATE OR DELETE ON mt.source_match FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER source_match_no_truncate BEFORE TRUNCATE ON mt.source_match FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.content_cluster ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.content_cluster FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.content_cluster TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.content_cluster TO mt_runtime;

ALTER TABLE mt.cluster_member ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.cluster_member FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.cluster_member TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.cluster_member TO mt_runtime;

CREATE TRIGGER cluster_member_append_only BEFORE UPDATE OR DELETE ON mt.cluster_member FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER cluster_member_no_truncate BEFORE TRUNCATE ON mt.cluster_member FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.first_source_candidate ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.first_source_candidate FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.first_source_candidate TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.first_source_candidate TO mt_runtime;

CREATE TRIGGER first_source_candidate_append_only BEFORE UPDATE OR DELETE ON mt.first_source_candidate FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER first_source_candidate_no_truncate BEFORE TRUNCATE ON mt.first_source_candidate FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.propagation_node ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.propagation_node FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.propagation_node TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.propagation_node TO mt_runtime;

ALTER TABLE mt.propagation_edge ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.propagation_edge FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.propagation_edge TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.propagation_edge TO mt_runtime;

ALTER TABLE mt.claim ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.claim FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.claim TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.claim TO mt_runtime;

CREATE TRIGGER claim_append_only BEFORE UPDATE OR DELETE ON mt.claim FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER claim_no_truncate BEFORE TRUNCATE ON mt.claim FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.claim_evidence_relation ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.claim_evidence_relation FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.claim_evidence_relation TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.claim_evidence_relation TO mt_runtime;

CREATE TRIGGER claim_evidence_relation_append_only BEFORE UPDATE OR DELETE ON mt.claim_evidence_relation FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER claim_evidence_relation_no_truncate BEFORE TRUNCATE ON mt.claim_evidence_relation FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.approval_request ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.approval_request FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.approval_request TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id))) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id)));

GRANT SELECT,INSERT,UPDATE ON mt.approval_request TO mt_runtime;

ALTER TABLE mt.approval_decision ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.approval_decision FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.approval_decision TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id))) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id)));

GRANT SELECT,INSERT ON mt.approval_decision TO mt_runtime;

CREATE TRIGGER approval_decision_append_only BEFORE UPDATE OR DELETE ON mt.approval_decision FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER approval_decision_no_truncate BEFORE TRUNCATE ON mt.approval_decision FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.operation_token ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.operation_token FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.operation_token TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id))) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id)));

GRANT SELECT,INSERT,UPDATE ON mt.operation_token TO mt_runtime;

ALTER TABLE mt.review_record ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.review_record FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.review_record TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.review_record TO mt_runtime;

CREATE TRIGGER review_record_append_only BEFORE UPDATE OR DELETE ON mt.review_record FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER review_record_no_truncate BEFORE TRUNCATE ON mt.review_record FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.review_evidence ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.review_evidence FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.review_evidence TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.review_evidence TO mt_runtime;

CREATE TRIGGER review_evidence_append_only BEFORE UPDATE OR DELETE ON mt.review_evidence FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER review_evidence_no_truncate BEFORE TRUNCATE ON mt.review_evidence FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.evidence_package ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.evidence_package FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.evidence_package TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.evidence_package TO mt_runtime;

CREATE TRIGGER evidence_package_append_only BEFORE UPDATE OR DELETE ON mt.evidence_package FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER evidence_package_no_truncate BEFORE TRUNCATE ON mt.evidence_package FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.package_item ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.package_item FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.package_item TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.package_item TO mt_runtime;

CREATE TRIGGER package_item_append_only BEFORE UPDATE OR DELETE ON mt.package_item FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER package_item_no_truncate BEFORE TRUNCATE ON mt.package_item FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.report ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.report FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.report TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.report TO mt_runtime;

ALTER TABLE mt.report_evidence ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.report_evidence FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.report_evidence TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT ON mt.report_evidence TO mt_runtime;

CREATE TRIGGER report_evidence_append_only BEFORE UPDATE OR DELETE ON mt.report_evidence FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER report_evidence_no_truncate BEFORE TRUNCATE ON mt.report_evidence FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.feedback_request ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.feedback_request FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.feedback_request TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.feedback_request TO mt_runtime;

ALTER TABLE mt.dataset_version ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.dataset_version FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.dataset_version TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org()) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org());

GRANT SELECT,INSERT ON mt.dataset_version TO mt_runtime;

CREATE TRIGGER dataset_version_append_only BEFORE UPDATE OR DELETE ON mt.dataset_version FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER dataset_version_no_truncate BEFORE TRUNCATE ON mt.dataset_version FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.audit_event ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.audit_event FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.audit_event TO mt_runtime USING(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id))) WITH CHECK(org_id=mt.org_id() AND mt.actor_in_org() AND (case_id IS NULL OR mt.can_access_case(case_id)));

GRANT SELECT,INSERT ON mt.audit_event TO mt_runtime;

CREATE TRIGGER audit_event_append_only BEFORE UPDATE OR DELETE ON mt.audit_event FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();

CREATE TRIGGER audit_event_no_truncate BEFORE TRUNCATE ON mt.audit_event FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

ALTER TABLE mt.audit_export ENABLE ROW LEVEL SECURITY;

ALTER TABLE mt.audit_export FORCE ROW LEVEL SECURITY;

CREATE POLICY scope_policy ON mt.audit_export TO mt_runtime USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));

GRANT SELECT,INSERT,UPDATE ON mt.audit_export TO mt_runtime;

CREATE INDEX media_hash_scope ON mt.media_asset(case_id,sha256);

CREATE INDEX outbox_unpublished ON mt.outbox_event(created_at) WHERE published_at IS NULL;

CREATE INDEX task_queue_ready ON mt.analysis_task(priority,created_at) WHERE state='QUEUED';


-- DB-RANK-001: immutable ranking snapshot; header and all items in one transaction.
ALTER TABLE mt.first_source_ranking ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt.first_source_ranking FORCE ROW LEVEL SECURITY;
CREATE POLICY scope_policy ON mt.first_source_ranking TO mt_runtime
USING(mt.can_access_case(case_id)) WITH CHECK(mt.can_access_case(case_id));
GRANT SELECT, INSERT ON mt.first_source_ranking TO mt_runtime;
CREATE TRIGGER first_source_ranking_append_only BEFORE UPDATE OR DELETE
ON mt.first_source_ranking FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation();
CREATE TRIGGER first_source_ranking_no_truncate BEFORE TRUNCATE
ON mt.first_source_ranking FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();
CREATE INDEX first_source_ranking_latest ON mt.first_source_ranking
(case_id,cluster_id,created_at DESC,ranking_id DESC);

CREATE OR REPLACE FUNCTION mt.check_first_source_item() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, mt AS $$
DECLARE h mt.first_source_ranking%ROWTYPE;
        key_name text; refs jsonb; item jsonb; ref_id uuid; seen uuid[];
BEGIN
 SELECT * INTO h FROM mt.first_source_ranking
 WHERE case_id=NEW.case_id AND ranking_id=NEW.ranking_id;
 IF NOT FOUND THEN
   RAISE EXCEPTION 'ranking snapshot absent or inaccessible' USING ERRCODE='23503';
 END IF;
 IF NEW.cluster_id IS DISTINCT FROM h.cluster_id
    OR NEW.org_id IS DISTINCT FROM h.org_id
    OR NEW.model_version IS DISTINCT FROM h.model_version
    OR NEW.status IS DISTINCT FROM h.status
    OR NEW.coverage_note IS DISTINCT FROM h.coverage_note
    OR NEW.rank>h.candidate_count THEN
   RAISE EXCEPTION 'candidate differs from ranking snapshot' USING ERRCODE='23514';
 END IF;

 -- JSON extraction can return SQL NULL: use explicit type/null checks.
 IF jsonb_typeof(NEW.evidence_refs) IS DISTINCT FROM 'object'
    OR (NEW.evidence_refs - ARRAY['evidence_ids','counter_evidence_ids']) <> '{}'::jsonb THEN
   RAISE EXCEPTION 'evidence_refs must be the declared object' USING ERRCODE='23514';
 END IF;
 FOREACH key_name IN ARRAY ARRAY['evidence_ids','counter_evidence_ids'] LOOP
   refs := NEW.evidence_refs->key_name;
   IF jsonb_typeof(refs) IS DISTINCT FROM 'array' THEN
     RAISE EXCEPTION 'missing or non-array evidence list' USING ERRCODE='23514';
   END IF;
   IF key_name='evidence_ids' AND jsonb_array_length(refs)=0 THEN
     RAISE EXCEPTION 'candidate requires supporting evidence' USING ERRCODE='23514';
   END IF;
   seen := ARRAY[]::uuid[];
   FOR item IN SELECT value FROM jsonb_array_elements(refs) LOOP
     IF jsonb_typeof(item) IS DISTINCT FROM 'string' THEN
       RAISE EXCEPTION 'evidence ID must be a UUID string' USING ERRCODE='23514';
     END IF;
     IF (item #>> '{}') !~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
       RAISE EXCEPTION 'evidence UUID must use canonical hyphenated form' USING ERRCODE='23514';
     END IF;
     BEGIN ref_id := (item #>> '{}')::uuid;
     EXCEPTION WHEN invalid_text_representation THEN
       RAISE EXCEPTION 'invalid evidence UUID' USING ERRCODE='23514';
     END;
     IF array_position(seen,ref_id) IS NOT NULL THEN
       RAISE EXCEPTION 'duplicate evidence within list' USING ERRCODE='23514';
     END IF;
     seen := array_append(seen,ref_id);
     IF NOT EXISTS(SELECT 1 FROM mt.evidence_item
                   WHERE case_id=NEW.case_id AND evidence_id=ref_id) THEN
       RAISE EXCEPTION 'evidence absent or outside accessible case' USING ERRCODE='23503';
     END IF;
   END LOOP;
 END LOOP;
 RETURN NEW;
END $$;
CREATE TRIGGER first_source_item_snapshot BEFORE INSERT ON mt.first_source_candidate
FOR EACH ROW EXECUTE FUNCTION mt.check_first_source_item();

CREATE OR REPLACE FUNCTION mt.check_first_source_complete() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, mt AS $$
DECLARE expected integer; actual integer; lo integer; hi integer;
BEGIN
 SELECT candidate_count INTO expected FROM mt.first_source_ranking
 WHERE case_id=NEW.case_id AND ranking_id=NEW.ranking_id;
 IF NOT FOUND THEN
   RAISE EXCEPTION 'ranking snapshot absent or inaccessible' USING ERRCODE='23503';
 END IF;
 SELECT count(*),min(rank),max(rank) INTO actual,lo,hi FROM mt.first_source_candidate
 WHERE case_id=NEW.case_id AND ranking_id=NEW.ranking_id;
 IF actual<>expected OR (actual>0 AND (lo<>1 OR hi<>expected)) THEN
   RAISE EXCEPTION 'ranking must contain exactly ranks 1 through candidate_count'
   USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER first_source_header_complete AFTER INSERT
ON mt.first_source_ranking DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION mt.check_first_source_complete();
CREATE CONSTRAINT TRIGGER first_source_items_complete AFTER INSERT
ON mt.first_source_candidate DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION mt.check_first_source_complete();

COMMENT ON TABLE mt.first_source_ranking IS '首发排序不可变结果快照；0.2-review候选';
COMMENT ON COLUMN mt.organizations.org_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.organizations.name IS '名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键';
COMMENT ON COLUMN mt.organizations.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.organizations.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.organizations.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.organizations.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.users.user_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.users.org_id IS '记录所属单位标识；单位授权范围由服务端认证上下文确定';
COMMENT ON COLUMN mt.users.subject IS '来自批准身份源，开发适配器另存密码散列，不设默认密码';
COMMENT ON COLUMN mt.users.enabled IS '认证主体是否启用；false禁止建立有效业务身份，true仍需核验角色与案件授权';
COMMENT ON COLUMN mt.users.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.users.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.users.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.users.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.roles.role_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.roles.code IS '稳定业务编码，供权限检查或角色绑定使用；显示名称变化不应改变该编码';
COMMENT ON COLUMN mt.roles.description IS '该目录条目的中文职责或权限说明，不用于替代机器权限编码';
COMMENT ON COLUMN mt.roles.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.roles.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.roles.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.roles.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.permissions.permission_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.permissions.code IS '稳定业务编码，供权限检查或角色绑定使用；显示名称变化不应改变该编码';
COMMENT ON COLUMN mt.permissions.description IS '该目录条目的中文职责或权限说明，不用于替代机器权限编码';
COMMENT ON COLUMN mt.permissions.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.permissions.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.permissions.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.permissions.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.user_roles.user_role_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.user_roles.user_id IS '用户与认证主体标识，指向users.user_id';
COMMENT ON COLUMN mt.user_roles.role_id IS '角色标识，指向roles.role_id';
COMMENT ON COLUMN mt.user_roles.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.user_roles.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.user_roles.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.user_roles.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.user_roles.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.role_permissions.role_permission_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.role_permissions.role_id IS '角色标识，指向roles.role_id';
COMMENT ON COLUMN mt.role_permissions.permission_id IS '功能权限标识，指向permissions.permission_id';
COMMENT ON COLUMN mt.role_permissions.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.role_permissions.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.role_permissions.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.role_permissions.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.cases.case_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.cases.org_id IS '记录所属单位标识；单位授权范围由服务端认证上下文确定';
COMMENT ON COLUMN mt.cases.display_code IS '同单位内展示和检索案件使用的业务编号，不是数据库主键';
COMMENT ON COLUMN mt.cases.status IS '案件隔离域的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.cases.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.cases.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.cases.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.cases.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.case_membership.membership_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.case_membership.case_id IS '案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限';
COMMENT ON COLUMN mt.case_membership.org_id IS '记录所属单位标识；单位授权范围由服务端认证上下文确定';
COMMENT ON COLUMN mt.case_membership.user_id IS '用户与认证主体标识，指向users.user_id';
COMMENT ON COLUMN mt.case_membership.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.case_membership.revoked_at IS '授权被撤销的时刻；为空表示尚未登记撤销，不替代到期与成员身份校验；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.case_membership.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.case_membership.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.case_membership.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.case_membership.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.source_registry.source_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.source_registry.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.source_registry.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.source_registry.name IS '名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键';
COMMENT ON COLUMN mt.source_registry.source_type IS '素材来源类别的编码；分类词表由接入配置定义，当前DDL未枚举限制';
COMMENT ON COLUMN mt.source_registry.authorization_ref IS '来源授权凭据的受控引用，供核查用途和期限；不存访问令牌或明文密钥';
COMMENT ON COLUMN mt.source_registry.purpose IS '本记录声明或申请的处理用途，实际动作需与有效授权用途相符';
COMMENT ON COLUMN mt.source_registry.authorization_status IS '来源或数据集用途授权的当前审核状态，未验证状态不得解释为可正式使用';
COMMENT ON COLUMN mt.source_registry.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.source_registry.authorization_version IS '本次处理采用的来源授权版本，用于撤销核查及历史追溯';
COMMENT ON COLUMN mt.source_registry.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.source_registry.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.source_registry.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.source_registry.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.content_item.content_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.content_item.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.content_item.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.content_item.source_id IS '数据来源登记标识，指向source_registry.source_id';
COMMENT ON COLUMN mt.content_item.platform IS '原始内容发布平台的标识或名称；缺失时为空，不推断平台';
COMMENT ON COLUMN mt.content_item.account_id IS '来源平台内的账号标识；属于平台命名空间，不是本系统users主键';
COMMENT ON COLUMN mt.content_item.published_at IS '可核查的来源发布时间；未知为NULL，不用发现时间或当前时间填补；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.content_item.discovered_at IS '系统首次发现该逻辑内容的时刻，与平台发布时间分开记录；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.content_item.title IS '来源内容标题；未知时为空，不强制生成标题代替原文';
COMMENT ON COLUMN mt.content_item.status IS '逻辑内容对象的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.content_item.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.content_item.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.content_item.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.content_item.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.object_version.object_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.object_version.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.object_version.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.object_version.bucket_alias IS '配置别名，不是云账号或外部地址';
COMMENT ON COLUMN mt.object_version.object_key IS '对象存储内部键，与bucket_alias和version_id共同定位字节版本；不直接作为公开下载地址';
COMMENT ON COLUMN mt.object_version.version_id IS '对象存储返回的版本标识；绑定确定字节版本，不等同数据库row_version';
COMMENT ON COLUMN mt.object_version.sha256 IS '该对象版本实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.object_version.size_bytes IS '文件或分片的字节长度，单位byte；有效值必须大于0';
COMMENT ON COLUMN mt.object_version.retention_policy_version IS '用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效';
COMMENT ON COLUMN mt.object_version.retain_until IS '对象计划保留截止时刻；NULL表示未登记具体截止时间，不能自动推导可删除；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.object_version.legal_hold IS '对象是否登记暂停删除要求；底层存储的实际执行结果需独立核验';
COMMENT ON COLUMN mt.object_version.object_lock_verified IS '是否已核验对象存储的锁定能力和该对象版本的锁定状态；不是普通文件只读标志';
COMMENT ON COLUMN mt.object_version.created_at IS '对象版本登记入库时刻；TIMESTAMPTZ保存时间点，显示时区由会话决定，不保留原始时区名称';
COMMENT ON COLUMN mt.object_version.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.object_version.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.object_version.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.media_asset.asset_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.media_asset.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.media_asset.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.media_asset.content_id IS '所属逻辑内容标识，指向content_item.content_id';
COMMENT ON COLUMN mt.media_asset.source_id IS '数据来源登记标识，指向source_registry.source_id';
COMMENT ON COLUMN mt.media_asset.object_id IS '所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用';
COMMENT ON COLUMN mt.media_asset.sha256 IS '媒体资产字节的SHA-256，应与引用对象版本核对；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.media_asset.mime IS '探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名';
COMMENT ON COLUMN mt.media_asset.size_bytes IS '文件或分片的字节长度，单位byte；有效值必须大于0';
COMMENT ON COLUMN mt.media_asset.duration_ms IS '媒体时长，单位毫秒；静态图像或未知时长允许NULL，0不能替代未知';
COMMENT ON COLUMN mt.media_asset.width IS '媒体帧或图像宽度，单位像素；有值时为正整数';
COMMENT ON COLUMN mt.media_asset.height IS '媒体帧或图像高度，单位像素；有值时为正整数';
COMMENT ON COLUMN mt.media_asset.kind IS '媒体身份：original为原始输入，derived为派生副本';
COMMENT ON COLUMN mt.media_asset.parent_asset_id IS '父媒体资产标识；原件可空，多父派生关系同时登记asset_lineage';
COMMENT ON COLUMN mt.media_asset.mapping_version IS '派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本';
COMMENT ON COLUMN mt.media_asset.state IS '原始或派生媒体的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.media_asset.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.media_asset.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.media_asset.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.media_asset.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.asset_lineage.lineage_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.asset_lineage.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.asset_lineage.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.asset_lineage.parent_asset_id IS '父媒体资产标识；原件可空，多父派生关系同时登记asset_lineage';
COMMENT ON COLUMN mt.asset_lineage.child_asset_id IS '派生得到的子媒体资产标识；不能与本行父资产相同';
COMMENT ON COLUMN mt.asset_lineage.operation IS '由父媒体生成子媒体的处理操作编码，与参数、代码摘要和映射版本一起重现派生过程';
COMMENT ON COLUMN mt.asset_lineage.parameters IS '媒体派生操作参数对象，例如抽帧策略和编码设置；值须按操作对应Schema校验并排除秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.asset_lineage.code_digest IS '执行派生处理代码或发布包的SHA-256，摘要范围由发布规范固定；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.asset_lineage.mapping_version IS '派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本';
COMMENT ON COLUMN mt.asset_lineage.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.asset_lineage.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.asset_lineage.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.asset_lineage.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.upload_session.upload_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.upload_session.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.upload_session.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.upload_session.source_id IS '数据来源登记标识，指向source_registry.source_id';
COMMENT ON COLUMN mt.upload_session.filename IS '上传时提供的展示文件名；不得直接拼接为服务器文件路径';
COMMENT ON COLUMN mt.upload_session.size_bytes IS '文件或分片的字节长度，单位byte；有效值必须大于0';
COMMENT ON COLUMN mt.upload_session.sha256 IS '上传方声明的完整文件SHA-256，合并后必须以实际字节重新计算核对；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.upload_session.mime IS '探测或声明的媒体类型字符串，例如image/png；服务端须核对实际内容，不能只信文件扩展名';
COMMENT ON COLUMN mt.upload_session.part_size_bytes IS '上传会话约定的标准分片大小，单位字节；末片可小于此值';
COMMENT ON COLUMN mt.upload_session.state IS '上传会话的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.upload_session.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.upload_session.owner_id IS '创建并持有上传会话的用户标识；不能直接接受客户端冒充';
COMMENT ON COLUMN mt.upload_session.duplicate_of IS '同案件重复资产引用；仅在完整摘要/媒体校验成功后登记，读取仍核验当前案件权限；NULL表示未确定重复。';
COMMENT ON COLUMN mt.upload_session.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.upload_session.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.upload_session.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.upload_session.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.upload_session.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.upload_part.part_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.upload_part.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.upload_part.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.upload_part.upload_id IS '所属上传会话标识，指向upload_session.upload_id';
COMMENT ON COLUMN mt.upload_part.part_no IS '上传分片编号，从1开始；同一会话内不得重复';
COMMENT ON COLUMN mt.upload_part.sha256 IS '该分片实际字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.upload_part.size_bytes IS '文件或分片的字节长度，单位byte；有效值必须大于0';
COMMENT ON COLUMN mt.upload_part.object_id IS '所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用';
COMMENT ON COLUMN mt.upload_part.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.upload_part.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.upload_part.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.upload_part.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.import_job.import_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.import_job.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.import_job.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.import_job.state IS '批量清单导入作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.import_job.requested_count IS '导入作业申请处理的条目总数，必须大于0；不等于成功导入数量';
COMMENT ON COLUMN mt.import_job.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.import_job.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.import_job.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.import_job.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.import_item.item_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.import_item.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.import_item.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.import_item.import_id IS '所属批量导入作业标识，指向import_job.import_id';
COMMENT ON COLUMN mt.import_item.ordinal IS '导入清单内的条目位置，从0开始；同一导入作业内唯一';
COMMENT ON COLUMN mt.import_item.source_id IS '数据来源登记标识，指向source_registry.source_id';
COMMENT ON COLUMN mt.import_item.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.import_item.state IS '逐条导入结果的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.import_item.error_code IS '失败原因的稳定错误码；无失败时允许NULL，用户说明与诊断堆栈分开';
COMMENT ON COLUMN mt.import_item.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.import_item.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.import_item.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.import_item.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.idempotency_record.idempotency_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.idempotency_record.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.idempotency_record.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.idempotency_record.actor_id IS '操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则';
COMMENT ON COLUMN mt.idempotency_record.operation IS '执行操作的稳定名称；用于审计、幂等分域或重现派生步骤，具体取值由对应模块登记';
COMMENT ON COLUMN mt.idempotency_record.idempotency_key IS '客户端提交的幂等键；与案件、主体和操作共同分域，同键请求摘要不同应报冲突';
COMMENT ON COLUMN mt.idempotency_record.request_sha256 IS '规范化请求内容的SHA-256，规范化规则由操作契约固定；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.idempotency_record.response_ref IS '首次成功处理的响应或结果引用对象，用于幂等重放；不缓存越权敏感内容。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.idempotency_record.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.idempotency_record.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.idempotency_record.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.idempotency_record.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.idempotency_record.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.policy_registry.policy_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.policy_registry.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.policy_registry.kind IS '策略类别，如标签、阈值、流程或保留规则；类别词表由配置登记';
COMMENT ON COLUMN mt.policy_registry.version IS '此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version';
COMMENT ON COLUMN mt.policy_registry.definition_ref IS '完整策略定义文档或配置的受控引用，应可定位不可变版本';
COMMENT ON COLUMN mt.policy_registry.status IS '标签阈值流程保留等策略的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.policy_registry.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.policy_registry.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.policy_registry.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.policy_registry.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.policy_registry.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.analysis_task.task_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.analysis_task.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.analysis_task.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.analysis_task.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.analysis_task.scene IS '分析场景编码，用于选择任务处理流程；实际场景词表仍依业务配置';
COMMENT ON COLUMN mt.analysis_task.priority IS '调度优先级；只影响排队策略，不改变权限或审核要求';
COMMENT ON COLUMN mt.analysis_task.state IS '分析任务当前投影的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.analysis_task.progress IS '当前运行版本的进度比例，0到1；不是准确率或任务正式通过率';
COMMENT ON COLUMN mt.analysis_task.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.analysis_task.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.analysis_task.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.analysis_task.modules IS '任务请求运行的模块编码列表；服务端检查模块是否允许、依赖是否满足';
COMMENT ON COLUMN mt.analysis_task.missing_modalities IS '输入缺失的模态列表，例如无音轨；空数组表示未登记缺失，不等于全部分析成功';
COMMENT ON COLUMN mt.analysis_task.report_eligibility IS '当前结果允许的报告使用等级；正式报告仍需核验审批和结果版本';
COMMENT ON COLUMN mt.analysis_task.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.analysis_task.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.analysis_task.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.analysis_task.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.task_run.task_run_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.task_run.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.task_run.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.task_run.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.task_run.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.task_run.input_sha256 IS '本次运行输入清单或输入对象的SHA-256，摘要对象须由DAG契约固定；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.task_run.dag_version IS '本次运行采用的任务依赖图版本，用于重现节点和执行顺序';
COMMENT ON COLUMN mt.task_run.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.task_run.fencing_epoch IS '防止旧worker写回的栅栏代数；服务层必须比较最新代数，正整数CHECK本身不阻止旧worker';
COMMENT ON COLUMN mt.task_run.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.task_run.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_run.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.task_run.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.task_result.result_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.task_result.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.task_result.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.task_result.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.task_result.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.task_result.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.task_result.sha256 IS '结果快照规范化表示的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.task_result.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.task_result.summary IS '结果快照的结构化摘要对象；不能作为证据事实表的替代。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.task_result.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.task_result.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_result.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.task_result.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.task_node_run.run_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.task_node_run.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.task_node_run.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.task_node_run.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.task_node_run.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.task_node_run.node_code IS '任务依赖图中的节点编码，在对应dag_version内解析';
COMMENT ON COLUMN mt.task_node_run.attempt IS '同一任务运行节点的尝试次数，从1开始，重试递增';
COMMENT ON COLUMN mt.task_node_run.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.task_node_run.input_hash IS '节点输入规范化清单的SHA-256，用于重试与缓存一致性；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.task_node_run.state IS '节点尝试与租约的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.task_node_run.required IS '该节点是否为本次DAG完成所必需；必需节点缺失不能直接当任务成功';
COMMENT ON COLUMN mt.task_node_run.reason IS '状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密';
COMMENT ON COLUMN mt.task_node_run.lease_token IS 'worker领取节点时获得的租约标识；写回须同时核验租约和fencing_epoch';
COMMENT ON COLUMN mt.task_node_run.fencing_epoch IS '防止旧worker写回的栅栏代数；服务层必须比较最新代数，正整数CHECK本身不阻止旧worker';
COMMENT ON COLUMN mt.task_node_run.started_at IS '该节点尝试实际开始执行的时刻；尚未开始时为空；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_node_run.ended_at IS '该节点尝试结束时刻；未结束为空，不能早于开始时刻；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_node_run.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.task_node_run.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_node_run.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.task_node_run.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.task_event.event_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.task_event.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.task_event.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.task_event.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.task_event.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.task_event.from_state IS '状态事件发生前的状态；首次创建事件可为空';
COMMENT ON COLUMN mt.task_event.to_state IS '状态事件发生后的状态；须由所属状态机验证合法转移';
COMMENT ON COLUMN mt.task_event.reason IS '状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密';
COMMENT ON COLUMN mt.task_event.request_id IS '贯穿接口、任务和审计的请求追踪标识；不充当权限凭证';
COMMENT ON COLUMN mt.task_event.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.task_event.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_event.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.task_event.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.outbox_event.event_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.outbox_event.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.outbox_event.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.outbox_event.topic IS '发件箱消息的逻辑主题名称，由消息契约登记';
COMMENT ON COLUMN mt.outbox_event.aggregate_id IS '事件所属聚合对象标识；具体对象类型由topic确定，不是通用外键';
COMMENT ON COLUMN mt.outbox_event.aggregate_version IS '该事件所描述聚合对象的版本号，同主题和对象下用于去重及顺序判断';
COMMENT ON COLUMN mt.outbox_event.payload IS '按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.outbox_event.published_at IS '事件已确认投递至消息后端的时刻；NULL表示未确认投递，与媒体发布时间无关；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.outbox_event.attempts IS '发件箱事件已尝试投递次数，从0开始；成功与否另看published_at';
COMMENT ON COLUMN mt.outbox_event.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.outbox_event.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.outbox_event.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.outbox_event.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.event_receipt.receipt_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.event_receipt.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.event_receipt.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.event_receipt.event_id IS '已处理的外部或内部事件标识；与consumer共同去重，未必来自本地发件箱';
COMMENT ON COLUMN mt.event_receipt.consumer IS '消费逻辑的稳定标识，区分不同消费者独立处理同一事件';
COMMENT ON COLUMN mt.event_receipt.effect_sha256 IS '消费已产生效果的规范化结果摘要，用于校验重复消费是否一致；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.event_receipt.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.event_receipt.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.event_receipt.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.event_receipt.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.shot.shot_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.shot.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.shot.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.shot.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.shot.start_ms IS '源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理';
COMMENT ON COLUMN mt.shot.end_ms IS '源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms';
COMMENT ON COLUMN mt.shot.score IS '镜头时间区间对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.shot.mapping_version IS '派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本';
COMMENT ON COLUMN mt.shot.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.shot.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.shot.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.shot.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.keyframe.frame_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.keyframe.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.keyframe.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.keyframe.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.keyframe.shot_id IS '关键帧所属镜头记录标识；未进行镜头切分时允许为空';
COMMENT ON COLUMN mt.keyframe.timestamp_ms IS '关键帧在源媒体时间轴上的位置，单位毫秒，非负';
COMMENT ON COLUMN mt.keyframe.object_id IS '所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用';
COMMENT ON COLUMN mt.keyframe.quality_score IS '关键帧对应的质量评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.keyframe.mapping_version IS '派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本';
COMMENT ON COLUMN mt.keyframe.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.keyframe.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.keyframe.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.keyframe.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.text_segment.segment_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.text_segment.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.text_segment.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.text_segment.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.text_segment.type IS '提取模态类别：OCR、ASR或SUBTITLE';
COMMENT ON COLUMN mt.text_segment.start_ms IS '源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理';
COMMENT ON COLUMN mt.text_segment.end_ms IS '源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms';
COMMENT ON COLUMN mt.text_segment.text IS 'OCR、ASR或字幕提取的文本原文；纠错或摘要应另存，不覆盖原文';
COMMENT ON COLUMN mt.text_segment.confidence IS 'OCR ASR字幕原文对应的提取置信分数，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.text_segment.bbox IS '源图像归一化定位框对象，使用x、y、width、height；不适用可用空对象，非空须校验边界。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.text_segment.mapping_version IS '派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本';
COMMENT ON COLUMN mt.text_segment.model_name IS '模型注册名称，与model_version共同定位产生该结果的模型';
COMMENT ON COLUMN mt.text_segment.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.text_segment.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.text_segment.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.text_segment.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.text_segment.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.model_registry.model_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.model_registry.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.model_registry.name IS '名称，供目录显示和识别；与稳定标识分离，不能用名称代替主键';
COMMENT ON COLUMN mt.model_registry.version IS '此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version';
COMMENT ON COLUMN mt.model_registry.capability IS '模型或索引提供的能力编码，取值对应内部推理能力契约';
COMMENT ON COLUMN mt.model_registry.digest IS '注册模型权重或模型包的SHA-256，具体制品范围记录于模型卡；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.model_registry.metric_json IS '模型评测指标摘要对象，须包含所用指标口径对应值；具体证据引用model_evaluation。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.model_registry.dataset_version IS '本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录';
COMMENT ON COLUMN mt.model_registry.model_card_ref IS '模型卡的受控版本引用，说明用途、限制和训练评测信息';
COMMENT ON COLUMN mt.model_registry.license_record_ref IS '代码与权重许可核查记录引用，需覆盖本项目预定用途';
COMMENT ON COLUMN mt.model_registry.backend IS '实际运行推理后端标识，例如经选型的框架适配器；不是模型名称';
COMMENT ON COLUMN mt.model_registry.environment_ref IS '可重建运行环境说明或镜像摘要的受控引用';
COMMENT ON COLUMN mt.model_registry.status IS '模型版本与许可引用的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.model_registry.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.model_registry.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.model_registry.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.model_registry.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.model_evaluation.evaluation_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.model_evaluation.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.model_evaluation.model_id IS '模型注册记录标识，引用同单位的model_registry.model_id';
COMMENT ON COLUMN mt.model_evaluation.dataset_id IS '数据集目录的稳定文本编号，例如D01；不是数据库UUID主键';
COMMENT ON COLUMN mt.model_evaluation.dataset_version IS '本次训练或评测采用的数据集版本，不能用最新版本覆盖历史记录';
COMMENT ON COLUMN mt.model_evaluation.protocol_id IS '评测协议标识，决定指标公式、样本计数、阈值及统计口径';
COMMENT ON COLUMN mt.model_evaluation.split IS '此次评测使用的划分用途；封存holdout不能用于训练或调参';
COMMENT ON COLUMN mt.model_evaluation.sample_count IS '按照评测协议统计的样本数，必须为正；不能混用帧数、素材组数和文件数';
COMMENT ON COLUMN mt.model_evaluation.failure_count IS '处理失败样本数，范围0到sample_count，不应从评测分母中隐式删除';
COMMENT ON COLUMN mt.model_evaluation.metrics IS '评测协议规定的指标结果对象；需保留失败计数和适用样本口径。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.model_evaluation.artifact_ref IS '评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.model_evaluation.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.model_evaluation.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.model_evaluation.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.model_evaluation.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.model_release.release_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.model_release.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.model_release.model_id IS '模型注册记录标识，引用同单位的model_registry.model_id';
COMMENT ON COLUMN mt.model_release.bundle_sha256 IS '完整模型发布包的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.model_release.calibration_version IS '分数校准方法和参数版本；未校准时为空，不把原始分数称为概率';
COMMENT ON COLUMN mt.model_release.backend IS '实际运行推理后端标识，例如经选型的框架适配器；不是模型名称';
COMMENT ON COLUMN mt.model_release.index_version IS '本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本';
COMMENT ON COLUMN mt.model_release.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.model_release.state IS '模型发布包的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.model_release.environment_ref IS '可重建运行环境说明或镜像摘要的受控引用';
COMMENT ON COLUMN mt.model_release.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.model_release.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.model_release.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.model_release.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.index_registry.index_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.index_registry.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.index_registry.capability IS '模型或索引提供的能力编码，取值对应内部推理能力契约';
COMMENT ON COLUMN mt.index_registry.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.index_registry.dimension IS '特征向量维度，必须为正整数并与模型及索引配置一致';
COMMENT ON COLUMN mt.index_registry.normalization IS '特征归一化方法，例如l2或none；应与训练、查询和索引构建保持一致';
COMMENT ON COLUMN mt.index_registry.index_version IS '本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本';
COMMENT ON COLUMN mt.index_registry.state IS '索引版本不混向量的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.index_registry.configuration IS '索引构建参数对象，包括距离与索引配置；具体字段由所选索引适配器校验。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.index_registry.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.index_registry.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.index_registry.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.index_registry.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.feature.feature_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.feature.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.feature.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.feature.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.feature.model_id IS '模型注册记录标识，引用同单位的model_registry.model_id';
COMMENT ON COLUMN mt.feature.dimension IS '特征向量维度，必须为正整数并与模型及索引配置一致';
COMMENT ON COLUMN mt.feature.normalization IS '特征归一化方法，例如l2或none；应与训练、查询和索引构建保持一致';
COMMENT ON COLUMN mt.feature.feature_ref IS '特征数据的受控存储定位与版本对象，不在该字段内混入不同模型向量。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.feature.index_version IS '本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本';
COMMENT ON COLUMN mt.feature.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.feature.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.feature.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.feature.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.evidence_item.evidence_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.evidence_item.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.evidence_item.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.evidence_item.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.evidence_item.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.evidence_item.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.evidence_item.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.evidence_item.type IS '证据类别编码，决定对象、时间范围和定位解释';
COMMENT ON COLUMN mt.evidence_item.object_id IS '所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用';
COMMENT ON COLUMN mt.evidence_item.sha256 IS '该证据版本绑定内容的SHA-256，摘要对象需在证据类型契约中明确；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.evidence_item.captured_at IS '证据采集或记录的实际时刻；可信时间来源由取证规则确定，不保证机器时钟天然可信；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.evidence_item.model_name IS '模型注册名称，与model_version共同定位产生该结果的模型';
COMMENT ON COLUMN mt.evidence_item.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.evidence_item.mapping_version IS '派生坐标或时间戳回映射到原媒体所用映射规则版本；原件也需明确恒等映射版本';
COMMENT ON COLUMN mt.evidence_item.authorization_version IS '本次处理采用的来源授权版本，用于撤销核查及历史追溯';
COMMENT ON COLUMN mt.evidence_item.immutable_state IS '证据事实版本的不可变记录状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.evidence_item.time_range IS '源媒体时间范围对象，使用start_ms、end_ms；非空时必须校验先后与源媒体范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.evidence_item.bbox IS '源图像归一化定位框对象，使用x、y、width、height；不适用可用空对象，非空须校验边界。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.evidence_item.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.evidence_item.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.evidence_item.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.evidence_item.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.risk_finding.finding_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.risk_finding.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.risk_finding.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.risk_finding.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.risk_finding.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.risk_finding.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.risk_finding.category IS '风险分类编码；取值、阈值和法律业务含义由有效标签策略确定';
COMMENT ON COLUMN mt.risk_finding.score IS '风险候选发现对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.risk_finding.calibrated_score IS '校准后的模型分数，范围0至1；未进行校准时为NULL，必须绑定相应校准版本和评测口径';
COMMENT ON COLUMN mt.risk_finding.start_ms IS '源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理';
COMMENT ON COLUMN mt.risk_finding.end_ms IS '源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms';
COMMENT ON COLUMN mt.risk_finding.model_name IS '模型注册名称，与model_version共同定位产生该结果的模型';
COMMENT ON COLUMN mt.risk_finding.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.risk_finding.threshold_version IS '将模型分数转为候选标签时使用的阈值配置版本';
COMMENT ON COLUMN mt.risk_finding.payload IS '按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.risk_finding.status IS '风险候选发现的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.risk_finding.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.risk_finding.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.risk_finding.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.risk_finding.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.tamper_finding.tamper_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.tamper_finding.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.tamper_finding.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.tamper_finding.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.tamper_finding.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.tamper_finding.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.tamper_finding.type IS '疑似篡改类型编码，取值由模型及标签策略约定';
COMMENT ON COLUMN mt.tamper_finding.score IS '疑似篡改发现对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.tamper_finding.calibrated_score IS '校准后的模型分数，范围0至1；未进行校准时为NULL，必须绑定相应校准版本和评测口径';
COMMENT ON COLUMN mt.tamper_finding.start_ms IS '源媒体半开区间起点，单位毫秒，包含该时刻；静态或不适用时按可空规则处理';
COMMENT ON COLUMN mt.tamper_finding.end_ms IS '源媒体半开区间终点，单位毫秒，不包含该时刻；有效区间必须大于start_ms';
COMMENT ON COLUMN mt.tamper_finding.model_name IS '模型注册名称，与model_version共同定位产生该结果的模型';
COMMENT ON COLUMN mt.tamper_finding.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.tamper_finding.threshold_version IS '将模型分数转为候选标签时使用的阈值配置版本';
COMMENT ON COLUMN mt.tamper_finding.payload IS '按事件或发现类型定义的结构化负载，须由对应Schema验证；JSONB类型不验证业务字段。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.tamper_finding.status IS '疑似篡改发现的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.tamper_finding.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.tamper_finding.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.tamper_finding.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.tamper_finding.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.finding_evidence.link_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.finding_evidence.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.finding_evidence.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.finding_evidence.risk_finding_id IS '关联风险发现标识；与tamper_finding_id按表级互斥规则择一';
COMMENT ON COLUMN mt.finding_evidence.tamper_finding_id IS '关联疑似篡改发现标识；与risk_finding_id按表级互斥规则择一';
COMMENT ON COLUMN mt.finding_evidence.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.finding_evidence.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.finding_evidence.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.finding_evidence.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.finding_evidence.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.task_evidence.link_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.task_evidence.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.task_evidence.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.task_evidence.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.task_evidence.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.task_evidence.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.task_evidence.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.task_evidence.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.task_evidence.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.search_job.search_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.search_job.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.search_job.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.search_job.query_asset_id IS '作为检索输入的媒体资产标识，需处于当前授权范围';
COMMENT ON COLUMN mt.search_job.kind IS '检索作业类别，用于区分图片与视频等查询流程';
COMMENT ON COLUMN mt.search_job.state IS '异步检索任务的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.search_job.index_version IS '本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本';
COMMENT ON COLUMN mt.search_job.error_code IS '失败原因的稳定错误码；无失败时允许NULL，用户说明与诊断堆栈分开';
COMMENT ON COLUMN mt.search_job.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.search_job.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.search_job.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.search_job.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.source_match.match_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.source_match.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.source_match.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.source_match.search_id IS '产生匹配候选的异步检索作业标识';
COMMENT ON COLUMN mt.source_match.query_asset_id IS '作为检索输入的媒体资产标识，需处于当前授权范围';
COMMENT ON COLUMN mt.source_match.candidate_asset_id IS '被检索返回的候选来源媒体资产标识；候选相似不能直接认定同源';
COMMENT ON COLUMN mt.source_match.score IS '同源或片段映射候选对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.source_match.verification_type IS '支持本匹配结果的验证方法编码，例如几何或时序验证；具体取值见约束';
COMMENT ON COLUMN mt.source_match.relation IS '查询与候选媒体间的关系类型，整体同源、局部包含和语义相似必须区分';
COMMENT ON COLUMN mt.source_match.query_start_ms IS '查询媒体中匹配片段起点，单位毫秒，半开区间包含起点';
COMMENT ON COLUMN mt.source_match.query_end_ms IS '查询媒体中匹配片段终点，单位毫秒，半开区间不包含终点';
COMMENT ON COLUMN mt.source_match.source_start_ms IS '候选来源媒体中匹配片段起点，单位毫秒';
COMMENT ON COLUMN mt.source_match.source_end_ms IS '候选来源媒体中匹配片段终点，单位毫秒，必须大于对应起点';
COMMENT ON COLUMN mt.source_match.direction IS '查询与来源片段的播放对应方向，不改变存储区间起点小于终点的约定';
COMMENT ON COLUMN mt.source_match.speed_ratio IS '查询片段时长除以来源片段时长的正比例（本轮工程约定）；倒放由direction单独表示，模型适配器负责转换其原生定义';
COMMENT ON COLUMN mt.source_match.evidence_refs IS '支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.source_match.index_version IS '本次使用或发布的检索索引版本；不能混合不同模型维度和预处理版本';
COMMENT ON COLUMN mt.source_match.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.source_match.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.source_match.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.source_match.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.content_cluster.cluster_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.content_cluster.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.content_cluster.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.content_cluster.scope IS '内容簇覆盖的比较范围标识或说明；整体同源与指定片段范围必须区分';
COMMENT ON COLUMN mt.content_cluster.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.content_cluster.status IS '高可信整内容簇的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.content_cluster.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.content_cluster.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.content_cluster.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.content_cluster.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.cluster_member.member_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.cluster_member.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.cluster_member.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.cluster_member.cluster_id IS '高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证';
COMMENT ON COLUMN mt.cluster_member.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.cluster_member.relation IS '成员与整内容簇的关系；当前只允许full_copy，片段拼接不能加入为整内容成员';
COMMENT ON COLUMN mt.cluster_member.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.cluster_member.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.cluster_member.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.cluster_member.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.cluster_member.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.first_source_candidate.candidate_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.first_source_candidate.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.first_source_candidate.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.first_source_candidate.cluster_id IS '高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证';
COMMENT ON COLUMN mt.first_source_candidate.asset_id IS '本批次列为首发候选的媒体资产标识；必须属于同案件及本簇cluster_member，不能引用簇外素材';
COMMENT ON COLUMN mt.first_source_candidate.rank IS '本次排序批次内的候选名次，从1连续排列到候选数量，最多3；不是确定首发结论';
COMMENT ON COLUMN mt.first_source_candidate.probability IS '已校准的候选可信度，范围0至1；未校准为NULL，不用于替代候选名次或确定首发结论';
COMMENT ON COLUMN mt.first_source_candidate.published_at IS '可核查的来源发布时间；未知为NULL，不用发现时间或当前时间填补；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.first_source_candidate.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.first_source_candidate.evidence_refs IS '首发候选证据对象，必须包含evidence_ids和counter_evidence_ids两个数组且无额外键；支持证据至少1项，各数组内UUID不可重复。SQL插入触发器核验ID格式、存在及同案件；证据是否有效支持该候选、实际用途授权与引用语义仍由应用复核';
COMMENT ON COLUMN mt.first_source_candidate.coverage_note IS '本次观察的平台、时间和素材覆盖范围及缺失说明；不能声称覆盖未知全网';
COMMENT ON COLUMN mt.first_source_candidate.status IS '首发候选及覆盖范围的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.first_source_candidate.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.first_source_candidate.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.first_source_candidate.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.first_source_candidate.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.first_source_candidate.ranking_id IS '所属首发排序快照ID；与案件及簇共同绑定first_source_ranking，不能混合不同计算结果';
COMMENT ON COLUMN mt.propagation_node.node_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.propagation_node.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.propagation_node.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.propagation_node.cluster_id IS '高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证';
COMMENT ON COLUMN mt.propagation_node.type IS '传播图节点类型，决定其展示及业务对象解释';
COMMENT ON COLUMN mt.propagation_node.display_label IS '传播图节点的人类可读展示标签，不作为节点主键或关系证据';
COMMENT ON COLUMN mt.propagation_node.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.propagation_node.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.propagation_node.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.propagation_node.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.propagation_edge.edge_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.propagation_edge.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.propagation_edge.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.propagation_edge.from_node_id IS '传播关系起点节点标识';
COMMENT ON COLUMN mt.propagation_edge.to_node_id IS '传播关系终点节点标识';
COMMENT ON COLUMN mt.propagation_edge.relation IS '传播关系类别；是否事实另由origin和证据决定';
COMMENT ON COLUMN mt.propagation_edge.origin IS '传播边依据类别，区分明确记录与算法推断；推断不能展示为事实';
COMMENT ON COLUMN mt.propagation_edge.probability IS '传播关系推断的已校准概率，范围0至1；未校准时为NULL，不能据此把推断边改成事实边';
COMMENT ON COLUMN mt.propagation_edge.evidence_refs IS '支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.propagation_edge.state IS '显式推断传播边的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.propagation_edge.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.propagation_edge.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.propagation_edge.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.propagation_edge.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.claim.claim_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.claim.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.claim.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.claim.asset_id IS '本记录关联的媒体资产标识，指向同案件media_asset.asset_id；NULL只在该列允许且资产尚未形成时使用';
COMMENT ON COLUMN mt.claim.subject IS '结构化主张中的主体表述，来自原文或模型抽取；不能当用户身份';
COMMENT ON COLUMN mt.claim.action IS '主张所描述行为或审计动作编码，具体语义由本表决定';
COMMENT ON COLUMN mt.claim.claim_time IS '主张原文中的时间表述，可能含模糊日期；未知为NULL，不强行转成精确时间戳';
COMMENT ON COLUMN mt.claim.place IS '主张原文中的地点表述；未知为空，不自动地理定位';
COMMENT ON COLUMN mt.claim.result IS '主张所陈述的结果，不代表系统已核实为真';
COMMENT ON COLUMN mt.claim.source_segment_refs IS '主张对应文本或媒体片段引用对象，需定位到资产、片段和时间或字符范围。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.claim.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.claim.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.claim.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.claim.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.claim.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.claim_evidence_relation.relation_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.claim_evidence_relation.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.claim_evidence_relation.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.claim_evidence_relation.claim_id IS '被证据支持、反对或关联的主张标识';
COMMENT ON COLUMN mt.claim_evidence_relation.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.claim_evidence_relation.relation IS '主张与证据的关系类别，支持、反对或不足等取值以CHECK枚举为准';
COMMENT ON COLUMN mt.claim_evidence_relation.score IS '主张证据关系对应的原始模型评分，本候选契约限定0至1；NULL表示未产生评分，未经校准不称为概率，不同模型分数不得直接比较';
COMMENT ON COLUMN mt.claim_evidence_relation.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.claim_evidence_relation.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.claim_evidence_relation.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.claim_evidence_relation.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.claim_evidence_relation.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.approval_request.approval_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.approval_request.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.approval_request.case_id IS '案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限';
COMMENT ON COLUMN mt.approval_request.object_type IS '审批或审计目标对象类型，决定object_id应指向哪种业务对象';
COMMENT ON COLUMN mt.approval_request.object_id IS '该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键';
COMMENT ON COLUMN mt.approval_request.object_version IS '审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批';
COMMENT ON COLUMN mt.approval_request.purpose IS '本记录声明或申请的处理用途，实际动作需与有效授权用途相符';
COMMENT ON COLUMN mt.approval_request.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.approval_request.requested_by IS '审批申请人的认证主体标识，由服务端设置';
COMMENT ON COLUMN mt.approval_request.state IS '按目的独立审批申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.approval_request.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.approval_request.reason IS '状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密';
COMMENT ON COLUMN mt.approval_request.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.approval_request.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.approval_request.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.approval_request.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.approval_request.run_version IS '分析对象绑定运行版本';
COMMENT ON COLUMN mt.approval_request.result_version IS '分析对象绑定结果版本';
COMMENT ON COLUMN mt.approval_decision.decision_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.approval_decision.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.approval_decision.case_id IS '案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限';
COMMENT ON COLUMN mt.approval_decision.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.approval_decision.decision IS '本次审批决定；取值由CHECK限制，不能替代对象版本和权限校验';
COMMENT ON COLUMN mt.approval_decision.decision_actor_id IS '作出审批决定的用户标识，由认证上下文与职责分离规则核验';
COMMENT ON COLUMN mt.approval_decision.reason IS '状态变化、跳过、拒绝或审批决定的原因说明，应足以定位业务原因且不泄露秘密';
COMMENT ON COLUMN mt.approval_decision.evidence_refs IS '支持与反对证据引用的结构化对象；引用需存在并属于授权案件，JSONB本身不建立外键。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.approval_decision.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.approval_decision.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.approval_decision.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.approval_decision.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.approval_decision.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.operation_token.token_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.operation_token.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.operation_token.case_id IS '案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限';
COMMENT ON COLUMN mt.operation_token.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.operation_token.actor_id IS '操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则';
COMMENT ON COLUMN mt.operation_token.purpose IS '本记录声明或申请的处理用途，实际动作需与有效授权用途相符';
COMMENT ON COLUMN mt.operation_token.object_id IS '该记录绑定的业务目标对象ID；沿用关联审批请求的对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键';
COMMENT ON COLUMN mt.operation_token.object_version IS '审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批';
COMMENT ON COLUMN mt.operation_token.token_sha256 IS '一次性操作凭据的SHA-256，不保存明文凭据，不能代替有效期与消费检查；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.operation_token.expires_at IS '此记录的有效截止时刻；到期后不能继续使用。可空时表示未记录截止，不自动表示已批准永久有效；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.operation_token.consumed_at IS '一次性操作凭据被消费的时刻；非空后不得重用；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.operation_token.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.operation_token.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.operation_token.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.operation_token.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.review_record.review_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.review_record.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.review_record.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.review_record.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.review_record.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.review_record.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.review_record.reviewer_id IS '执行本次业务复核的用户标识，需有对应功能和案件权限';
COMMENT ON COLUMN mt.review_record.decision IS '本次业务复核决定；取值由CHECK限制，不能替代对象版本和权限校验';
COMMENT ON COLUMN mt.review_record.comments IS '复核意见原文，说明证据取舍及处理理由，后续更正追加版本';
COMMENT ON COLUMN mt.review_record.review_version IS '针对结果形成的复核版本号，复核更正不能覆盖历史记录';
COMMENT ON COLUMN mt.review_record.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.review_record.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.review_record.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.review_record.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.review_record.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.review_evidence.link_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.review_evidence.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.review_evidence.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.review_evidence.review_id IS '所引用业务复核记录标识';
COMMENT ON COLUMN mt.review_evidence.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.review_evidence.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.review_evidence.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.review_evidence.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.review_evidence.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.evidence_package.package_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.evidence_package.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.evidence_package.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.evidence_package.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.evidence_package.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.evidence_package.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.evidence_package.version IS '此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version';
COMMENT ON COLUMN mt.evidence_package.manifest_sha256 IS '固化证据包规范化清单的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.evidence_package.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.evidence_package.signature_status IS '证据包签名处理状态；状态文字不能代替签名验证证据';
COMMENT ON COLUMN mt.evidence_package.retention_policy_version IS '用于本对象或证据包的保留策略版本；版本本身不代表底层保留能力已生效';
COMMENT ON COLUMN mt.evidence_package.state IS '固化证据包版本的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.evidence_package.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.evidence_package.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.evidence_package.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.evidence_package.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.package_item.package_item_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.package_item.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.package_item.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.package_item.package_id IS '固化证据包的版本记录标识';
COMMENT ON COLUMN mt.package_item.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.package_item.object_id IS '所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用';
COMMENT ON COLUMN mt.package_item.sha256 IS '清单中引用对象固定版本字节的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.package_item.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.package_item.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.package_item.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.package_item.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.report.report_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.report.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.report.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.report.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.report.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.report.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.report.version IS '此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version';
COMMENT ON COLUMN mt.report.template_version IS '生成报告使用的模板版本，确保历史报告可以重现';
COMMENT ON COLUMN mt.report.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.report.object_id IS '所关联对象字节版本的内部标识；具体引用目标见本表外键，不能与对象存储version_id混用';
COMMENT ON COLUMN mt.report.state IS '报告生成与下载状态的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.report.snapshot_sha256 IS '报告所绑定内容快照的SHA-256，不代表数字签名；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.report.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.report.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.report.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.report.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.report_evidence.link_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.report_evidence.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.report_evidence.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.report_evidence.report_id IS '报告版本记录标识';
COMMENT ON COLUMN mt.report_evidence.evidence_id IS '所引用证据事实版本标识，指向同案件evidence_item.evidence_id';
COMMENT ON COLUMN mt.report_evidence.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.report_evidence.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.report_evidence.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.report_evidence.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.feedback_request.feedback_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.feedback_request.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.feedback_request.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.feedback_request.finding_id IS '申请回流的风险发现标识；用途审批通过也须另核验来源授权';
COMMENT ON COLUMN mt.feedback_request.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.feedback_request.label_version IS '本次标注使用的标签体系版本';
COMMENT ON COLUMN mt.feedback_request.label IS '人工确认或申请使用的训练标签；不可直接把模型预测视为真值';
COMMENT ON COLUMN mt.feedback_request.purpose IS '本记录声明或申请的处理用途，实际动作需与有效授权用途相符';
COMMENT ON COLUMN mt.feedback_request.source_authorization_ref IS '允许该素材用于指定回流或训练用途的来源授权记录引用';
COMMENT ON COLUMN mt.feedback_request.state IS '纠错训练用途申请的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.feedback_request.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.feedback_request.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.feedback_request.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.feedback_request.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.dataset_version.dataset_version_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.dataset_version.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.dataset_version.dataset_id IS '数据集目录的稳定文本编号，例如D01；不是数据库UUID主键';
COMMENT ON COLUMN mt.dataset_version.version IS '此记录对应的业务或模型版本，具体命名由所属目录约定；不同于并发控制row_version';
COMMENT ON COLUMN mt.dataset_version.catalog_sha256 IS '数据集版本目录规范化清单的SHA-256；存储64位小写十六进制，正则只检查格式不验证字节真实性';
COMMENT ON COLUMN mt.dataset_version.authorization_status IS '来源或数据集用途授权的当前审核状态，未验证状态不得解释为可正式使用';
COMMENT ON COLUMN mt.dataset_version.split_manifest_ref IS '数据集训练、验证、校准及封存测试划分清单的版本引用';
COMMENT ON COLUMN mt.dataset_version.actual_count IS '按数据卡计数单位核验的实际数量；NULL表示未核验，不用预算数量代替';
COMMENT ON COLUMN mt.dataset_version.status IS '数据版本元数据不存真实样本的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.dataset_version.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.dataset_version.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.dataset_version.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.dataset_version.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.audit_event.event_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.audit_event.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.audit_event.case_id IS '案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限';
COMMENT ON COLUMN mt.audit_event.actor_id IS '操作主体标识；从服务端认证上下文取得，系统动作的可空条件须另有审计规则';
COMMENT ON COLUMN mt.audit_event.action IS '被审计业务操作的稳定编码，不是主张文本中的行为';
COMMENT ON COLUMN mt.audit_event.object_type IS '审批或审计目标对象类型，决定object_id应指向哪种业务对象';
COMMENT ON COLUMN mt.audit_event.object_id IS '该记录绑定的业务目标对象ID；由object_type确定对象类型，不是对象存储版本ID；多态引用需服务端核验实际对象、案件和版本，DDL没有通用对象外键';
COMMENT ON COLUMN mt.audit_event.object_version IS '审批或审计绑定的业务对象版本，正整数；新版本不能复用旧审批';
COMMENT ON COLUMN mt.audit_event.outcome IS '审计操作的结果编码，例如允许、拒绝或失败；须与实际处理一致';
COMMENT ON COLUMN mt.audit_event.request_id IS '贯穿接口、任务和审计的请求追踪标识；不充当权限凭证';
COMMENT ON COLUMN mt.audit_event.occurred_at IS '被审计操作实际发生时刻，区别于记录写入时间created_at；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.audit_event.details IS '脱敏后的审计上下文对象，记录必要原因和关联ID，不记录令牌、密码或原始敏感内容。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.audit_event.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.audit_event.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.audit_event.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.audit_event.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.audit_export.export_id IS '主键，由应用提供UUID；不视为访问凭证';
COMMENT ON COLUMN mt.audit_export.org_id IS '该记录所属单位标识；与案件归属、认证上下文和RLS共同限定访问，客户端不得自行指定越权单位';
COMMENT ON COLUMN mt.audit_export.case_id IS '该记录所属案件标识；复合外键阻止跨案件关联，访问还须通过案件授权校验';
COMMENT ON COLUMN mt.audit_export.approval_id IS '与本动作对应的审批请求标识；必须核验用途、对象、版本、状态和有效期，非空不等于审批已通过';
COMMENT ON COLUMN mt.audit_export.start_at IS '审计导出查询的起始时刻；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.audit_export.end_at IS '审计导出查询的结束时刻，必须与起始时刻构成有效区间；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.audit_export.purpose IS '本记录声明或申请的处理用途，实际动作需与有效授权用途相符';
COMMENT ON COLUMN mt.audit_export.state IS '审计导出作业的业务状态；允许值以本行CHECK为准，状态转移还须服务层验证；未列CHECK时为待定词表，不代表任意值均业务有效';
COMMENT ON COLUMN mt.audit_export.artifact_ref IS '评测产物或导出文件的受控定位与摘要对象，禁止包含临时访问秘密。数据库仅保存JSON值；键名、类型、引用存在性及版本需按关联接口/模型Schema在写入前检查，未关联Schema的扩展参数由适配器定义后启用';
COMMENT ON COLUMN mt.audit_export.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.audit_export.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.audit_export.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.audit_export.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMENT ON COLUMN mt.first_source_ranking.ranking_id IS '一次首发排序结果快照的唯一标识；重算或复核更正生成新快照';
COMMENT ON COLUMN mt.first_source_ranking.org_id IS '记录所属单位标识；单位授权范围由服务端认证上下文确定';
COMMENT ON COLUMN mt.first_source_ranking.case_id IS '案件隔离域标识；写入和读取均须验证当前主体有访问该案件的权限';
COMMENT ON COLUMN mt.first_source_ranking.cluster_id IS '高可信内容簇标识，指向同案件content_cluster.cluster_id；不得用相似度连通关系替代整内容同源验证';
COMMENT ON COLUMN mt.first_source_ranking.task_id IS '关联分析任务标识，指向analysis_task.task_id；历史结果需结合运行和结果版本';
COMMENT ON COLUMN mt.first_source_ranking.run_version IS '分析任务的运行版本号；重新计算创建新版本，节点重试不等同重算';
COMMENT ON COLUMN mt.first_source_ranking.result_version IS '给定任务运行下的结果快照版本号；与task_id和run_version共同定位结果';
COMMENT ON COLUMN mt.first_source_ranking.candidate_count IS '该快照应包含的候选总数；事务提交时必须与明细数量相等，0表示有结果但无足够候选';
COMMENT ON COLUMN mt.first_source_ranking.model_version IS '生成结果或特征的具体模型版本；绑定相应模型名称或能力，不等同策略版本';
COMMENT ON COLUMN mt.first_source_ranking.policy_version IS '本记录使用的业务、阈值或流程策略版本，需按其实际用途解析';
COMMENT ON COLUMN mt.first_source_ranking.coverage_note IS '本次观察的平台、时间和素材覆盖范围及缺失说明；不能声称覆盖未知全网';
COMMENT ON COLUMN mt.first_source_ranking.status IS 'candidate为待核查候选，insufficient为证据不足，reviewed为已复核快照；reviewed仍非法律结论';
COMMENT ON COLUMN mt.first_source_ranking.created_at IS '记录创建时间点；TIMESTAMPTZ按会话时区显示，接口统一输出带时区时间，不保存原始时区名';
COMMENT ON COLUMN mt.first_source_ranking.updated_at IS '更新时刻；不可变表保持原值；存储时间点，显示受会话时区影响，接口必须携带时区';
COMMENT ON COLUMN mt.first_source_ranking.row_version IS '本行乐观并发版本，初始1；可变表由应用条件更新并递增，无自动递增触发器；不可变快照保持原值';
COMMENT ON COLUMN mt.first_source_ranking.created_by IS '创建主体；迁移/系统事件可空，业务应用必须填';
COMMIT;
