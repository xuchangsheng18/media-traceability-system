-- T014 read-only facts. No formal roles, users, policies or ALLOW seeds.
DO $$
DECLARE other text;
BEGIN
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='mt_permission_lookup') THEN
    CREATE ROLE mt_permission_lookup NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB NOREPLICATION;
  ELSIF EXISTS(SELECT 1 FROM pg_roles WHERE rolname='mt_permission_lookup'
      AND (rolcanlogin OR rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb OR rolreplication)) THEN
    RAISE EXCEPTION 'UNSAFE_PERMISSION_LOOKUP_ROLE' USING ERRCODE='55000';
  END IF;
  FOREACH other IN ARRAY ARRAY['mt_runtime','mt_identity_lookup','mt_directory_manager',
      'pg_read_all_data','pg_write_all_data','pg_read_server_files','pg_write_server_files',
      'pg_execute_server_program','pg_signal_backend','pg_checkpoint'] LOOP
    IF pg_has_role('mt_permission_lookup',other,'MEMBER')
       OR pg_has_role(other,'mt_permission_lookup','MEMBER') THEN
      RAISE EXCEPTION 'UNSAFE_PERMISSION_LOOKUP_INHERITANCE' USING ERRCODE='55000';
    END IF;
  END LOOP;
  IF EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='mt' AND c.relkind IN ('r','p','v','m')
      AND has_table_privilege('mt_permission_lookup',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')) THEN
    RAISE EXCEPTION 'UNSAFE_PERMISSION_LOOKUP_TABLE_GRANT' USING ERRCODE='55000';
  END IF;
END $$;

CREATE FUNCTION mt.lookup_permission(wanted_issuer text,wanted_subject text,expected_user uuid,expected_org uuid,wanted_permission text)
RETURNS TABLE(identity_id uuid,user_id uuid,org_id uuid,mapping_version text,
  identity_version bigint,user_version bigint,org_version bigint,identity_expires_epoch text,
  permission_code text,permission_id uuid,permission_version bigint,permission_enabled boolean,
  eligible boolean,bindings jsonb)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT i.identity_id,i.user_id,i.org_id,i.mapping_version,i.row_version,u.row_version,o.row_version,
  extract(epoch FROM i.expires_at)::text,wanted_permission,p.permission_id,p.row_version,p.enabled,
  facts.items<>'[]'::jsonb,facts.items
FROM mt.user_identities i
JOIN mt.users u ON (u.user_id,u.org_id)=(i.user_id,i.org_id)
JOIN mt.organizations o ON o.org_id=i.org_id
LEFT JOIN mt.permissions p ON p.code=wanted_permission COLLATE "C"
CROSS JOIN LATERAL (
  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'user_role_id',ur.user_role_id,'user_role_version',ur.row_version,
    'role_id',r.role_id,'role_version',r.row_version,
    'role_permission_id',rp.role_permission_id,'role_permission_version',rp.row_version,
    'expires_epoch',extract(epoch FROM ur.expires_at)::text)
    ORDER BY ur.user_role_id,rp.role_permission_id),'[]'::jsonb) AS items
  FROM mt.user_roles ur
  JOIN mt.roles r ON r.role_id=ur.role_id
  JOIN mt.role_permissions rp ON rp.role_id=r.role_id AND rp.permission_id=p.permission_id
  WHERE ur.user_id=i.user_id AND r.enabled AND p.enabled
    AND ur.revoked_at IS NULL AND (ur.expires_at IS NULL OR ur.expires_at>statement_timestamp())
    AND rp.revoked_at IS NULL
) facts
WHERE i.issuer=wanted_issuer COLLATE "C" AND i.subject=wanted_subject COLLATE "C"
  AND i.user_id=expected_user AND i.org_id=expected_org
  AND i.enabled AND i.revoked_at IS NULL AND (i.expires_at IS NULL OR i.expires_at>statement_timestamp())
  AND u.enabled AND o.enabled
$$;
REVOKE ALL ON FUNCTION mt.lookup_permission(text,text,uuid,uuid,text) FROM PUBLIC;
GRANT USAGE ON SCHEMA mt TO mt_permission_lookup;
GRANT EXECUTE ON FUNCTION mt.lookup_permission(text,text,uuid,uuid,text) TO mt_permission_lookup;
COMMENT ON FUNCTION mt.lookup_permission(text,text,uuid,uuid,text) IS
  'Trusted backend-only permission facts; authenticated caller binding and explicit approved policy remain mandatory. Never grant catalog manager privileges to the API.';
