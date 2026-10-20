-- Narrow work-identity resolution only. Job ownership remains an RLS runtime read.
CREATE FUNCTION mt.lookup_actor_work_role_facts(wanted_identity uuid,wanted_mapping text,wanted_permission text)
RETURNS TABLE(identity_id uuid,user_id uuid,org_id uuid,mapping_version text,
 identity_version bigint,user_version bigint,org_version bigint,identity_expires_epoch text,
 permission_code text,permission_id uuid,permission_version bigint,permission_enabled boolean,
 eligible boolean,bindings jsonb,active_roles jsonb,permission_role_ids jsonb)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT f.* FROM mt.user_identities i
CROSS JOIN LATERAL mt.lookup_role_facts(i.issuer,i.subject,mt.actor_id(),mt.org_id(),wanted_permission) f
WHERE i.identity_id=wanted_identity AND i.mapping_version=wanted_mapping
 AND i.user_id=mt.actor_id() AND i.org_id=mt.org_id()
 AND f.identity_id=i.identity_id AND f.mapping_version=wanted_mapping
$$;
REVOKE ALL ON FUNCTION mt.lookup_actor_work_role_facts(uuid,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.lookup_actor_work_role_facts(uuid,text,text) TO mt_runtime;
COMMENT ON FUNCTION mt.lookup_actor_work_role_facts(uuid,text,text) IS
 'Actor/org and exact live identity mapping bound work facts; no JWT impersonation, no job/delegation/service ALLOW.';
