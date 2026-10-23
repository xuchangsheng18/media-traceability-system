-- Persisted report metadata only; no role grants, table changes or generated artifacts.
-- Preserve 0012 operation/lookup behavior and function ACLs; add only getReport.
CREATE OR REPLACE FUNCTION mt.scope_operation() RETURNS text LANGUAGE sql STABLE AS $$
SELECT CASE WHEN current_setting('app.operation_id',true) = ANY(ARRAY[
 'getReport','getAsset','listAssets','listTasks','issueOperationToken','sealEvidence',
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
 WHEN 'report' THEN wanted_operation=ANY(ARRAY['getReport','requestApproval'])
 WHEN 'review' THEN wanted_operation=ANY(ARRAY['getReview','listReviews'])
 WHEN 'source' THEN wanted_operation=ANY(ARRAY['createImport','createUpload','getSource','syncSourceAuthorization'])
 WHEN 'task' THEN wanted_operation=ANY(ARRAY['cancelTask','cancelTaskWork','createReview','finishTaskNodeWork','getForensics','getReviewContext','getRiskFindings','getTask','getTaskEvidence','getTaskExecution','listPendingReviews','listTasks','listTaskEvents','listTaskNodes','requestApproval','issueOperationToken','sealEvidence','startTaskNodeWork'])
 WHEN 'upload' THEN wanted_operation=ANY(ARRAY['completeUpload','getUploadStatus','listUploadParts','putUploadPart','validateUploadWork'])
 WHEN 'user' THEN wanted_operation=ANY(ARRAY['createPolicy','getCurrentUser','listPolicies'])
 ELSE false END,false)
$$;

-- Exact report source metadata extends the existing checksum-bound function.
CREATE OR REPLACE FUNCTION mt.lookup_scope_metadata(wanted_kind text,wanted_id uuid) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,mt AS $$
DECLARE
 table_name text; key_name text; columns text[]; raw jsonb; item jsonb; case_value uuid;
 member_rows jsonb := '[]'; related jsonb := '[]'; source_rows jsonb := '[]'; source_ids uuid[] := '{}';
 row_scope text; locking boolean := mt.scope_mode() IN ('CASE','ORGANIZATION'); suffix text; result jsonb;
BEGIN
 IF wanted_id IS NULL OR wanted_id='00000000-0000-0000-0000-000000000000'::uuid
  OR mt.scope_mode() IS NULL OR NOT mt.actor_in_org() THEN RETURN NULL; END IF;
 IF mt.scope_mode()='LOOKUP' AND (
   current_setting('transaction_read_only')<>'on'
   OR current_setting('app.lookup_kind',true) IS DISTINCT FROM wanted_kind
   OR current_setting('app.lookup_id',true) IS DISTINCT FROM wanted_id::text) THEN RETURN NULL; END IF;
 CASE wanted_kind
 WHEN 'approval' THEN table_name:='approval_request';key_name:='approval_id';columns:=ARRAY['object_type','object_id','object_version','purpose','requested_by','state','expires_at','policy_version','run_version','result_version'];
 WHEN 'review' THEN table_name:='review_record';key_name:='review_id';columns:=ARRAY['task_id','run_version','result_version','reviewer_id','review_version','policy_version'];
 WHEN 'export' THEN table_name:='audit_export';key_name:='export_id';columns:=ARRAY['approval_id','purpose','state','start_at','end_at'];
 WHEN 'feedback' THEN table_name:='feedback_request';key_name:='feedback_id';columns:=ARRAY['finding_id','approval_id','purpose','state','label_version'];
 WHEN 'source' THEN table_name:='source_registry';key_name:='source_id';columns:=ARRAY['authorization_status','authorization_version','purpose','expires_at'];
 WHEN 'import' THEN table_name:='import_job';key_name:='import_id';columns:=ARRAY['state','requested_count'];
 WHEN 'task' THEN table_name:='analysis_task';key_name:='task_id';columns:=ARRAY['asset_id','run_version','result_version','state','policy_version'];
 WHEN 'asset' THEN table_name:='media_asset';key_name:='asset_id';columns:=ARRAY['source_id','parent_asset_id','mapping_version','state'];
 WHEN 'cluster' THEN table_name:='content_cluster';key_name:='cluster_id';columns:=ARRAY['scope','policy_version','status'];
 WHEN 'upload' THEN table_name:='upload_session';key_name:='upload_id';columns:=ARRAY['source_id','owner_id','asset_id','state','expires_at'];
 WHEN 'policy' THEN table_name:='policy_registry';key_name:='policy_id';columns:=ARRAY['kind','version','status','approval_id'];
 WHEN 'report' THEN table_name:='report';key_name:='report_id';columns:=ARRAY['task_id','run_version','result_version','version','approval_id','state'];
 WHEN 'evidence_package' THEN table_name:='evidence_package';key_name:='package_id';columns:=ARRAY['task_id','run_version','result_version','version','approval_id','state'];
 WHEN 'operation' THEN table_name:='cases';key_name:='case_id';columns:=ARRAY['status'];
 WHEN 'user' THEN table_name:='users';key_name:='user_id';columns:=ARRAY['enabled'];
 ELSE RETURN NULL;
 END CASE;
 IF NOT mt.scope_lookup_kind_allowed(wanted_kind,mt.scope_operation()) THEN RETURN NULL; END IF;
 IF wanted_kind='user' AND wanted_id<>mt.actor_id() THEN RETURN NULL; END IF;
 suffix := CASE WHEN locking AND wanted_kind NOT IN ('review','evidence_package') THEN ' FOR SHARE' ELSE '' END;
 row_scope := CASE WHEN wanted_kind IN ('policy','user') OR mt.scope_mode()='LOOKUP' THEN ''
  WHEN mt.scope_mode()='CASE' THEN ' AND case_id=mt.scope_case_id()'
  ELSE ' AND case_id IS NULL' END;
 -- table and key are chosen solely above; the caller cannot supply an SQL identifier.
 EXECUTE format('SELECT to_jsonb(t) FROM mt.%I t WHERE %I=$1 AND org_id=mt.org_id()%s%s',table_name,key_name,row_scope,suffix)
  INTO raw USING wanted_id;
 IF raw IS NULL THEN RETURN NULL; END IF;
 case_value := NULLIF(raw->>'case_id','')::uuid;
 IF case_value IS NOT NULL AND NOT mt.can_access_case(case_value) THEN RETURN NULL; END IF;
 IF mt.scope_mode()='CASE' AND case_value IS NOT NULL AND case_value IS DISTINCT FROM mt.scope_case_id() THEN RETURN NULL; END IF;
 IF mt.scope_mode()='ORGANIZATION' AND case_value IS NOT NULL THEN RETURN NULL; END IF;
 columns := columns || ARRAY[key_name,'org_id','row_version','created_by'];
 IF wanted_kind NOT IN ('policy','user') THEN columns := columns || ARRAY['case_id']; END IF;
 SELECT jsonb_object_agg(k,v) INTO item FROM jsonb_each(raw) f(k,v) WHERE k=ANY(columns);
 item := item || jsonb_build_object('_row_sha256',encode(sha256(convert_to(raw::text,'UTF8')),'hex'));
 IF case_value IS NOT NULL THEN
  SELECT coalesce(jsonb_agg(jsonb_build_object('membership_id',m.membership_id,'row_version',m.row_version,
   'expires_at',m.expires_at,'case_version',c.row_version,'status',c.status) ORDER BY m.membership_id),'[]')
   INTO member_rows FROM mt.case_membership m JOIN mt.cases c ON c.case_id=m.case_id AND c.org_id=m.org_id
   WHERE m.case_id=case_value AND m.org_id=mt.org_id() AND m.user_id=mt.actor_id() AND m.revoked_at IS NULL
    AND (m.expires_at IS NULL OR m.expires_at>statement_timestamp());
  IF member_rows='[]'::jsonb THEN RETURN NULL; END IF;
 END IF;
 IF wanted_kind='source' THEN source_ids:=ARRAY[wanted_id];
 ELSIF raw->>'source_id' IS NOT NULL THEN source_ids:=ARRAY[(raw->>'source_id')::uuid];
 ELSIF raw->>'asset_id' IS NOT NULL THEN
  IF locking THEN PERFORM 1 FROM mt.media_asset WHERE asset_id=(raw->>'asset_id')::uuid AND org_id=mt.org_id() AND case_id=case_value FOR SHARE; END IF;
  SELECT array_agg(source_id) INTO source_ids FROM mt.media_asset WHERE asset_id=(raw->>'asset_id')::uuid AND org_id=mt.org_id() AND case_id=case_value;
 ELSIF wanted_kind='import' THEN
  IF locking THEN PERFORM 1 FROM mt.import_item WHERE import_id=wanted_id AND org_id=mt.org_id() AND case_id=case_value FOR SHARE; END IF;
  SELECT coalesce(jsonb_agg(jsonb_build_object('item_id',item_id,'ordinal',ordinal,'source_id',source_id,'row_version',row_version) ORDER BY ordinal),'[]'),array_agg(source_id ORDER BY ordinal)
   INTO related,source_ids FROM mt.import_item WHERE import_id=wanted_id AND org_id=mt.org_id() AND case_id=case_value;
 ELSIF wanted_kind='review' THEN
  IF locking THEN PERFORM 1 FROM mt.analysis_task t JOIN mt.media_asset a ON a.asset_id=t.asset_id AND a.org_id=t.org_id AND a.case_id=t.case_id WHERE t.task_id=(raw->>'task_id')::uuid AND t.org_id=mt.org_id() AND t.case_id=case_value FOR SHARE OF t,a; END IF;
  SELECT coalesce(jsonb_agg(jsonb_build_object('task_id',t.task_id,'task_version',t.row_version,'asset_id',a.asset_id,'asset_version',a.row_version,'source_id',a.source_id)),'[]'),array_agg(a.source_id)
   INTO related,source_ids FROM mt.analysis_task t JOIN mt.media_asset a ON a.asset_id=t.asset_id AND a.org_id=t.org_id AND a.case_id=t.case_id WHERE t.task_id=(raw->>'task_id')::uuid AND t.org_id=mt.org_id() AND t.case_id=case_value;
 ELSIF wanted_kind='report' AND mt.scope_operation()='getReport' THEN
  -- Include every referenced evidence source, not only the task's primary source.
  -- No object payload, storage path, text or result snapshot is disclosed here.
  IF locking THEN
   PERFORM 1 FROM mt.analysis_task t JOIN mt.media_asset a
    ON a.asset_id=t.asset_id AND a.org_id=t.org_id AND a.case_id=t.case_id
    WHERE t.task_id=(raw->>'task_id')::uuid AND t.org_id=mt.org_id() AND t.case_id=case_value FOR SHARE OF t,a;
   PERFORM 1 FROM mt.media_asset a WHERE a.org_id=mt.org_id() AND a.case_id=case_value
    AND a.asset_id IN (SELECT e.asset_id FROM mt.report_evidence r JOIN mt.evidence_item e
     ON e.evidence_id=r.evidence_id AND e.org_id=r.org_id AND e.case_id=r.case_id
     WHERE r.report_id=wanted_id AND r.org_id=mt.org_id() AND r.case_id=case_value)
    ORDER BY a.asset_id FOR SHARE;
  END IF;
  SELECT coalesce(jsonb_agg(v.metadata ORDER BY v.order_key),'[]'),array_agg(v.source_id ORDER BY v.order_key)
   INTO related,source_ids FROM (
    SELECT 'task:'||t.task_id::text AS order_key,a.source_id,
     jsonb_build_object('task_id',t.task_id,'task_version',t.row_version,'asset_id',a.asset_id,
      'asset_version',a.row_version,'source_id',a.source_id) AS metadata
     FROM mt.analysis_task t JOIN mt.media_asset a
      ON a.asset_id=t.asset_id AND a.org_id=t.org_id AND a.case_id=t.case_id
     WHERE t.task_id=(raw->>'task_id')::uuid AND t.org_id=mt.org_id() AND t.case_id=case_value
    UNION ALL
    SELECT 'evidence:'||r.link_id::text,a.source_id,
     jsonb_build_object('link_id',r.link_id,'link_version',r.row_version,'evidence_id',e.evidence_id,
      'evidence_version',e.row_version,'task_id',e.task_id,'run_version',e.run_version,
      'result_version',e.result_version,'asset_id',a.asset_id,'asset_version',a.row_version,'source_id',a.source_id)
     FROM mt.report_evidence r JOIN mt.evidence_item e
      ON e.evidence_id=r.evidence_id AND e.org_id=r.org_id AND e.case_id=r.case_id
     JOIN mt.media_asset a ON a.asset_id=e.asset_id AND a.org_id=e.org_id AND a.case_id=e.case_id
     WHERE r.report_id=wanted_id AND r.org_id=mt.org_id() AND r.case_id=case_value
   ) v;
 ELSIF wanted_kind='cluster' THEN
  IF locking THEN PERFORM 1 FROM mt.cluster_member m JOIN mt.media_asset a ON a.asset_id=m.asset_id AND a.org_id=m.org_id AND a.case_id=m.case_id WHERE m.cluster_id=wanted_id AND m.org_id=mt.org_id() AND m.case_id=case_value FOR SHARE OF a; END IF;
  SELECT coalesce(jsonb_agg(jsonb_build_object('member_id',m.member_id,'member_version',m.row_version,'asset_id',a.asset_id,'asset_version',a.row_version,'source_id',a.source_id) ORDER BY m.member_id),'[]'),array_agg(a.source_id)
   INTO related,source_ids FROM mt.cluster_member m JOIN mt.media_asset a ON a.asset_id=m.asset_id AND a.org_id=m.org_id AND a.case_id=m.case_id WHERE m.cluster_id=wanted_id AND m.org_id=mt.org_id() AND m.case_id=case_value;
 END IF;
 IF locking THEN PERFORM 1 FROM mt.source_registry WHERE org_id=mt.org_id() AND case_id=case_value AND source_id=ANY(source_ids) ORDER BY source_id FOR SHARE; END IF;
 SELECT coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'org_id',org_id,'case_id',case_id,
   'authorization_status',authorization_status,'authorization_version',authorization_version,
   'purpose',purpose,'expires_at',expires_at,'row_version',row_version) ORDER BY source_id),'[]')
  INTO source_rows FROM mt.source_registry WHERE org_id=mt.org_id() AND case_id=case_value AND source_id=ANY(source_ids);
 IF (SELECT count(DISTINCT v) FROM unnest(source_ids) v)<>jsonb_array_length(source_rows) THEN RETURN NULL; END IF;
 result := jsonb_build_object('record',item,'memberships',member_rows,'related',related,'sources',source_rows,'same_org',true);
 RETURN result;
END
$$;
REVOKE ALL ON FUNCTION mt.lookup_scope_metadata(text,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.lookup_scope_metadata(text,uuid) TO mt_runtime;
