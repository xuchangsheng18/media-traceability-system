-- I02 fixed plan observations only. No adoption management or task creation.
-- PG16 row locks require UPDATE ACL plus UPDATE USING policies. Keep lookup
-- SELECT-only; the separate CASE owner has only row_version column ACL and
-- restrictive WITH CHECK(false), so actual row mutations remain forbidden.
-- A non-super mt schema owner needs explicit administrator preparation:
-- both private roles precreated, then temporary SET-only / NOINHERIT / no-ADMIN
-- membership for that exact migration owner. The administrator must revoke
-- these temporary installation grants in a finally handoff afterwards.
-- This migration never RESET ROLE, escalates to session_user, or grants roles.
DO $$
DECLARE private_roles oid[]; migration_owner oid; is_super boolean; edge record;
BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='mt_task_plan_case_reader') THEN
  CREATE ROLE mt_task_plan_case_reader NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION;
 END IF;
 IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=ANY(ARRAY['mt_task_plan_lookup','mt_task_plan_case_reader']) AND
  (rolcanlogin OR rolinherit OR rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb OR rolreplication)) THEN
  RAISE EXCEPTION 'UNSAFE_TASK_PLAN_CASE_ROLE' USING ERRCODE='55000';
 END IF;
 SELECT array_agg(oid) INTO private_roles FROM pg_roles WHERE rolname=ANY(ARRAY['mt_task_plan_lookup','mt_task_plan_case_reader']);
 SELECT oid,rolsuper INTO STRICT migration_owner,is_super FROM pg_roles WHERE rolname=current_user;
 IF EXISTS(SELECT 1 FROM pg_auth_members WHERE member=ANY(private_roles)) THEN
  RAISE EXCEPTION 'UNSAFE_TASK_PLAN_PRIVATE_ROLE_INHERITANCE' USING ERRCODE='55000';
 END IF;
 FOR edge IN SELECT * FROM pg_auth_members WHERE roleid=ANY(private_roles) LOOP
  IF is_super OR edge.member<>migration_owner OR edge.inherit_option OR NOT edge.set_option OR edge.admin_option
   OR migration_owner<>(SELECT nspowner FROM pg_namespace WHERE nspname='mt')
   OR current_user='mt_runtime' OR pg_has_role(current_user,'mt_runtime','MEMBER') THEN
   RAISE EXCEPTION 'UNSAFE_TASK_PLAN_TEMPORARY_SET_MEMBERSHIP' USING ERRCODE='55000';
  END IF;
 END LOOP;
 IF NOT is_super AND (
  migration_owner<>(SELECT nspowner FROM pg_namespace WHERE nspname='mt')
  OR current_user='mt_runtime' OR pg_has_role(current_user,'mt_runtime','MEMBER')
  OR (SELECT count(*) FROM pg_auth_members WHERE roleid=ANY(private_roles) AND member=migration_owner)<>2
 ) THEN
  RAISE EXCEPTION 'TASK_PLAN_EXPLICIT_ADMIN_SET_PREPARATION_REQUIRED' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM pg_class WHERE relnamespace='mt'::regnamespace AND relowner='mt_task_plan_case_reader'::regrole) THEN
  RAISE EXCEPTION 'UNSAFE_TASK_PLAN_CASE_TABLE_OWNER' USING ERRCODE='55000';
 END IF;
END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA mt FROM mt_task_plan_case_reader;
GRANT USAGE ON SCHEMA mt TO mt_task_plan_case_reader;
CREATE OR REPLACE FUNCTION mt.scope_operation() RETURNS text LANGUAGE sql STABLE AS $$
SELECT CASE WHEN current_setting('app.operation_id',true) = ANY(ARRAY[
 'createTask','downloadAsset','createSource','listModels','listEvaluations','getReport','getAsset','listAssets','listTasks','issueOperationToken','sealEvidence',
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
 WHEN 'asset' THEN wanted_operation=ANY(ARRAY['createTask','downloadAsset','getAsset','listAssets','getTimeline'])
 WHEN 'cluster' THEN wanted_operation=ANY(ARRAY['getFirstSource','getPropagation'])
 WHEN 'evidence_package' THEN wanted_operation=ANY(ARRAY['requestApproval'])
 WHEN 'export' THEN wanted_operation=ANY(ARRAY['downloadAuditExport','getAuditExport','processAuditExportWork'])
 WHEN 'feedback' THEN wanted_operation=ANY(ARRAY['getFeedback','requestApproval'])
 WHEN 'import' THEN wanted_operation=ANY(ARRAY['getImport'])
 WHEN 'operation' THEN wanted_operation=ANY(ARRAY['createSource','listApprovals','listAuditEvents','listPendingReviews','listReviews','listSources','listAssets','listTasks','requestApproval'])
 WHEN 'policy' THEN wanted_operation=ANY(ARRAY['getPolicy','getPolicyDefinition'])
 WHEN 'report' THEN wanted_operation=ANY(ARRAY['getReport','requestApproval'])
 WHEN 'review' THEN wanted_operation=ANY(ARRAY['getReview','listReviews'])
 WHEN 'source' THEN wanted_operation=ANY(ARRAY['createImport','createUpload','getSource','syncSourceAuthorization'])
 WHEN 'task' THEN wanted_operation=ANY(ARRAY['cancelTask','cancelTaskWork','createReview','finishTaskNodeWork','getForensics','getReviewContext','getRiskFindings','getTask','getTaskEvidence','getTaskExecution','listPendingReviews','listTasks','listTaskEvents','listTaskNodes','requestApproval','issueOperationToken','sealEvidence','startTaskNodeWork'])
 WHEN 'upload' THEN wanted_operation=ANY(ARRAY['completeUpload','getUploadStatus','listUploadParts','putUploadPart','validateUploadWork'])
 WHEN 'user' THEN wanted_operation=ANY(ARRAY['createPolicy','getCurrentUser','listPolicies','listModels','listEvaluations'])
 WHEN 'model' THEN wanted_operation='listModels'
 WHEN 'model_evaluation' THEN wanted_operation='listEvaluations'
 ELSE false END,false)
$$;

GRANT EXECUTE ON FUNCTION mt.actor_id(),mt.org_id(),mt.actor_in_org(),mt.can_access_case(uuid),mt.scope_operation(),mt.scope_mode(),mt.scope_case_id(),mt.scope_allows_case(uuid),mt.task_plan_modules_valid(text[]) TO mt_task_plan_lookup,mt_task_plan_case_reader;
GRANT EXECUTE ON FUNCTION mt.hold_authorization_epoch() TO mt_task_plan_case_reader;
GRANT SELECT(singleton,epoch,policy_version,policy_sha256,recovery_generation) ON mt.authorization_epoch TO mt_task_plan_lookup;
GRANT SELECT(org_id,enabled,row_version) ON mt.organizations TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.organizations FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
CREATE POLICY task_create_lookup_read_guard ON mt.organizations AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
GRANT SELECT(org_id,enabled,row_version) ON mt.organizations TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.organizations FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
CREATE POLICY task_create_case_read_guard ON mt.organizations AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
GRANT SELECT(user_id,org_id,enabled,row_version) ON mt.users TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.users FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))) AND user_id=mt.actor_id());
CREATE POLICY task_create_lookup_read_guard ON mt.users AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))) AND user_id=mt.actor_id());
GRANT SELECT(user_id,org_id,enabled,row_version) ON mt.users TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.users FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())) AND user_id=mt.actor_id());
CREATE POLICY task_create_case_read_guard ON mt.users AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())) AND user_id=mt.actor_id());
GRANT SELECT(case_id,org_id,status,row_version) ON mt.cases TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.cases FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=cases.case_id))));
CREATE POLICY task_create_lookup_read_guard ON mt.cases AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=cases.case_id))));
GRANT SELECT(case_id,org_id,status,row_version) ON mt.cases TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.cases FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
CREATE POLICY task_create_case_read_guard ON mt.cases AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
GRANT SELECT(membership_id,org_id,case_id,user_id,revoked_at,expires_at,row_version) ON mt.case_membership TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.case_membership FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=case_membership.case_id))) AND user_id=mt.actor_id());
CREATE POLICY task_create_lookup_read_guard ON mt.case_membership AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=case_membership.case_id))) AND user_id=mt.actor_id());
GRANT SELECT(membership_id,org_id,case_id,user_id,revoked_at,expires_at,row_version) ON mt.case_membership TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.case_membership FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()) AND user_id=mt.actor_id());
CREATE POLICY task_create_case_read_guard ON mt.case_membership AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()) AND user_id=mt.actor_id());
GRANT SELECT(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,duration_ms,width,height,kind,mapping_version,state,created_at,row_version) ON mt.media_asset TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.media_asset FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND mt.can_access_case(case_id))));
CREATE POLICY task_create_lookup_read_guard ON mt.media_asset AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND mt.can_access_case(case_id))));
GRANT SELECT(asset_id,org_id,case_id,content_id,source_id,object_id,sha256,mime,size_bytes,duration_ms,width,height,kind,mapping_version,state,created_at,row_version) ON mt.media_asset TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.media_asset FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
CREATE POLICY task_create_case_read_guard ON mt.media_asset AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
GRANT SELECT(source_id,org_id,case_id,authorization_status,authorization_version,purpose,expires_at,row_version) ON mt.source_registry TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.source_registry FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.source_id=source_registry.source_id))));
CREATE POLICY task_create_lookup_read_guard ON mt.source_registry AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.source_id=source_registry.source_id))));
GRANT SELECT(source_id,org_id,case_id,authorization_status,authorization_version,purpose,expires_at,row_version) ON mt.source_registry TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.source_registry FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
CREATE POLICY task_create_case_read_guard ON mt.source_registry AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
GRANT SELECT(object_id,org_id,case_id,version_id,sha256,size_bytes) ON mt.object_version TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.object_version FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.object_id=object_version.object_id))));
CREATE POLICY task_create_lookup_read_guard ON mt.object_version AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.object_id=object_version.object_id))));
GRANT SELECT(object_id,org_id,case_id,version_id,sha256,size_bytes) ON mt.object_version TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.object_version FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
CREATE POLICY task_create_case_read_guard ON mt.object_version AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
GRANT SELECT(policy_id,org_id,kind,version,status,row_version) ON mt.policy_registry TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.policy_registry FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
CREATE POLICY task_create_lookup_read_guard ON mt.policy_registry AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
GRANT SELECT(policy_id,org_id,kind,version,status,row_version) ON mt.policy_registry TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.policy_registry FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
CREATE POLICY task_create_case_read_guard ON mt.policy_registry AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
GRANT SELECT(org_id,case_id,scene,policy_id,policy_version,modules,priority,revision_id,state,row_version) ON mt.task_plan_mapping_head TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.task_plan_mapping_head FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=task_plan_mapping_head.case_id))));
CREATE POLICY task_create_lookup_read_guard ON mt.task_plan_mapping_head AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=task_plan_mapping_head.case_id))));
GRANT SELECT(org_id,case_id,scene,policy_id,policy_version,modules,priority,revision_id,state,row_version) ON mt.task_plan_mapping_head TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.task_plan_mapping_head FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
CREATE POLICY task_create_case_read_guard ON mt.task_plan_mapping_head AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
GRANT SELECT(revision_id,org_id,case_id,mapping_id,mapping_version,authority_version,scene,modules,priority,policy_id,policy_kind,policy_version,policy_sha256,plan_id,plan_version,plan_sha256,capability_id,capability_version,capability_sha256,valid_from,valid_until,recovery_generation,validation_receipt_bytes,validation_receipt_sha256) ON mt.task_plan_mapping_revision TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.task_plan_mapping_revision FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=task_plan_mapping_revision.case_id))));
CREATE POLICY task_create_lookup_read_guard ON mt.task_plan_mapping_revision AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id() OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id) AND a.case_id=task_plan_mapping_revision.case_id))));
GRANT SELECT(revision_id,org_id,case_id,mapping_id,mapping_version,authority_version,scene,modules,priority,policy_id,policy_kind,policy_version,policy_sha256,plan_id,plan_version,plan_sha256,capability_id,capability_version,capability_sha256,valid_from,valid_until,recovery_generation,validation_receipt_bytes,validation_receipt_sha256) ON mt.task_plan_mapping_revision TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.task_plan_mapping_revision FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
CREATE POLICY task_create_case_read_guard ON mt.task_plan_mapping_revision AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id()));
GRANT SELECT(org_id,policy_id,policy_kind,policy_version,canonical_bytes,policy_sha256,schema_version,canonicalization_version) ON mt.task_policy_artifact TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.task_policy_artifact FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
CREATE POLICY task_create_lookup_read_guard ON mt.task_policy_artifact AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
GRANT SELECT(org_id,policy_id,policy_kind,policy_version,canonical_bytes,policy_sha256,schema_version,canonicalization_version) ON mt.task_policy_artifact TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.task_policy_artifact FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
CREATE POLICY task_create_case_read_guard ON mt.task_policy_artifact AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
GRANT SELECT(org_id,plan_id,plan_version,canonical_bytes,plan_sha256,schema_version,canonicalization_version) ON mt.task_plan_artifact TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.task_plan_artifact FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
CREATE POLICY task_create_lookup_read_guard ON mt.task_plan_artifact AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
GRANT SELECT(org_id,plan_id,plan_version,canonical_bytes,plan_sha256,schema_version,canonicalization_version) ON mt.task_plan_artifact TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.task_plan_artifact FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
CREATE POLICY task_create_case_read_guard ON mt.task_plan_artifact AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
GRANT SELECT(org_id,capability_id,capability_version,canonical_bytes,capability_sha256,schema_version,canonicalization_version) ON mt.task_capability_manifest TO mt_task_plan_lookup;
CREATE POLICY task_create_lookup_read ON mt.task_capability_manifest FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
CREATE POLICY task_create_lookup_read_guard ON mt.task_capability_manifest AS RESTRICTIVE FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()) OR (mt.scope_mode()='LOOKUP' AND current_setting('transaction_read_only')='on' AND current_setting('app.lookup_kind',true)='asset' AND EXISTS(SELECT 1 FROM mt.media_asset a WHERE a.asset_id=NULLIF(current_setting('app.lookup_id',true),'')::uuid AND a.org_id=mt.org_id() AND mt.can_access_case(a.case_id)))));
GRANT SELECT(org_id,capability_id,capability_version,canonical_bytes,capability_sha256,schema_version,canonicalization_version) ON mt.task_capability_manifest TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_read ON mt.task_capability_manifest FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
CREATE POLICY task_create_case_read_guard ON mt.task_capability_manifest AS RESTRICTIVE FOR SELECT TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id())));
GRANT UPDATE(row_version) ON mt.media_asset TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_lock ON mt.media_asset FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id())) WITH CHECK(false);
CREATE POLICY task_create_case_no_write ON mt.media_asset AS RESTRICTIVE FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id())) WITH CHECK(false);
GRANT UPDATE(row_version) ON mt.source_registry TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_lock ON mt.source_registry FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id())) WITH CHECK(false);
CREATE POLICY task_create_case_no_write ON mt.source_registry AS RESTRICTIVE FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id())) WITH CHECK(false);
GRANT UPDATE(row_version) ON mt.policy_registry TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_lock ON mt.policy_registry FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()))) WITH CHECK(false);
CREATE POLICY task_create_case_no_write ON mt.policy_registry AS RESTRICTIVE FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(mt.scope_case_id()))) WITH CHECK(false);
GRANT UPDATE(row_version) ON mt.task_plan_mapping_head TO mt_task_plan_case_reader;
CREATE POLICY task_create_case_lock ON mt.task_plan_mapping_head FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id())) WITH CHECK(false);
CREATE POLICY task_create_case_no_write ON mt.task_plan_mapping_head AS RESTRICTIVE FOR UPDATE TO mt_task_plan_case_reader USING(org_id=mt.org_id() AND mt.scope_operation()='createTask' AND mt.actor_in_org() AND (mt.scope_mode()='CASE' AND mt.scope_allows_case(case_id) AND case_id=mt.scope_case_id())) WITH CHECK(false);

-- RLS WITH CHECK is not evaluated for a zero-row UPDATE. Reject every
-- case-reader DML statement before any other statement trigger can bump epoch.
-- INVOKER preserves effective current_user; SELECT FOR SHARE fires no DML trigger.
CREATE FUNCTION mt.reject_task_plan_case_reader_dml() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,mt,pg_temp AS $$
BEGIN
 IF current_user='mt_task_plan_case_reader' THEN
  RAISE EXCEPTION 'TASK_PLAN_CASE_READER_DML_FORBIDDEN' USING ERRCODE='42501';
 END IF;
 RETURN NULL;
END
$$;
REVOKE ALL ON FUNCTION mt.reject_task_plan_case_reader_dml() FROM PUBLIC,mt_runtime,mt_task_plan_case_reader,mt_task_plan_lookup;
DO $$
DECLARE table_name text;
BEGIN
 FOREACH table_name IN ARRAY ARRAY['media_asset','source_registry','policy_registry','task_plan_mapping_head'] LOOP
  EXECUTE format('CREATE TRIGGER aaa_task_plan_case_reader_no_dml BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON mt.%I FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_task_plan_case_reader_dml()',table_name);
 END LOOP;
END
$$;

-- All head changes order before a held authorization epoch, including phantom
-- insertion of another policy-id head for the same externally supplied version.
-- This grants no management entry or write policy to a person/runtime role.
CREATE TRIGGER task_plan_head_epoch_before_change BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE
 ON mt.task_plan_mapping_head FOR EACH STATEMENT EXECUTE FUNCTION mt.bump_authorization_epoch();
CREATE FUNCTION mt.task_create_execution_plan(wanted_asset uuid,wanted_case uuid,wanted_scene text,wanted_policy_version text,wanted_modules text[],wanted_priority text,expected_revision uuid,expected_policy_sha256 text,expected_plan_sha256 text,expected_capability_sha256 text) RETURNS TABLE(revision_id uuid,head_row_version bigint,policy_bytes bytea,plan_bytes bytea,capability_bytes bytea,validation_receipt_bytes bytea,current_state_facts jsonb,valid_until timestamptz,recovery_generation text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
DECLARE
 v_head record; v_candidate record; v_revision record; v_policy record;
 v_asset record; v_source record; v_object record; v_user record; v_org record; v_case record;
 v_generation record; v_members jsonb; v_facts jsonb; v_execution record;
 v_policy_bytes bytea; v_plan_bytes bytea; v_capability_bytes bytea;
 v_capability jsonb; v_receipt jsonb; v_receipt_projection jsonb; v_refs jsonb;
BEGIN
 IF wanted_asset IS NULL OR wanted_asset='00000000-0000-0000-0000-000000000000'::uuid
 OR wanted_case IS NULL OR wanted_case='00000000-0000-0000-0000-000000000000'::uuid
 OR wanted_scene IS NULL OR wanted_scene<>ALL(ARRAY['accident_rumor','harmful_content','repost_tamper_trace'])
 OR wanted_policy_version IS NULL OR char_length(wanted_policy_version) NOT BETWEEN 1 AND 128
 OR wanted_priority IS NULL OR wanted_priority<>ALL(ARRAY['low','normal','high'])
 OR NOT mt.task_plan_modules_valid(wanted_modules)
 OR mt.scope_operation() IS DISTINCT FROM 'createTask' OR NOT mt.actor_in_org()
 THEN RETURN; END IF;
 IF mt.scope_mode() IS DISTINCT FROM 'CASE' OR mt.scope_case_id() IS DISTINCT FROM wanted_case
 OR current_setting('transaction_read_only')<>'off' OR NOT mt.can_access_case(wanted_case)
 OR expected_revision IS NULL OR expected_revision='00000000-0000-0000-0000-000000000000'::uuid
 OR expected_policy_sha256 IS NULL OR expected_policy_sha256 !~ '^[a-f0-9]{64}$'
 OR expected_plan_sha256 IS NULL OR expected_plan_sha256 !~ '^[a-f0-9]{64}$'
 OR expected_capability_sha256 IS NULL OR expected_capability_sha256 !~ '^[a-f0-9]{64}$'
 THEN RETURN; END IF;
 -- Epoch -> exact asset/source -> policy/head/materials. Never reverse this
 -- order relative to the existing ObjectFacts CASE reader and root fence.
 SELECT e.* INTO STRICT v_generation FROM mt.hold_authorization_epoch() e;
 SELECT h.org_id,h.case_id,h.scene,h.policy_id,h.policy_version,h.modules,h.priority,h.revision_id,h.state,h.row_version INTO STRICT v_candidate FROM mt.task_plan_mapping_head h WHERE h.org_id=mt.org_id() AND h.case_id=wanted_case AND h.scene=wanted_scene AND h.policy_version=wanted_policy_version AND h.modules=wanted_modules AND h.priority=wanted_priority AND h.state='ACTIVE';
 SELECT r.revision_id,r.org_id,r.case_id,r.mapping_id,r.mapping_version,r.authority_version,r.scene,r.modules,r.priority,r.policy_id,r.policy_kind,r.policy_version,r.policy_sha256,r.plan_id,r.plan_version,r.plan_sha256,r.capability_id,r.capability_version,r.capability_sha256,r.valid_from,r.valid_until,r.recovery_generation,r.validation_receipt_bytes,r.validation_receipt_sha256 INTO STRICT v_revision FROM mt.task_plan_mapping_revision r WHERE r.org_id=mt.org_id() AND r.case_id=wanted_case AND r.revision_id=v_candidate.revision_id;
 SELECT a.asset_id,a.org_id,a.case_id,a.content_id,a.source_id,a.object_id,a.sha256,a.mime,a.size_bytes,a.duration_ms,a.width,a.height,a.kind,a.mapping_version,a.state,a.created_at,a.row_version INTO STRICT v_asset FROM mt.media_asset a WHERE a.asset_id=wanted_asset AND a.org_id=mt.org_id() AND a.case_id=wanted_case FOR SHARE OF a;
 SELECT s.source_id,s.org_id,s.case_id,s.authorization_status,s.authorization_version,s.purpose,s.expires_at,s.row_version INTO STRICT v_source FROM mt.source_registry s WHERE s.source_id=v_asset.source_id AND s.org_id=mt.org_id() AND s.case_id=wanted_case FOR SHARE OF s;
 SELECT o.object_id,o.org_id,o.case_id,o.version_id,o.sha256,o.size_bytes INTO STRICT v_object FROM mt.object_version o WHERE o.object_id=v_asset.object_id AND o.org_id=mt.org_id() AND o.case_id=wanted_case;
 IF v_asset.sha256 IS DISTINCT FROM v_object.sha256 OR v_asset.size_bytes IS DISTINCT FROM v_object.size_bytes THEN RETURN; END IF;
 SELECT u.user_id,u.org_id,u.enabled,u.row_version INTO STRICT v_user FROM mt.users u WHERE u.user_id=mt.actor_id() AND u.org_id=mt.org_id() AND u.enabled;
 SELECT o.org_id,o.enabled,o.row_version INTO STRICT v_org FROM mt.organizations o WHERE o.org_id=mt.org_id() AND o.enabled;
 SELECT c.case_id,c.org_id,c.status,c.row_version INTO STRICT v_case FROM mt.cases c WHERE c.case_id=wanted_case AND c.org_id=mt.org_id();
 SELECT p.policy_id,p.org_id,p.kind,p.version,p.status,p.row_version INTO STRICT v_policy FROM mt.policy_registry p WHERE p.policy_id=v_revision.policy_id AND p.org_id=mt.org_id() AND p.kind=v_revision.policy_kind AND p.version=v_revision.policy_version FOR SHARE OF p;
 SELECT jsonb_agg(jsonb_build_object('membership_id',m.membership_id,'row_version',m.row_version,'expires_at',CASE WHEN m.expires_at IS NULL THEN NULL ELSE to_char(m.expires_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END) ORDER BY m.membership_id)
 INTO v_members FROM mt.case_membership m WHERE m.org_id=mt.org_id() AND m.case_id=wanted_case AND m.user_id=mt.actor_id() AND m.revoked_at IS NULL AND (m.expires_at IS NULL OR m.expires_at>clock_timestamp());
 IF v_members IS NULL THEN RETURN; END IF;
 SELECT h.org_id,h.case_id,h.scene,h.policy_id,h.policy_version,h.modules,h.priority,h.revision_id,h.state,h.row_version INTO STRICT v_head FROM mt.task_plan_mapping_head h WHERE h.org_id=mt.org_id() AND h.case_id=wanted_case AND h.scene=wanted_scene AND h.policy_version=wanted_policy_version AND h.modules=wanted_modules AND h.priority=wanted_priority AND h.state='ACTIVE' ORDER BY h.policy_id FOR SHARE OF h;
 IF v_head.revision_id IS DISTINCT FROM v_candidate.revision_id OR v_head.row_version IS DISTINCT FROM v_candidate.row_version
 OR v_head.revision_id IS DISTINCT FROM expected_revision
 OR v_revision.policy_sha256 IS DISTINCT FROM expected_policy_sha256
 OR v_revision.plan_sha256 IS DISTINCT FROM expected_plan_sha256
 OR v_revision.capability_sha256 IS DISTINCT FROM expected_capability_sha256
 THEN RETURN; END IF;
 IF NOT (v_revision.valid_from<=clock_timestamp() AND clock_timestamp()<v_revision.valid_until) THEN RETURN; END IF;
 SELECT p.canonical_bytes INTO STRICT v_policy_bytes FROM mt.task_policy_artifact p WHERE p.org_id=mt.org_id() AND p.policy_id=v_revision.policy_id AND p.policy_kind=v_revision.policy_kind AND p.policy_version=v_revision.policy_version AND p.policy_sha256=v_revision.policy_sha256;
 SELECT p.canonical_bytes INTO STRICT v_plan_bytes FROM mt.task_plan_artifact p WHERE p.org_id=mt.org_id() AND p.plan_id=v_revision.plan_id AND p.plan_version=v_revision.plan_version AND p.plan_sha256=v_revision.plan_sha256;
 SELECT c.canonical_bytes INTO STRICT v_capability_bytes FROM mt.task_capability_manifest c WHERE c.org_id=mt.org_id() AND c.capability_id=v_revision.capability_id AND c.capability_version=v_revision.capability_version AND c.capability_sha256=v_revision.capability_sha256;
 v_facts:=jsonb_build_object(
 'asset',jsonb_build_object('asset_id',v_asset.asset_id,'org_id',v_asset.org_id,'case_id',v_asset.case_id,'content_id',v_asset.content_id,'source_id',v_asset.source_id,'kind',v_asset.kind,'object_ref',jsonb_build_object('object_id',v_object.object_id,'version_id',v_object.version_id,'sha256',v_object.sha256),'mime',v_asset.mime,'size_bytes',v_asset.size_bytes,'duration_ms',v_asset.duration_ms,'width',v_asset.width,'height',v_asset.height,'state',v_asset.state,'version',v_asset.row_version,'created_at',to_char(v_asset.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'mapping_version',v_asset.mapping_version,'sha256',v_asset.sha256),
 'source',jsonb_build_object('source_id',v_source.source_id,'org_id',v_source.org_id,'case_id',v_source.case_id,'authorization_status',v_source.authorization_status,'authorization_version',v_source.authorization_version,'purpose',v_source.purpose,'expires_at',CASE WHEN v_source.expires_at IS NULL THEN NULL ELSE to_char(v_source.expires_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,'row_version',v_source.row_version),
 'policy',jsonb_build_object('policy_id',v_policy.policy_id,'kind',v_policy.kind,'version',v_policy.version,'status',v_policy.status,'row_version',v_policy.row_version),
 'case',jsonb_build_object('case_id',v_case.case_id,'status',v_case.status,'row_version',v_case.row_version),
 'memberships',v_members,
 'actor',jsonb_build_object('user_id',v_user.user_id,'org_id',v_user.org_id,'enabled',v_user.enabled,'row_version',v_user.row_version),
 'organization',jsonb_build_object('org_id',v_org.org_id,'enabled',v_org.enabled,'row_version',v_org.row_version),
 'head',jsonb_build_object('revision_id',v_head.revision_id,'state',v_head.state,'row_version',v_head.row_version),
 'generation',jsonb_build_object('database_oid',v_generation.database_oid,'epoch',v_generation.epoch,'policy_version',v_generation.policy_version,'policy_sha256',v_generation.policy_sha256,'recovery_generation',v_generation.recovery_generation));
 IF v_asset.state<>'VALID' OR v_source.authorization_status<>'verified' OR NOT ('analysis'=ANY(v_source.purpose))
 OR (v_source.expires_at IS NOT NULL AND v_source.expires_at<=clock_timestamp())
 OR v_generation.recovery_generation IS NULL OR v_generation.recovery_generation IS DISTINCT FROM v_revision.recovery_generation
 THEN RETURN; END IF;
 RETURN QUERY SELECT v_revision.revision_id,v_head.row_version,v_policy_bytes,v_plan_bytes,v_capability_bytes,v_revision.validation_receipt_bytes,v_facts,v_revision.valid_until,v_revision.recovery_generation;
EXCEPTION WHEN no_data_found OR too_many_rows OR invalid_text_representation OR character_not_in_repertoire THEN RETURN;
END
$$;
CREATE FUNCTION mt.task_create_plan_metadata(wanted_asset uuid,wanted_case uuid,wanted_scene text,wanted_policy_version text,wanted_modules text[],wanted_priority text) RETURNS TABLE(revision_id uuid,mapping_id text,mapping_version text,authority_version text,head_row_version bigint,policy_id uuid,policy_kind text,policy_version text,policy_sha256 text,plan_id text,plan_version text,plan_sha256 text,capability_id text,capability_version text,capability_sha256 text,valid_from timestamptz,valid_until timestamptz,recovery_generation text,validation_receipt jsonb,required_capability_refs jsonb,current_state_facts jsonb)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
DECLARE
 v_head record; v_candidate record; v_revision record; v_policy record;
 v_asset record; v_source record; v_object record; v_user record; v_org record; v_case record;
 v_generation record; v_members jsonb; v_facts jsonb; v_execution record;
 v_policy_bytes bytea; v_plan_bytes bytea; v_capability_bytes bytea;
 v_capability jsonb; v_receipt jsonb; v_receipt_projection jsonb; v_refs jsonb;
BEGIN
 IF wanted_asset IS NULL OR wanted_asset='00000000-0000-0000-0000-000000000000'::uuid
 OR wanted_case IS NULL OR wanted_case='00000000-0000-0000-0000-000000000000'::uuid
 OR wanted_scene IS NULL OR wanted_scene<>ALL(ARRAY['accident_rumor','harmful_content','repost_tamper_trace'])
 OR wanted_policy_version IS NULL OR char_length(wanted_policy_version) NOT BETWEEN 1 AND 128
 OR wanted_priority IS NULL OR wanted_priority<>ALL(ARRAY['low','normal','high'])
 OR NOT mt.task_plan_modules_valid(wanted_modules)
 OR mt.scope_operation() IS DISTINCT FROM 'createTask' OR NOT mt.actor_in_org()
 THEN RETURN; END IF;
 IF mt.scope_mode()='LOOKUP' THEN
  IF current_setting('transaction_read_only')<>'on' OR current_setting('app.lookup_kind',true) IS DISTINCT FROM 'asset'
   OR current_setting('app.lookup_id',true) IS DISTINCT FROM wanted_asset::text THEN RETURN; END IF;
 ELSIF mt.scope_mode()='CASE' THEN
  IF current_setting('transaction_read_only')<>'off' OR mt.scope_case_id() IS DISTINCT FROM wanted_case THEN RETURN; END IF;
 ELSE RETURN;
 END IF;
 IF NOT mt.can_access_case(wanted_case) THEN RETURN; END IF;
 SELECT h.org_id,h.case_id,h.scene,h.policy_id,h.policy_version,h.modules,h.priority,h.revision_id,h.state,h.row_version INTO STRICT v_candidate FROM mt.task_plan_mapping_head h WHERE h.org_id=mt.org_id() AND h.case_id=wanted_case AND h.scene=wanted_scene AND h.policy_version=wanted_policy_version AND h.modules=wanted_modules AND h.priority=wanted_priority AND h.state='ACTIVE';
 SELECT r.revision_id,r.org_id,r.case_id,r.mapping_id,r.mapping_version,r.authority_version,r.scene,r.modules,r.priority,r.policy_id,r.policy_kind,r.policy_version,r.policy_sha256,r.plan_id,r.plan_version,r.plan_sha256,r.capability_id,r.capability_version,r.capability_sha256,r.valid_from,r.valid_until,r.recovery_generation,r.validation_receipt_bytes,r.validation_receipt_sha256 INTO STRICT v_revision FROM mt.task_plan_mapping_revision r WHERE r.org_id=mt.org_id() AND r.case_id=wanted_case AND r.revision_id=v_candidate.revision_id;
 IF NOT (v_revision.valid_from<=clock_timestamp() AND clock_timestamp()<v_revision.valid_until) THEN RETURN; END IF;
 v_head:=v_candidate;
 IF mt.scope_mode()='CASE' THEN
  -- Lookup owner itself has no UPDATE ACL. The only CASE-lock delegate is the
  -- second fixed function, whose separate nonowner role cannot perform DML.
  SELECT e.* INTO STRICT v_execution FROM mt.task_create_execution_plan(wanted_asset,wanted_case,wanted_scene,wanted_policy_version,wanted_modules,wanted_priority,v_revision.revision_id,v_revision.policy_sha256,v_revision.plan_sha256,v_revision.capability_sha256) e;
  IF v_execution.revision_id IS DISTINCT FROM v_revision.revision_id OR v_execution.head_row_version IS DISTINCT FROM v_candidate.row_version
   OR v_execution.valid_until IS DISTINCT FROM v_revision.valid_until OR v_execution.recovery_generation IS DISTINCT FROM v_revision.recovery_generation THEN RETURN; END IF;
  v_facts:=v_execution.current_state_facts;
 ELSE
  -- No row-lock or body-function call occurs in this readonly branch.
 SELECT a.asset_id,a.org_id,a.case_id,a.content_id,a.source_id,a.object_id,a.sha256,a.mime,a.size_bytes,a.duration_ms,a.width,a.height,a.kind,a.mapping_version,a.state,a.created_at,a.row_version INTO STRICT v_asset FROM mt.media_asset a WHERE a.asset_id=wanted_asset AND a.org_id=mt.org_id() AND a.case_id=wanted_case;
 SELECT s.source_id,s.org_id,s.case_id,s.authorization_status,s.authorization_version,s.purpose,s.expires_at,s.row_version INTO STRICT v_source FROM mt.source_registry s WHERE s.source_id=v_asset.source_id AND s.org_id=mt.org_id() AND s.case_id=wanted_case;
 SELECT o.object_id,o.org_id,o.case_id,o.version_id,o.sha256,o.size_bytes INTO STRICT v_object FROM mt.object_version o WHERE o.object_id=v_asset.object_id AND o.org_id=mt.org_id() AND o.case_id=wanted_case;
 IF v_asset.sha256 IS DISTINCT FROM v_object.sha256 OR v_asset.size_bytes IS DISTINCT FROM v_object.size_bytes THEN RETURN; END IF;
 SELECT u.user_id,u.org_id,u.enabled,u.row_version INTO STRICT v_user FROM mt.users u WHERE u.user_id=mt.actor_id() AND u.org_id=mt.org_id() AND u.enabled;
 SELECT o.org_id,o.enabled,o.row_version INTO STRICT v_org FROM mt.organizations o WHERE o.org_id=mt.org_id() AND o.enabled;
 SELECT c.case_id,c.org_id,c.status,c.row_version INTO STRICT v_case FROM mt.cases c WHERE c.case_id=wanted_case AND c.org_id=mt.org_id();
 SELECT p.policy_id,p.org_id,p.kind,p.version,p.status,p.row_version INTO STRICT v_policy FROM mt.policy_registry p WHERE p.policy_id=v_revision.policy_id AND p.org_id=mt.org_id() AND p.kind=v_revision.policy_kind AND p.version=v_revision.policy_version;
 SELECT jsonb_agg(jsonb_build_object('membership_id',m.membership_id,'row_version',m.row_version,'expires_at',CASE WHEN m.expires_at IS NULL THEN NULL ELSE to_char(m.expires_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END) ORDER BY m.membership_id)
 INTO v_members FROM mt.case_membership m WHERE m.org_id=mt.org_id() AND m.case_id=wanted_case AND m.user_id=mt.actor_id() AND m.revoked_at IS NULL AND (m.expires_at IS NULL OR m.expires_at>clock_timestamp());
 IF v_members IS NULL THEN RETURN; END IF;
 SELECT e.epoch,d.oid AS database_oid,e.policy_version,e.policy_sha256,e.recovery_generation INTO STRICT v_generation FROM mt.authorization_epoch e JOIN pg_catalog.pg_database d ON d.datname=current_database() WHERE e.singleton;
 v_facts:=jsonb_build_object(
 'asset',jsonb_build_object('asset_id',v_asset.asset_id,'org_id',v_asset.org_id,'case_id',v_asset.case_id,'content_id',v_asset.content_id,'source_id',v_asset.source_id,'kind',v_asset.kind,'object_ref',jsonb_build_object('object_id',v_object.object_id,'version_id',v_object.version_id,'sha256',v_object.sha256),'mime',v_asset.mime,'size_bytes',v_asset.size_bytes,'duration_ms',v_asset.duration_ms,'width',v_asset.width,'height',v_asset.height,'state',v_asset.state,'version',v_asset.row_version,'created_at',to_char(v_asset.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'mapping_version',v_asset.mapping_version,'sha256',v_asset.sha256),
 'source',jsonb_build_object('source_id',v_source.source_id,'org_id',v_source.org_id,'case_id',v_source.case_id,'authorization_status',v_source.authorization_status,'authorization_version',v_source.authorization_version,'purpose',v_source.purpose,'expires_at',CASE WHEN v_source.expires_at IS NULL THEN NULL ELSE to_char(v_source.expires_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,'row_version',v_source.row_version),
 'policy',jsonb_build_object('policy_id',v_policy.policy_id,'kind',v_policy.kind,'version',v_policy.version,'status',v_policy.status,'row_version',v_policy.row_version),
 'case',jsonb_build_object('case_id',v_case.case_id,'status',v_case.status,'row_version',v_case.row_version),
 'memberships',v_members,
 'actor',jsonb_build_object('user_id',v_user.user_id,'org_id',v_user.org_id,'enabled',v_user.enabled,'row_version',v_user.row_version),
 'organization',jsonb_build_object('org_id',v_org.org_id,'enabled',v_org.enabled,'row_version',v_org.row_version),
 'head',jsonb_build_object('revision_id',v_head.revision_id,'state',v_head.state,'row_version',v_head.row_version),
 'generation',jsonb_build_object('database_oid',v_generation.database_oid,'epoch',v_generation.epoch,'policy_version',v_generation.policy_version,'policy_sha256',v_generation.policy_sha256,'recovery_generation',v_generation.recovery_generation));
 END IF;
 SELECT c.canonical_bytes INTO STRICT v_capability_bytes FROM mt.task_capability_manifest c WHERE c.org_id=mt.org_id() AND c.capability_id=v_revision.capability_id AND c.capability_version=v_revision.capability_version AND c.capability_sha256=v_revision.capability_sha256;
 IF NOT (convert_from(v_capability_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS)
 OR NOT (convert_from(v_revision.validation_receipt_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN RETURN; END IF;
 v_capability:=convert_from(v_capability_bytes,'UTF8')::jsonb;
 v_receipt:=convert_from(v_revision.validation_receipt_bytes,'UTF8')::jsonb;
 IF v_capability->>'schema_id' IS DISTINCT FROM 'urn:media-trace:task-capability-manifest:1.0.0'
 OR v_capability->>'capability_id' IS DISTINCT FROM v_revision.capability_id
 OR v_capability->>'capability_version' IS DISTINCT FROM v_revision.capability_version
 OR jsonb_typeof(v_capability->'handlers') IS DISTINCT FROM 'array' THEN RETURN; END IF;
 v_refs:=jsonb_build_object('capability_id',v_revision.capability_id,'capability_version',v_revision.capability_version,'capability_sha256',v_revision.capability_sha256,'handlers',v_capability->'handlers');
 -- Original raw receipt SHA is retained. These nullable string projections are
 -- observations only; no validator/provider or semantic licence is invented.
 v_receipt_projection:=jsonb_build_object('sha256',v_revision.validation_receipt_sha256,
 'validator_id',CASE WHEN jsonb_typeof(v_receipt->'validator_id')='string' AND char_length(v_receipt->>'validator_id') BETWEEN 1 AND 128 THEN v_receipt->>'validator_id' ELSE NULL END,
 'validator_version',CASE WHEN jsonb_typeof(v_receipt->'validator_version')='string' AND char_length(v_receipt->>'validator_version') BETWEEN 1 AND 128 THEN v_receipt->>'validator_version' ELSE NULL END,
 'schema_id',CASE WHEN jsonb_typeof(v_receipt->'schema_id')='string' AND char_length(v_receipt->>'schema_id') BETWEEN 1 AND 128 THEN v_receipt->>'schema_id' ELSE NULL END,
 'schema_version',CASE WHEN jsonb_typeof(v_receipt->'schema_version')='string' AND char_length(v_receipt->>'schema_version') BETWEEN 1 AND 128 THEN v_receipt->>'schema_version' ELSE NULL END);
 IF NOT (v_revision.valid_from<=clock_timestamp() AND clock_timestamp()<v_revision.valid_until) THEN RETURN; END IF;
 IF mt.scope_mode()='CASE' AND (
  v_facts->'source'->>'authorization_status' IS DISTINCT FROM 'verified'
  OR NOT (v_facts->'source'->'purpose' ? 'analysis')
  OR (v_facts->'source'->>'expires_at' IS NOT NULL
      AND (v_facts->'source'->>'expires_at')::timestamptz<=clock_timestamp())
 ) THEN RETURN; END IF;
 RETURN QUERY SELECT v_revision.revision_id,v_revision.mapping_id,v_revision.mapping_version,v_revision.authority_version,v_head.row_version,v_revision.policy_id,v_revision.policy_kind,v_revision.policy_version,v_revision.policy_sha256,v_revision.plan_id,v_revision.plan_version,v_revision.plan_sha256,v_revision.capability_id,v_revision.capability_version,v_revision.capability_sha256,v_revision.valid_from,v_revision.valid_until,v_revision.recovery_generation,v_receipt_projection,v_refs,v_facts;
EXCEPTION WHEN no_data_found OR too_many_rows OR invalid_text_representation OR character_not_in_repertoire THEN RETURN;
END
$$;
REVOKE ALL ON FUNCTION mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text),mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text) FROM PUBLIC;
-- Finish owner-bound ACL/comments before transferring ownership; the explicit
-- temporary installer memberships have SET only and never INHERIT privileges.
GRANT EXECUTE ON FUNCTION mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text) TO mt_runtime,mt_task_plan_lookup;
GRANT EXECUTE ON FUNCTION mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text) TO mt_runtime;
COMMENT ON FUNCTION mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text) IS 'CASE-only fixed exact-revision material read under a restricted non-tableowner; column UPDATE ACL is row-lock prerequisite; INVOKER statement guard forbids even zero-row DML and restrictive WITH CHECK(false) adds row defence';
COMMENT ON FUNCTION mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text) IS 'Readonly exact-asset LOOKUP returns bounded projections, CASE delegates locking to fixed body reader; no Proof/ALLOW, adoption or handler licence is established';
GRANT CREATE ON SCHEMA mt TO mt_task_plan_lookup,mt_task_plan_case_reader;
ALTER FUNCTION mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text) OWNER TO mt_task_plan_case_reader;
ALTER FUNCTION mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text) OWNER TO mt_task_plan_lookup;
REVOKE CREATE ON SCHEMA mt FROM mt_task_plan_lookup,mt_task_plan_case_reader;
