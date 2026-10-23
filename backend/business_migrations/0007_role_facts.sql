-- Complete activity facts, separate from a formal rule decision. No role/user seeds.
CREATE FUNCTION mt.lookup_role_facts(wanted_issuer text,wanted_subject text,expected_user uuid,expected_org uuid,wanted_permission text)
RETURNS TABLE(identity_id uuid,user_id uuid,org_id uuid,mapping_version text,
  identity_version bigint,user_version bigint,org_version bigint,identity_expires_epoch text,
  permission_code text,permission_id uuid,permission_version bigint,permission_enabled boolean,
  eligible boolean,bindings jsonb,active_roles jsonb,permission_role_ids jsonb)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT p.*,activity.items,coalesce((
  SELECT jsonb_agg(ids.role_id ORDER BY ids.role_id)
  FROM (SELECT DISTINCT x->>'role_id' AS role_id FROM jsonb_array_elements(p.bindings) x) ids
),'[]'::jsonb)
FROM mt.lookup_permission(wanted_issuer,wanted_subject,expected_user,expected_org,wanted_permission) p
CROSS JOIN LATERAL (
  SELECT coalesce(jsonb_agg(jsonb_build_object(
    'role_id',r.role_id,'code',r.code,'binding_id',ur.user_role_id,
    'binding_version',ur.row_version,'role_version',r.row_version,
    'expires_epoch',extract(epoch FROM ur.expires_at)::text)
    ORDER BY ur.user_role_id),'[]'::jsonb) AS items
  FROM mt.user_roles ur JOIN mt.roles r ON r.role_id=ur.role_id
  WHERE ur.user_id=p.user_id AND r.enabled AND ur.revoked_at IS NULL
    AND (ur.expires_at IS NULL OR ur.expires_at>statement_timestamp())
) activity
$$;
REVOKE ALL ON FUNCTION mt.lookup_role_facts(text,text,uuid,uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.lookup_role_facts(text,text,uuid,uuid,text) TO mt_permission_lookup;

CREATE FUNCTION mt.lookup_actor_role_facts(wanted_issuer text,wanted_subject text,wanted_permission text)
RETURNS TABLE(identity_id uuid,user_id uuid,org_id uuid,mapping_version text,
  identity_version bigint,user_version bigint,org_version bigint,identity_expires_epoch text,
  permission_code text,permission_id uuid,permission_version bigint,permission_enabled boolean,
  eligible boolean,bindings jsonb,active_roles jsonb,permission_role_ids jsonb)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,mt,pg_temp AS $$
SELECT * FROM mt.lookup_role_facts(wanted_issuer,wanted_subject,mt.actor_id(),mt.org_id(),wanted_permission)
$$;
REVOKE ALL ON FUNCTION mt.lookup_actor_role_facts(text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION mt.lookup_actor_role_facts(text,text,text) TO mt_runtime;
COMMENT ON FUNCTION mt.lookup_role_facts(text,text,uuid,uuid,text) IS
  'Backend-only complete activity facts, including roles without the requested permission; never an ALLOW.';
COMMENT ON FUNCTION mt.lookup_actor_role_facts(text,text,text) IS
  'Transaction-only facts bound to server-set app.actor_id/org_id; no caller-selected alternate identity or manager grant.';
