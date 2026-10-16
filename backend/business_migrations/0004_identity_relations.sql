-- Additive identity directory extension. No provider, user or approved policy seeds.
DO $$
DECLARE name text;
BEGIN
  FOREACH name IN ARRAY ARRAY['mt_directory_manager','mt_identity_lookup'] LOOP
    IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=name) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN NOSUPERUSER NOBYPASSRLS',name);
    ELSIF EXISTS(SELECT 1 FROM pg_roles WHERE rolname=name AND (rolsuper OR rolbypassrls OR rolcanlogin)) THEN
      RAISE EXCEPTION 'unsafe identity group role' USING ERRCODE='55000';
    END IF;
  END LOOP;
  IF pg_has_role('mt_runtime','mt_directory_manager','MEMBER')
     OR pg_has_role('mt_runtime','mt_identity_lookup','MEMBER')
     OR pg_has_role('mt_identity_lookup','mt_directory_manager','MEMBER') THEN
    RAISE EXCEPTION 'UNSAFE_IDENTITY_ROLE_INHERITANCE' USING ERRCODE='55000';
  END IF;
END $$;

ALTER TABLE mt.organizations ADD COLUMN enabled boolean NOT NULL DEFAULT true;
ALTER TABLE mt.users ADD CONSTRAINT users_id_org_unique UNIQUE(user_id,org_id);
ALTER TABLE mt.case_membership ADD CONSTRAINT membership_user_org_fk
  FOREIGN KEY(user_id,org_id) REFERENCES mt.users(user_id,org_id);
ALTER TABLE mt.user_roles ADD COLUMN revoked_at timestamptz;

CREATE TABLE mt.user_identities (
  identity_id uuid PRIMARY KEY,
  user_id uuid NOT NULL,
  org_id uuid NOT NULL,
  issuer text COLLATE "C" NOT NULL CHECK(issuer<>'' AND issuer=btrim(issuer) AND length(issuer)<=2048 AND issuer !~ '[[:cntrl:]]'),
  subject text COLLATE "C" NOT NULL CHECK(subject<>'' AND subject=btrim(subject) AND length(subject)<=1024 AND subject !~ '[[:cntrl:]]'),
  enabled boolean NOT NULL DEFAULT false,
  expires_at timestamptz,
  revoked_at timestamptz,
  mapping_version text NOT NULL CHECK(mapping_version<>'' AND mapping_version=btrim(mapping_version)),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
  created_by uuid,
  UNIQUE(issuer,subject),
  FOREIGN KEY(user_id,org_id) REFERENCES mt.users(user_id,org_id),
  CHECK(revoked_at IS NULL OR NOT enabled)
);
COMMENT ON TABLE mt.user_identities IS 'Explicit external identity mapping; does not authenticate tokens or grant permissions';
COMMENT ON COLUMN mt.users.subject IS 'Legacy unique internal label; never use alone to resolve an external provider identity';
CREATE INDEX identity_user_org ON mt.user_identities(user_id,org_id);

CREATE FUNCTION mt.preserve_directory_keys() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,mt,pg_temp AS $$
BEGIN
  IF TG_TABLE_NAME='users' THEN
    IF ROW(NEW.user_id,NEW.org_id,NEW.subject) IS DISTINCT FROM ROW(OLD.user_id,OLD.org_id,OLD.subject) THEN
      RAISE EXCEPTION 'stable user keys cannot be reassigned' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='organizations' THEN
    IF NEW.org_id IS DISTINCT FROM OLD.org_id THEN
      RAISE EXCEPTION 'stable unit key cannot be reassigned' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='cases' THEN
    IF ROW(NEW.case_id,NEW.org_id) IS DISTINCT FROM ROW(OLD.case_id,OLD.org_id) THEN
      RAISE EXCEPTION 'stable case scope cannot be reassigned' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='user_identities' THEN
    IF ROW(NEW.identity_id,NEW.user_id,NEW.org_id,NEW.issuer,NEW.subject) IS DISTINCT FROM
       ROW(OLD.identity_id,OLD.user_id,OLD.org_id,OLD.issuer,OLD.subject) THEN
      RAISE EXCEPTION 'external identity cannot be reassigned' USING ERRCODE='55000';
    END IF;
    IF OLD.revoked_at IS NOT NULL AND (NEW.enabled OR NEW.revoked_at IS DISTINCT FROM OLD.revoked_at) THEN
      RAISE EXCEPTION 'revoked identity is terminal' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='case_membership' THEN
    IF ROW(NEW.membership_id,NEW.user_id,NEW.org_id,NEW.case_id) IS DISTINCT FROM
       ROW(OLD.membership_id,OLD.user_id,OLD.org_id,OLD.case_id) THEN
      RAISE EXCEPTION 'membership cannot be reassigned' USING ERRCODE='55000';
    END IF;
    IF OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at THEN
      RAISE EXCEPTION 'revoked membership is terminal' USING ERRCODE='55000';
    END IF;
  ELSIF TG_TABLE_NAME='user_roles' THEN
    IF ROW(NEW.user_role_id,NEW.user_id,NEW.role_id) IS DISTINCT FROM ROW(OLD.user_role_id,OLD.user_id,OLD.role_id) THEN
      RAISE EXCEPTION 'role binding cannot be reassigned' USING ERRCODE='55000';
    END IF;
    IF OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at THEN
      RAISE EXCEPTION 'revoked role binding is terminal' USING ERRCODE='55000';
    END IF;
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION mt.preserve_directory_keys() FROM PUBLIC;
DO $$
DECLARE name text;
BEGIN
  FOREACH name IN ARRAY ARRAY['users','organizations','cases','user_identities','case_membership','user_roles'] LOOP
    EXECUTE format('CREATE TRIGGER preserve_directory_keys BEFORE UPDATE ON mt.%I FOR EACH ROW EXECUTE FUNCTION mt.preserve_directory_keys()',name);
  END LOOP;
END $$;
CREATE TRIGGER identity_no_delete BEFORE DELETE OR TRUNCATE ON mt.user_identities
  FOR EACH STATEMENT EXECUTE FUNCTION mt.reject_mutation();

CREATE OR REPLACE FUNCTION mt.actor_in_org() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT EXISTS(SELECT 1 FROM mt.users u JOIN mt.organizations o USING(org_id)
 WHERE u.user_id=mt.actor_id() AND u.org_id=mt.org_id() AND u.enabled AND o.enabled)
$$;
CREATE OR REPLACE FUNCTION mt.can_access_case(wanted uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT EXISTS(SELECT 1 FROM mt.case_membership m JOIN mt.users u ON u.user_id=m.user_id AND u.org_id=m.org_id
 JOIN mt.organizations o ON o.org_id=u.org_id
 WHERE m.case_id=wanted AND m.user_id=mt.actor_id() AND m.org_id=mt.org_id() AND u.enabled AND o.enabled
 AND m.revoked_at IS NULL AND (m.expires_at IS NULL OR m.expires_at>statement_timestamp()))
$$;

CREATE FUNCTION mt.resolve_identity(wanted_issuer text,wanted_subject text)
RETURNS TABLE(identity_id uuid,user_id uuid,org_id uuid,mapping_version text,identity_version bigint,user_version bigint,org_version bigint)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT i.identity_id,i.user_id,i.org_id,i.mapping_version,i.row_version,u.row_version,o.row_version
FROM mt.user_identities i JOIN mt.users u ON (u.user_id,u.org_id)=(i.user_id,i.org_id)
JOIN mt.organizations o ON o.org_id=i.org_id
WHERE i.issuer=wanted_issuer COLLATE "C" AND i.subject=wanted_subject COLLATE "C"
 AND i.enabled AND i.revoked_at IS NULL AND (i.expires_at IS NULL OR i.expires_at>statement_timestamp())
 AND u.enabled AND o.enabled
$$;
REVOKE ALL ON FUNCTION mt.resolve_identity(text,text) FROM PUBLIC;
GRANT USAGE ON SCHEMA mt TO mt_directory_manager,mt_identity_lookup;
GRANT EXECUTE ON FUNCTION mt.resolve_identity(text,text) TO mt_identity_lookup;
GRANT SELECT ON mt.roles,mt.permissions,mt.role_permissions TO mt_directory_manager;
GRANT SELECT,INSERT,UPDATE ON mt.organizations,mt.users,mt.cases,mt.case_membership,mt.user_roles,mt.user_identities TO mt_directory_manager;
ALTER TABLE mt.user_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE mt.user_identities FORCE ROW LEVEL SECURITY;
-- The fixed, trusted function/table owner also works without SUPERUSER/BYPASSRLS.
CREATE POLICY identity_schema_owner ON mt.user_identities TO CURRENT_USER USING(true) WITH CHECK(true);
DO $$
DECLARE name text;
BEGIN
  FOREACH name IN ARRAY ARRAY['organizations','users','cases','case_membership','user_roles','user_identities'] LOOP
    EXECUTE format('CREATE POLICY trusted_directory_management ON mt.%I TO mt_directory_manager USING(true) WITH CHECK(true)',name);
  END LOOP;
END $$;
