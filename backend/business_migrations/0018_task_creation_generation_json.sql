-- Exact 0017 follow-up: JSON generation.database_oid is an integer, not an
-- OID's JSON string representation. Keep the published migration and strict
-- Python reader unchanged. No adoption, grants to runtime, or data writes.
-- The migration runner executes this whole file and its ledger in one
-- transaction. A non-super mt owner needs the same administrator-prepared
-- SET-only / NOINHERIT / no-ADMIN edges as 0017, revoked by that administrator
-- after installation. This file never creates or modifies role memberships.
DO $generation_json$
DECLARE
 v_installer text := current_user;
 v_installer_oid oid;
 v_is_super boolean;
 v_private_roles oid[];
 v_edge record;
 v_item record;
 v_function oid;
 v_proc record;
 v_before jsonb := '{}'::jsonb;
 v_comments jsonb := '{}'::jsonb;
 v_after jsonb;
 v_schema_acl aclitem[];
 v_definition text;
 v_old text := '''database_oid'',v_generation.database_oid,''epoch''';
 v_new text := '''database_oid'',v_generation.database_oid::bigint,''epoch''';
BEGIN
 SELECT r.oid,r.rolsuper INTO STRICT v_installer_oid,v_is_super
 FROM pg_catalog.pg_roles r WHERE r.rolname=v_installer;
 SELECT n.nspacl INTO STRICT v_schema_acl FROM pg_catalog.pg_namespace n WHERE n.nspname='mt';
 IF NOT v_is_super AND (
  v_installer_oid<>(SELECT nspowner FROM pg_catalog.pg_namespace WHERE nspname='mt')
  OR v_installer='mt_runtime' OR pg_catalog.pg_has_role(v_installer,'mt_runtime','MEMBER')
 ) THEN
  RAISE EXCEPTION 'TASK_CREATION_GENERATION_INSTALLER_UNSAFE' USING ERRCODE='55000';
 END IF;
 SELECT array_agg(r.oid ORDER BY r.oid) INTO v_private_roles
 FROM pg_catalog.pg_roles r WHERE r.rolname=ANY(ARRAY['mt_task_plan_lookup','mt_task_plan_case_reader']);
 IF coalesce(array_length(v_private_roles,1),0)<>2 OR EXISTS(
  SELECT 1 FROM pg_catalog.pg_roles r WHERE r.oid=ANY(v_private_roles) AND
   (r.rolcanlogin OR r.rolinherit OR r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication)
 ) OR EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members WHERE member=ANY(v_private_roles))
 OR EXISTS(SELECT 1 FROM pg_catalog.pg_class WHERE relnamespace='mt'::regnamespace AND relowner=ANY(v_private_roles))
 OR pg_catalog.has_schema_privilege('mt_task_plan_lookup','mt','CREATE')
 OR pg_catalog.has_schema_privilege('mt_task_plan_case_reader','mt','CREATE') THEN
  RAISE EXCEPTION 'TASK_CREATION_GENERATION_ROLE_UNSAFE' USING ERRCODE='55000';
 END IF;
 FOR v_edge IN SELECT * FROM pg_catalog.pg_auth_members WHERE roleid=ANY(v_private_roles) LOOP
  IF v_is_super OR v_edge.member<>v_installer_oid OR v_edge.inherit_option
   OR NOT v_edge.set_option OR v_edge.admin_option THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_INSTALLER_UNSAFE' USING ERRCODE='55000';
  END IF;
 END LOOP;
 IF NOT v_is_super AND (
  SELECT count(*) FROM pg_catalog.pg_auth_members
  WHERE roleid=ANY(v_private_roles) AND member=v_installer_oid
 )<>2 THEN
  RAISE EXCEPTION 'TASK_CREATION_GENERATION_INSTALLER_UNSAFE' USING ERRCODE='55000';
 END IF;

 -- These are SHA-256s of the literal AS $$ bodies in published 0017, including
 -- their leading/trailing LF. Unknown/custom bodies are refused, not replaced.
 -- Each old token must occur exactly once. Both routines are checked before
 -- temporary CREATE privilege or the first replacement is attempted.
 FOR v_item IN SELECT * FROM (VALUES
  ('mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text)',
   'mt_task_plan_case_reader',
   '9672e5538c3e7880bf12a37b93bf865325d943dc9aea5671efb4db707a65d34b',
   '53bf1ff1c201a91c761dbebde0826e47e5bdb1d7ed7d31a322bc30b3bdcb0a94'),
  ('mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text)',
   'mt_task_plan_lookup',
   '47e5f76efd3eac3eed938baaf47a8ed5443db857ac65d7af5a3309cf566c3b1b',
   'cc0177977ebe6aca94c7fcfbb0b7d6689eb55596a6c01470d87a886990100067')
 ) AS expected(signature,owner_name,old_sha256,new_sha256) LOOP
  v_function:=pg_catalog.to_regprocedure(v_item.signature);
  IF v_function IS NULL THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_FUNCTION_UNEXPECTED' USING ERRCODE='55000';
  END IF;
  SELECT p.*,l.lanname INTO STRICT v_proc FROM pg_catalog.pg_proc p
   JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE p.oid=v_function;
  IF v_proc.proowner<>v_item.owner_name::regrole OR v_proc.lanname<>'plpgsql'
   OR NOT v_proc.prosecdef OR v_proc.provolatile<>'v' OR v_proc.prokind<>'f'
   OR v_proc.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, mt, pg_temp']::text[]
   OR pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(v_proc.prosrc,'UTF8')),'hex')<>v_item.old_sha256
   OR (length(v_proc.prosrc)-length(pg_catalog.replace(v_proc.prosrc,v_old,'')))<>length(v_old) THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_FUNCTION_UNEXPECTED' USING ERRCODE='55000';
  END IF;
  v_before:=v_before || pg_catalog.jsonb_build_object(v_item.signature,
   (SELECT to_jsonb(p) FROM pg_catalog.pg_proc p WHERE p.oid=v_function));
  v_comments:=v_comments || pg_catalog.jsonb_build_object(v_item.signature,
   pg_catalog.obj_description(v_function,'pg_proc'));
 END LOOP;

 -- A temporary schema CREATE bit is required by CREATE OR REPLACE under each
 -- existing function owner. It is not inherited by the installer or runtime.
 GRANT CREATE ON SCHEMA mt TO mt_task_plan_lookup,mt_task_plan_case_reader;
 FOR v_item IN SELECT * FROM (VALUES
  ('mt.task_create_execution_plan(uuid,uuid,text,text,text[],text,uuid,text,text,text)',
   'mt_task_plan_case_reader','53bf1ff1c201a91c761dbebde0826e47e5bdb1d7ed7d31a322bc30b3bdcb0a94'),
  ('mt.task_create_plan_metadata(uuid,uuid,text,text,text[],text)',
   'mt_task_plan_lookup','cc0177977ebe6aca94c7fcfbb0b7d6689eb55596a6c01470d87a886990100067')
 ) AS expected(signature,owner_name,new_sha256) LOOP
  v_function:=pg_catalog.to_regprocedure(v_item.signature);
  SELECT to_jsonb(p) INTO STRICT v_after FROM pg_catalog.pg_proc p WHERE p.oid=v_function;
  IF v_after IS DISTINCT FROM v_before->v_item.signature THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_FUNCTION_UNEXPECTED' USING ERRCODE='55000';
  END IF;
  v_definition:=pg_catalog.pg_get_functiondef(v_function);
  IF (length(v_definition)-length(pg_catalog.replace(v_definition,v_old,'')))<>length(v_old) THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_PATCH_UNEXPECTED' USING ERRCODE='55000';
  END IF;
  EXECUTE pg_catalog.format('SET LOCAL ROLE %I',v_item.owner_name);
  EXECUTE pg_catalog.replace(v_definition,v_old,v_new);
  EXECUTE pg_catalog.format('SET LOCAL ROLE %I',v_installer);
  IF current_user<>v_installer THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_INSTALLER_UNSAFE' USING ERRCODE='55000';
  END IF;
  SELECT to_jsonb(p) INTO STRICT v_after FROM pg_catalog.pg_proc p WHERE p.oid=v_function;
  IF pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(v_after->>'prosrc','UTF8')),'hex')<>v_item.new_sha256
   OR (v_after-'prosrc') IS DISTINCT FROM ((v_before->v_item.signature)-'prosrc')
   OR coalesce(to_jsonb(pg_catalog.obj_description(v_function,'pg_proc')),'null'::jsonb)
      IS DISTINCT FROM v_comments->v_item.signature THEN
   RAISE EXCEPTION 'TASK_CREATION_GENERATION_METADATA_CHANGED' USING ERRCODE='55000';
  END IF;
 END LOOP;
 REVOKE CREATE ON SCHEMA mt FROM mt_task_plan_lookup,mt_task_plan_case_reader;
 IF pg_catalog.has_schema_privilege('mt_task_plan_lookup','mt','CREATE')
  OR pg_catalog.has_schema_privilege('mt_task_plan_case_reader','mt','CREATE')
  OR v_schema_acl IS DISTINCT FROM (SELECT nspacl FROM pg_catalog.pg_namespace WHERE nspname='mt') THEN
  RAISE EXCEPTION 'TASK_CREATION_GENERATION_PRIVILEGE_LEAK' USING ERRCODE='55000';
 END IF;
END
$generation_json$;
