-- Current catalog reads only; no role grants or business table changes.
-- Extend both fixed operation and lookup registries; preserve all existing entries.
CREATE OR REPLACE FUNCTION mt.scope_operation() RETURNS text LANGUAGE sql STABLE AS $$
SELECT CASE WHEN current_setting('app.operation_id',true) = ANY(ARRAY[
 'getAsset','listAssets','listTasks','issueOperationToken','sealEvidence',
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
 WHEN 'asset' THEN wanted_operation=ANY(ARRAY['getAsset','listAssets','getTimeline'])
 WHEN 'cluster' THEN wanted_operation=ANY(ARRAY['getFirstSource','getPropagation'])
 WHEN 'evidence_package' THEN wanted_operation=ANY(ARRAY['requestApproval'])
 WHEN 'export' THEN wanted_operation=ANY(ARRAY['downloadAuditExport','getAuditExport','processAuditExportWork'])
 WHEN 'feedback' THEN wanted_operation=ANY(ARRAY['getFeedback','requestApproval'])
 WHEN 'import' THEN wanted_operation=ANY(ARRAY['getImport'])
 WHEN 'operation' THEN wanted_operation=ANY(ARRAY['listApprovals','listAuditEvents','listPendingReviews','listReviews','listSources','listAssets','listTasks','requestApproval'])
 WHEN 'policy' THEN wanted_operation=ANY(ARRAY['getPolicy','getPolicyDefinition'])
 WHEN 'report' THEN wanted_operation=ANY(ARRAY['requestApproval'])
 WHEN 'review' THEN wanted_operation=ANY(ARRAY['getReview','listReviews'])
 WHEN 'source' THEN wanted_operation=ANY(ARRAY['createImport','createUpload','getSource','syncSourceAuthorization'])
 WHEN 'task' THEN wanted_operation=ANY(ARRAY['cancelTask','cancelTaskWork','createReview','finishTaskNodeWork','getForensics','getReviewContext','getRiskFindings','getTask','getTaskEvidence','getTaskExecution','listPendingReviews','listTasks','listTaskEvents','listTaskNodes','requestApproval','issueOperationToken','sealEvidence','startTaskNodeWork'])
 WHEN 'upload' THEN wanted_operation=ANY(ARRAY['completeUpload','getUploadStatus','listUploadParts','putUploadPart','validateUploadWork'])
 WHEN 'user' THEN wanted_operation=ANY(ARRAY['createPolicy','getCurrentUser','listPolicies'])
 ELSE false END,false)
$$;
