-- Additive upgrade. Keep the 0001 and 0002 bytes and their ledger digests unchanged.
-- No seed approval, authority, production rule, model, or sensitive data.
CREATE FUNCTION mt.validate_control_link() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE a mt.approval_request; r mt.review_record; e mt.evidence_item;
BEGIN
 IF TG_TABLE_NAME = 'approval_decision' THEN
  SELECT * INTO a FROM mt.approval_request WHERE approval_id=NEW.approval_id;
  IF a.org_id IS DISTINCT FROM NEW.org_id OR a.case_id IS DISTINCT FROM NEW.case_id
   OR a.policy_version IS DISTINCT FROM NEW.policy_version
   OR NOT EXISTS(SELECT 1 FROM mt.users WHERE user_id=NEW.decision_actor_id AND org_id=NEW.org_id AND enabled)
  THEN RAISE EXCEPTION 'approval decision authority binding mismatch' USING ERRCODE='23514'; END IF;
 ELSIF TG_TABLE_NAME = 'review_evidence' THEN
  SELECT * INTO r FROM mt.review_record WHERE case_id=NEW.case_id AND review_id=NEW.review_id;
  SELECT * INTO e FROM mt.evidence_item WHERE case_id=NEW.case_id AND evidence_id=NEW.evidence_id;
  IF r.task_id IS DISTINCT FROM e.task_id OR r.run_version IS DISTINCT FROM e.run_version
   OR r.result_version IS DISTINCT FROM e.result_version OR r.org_id IS DISTINCT FROM NEW.org_id
   OR e.org_id IS DISTINCT FROM NEW.org_id
  THEN RAISE EXCEPTION 'review evidence result binding mismatch' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER approval_decision_control_link BEFORE INSERT ON mt.approval_decision
 FOR EACH ROW EXECUTE FUNCTION mt.validate_control_link();
CREATE TRIGGER review_evidence_control_link BEFORE INSERT ON mt.review_evidence
 FOR EACH ROW EXECUTE FUNCTION mt.validate_control_link();
CREATE UNIQUE INDEX review_evidence_unique_reference ON mt.review_evidence(case_id,review_id,evidence_id);
ALTER TABLE mt.audit_export ADD CONSTRAINT audit_export_runtime_state
 CHECK(state IN ('REQUESTED','READY','FAILED','EXPIRED','REVOKED'));
ALTER TABLE mt.audit_export ADD CONSTRAINT audit_export_ready_fixed_reference
 CHECK(state <> 'READY' OR (artifact_ref ?& ARRAY['object_id','version_id','sha256','size_bytes','expires_at','rule_version']
 AND artifact_ref->>'sha256' ~ '^[a-f0-9]{64}$' AND (artifact_ref->>'size_bytes')::bigint >= 0));
CREATE FUNCTION mt.protect_policy_definition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.org_id IS DISTINCT FROM OLD.org_id OR NEW.policy_id IS DISTINCT FROM OLD.policy_id
 OR NEW.kind IS DISTINCT FROM OLD.kind OR NEW.version IS DISTINCT FROM OLD.version
 OR NEW.definition_ref IS DISTINCT FROM OLD.definition_ref
 THEN RAISE EXCEPTION 'policy definition changes require a new version' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER policy_definition_new_version BEFORE UPDATE ON mt.policy_registry
 FOR EACH ROW EXECUTE FUNCTION mt.protect_policy_definition();
