-- Extend both fixed operation and lookup registries; preserve all existing entries.
CREATE OR REPLACE FUNCTION mt.scope_operation() RETURNS text LANGUAGE sql STABLE AS $$
SELECT CASE WHEN current_setting('app.operation_id',true) = ANY(ARRAY[
 'issueOperationToken','sealEvidence',
 'cancelTask','cancelTaskWork','completeUpload','createImport','createPolicy','createReview','createUpload',
 'decideApproval','downloadAuditExport','exportAudit','finishTaskNodeWork','getApproval','getAuditExport',
 'getCurrentUser','getFeedback','getFirstSource','getForensics','getImport','getModelOperation','getPolicy',
 'getPolicyDefinition','getPropagation','getReview','getReviewContext','getRiskFindings','getSource','getTask',
 'getTaskEvidence','getTaskExecution','getTimeline','getUploadStatus','listApprovals','listAuditEvents',
 'listPendingReviews','listPolicies','listReviews','listSources','listTaskEvents','listTaskNodes','listUploadParts',
 'processAuditExportWork','putUploadPart','requestApproval','revokeApproval','startTaskNodeWork',
 'syncSourceAuthorization','validateUploadWork'
]::text[]) THEN current_setting('app.operation_id',true) ELSE NULL END
$$;

CREATE OR REPLACE FUNCTION mt.scope_lookup_kind_allowed(wanted_kind text,wanted_operation text) RETURNS boolean
LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,mt AS $$
 SELECT COALESCE(CASE wanted_kind
 WHEN 'approval' THEN wanted_operation=ANY(ARRAY['decideApproval','exportAudit','getApproval','issueOperationToken','revokeApproval'])
 WHEN 'asset' THEN wanted_operation=ANY(ARRAY['getTimeline'])
 WHEN 'cluster' THEN wanted_operation=ANY(ARRAY['getFirstSource','getPropagation'])
 WHEN 'evidence_package' THEN wanted_operation=ANY(ARRAY['requestApproval'])
 WHEN 'export' THEN wanted_operation=ANY(ARRAY['downloadAuditExport','getAuditExport','processAuditExportWork'])
 WHEN 'feedback' THEN wanted_operation=ANY(ARRAY['getFeedback','requestApproval'])
 WHEN 'import' THEN wanted_operation=ANY(ARRAY['getImport'])
 WHEN 'operation' THEN wanted_operation=ANY(ARRAY['listApprovals','listAuditEvents','listPendingReviews','listReviews','listSources','requestApproval'])
 WHEN 'policy' THEN wanted_operation=ANY(ARRAY['getPolicy','getPolicyDefinition'])
 WHEN 'report' THEN wanted_operation=ANY(ARRAY['requestApproval'])
 WHEN 'review' THEN wanted_operation=ANY(ARRAY['getReview','listReviews'])
 WHEN 'source' THEN wanted_operation=ANY(ARRAY['createImport','createUpload','getSource','syncSourceAuthorization'])
 WHEN 'task' THEN wanted_operation=ANY(ARRAY['cancelTask','cancelTaskWork','createReview','finishTaskNodeWork','getForensics','getReviewContext','getRiskFindings','getTask','getTaskEvidence','getTaskExecution','listPendingReviews','listTaskEvents','listTaskNodes','requestApproval','issueOperationToken','sealEvidence','startTaskNodeWork'])
 WHEN 'upload' THEN wanted_operation=ANY(ARRAY['completeUpload','getUploadStatus','listUploadParts','putUploadPart','validateUploadWork'])
 WHEN 'user' THEN wanted_operation=ANY(ARRAY['createPolicy','getCurrentUser','listPolicies'])
 ELSE false END,false)
$$;

-- Exact case token metadata; old rows retain version0 and are never consumed.
ALTER TABLE mt.operation_token
 ADD COLUMN storage_version smallint NOT NULL DEFAULT 0,
 ADD COLUMN action text,
 ADD COLUMN object_type text,
 ADD COLUMN approval_version bigint,
 ADD COLUMN approval_policy_version text,
 ADD COLUMN permission_policy_version text,
 ADD COLUMN rule_version text,
 ADD COLUMN recovery_generation text,
 ADD COLUMN key_id text,
 ADD COLUMN principal_sha256 text,
 ADD COLUMN request_sha256 text,
 ADD COLUMN idempotency_key text;
ALTER TABLE mt.operation_token ALTER COLUMN storage_version SET DEFAULT 1;
ALTER TABLE mt.operation_token ADD CONSTRAINT operation_token_v1_binding CHECK ((
 storage_version=0 OR (storage_version=1 AND case_id IS NOT NULL AND action='sealEvidence'
 AND object_type='task' AND purpose='seal' AND approval_version>0
 AND length(approval_policy_version) BETWEEN 1 AND 1024
 AND length(permission_policy_version) BETWEEN 1 AND 1024
 AND permission_policy_version=btrim(permission_policy_version)
 AND rule_version ~ '^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$'
 AND length(recovery_generation) BETWEEN 1 AND 1024
 AND recovery_generation=btrim(recovery_generation)
 AND key_id ~ '^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$'
 AND principal_sha256 ~ '^[a-f0-9]{64}$' AND request_sha256 ~ '^[a-f0-9]{64}$'
 AND idempotency_key IS NOT NULL AND length(idempotency_key) BETWEEN 1 AND 128
 AND created_by=actor_id AND row_version>0)
) IS TRUE);
CREATE UNIQUE INDEX operation_token_retry_identity
 ON mt.operation_token(org_id,case_id,actor_id,idempotency_key) WHERE storage_version=1;

CREATE OR REPLACE FUNCTION mt.prevent_token_reuse() RETURNS trigger LANGUAGE plpgsql
SET search_path=pg_catalog,mt AS $$
DECLARE a mt.approval_request;
BEGIN
 IF TG_OP='UPDATE' AND OLD.storage_version<>1 THEN
  RAISE EXCEPTION 'legacy token has no verified binding' USING ERRCODE='23514'; END IF;
 IF NEW.storage_version<>1 OR NEW.case_id IS NULL THEN
  RAISE EXCEPTION 'versioned case token required' USING ERRCODE='23514'; END IF;
 IF NEW.actor_id IS DISTINCT FROM mt.actor_id() OR NEW.org_id IS DISTINCT FROM mt.org_id()
  OR NEW.case_id IS DISTINCT FROM mt.scope_case_id() OR NOT mt.can_access_case(NEW.case_id) THEN
  RAISE EXCEPTION 'token actor case binding invalid' USING ERRCODE='23514'; END IF;
 IF TG_OP='INSERT' THEN
  IF mt.scope_operation() IS DISTINCT FROM 'issueOperationToken' OR NEW.consumed_at IS NOT NULL
    OR NEW.row_version<>1 OR NEW.created_by IS DISTINCT FROM NEW.actor_id THEN
   RAISE EXCEPTION 'initial token state invalid' USING ERRCODE='23514'; END IF;
 ELSE
  IF OLD.consumed_at IS NOT NULL THEN
   RAISE EXCEPTION 'token already consumed' USING ERRCODE='55000'; END IF;
  IF (to_jsonb(OLD)-ARRAY['consumed_at','updated_at','row_version'])
    IS DISTINCT FROM (to_jsonb(NEW)-ARRAY['consumed_at','updated_at','row_version']) THEN
   RAISE EXCEPTION 'token binding is immutable' USING ERRCODE='55000'; END IF;
  IF mt.scope_operation() IS DISTINCT FROM NEW.action OR NEW.consumed_at IS NULL
    OR NEW.row_version<>OLD.row_version+1 THEN
   RAISE EXCEPTION 'exact action token transition required' USING ERRCODE='23514'; END IF;
  NEW.consumed_at:=clock_timestamp(); NEW.updated_at:=NEW.consumed_at;
 END IF;
 SELECT * INTO a FROM mt.approval_request WHERE approval_id=NEW.approval_id FOR SHARE;
 IF NOT FOUND OR a.org_id IS DISTINCT FROM NEW.org_id OR a.case_id IS DISTINCT FROM NEW.case_id
  OR a.object_type IS DISTINCT FROM NEW.object_type OR a.object_id IS DISTINCT FROM NEW.object_id
  OR a.object_version IS DISTINCT FROM NEW.object_version OR a.purpose IS DISTINCT FROM NEW.purpose
  OR a.policy_version IS DISTINCT FROM NEW.approval_policy_version
  OR a.row_version IS DISTINCT FROM NEW.approval_version OR a.state<>'APPROVED'
  OR a.expires_at IS NULL OR a.expires_at<=clock_timestamp() OR NEW.expires_at>a.expires_at THEN
  RAISE EXCEPTION 'current token approval binding invalid' USING ERRCODE='23514'; END IF;
 IF NEW.expires_at<=clock_timestamp() OR NEW.expires_at<=NEW.created_at
  OR NEW.created_at>clock_timestamp() THEN
  RAISE EXCEPTION 'token expired or creation time invalid' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION mt.prevent_token_reuse() FROM PUBLIC;
DROP TRIGGER token_use ON mt.operation_token;
CREATE TRIGGER token_use BEFORE INSERT OR UPDATE ON mt.operation_token
 FOR EACH ROW EXECUTE FUNCTION mt.prevent_token_reuse();

COMMENT ON COLUMN mt.operation_token.storage_version IS '0 preserves historical rows without fabricated bindings; only complete version1 rows can be issued or consumed';
COMMENT ON COLUMN mt.operation_token.action IS 'Exact server action; this migration supports the internal sealEvidence consumer boundary, not an exposed seal route';
COMMENT ON COLUMN mt.operation_token.object_type IS 'Exact approved object type; current case token is task-bound';
COMMENT ON COLUMN mt.operation_token.approval_version IS 'Approval row version verified at issue and consume';
COMMENT ON COLUMN mt.operation_token.approval_policy_version IS 'Business approval policy, distinct from permission policy';
COMMENT ON COLUMN mt.operation_token.permission_policy_version IS 'Permission snapshot version bound to the credential';
COMMENT ON COLUMN mt.operation_token.rule_version IS 'Explicit server-side purpose to action and TTL rule version';
COMMENT ON COLUMN mt.operation_token.recovery_generation IS 'Independent authorization recovery generation; old generations cannot be revived';
COMMENT ON COLUMN mt.operation_token.key_id IS 'Nonsecret identifier for a separately protected HMAC key; key material is never stored here';
COMMENT ON COLUMN mt.operation_token.principal_sha256 IS 'Issuer, subject and actor binding digest; not a bearer or identity credential';
COMMENT ON COLUMN mt.operation_token.request_sha256 IS 'Canonical validated request plus approved detail digest, binding the exact approval snapshot including run/result and decisions';
COMMENT ON COLUMN mt.operation_token.idempotency_key IS 'Actor and case-scoped issuance retry key; one record remains for expired or consumed credentials';
