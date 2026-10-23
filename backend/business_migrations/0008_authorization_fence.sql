-- Transaction ordering only. No formal policy or recovery generation is activated by this migration.
CREATE TABLE mt.authorization_epoch (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 epoch bigint NOT NULL DEFAULT 1 CHECK(epoch>0),
 changed_at timestamptz NOT NULL DEFAULT statement_timestamp(),
 policy_version text,
 policy_sha256 text CHECK(policy_sha256 IS NULL OR policy_sha256 ~ '^[a-f0-9]{64}$'),
 recovery_generation text,
 CHECK((policy_version IS NULL AND policy_sha256 IS NULL AND recovery_generation IS NULL)
   OR (policy_version IS NOT NULL AND recovery_generation IS NOT NULL
       AND length(policy_version) BETWEEN 1 AND 1024 AND policy_sha256 IS NOT NULL
       AND length(recovery_generation) BETWEEN 1 AND 1024))
);
REVOKE ALL ON mt.authorization_epoch FROM PUBLIC,mt_runtime,mt_permission_lookup,mt_directory_manager;
INSERT INTO mt.authorization_epoch(singleton) VALUES(true);

CREATE FUNCTION mt.advance_authorization_epoch() RETURNS bigint
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
 UPDATE mt.authorization_epoch SET epoch=epoch+1,changed_at=statement_timestamp()
 WHERE singleton RETURNING epoch
$$;
REVOKE ALL ON FUNCTION mt.advance_authorization_epoch() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.advance_authorization_epoch() TO mt_directory_manager;

CREATE FUNCTION mt.bump_authorization_epoch() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
BEGIN
 PERFORM mt.advance_authorization_epoch();
 RETURN NULL;
END $$;
REVOKE ALL ON FUNCTION mt.bump_authorization_epoch() FROM PUBLIC;

DO $$
DECLARE table_name text;
BEGIN
 FOREACH table_name IN ARRAY ARRAY['organizations','users','user_identities','roles','permissions',
   'user_roles','role_permissions','case_membership','cases']
 LOOP
  EXECUTE format('CREATE TRIGGER authorization_epoch_before_change BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON mt.%I FOR EACH STATEMENT EXECUTE FUNCTION mt.bump_authorization_epoch()',table_name);
 END LOOP;
END $$;

CREATE FUNCTION mt.hold_authorization_epoch()
RETURNS TABLE(epoch bigint,database_name text,database_oid oid,policy_version text,policy_sha256 text,recovery_generation text)
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
 SELECT e.epoch,current_database()::text,d.oid,e.policy_version,e.policy_sha256,e.recovery_generation
 FROM mt.authorization_epoch e JOIN pg_catalog.pg_database d ON d.datname=current_database()
 WHERE e.singleton FOR SHARE OF e
$$;
REVOKE ALL ON FUNCTION mt.hold_authorization_epoch() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.hold_authorization_epoch() TO mt_runtime;

CREATE FUNCTION mt.activate_authorization_generation(wanted_version text,wanted_sha256 text,wanted_generation text,expected_epoch bigint)
RETURNS bigint LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
DECLARE activated bigint;
BEGIN
 IF wanted_version IS NULL OR length(wanted_version) NOT BETWEEN 1 AND 1024
 OR wanted_generation IS NULL OR length(wanted_generation) NOT BETWEEN 1 AND 1024
 OR wanted_sha256 IS NULL OR wanted_sha256 !~ '^[a-f0-9]{64}$'
 OR expected_epoch IS NULL OR expected_epoch<1
 THEN RAISE EXCEPTION 'authorization activation input invalid' USING ERRCODE='22023'; END IF;
 UPDATE mt.authorization_epoch SET epoch=epoch+1,changed_at=statement_timestamp(),
   policy_version=wanted_version,policy_sha256=wanted_sha256,recovery_generation=wanted_generation
 WHERE singleton AND epoch=expected_epoch RETURNING epoch INTO activated;
 IF activated IS NULL THEN
  RAISE EXCEPTION 'authorization activation epoch changed' USING ERRCODE='40001';
 END IF;
 RETURN activated;
END $$;
REVOKE ALL ON FUNCTION mt.activate_authorization_generation(text,text,text,bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.activate_authorization_generation(text,text,text,bigint) TO mt_directory_manager;
COMMENT ON TABLE mt.authorization_epoch IS
 'Candidate shared lock orders catalog revocations and business commits. NULL generation means not activated; recovery needs an independent, explicit external proof.';
