-- T012 internal role catalog lifecycle. No account, formal policy or role seeds.
DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname IN ('mt_directory_manager','mt_identity_lookup')
      AND (rolsuper OR rolbypassrls OR rolcanlogin OR rolcreaterole OR rolcreatedb OR rolreplication))
    OR pg_has_role('mt_runtime','mt_directory_manager','MEMBER')
    OR pg_has_role('mt_runtime','mt_identity_lookup','MEMBER')
    OR pg_has_role('mt_identity_lookup','mt_directory_manager','MEMBER') THEN
    RAISE EXCEPTION 'UNSAFE_ROLE_CATALOG_MANAGEMENT' USING ERRCODE='55000';
  END IF;
END $$;

-- Preserve the pre-switch state of legacy catalogs; new rows default disabled.
ALTER TABLE mt.roles ADD COLUMN enabled boolean NOT NULL DEFAULT true;
ALTER TABLE mt.roles ALTER COLUMN enabled SET DEFAULT false;
ALTER TABLE mt.permissions ADD COLUMN enabled boolean NOT NULL DEFAULT true;
ALTER TABLE mt.permissions ALTER COLUMN enabled SET DEFAULT false;
ALTER TABLE mt.role_permissions ADD COLUMN revoked_at timestamptz;
ALTER TABLE mt.roles ADD CONSTRAINT role_code_valid
  CHECK(code<>'' AND code=btrim(code) AND length(code)<=1024 AND code !~ '[[:cntrl:]]');
ALTER TABLE mt.permissions ADD CONSTRAINT permission_code_valid
  CHECK(code<>'' AND code=btrim(code) AND length(code)<=1024 AND code !~ '[[:cntrl:]]');
COMMENT ON COLUMN mt.roles.enabled IS 'Directory switch only, not formal authorization; new rows disabled, legacy rows retained';
COMMENT ON COLUMN mt.permissions.enabled IS 'Directory switch only; effective route/case authorization remains independent';
COMMENT ON COLUMN mt.role_permissions.revoked_at IS 'Terminal binding revocation; historical unique pair is retained, no automatic regrant';

CREATE FUNCTION mt.preserve_role_catalog() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,mt,pg_temp AS $$
BEGIN
  IF TG_TABLE_NAME='roles' THEN
    IF ROW(NEW.role_id,NEW.code) IS DISTINCT FROM ROW(OLD.role_id,OLD.code) THEN
      RAISE EXCEPTION 'role keys cannot be reassigned' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='permissions' THEN
    IF ROW(NEW.permission_id,NEW.code) IS DISTINCT FROM ROW(OLD.permission_id,OLD.code) THEN
      RAISE EXCEPTION 'permission keys cannot be reassigned' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='role_permissions' THEN
    IF ROW(NEW.role_permission_id,NEW.role_id,NEW.permission_id) IS DISTINCT FROM
       ROW(OLD.role_permission_id,OLD.role_id,OLD.permission_id) THEN
      RAISE EXCEPTION 'role permission binding cannot be reassigned' USING ERRCODE='55000';
    END IF;
    IF OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at THEN
      RAISE EXCEPTION 'revoked role permission binding is terminal' USING ERRCODE='55000';
    END IF;
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION mt.preserve_role_catalog() FROM PUBLIC;
DO $$
DECLARE name text;
BEGIN
  FOREACH name IN ARRAY ARRAY['roles','permissions','role_permissions'] LOOP
    EXECUTE format('CREATE TRIGGER preserve_role_catalog BEFORE UPDATE ON mt.%I FOR EACH ROW EXECUTE FUNCTION mt.preserve_role_catalog()',name);
  END LOOP;
  FOREACH name IN ARRAY ARRAY['roles','permissions','role_permissions','user_roles'] LOOP
    EXECUTE format('CREATE TRIGGER catalog_history_no_delete BEFORE DELETE OR TRUNCATE ON mt.%I FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation()',name);
  END LOOP;
END $$;
GRANT INSERT,UPDATE ON mt.roles,mt.permissions,mt.role_permissions TO mt_directory_manager;
