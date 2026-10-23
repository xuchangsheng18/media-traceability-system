-- I01 only: immutable internal materials and run bindings. No adopted mapping,
-- public operation registration, runtime provider or management function is installed.
DO $$
DECLARE name text; identities oid[];
BEGIN
 FOREACH name IN ARRAY ARRAY['mt_task_plan_lookup','mt_task_plan_manager'] LOOP
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=name) THEN
   EXECUTE format('CREATE ROLE %I NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION',name);
  ELSIF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=name AND
   (rolcanlogin OR rolinherit OR rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb OR rolreplication)) THEN
   RAISE EXCEPTION 'UNSAFE_TASK_PLAN_ROLE' USING ERRCODE='55000';
  END IF;
 END LOOP;
 SELECT array_agg(oid) INTO identities FROM pg_roles
  WHERE rolname=ANY(ARRAY['mt_task_plan_lookup','mt_task_plan_manager']);
 IF EXISTS(SELECT 1 FROM pg_auth_members WHERE roleid=ANY(identities) OR member=ANY(identities)) THEN
  RAISE EXCEPTION 'UNSAFE_TASK_PLAN_ROLE_INHERITANCE' USING ERRCODE='55000';
 END IF;
END $$;

ALTER TABLE mt.policy_registry ADD CONSTRAINT task_policy_registry_org_identity_unique UNIQUE(org_id,policy_id);
ALTER TABLE mt.policy_registry ADD CONSTRAINT task_policy_registry_full_identity_unique UNIQUE(org_id,policy_id,kind,version);
ALTER TABLE mt.task_run ADD CONSTRAINT task_run_input_policy_identity_unique
 UNIQUE(case_id,task_id,run_version,input_sha256,policy_version);

CREATE FUNCTION mt.task_plan_modules_valid(wanted text[]) RETURNS boolean
LANGUAGE sql IMMUTABLE SET search_path=pg_catalog,mt,pg_temp AS $$
 SELECT COALESCE(array_ndims(wanted)=1 AND array_lower(wanted,1)=1 AND cardinality(wanted)>0
  AND NOT EXISTS(SELECT 1 FROM unnest(wanted) AS v WHERE v IS NULL OR v<>ALL(ARRAY[
   'INGEST','RESOURCE','MEDIA','RISK','FORENSIC','IMGRET','VIDTRACE','ORIGIN','PROPAGATION','CLAIM','REVIEW','OPS']))
  AND cardinality(wanted)=(SELECT count(DISTINCT v) FROM unnest(wanted) AS v),false)
$$;
REVOKE ALL ON FUNCTION mt.task_plan_modules_valid(text[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.task_plan_modules_valid(text[]) TO mt_task_plan_manager;

CREATE TABLE mt.task_policy_artifact (
 org_id uuid NOT NULL REFERENCES mt.organizations(org_id) CHECK(org_id<>'00000000-0000-0000-0000-000000000000'),
 policy_id uuid NOT NULL CHECK(policy_id<>'00000000-0000-0000-0000-000000000000'),
 policy_kind text NOT NULL CHECK(char_length(policy_kind) BETWEEN 1 AND 128),
 policy_version text NOT NULL CHECK(char_length(policy_version) BETWEEN 1 AND 128),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes)>0),
 policy_sha256 text NOT NULL CHECK(policy_sha256 ~ '^[a-f0-9]{64}$' AND policy_sha256=encode(sha256(canonical_bytes),'hex')),
 schema_version text NOT NULL CHECK(schema_version='urn:media-trace:api:0.1.0#/$defs/PolicyDefinition'),
 canonicalization_version text NOT NULL CHECK(canonicalization_version='task-material-json-utf8-sortkeys-v1'),
 provenance_ref text NOT NULL CHECK(char_length(provenance_ref)>0),
 created_by uuid NOT NULL CHECK(created_by<>'00000000-0000-0000-0000-000000000000'),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,policy_id,policy_kind,policy_version),
 UNIQUE(org_id,policy_id,policy_kind,policy_version,policy_sha256),
 FOREIGN KEY(org_id,policy_id,policy_kind,policy_version) REFERENCES mt.policy_registry(org_id,policy_id,kind,version),
 FOREIGN KEY(created_by,org_id) REFERENCES mt.users(user_id,org_id)
);

CREATE TABLE mt.task_plan_artifact (
 org_id uuid NOT NULL REFERENCES mt.organizations(org_id) CHECK(org_id<>'00000000-0000-0000-0000-000000000000'),
 plan_id text NOT NULL CHECK(char_length(plan_id) BETWEEN 1 AND 128),
 plan_version text NOT NULL CHECK(char_length(plan_version) BETWEEN 1 AND 128),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes)>0),
 plan_sha256 text NOT NULL CHECK(plan_sha256 ~ '^[a-f0-9]{64}$' AND plan_sha256=encode(sha256(canonical_bytes),'hex')),
 schema_version text NOT NULL CHECK(schema_version='urn:media-trace:task-execution-plan:1.0.0'),
 canonicalization_version text NOT NULL CHECK(canonicalization_version='task-material-json-utf8-sortkeys-v1'),
 provenance_ref text NOT NULL CHECK(char_length(provenance_ref)>0),
 created_by uuid NOT NULL CHECK(created_by<>'00000000-0000-0000-0000-000000000000'),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,plan_id,plan_version),
 UNIQUE(org_id,plan_id,plan_version,plan_sha256),
 FOREIGN KEY(created_by,org_id) REFERENCES mt.users(user_id,org_id)
);

CREATE TABLE mt.task_capability_manifest (
 org_id uuid NOT NULL REFERENCES mt.organizations(org_id) CHECK(org_id<>'00000000-0000-0000-0000-000000000000'),
 capability_id text NOT NULL CHECK(char_length(capability_id) BETWEEN 1 AND 128),
 capability_version text NOT NULL CHECK(char_length(capability_version) BETWEEN 1 AND 128),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes)>0),
 capability_sha256 text NOT NULL CHECK(capability_sha256 ~ '^[a-f0-9]{64}$' AND capability_sha256=encode(sha256(canonical_bytes),'hex')),
 schema_version text NOT NULL CHECK(schema_version='urn:media-trace:task-capability-manifest:1.0.0'),
 canonicalization_version text NOT NULL CHECK(canonicalization_version='task-material-json-utf8-sortkeys-v1'),
 provenance_ref text NOT NULL CHECK(char_length(provenance_ref)>0),
 created_by uuid NOT NULL CHECK(created_by<>'00000000-0000-0000-0000-000000000000'),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,capability_id,capability_version),
 UNIQUE(org_id,capability_id,capability_version,capability_sha256),
 FOREIGN KEY(created_by,org_id) REFERENCES mt.users(user_id,org_id)
);

CREATE TABLE mt.task_plan_mapping_revision (
 revision_id uuid PRIMARY KEY CHECK(revision_id<>'00000000-0000-0000-0000-000000000000'),
 org_id uuid NOT NULL REFERENCES mt.organizations(org_id) CHECK(org_id<>'00000000-0000-0000-0000-000000000000'),
 case_id uuid NOT NULL CHECK(case_id<>'00000000-0000-0000-0000-000000000000'),
 mapping_id text NOT NULL CHECK(char_length(mapping_id) BETWEEN 1 AND 128),
 mapping_version text NOT NULL CHECK(char_length(mapping_version) BETWEEN 1 AND 128),
 authority_version text NOT NULL CHECK(char_length(authority_version) BETWEEN 1 AND 128),
 scene text NOT NULL CHECK(scene IN ('accident_rumor','harmful_content','repost_tamper_trace')),
 modules text[] NOT NULL CHECK(mt.task_plan_modules_valid(modules)),
 priority text NOT NULL CHECK(priority IN ('low','normal','high')),
 policy_id uuid NOT NULL CHECK(policy_id<>'00000000-0000-0000-0000-000000000000'),
 policy_kind text NOT NULL CHECK(char_length(policy_kind) BETWEEN 1 AND 128),
 policy_version text NOT NULL CHECK(char_length(policy_version) BETWEEN 1 AND 128),
 policy_sha256 text NOT NULL CHECK(policy_sha256 ~ '^[a-f0-9]{64}$'),
 plan_id text NOT NULL CHECK(char_length(plan_id) BETWEEN 1 AND 128),
 plan_version text NOT NULL CHECK(char_length(plan_version) BETWEEN 1 AND 128),
 plan_sha256 text NOT NULL CHECK(plan_sha256 ~ '^[a-f0-9]{64}$'),
 capability_id text NOT NULL CHECK(char_length(capability_id) BETWEEN 1 AND 128),
 capability_version text NOT NULL CHECK(char_length(capability_version) BETWEEN 1 AND 128),
 capability_sha256 text NOT NULL CHECK(capability_sha256 ~ '^[a-f0-9]{64}$'),
 valid_from timestamptz NOT NULL,
 valid_until timestamptz NOT NULL CHECK(valid_until>valid_from),
 adoption_basis_ref text NOT NULL CHECK(char_length(adoption_basis_ref)>0),
 recovery_generation text NOT NULL CHECK(char_length(recovery_generation) BETWEEN 1 AND 128),
 validation_receipt_bytes bytea NOT NULL CHECK(octet_length(validation_receipt_bytes)>0),
 validation_receipt_sha256 text NOT NULL CHECK(validation_receipt_sha256 ~ '^[a-f0-9]{64}$'
  AND validation_receipt_sha256=encode(sha256(validation_receipt_bytes),'hex')),
 created_by uuid NOT NULL CHECK(created_by<>'00000000-0000-0000-0000-000000000000'),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(org_id,mapping_id,mapping_version),
 UNIQUE(org_id,case_id,revision_id),
 UNIQUE(org_id,case_id,revision_id,mapping_id,mapping_version,authority_version),
 UNIQUE(org_id,case_id,revision_id,policy_id,policy_kind,policy_version,policy_sha256),
 UNIQUE(org_id,case_id,revision_id,plan_id,plan_version,plan_sha256),
 UNIQUE(org_id,case_id,revision_id,capability_id,capability_version,capability_sha256),
 UNIQUE(org_id,case_id,revision_id,validation_receipt_sha256,recovery_generation,valid_from,valid_until),
 UNIQUE(org_id,case_id,revision_id,scene,policy_id,policy_version,modules,priority),
 FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
 FOREIGN KEY(created_by,org_id) REFERENCES mt.users(user_id,org_id),
 FOREIGN KEY(org_id,policy_id,policy_kind,policy_version,policy_sha256)
  REFERENCES mt.task_policy_artifact(org_id,policy_id,policy_kind,policy_version,policy_sha256),
 FOREIGN KEY(org_id,plan_id,plan_version,plan_sha256)
  REFERENCES mt.task_plan_artifact(org_id,plan_id,plan_version,plan_sha256),
 FOREIGN KEY(org_id,capability_id,capability_version,capability_sha256)
  REFERENCES mt.task_capability_manifest(org_id,capability_id,capability_version,capability_sha256)
);

CREATE TABLE mt.task_plan_mapping_head (
 org_id uuid NOT NULL REFERENCES mt.organizations(org_id) CHECK(org_id<>'00000000-0000-0000-0000-000000000000'),
 case_id uuid NOT NULL CHECK(case_id<>'00000000-0000-0000-0000-000000000000'),
 scene text NOT NULL CHECK(scene IN ('accident_rumor','harmful_content','repost_tamper_trace')),
 policy_id uuid NOT NULL CHECK(policy_id<>'00000000-0000-0000-0000-000000000000'),
 policy_version text NOT NULL CHECK(char_length(policy_version) BETWEEN 1 AND 128),
 modules text[] NOT NULL CHECK(mt.task_plan_modules_valid(modules)),
 priority text NOT NULL CHECK(priority IN ('low','normal','high')),
 revision_id uuid NOT NULL CHECK(revision_id<>'00000000-0000-0000-0000-000000000000'),
 state text NOT NULL CHECK(state IN ('INACTIVE','ACTIVE','REVOKED')),
 row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
 changed_by uuid NOT NULL CHECK(changed_by<>'00000000-0000-0000-0000-000000000000'),
 changed_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(org_id,case_id,scene,policy_id,policy_version,modules,priority),
 FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
 FOREIGN KEY(changed_by,org_id) REFERENCES mt.users(user_id,org_id),
 FOREIGN KEY(org_id,case_id,revision_id,scene,policy_id,policy_version,modules,priority)
  REFERENCES mt.task_plan_mapping_revision(org_id,case_id,revision_id,scene,policy_id,policy_version,modules,priority)
);

CREATE TABLE mt.task_run_plan (
 case_id uuid NOT NULL CHECK(case_id<>'00000000-0000-0000-0000-000000000000'),
 task_id uuid NOT NULL CHECK(task_id<>'00000000-0000-0000-0000-000000000000'),
 run_version bigint NOT NULL CHECK(run_version>0),
 org_id uuid NOT NULL REFERENCES mt.organizations(org_id) CHECK(org_id<>'00000000-0000-0000-0000-000000000000'),
 created_by uuid NOT NULL CHECK(created_by<>'00000000-0000-0000-0000-000000000000'),
 created_at timestamptz NOT NULL DEFAULT now(),
 request_body_bytes bytea NOT NULL CHECK(octet_length(request_body_bytes)>0),
 request_body_sha256 text NOT NULL CHECK(request_body_sha256 ~ '^[a-f0-9]{64}$'
  AND request_body_sha256=encode(sha256(request_body_bytes),'hex')),
 authorization_request_digest text NOT NULL CHECK(authorization_request_digest ~ '^[a-f0-9]{64}$'),
 revision_id uuid NOT NULL CHECK(revision_id<>'00000000-0000-0000-0000-000000000000'),
 mapping_id text NOT NULL CHECK(char_length(mapping_id) BETWEEN 1 AND 128),
 mapping_version text NOT NULL CHECK(char_length(mapping_version) BETWEEN 1 AND 128),
 authority_version text NOT NULL CHECK(char_length(authority_version) BETWEEN 1 AND 128),
 head_row_version bigint NOT NULL CHECK(head_row_version>0),
 policy_id uuid NOT NULL CHECK(policy_id<>'00000000-0000-0000-0000-000000000000'),
 policy_kind text NOT NULL CHECK(char_length(policy_kind) BETWEEN 1 AND 128),
 policy_version text NOT NULL CHECK(char_length(policy_version) BETWEEN 1 AND 128),
 policy_sha256 text NOT NULL CHECK(policy_sha256 ~ '^[a-f0-9]{64}$' AND policy_sha256=encode(sha256(policy_bytes),'hex')),
 policy_bytes bytea NOT NULL CHECK(octet_length(policy_bytes)>0),
 plan_id text NOT NULL CHECK(char_length(plan_id) BETWEEN 1 AND 128),
 plan_version text NOT NULL CHECK(char_length(plan_version) BETWEEN 1 AND 128),
 plan_sha256 text NOT NULL CHECK(plan_sha256 ~ '^[a-f0-9]{64}$' AND plan_sha256=encode(sha256(plan_bytes),'hex')),
 plan_bytes bytea NOT NULL CHECK(octet_length(plan_bytes)>0),
 capability_id text NOT NULL CHECK(char_length(capability_id) BETWEEN 1 AND 128),
 capability_version text NOT NULL CHECK(char_length(capability_version) BETWEEN 1 AND 128),
 capability_sha256 text NOT NULL CHECK(capability_sha256 ~ '^[a-f0-9]{64}$' AND capability_sha256=encode(sha256(capability_bytes),'hex')),
 capability_bytes bytea NOT NULL CHECK(octet_length(capability_bytes)>0),
 input_manifest_bytes bytea NOT NULL CHECK(octet_length(input_manifest_bytes)>0),
 input_sha256 text NOT NULL CHECK(input_sha256 ~ '^[a-f0-9]{64}$' AND input_sha256=encode(sha256(input_manifest_bytes),'hex')),
 validation_receipt_bytes bytea NOT NULL CHECK(octet_length(validation_receipt_bytes)>0),
 validation_receipt_sha256 text NOT NULL CHECK(validation_receipt_sha256 ~ '^[a-f0-9]{64}$'
  AND validation_receipt_sha256=encode(sha256(validation_receipt_bytes),'hex')),
 mapping_valid_from timestamptz NOT NULL,
 mapping_valid_until timestamptz NOT NULL CHECK(mapping_valid_until>mapping_valid_from),
 proof_observed_at timestamptz NOT NULL CHECK(proof_observed_at>=mapping_valid_from),
 proof_valid_until timestamptz NOT NULL CHECK(proof_valid_until>proof_observed_at AND proof_valid_until<=mapping_valid_until),
 recovery_generation text NOT NULL CHECK(char_length(recovery_generation) BETWEEN 1 AND 128),
 PRIMARY KEY(case_id,task_id,run_version),
 FOREIGN KEY(case_id,org_id) REFERENCES mt.cases(case_id,org_id),
 FOREIGN KEY(created_by,org_id) REFERENCES mt.users(user_id,org_id),
 FOREIGN KEY(case_id,task_id,run_version) REFERENCES mt.task_run(case_id,task_id,run_version),
 FOREIGN KEY(case_id,task_id,run_version,input_sha256,policy_version)
  REFERENCES mt.task_run(case_id,task_id,run_version,input_sha256,policy_version),
 FOREIGN KEY(org_id,case_id,revision_id,mapping_id,mapping_version,authority_version)
  REFERENCES mt.task_plan_mapping_revision(org_id,case_id,revision_id,mapping_id,mapping_version,authority_version),
 FOREIGN KEY(org_id,case_id,revision_id,policy_id,policy_kind,policy_version,policy_sha256)
  REFERENCES mt.task_plan_mapping_revision(org_id,case_id,revision_id,policy_id,policy_kind,policy_version,policy_sha256),
 FOREIGN KEY(org_id,case_id,revision_id,plan_id,plan_version,plan_sha256)
  REFERENCES mt.task_plan_mapping_revision(org_id,case_id,revision_id,plan_id,plan_version,plan_sha256),
 FOREIGN KEY(org_id,case_id,revision_id,capability_id,capability_version,capability_sha256)
  REFERENCES mt.task_plan_mapping_revision(org_id,case_id,revision_id,capability_id,capability_version,capability_sha256),
 FOREIGN KEY(org_id,case_id,revision_id,validation_receipt_sha256,recovery_generation,mapping_valid_from,mapping_valid_until)
  REFERENCES mt.task_plan_mapping_revision(org_id,case_id,revision_id,validation_receipt_sha256,recovery_generation,valid_from,valid_until)
);

CREATE FUNCTION mt.preserve_task_plan_head() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,mt,pg_temp AS $$
BEGIN
 IF TG_OP='INSERT' THEN
  IF NEW.row_version<>1 THEN RAISE EXCEPTION 'TASK_PLAN_HEAD_INITIAL_VERSION_INVALID' USING ERRCODE='55000'; END IF;
 ELSIF ROW(NEW.org_id,NEW.case_id,NEW.scene,NEW.policy_id,NEW.policy_version,NEW.modules,NEW.priority)
   IS DISTINCT FROM ROW(OLD.org_id,OLD.case_id,OLD.scene,OLD.policy_id,OLD.policy_version,OLD.modules,OLD.priority)
   OR NEW.row_version<>OLD.row_version+1 THEN
  RAISE EXCEPTION 'TASK_PLAN_HEAD_VERSION_OR_IDENTITY_INVALID' USING ERRCODE='55000';
 END IF;
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION mt.preserve_task_plan_head() FROM PUBLIC;
CREATE TRIGGER task_plan_head_version BEFORE INSERT OR UPDATE ON mt.task_plan_mapping_head
 FOR EACH ROW EXECUTE FUNCTION mt.preserve_task_plan_head();
CREATE TRIGGER task_plan_head_no_delete BEFORE DELETE OR TRUNCATE ON mt.task_plan_mapping_head
 FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

DO $$
DECLARE name text;
BEGIN
 FOREACH name IN ARRAY ARRAY['task_policy_artifact','task_plan_artifact','task_capability_manifest',
  'task_plan_mapping_revision','task_run_plan'] LOOP
  EXECUTE format('CREATE TRIGGER task_material_append_only BEFORE UPDATE OR DELETE ON mt.%I FOR EACH ROW EXECUTE FUNCTION mt.reject_mutation()',name);
  EXECUTE format('CREATE TRIGGER task_material_no_truncate BEFORE TRUNCATE ON mt.%I FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation()',name);
 END LOOP;
 FOREACH name IN ARRAY ARRAY['task_policy_artifact','task_plan_artifact','task_capability_manifest',
  'task_plan_mapping_revision','task_plan_mapping_head','task_run_plan'] LOOP
  EXECUTE format('ALTER TABLE mt.%I ENABLE ROW LEVEL SECURITY',name);
  EXECUTE format('ALTER TABLE mt.%I FORCE ROW LEVEL SECURITY',name);
  EXECUTE format('REVOKE ALL ON mt.%I FROM PUBLIC,mt_runtime',name);
 END LOOP;
 FOREACH name IN ARRAY ARRAY['task_policy_artifact','task_plan_artifact','task_capability_manifest',
  'task_plan_mapping_revision','task_plan_mapping_head'] LOOP
  EXECUTE format('GRANT SELECT ON mt.%I TO mt_task_plan_lookup',name);
  EXECUTE format('GRANT SELECT,INSERT ON mt.%I TO mt_task_plan_manager',name);
  -- I01 has no registered createTask scope or controlled management entry
  -- point. Neither a role grant nor a forged raw GUC enables material access.
  EXECUTE format('CREATE POLICY task_plan_lookup_read ON mt.%I FOR SELECT TO mt_task_plan_lookup USING(org_id=mt.org_id() AND mt.scope_operation()=''createTask'' AND mt.scope_allows_case(mt.scope_case_id())%s)',name,
   CASE WHEN name IN ('task_plan_mapping_revision','task_plan_mapping_head') THEN ' AND case_id=mt.scope_case_id()' ELSE '' END);
  EXECUTE format('CREATE POLICY task_plan_manager_read ON mt.%I FOR SELECT TO mt_task_plan_manager USING(false)',name);
  EXECUTE format('CREATE POLICY task_plan_manager_append ON mt.%I FOR INSERT TO mt_task_plan_manager WITH CHECK(false)',name);
 END LOOP;
END $$;
GRANT USAGE ON SCHEMA mt TO mt_task_plan_lookup,mt_task_plan_manager;
GRANT EXECUTE ON FUNCTION mt.org_id(),mt.scope_operation(),mt.scope_mode(),mt.scope_case_id(),
 mt.scope_allows_case(uuid),mt.can_access_case(uuid) TO mt_task_plan_lookup;
GRANT UPDATE ON mt.task_plan_mapping_head TO mt_task_plan_manager;
CREATE POLICY task_plan_manager_head_update ON mt.task_plan_mapping_head FOR UPDATE
 TO mt_task_plan_manager USING(false) WITH CHECK(false);

-- The necessary runtime ACL remains unusable until I02 registers createTask in
-- the existing scope whitelist. No raw-GUC shortcut or early ALLOW is added.
GRANT SELECT,INSERT ON mt.task_run_plan TO mt_runtime;
-- Preserve the mandatory T015 CASE-table guard independently of permissive
-- operation policies, so a later broader policy cannot bypass org/case scope.
CREATE POLICY request_data_scope ON mt.task_run_plan AS RESTRICTIVE TO mt_runtime
 USING(org_id=mt.org_id() AND mt.scope_allows_case(case_id))
 WITH CHECK(org_id=mt.org_id() AND mt.scope_allows_case(case_id));
CREATE POLICY task_run_plan_read ON mt.task_run_plan FOR SELECT TO mt_runtime
 USING(org_id=mt.org_id() AND mt.scope_mode()='CASE' AND mt.scope_operation()='createTask'
  AND mt.scope_allows_case(case_id));
CREATE POLICY task_run_plan_append ON mt.task_run_plan FOR INSERT TO mt_runtime
 WITH CHECK(org_id=mt.org_id() AND mt.scope_mode()='CASE' AND mt.scope_operation()='createTask'
  AND mt.scope_allows_case(case_id) AND created_by=mt.actor_id());

COMMENT ON TABLE mt.task_plan_mapping_head IS 'Private adoption head only; no adopted rows or management entry point are seeded by I01';
COMMENT ON TABLE mt.task_run_plan IS 'Append-only exact run/request/material binding; I01 does not enable createTask or backfill historical runs';
