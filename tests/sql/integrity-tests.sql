-- Synthetic-only isolated database. Not approval or production data.
BEGIN;
INSERT INTO mt.organizations(org_id,name) VALUES
('00000000-0000-4000-8000-000000000001','SYN-ORG-A'),
('00000000-0000-4000-8000-000000000002','SYN-ORG-B');
INSERT INTO mt.users(user_id,org_id,subject,enabled) VALUES
('10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','SYN-ACTOR-A',true),
('10000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','SYN-ACTOR-B',true);
INSERT INTO mt.cases(case_id,org_id,display_code,status) VALUES
('20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','SYN-CASE-A','ACTIVE'),
('20000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','SYN-CASE-B','ACTIVE');
INSERT INTO mt.case_membership(membership_id,case_id,org_id,user_id) VALUES
('30000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001');
INSERT INTO mt.source_registry(source_id,case_id,org_id,name,source_type,authorization_ref,purpose,authorization_status,authorization_version) VALUES
('40000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','SYN-A','synthetic','fixture-not-real-authority',ARRAY['analysis'],'verified','fixture-v1'),
('40000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','SYN-B','synthetic','fixture-not-real-authority',ARRAY['analysis'],'verified','fixture-v1');
INSERT INTO mt.content_item(content_id,case_id,org_id,source_id,discovered_at,status) VALUES
('50000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','40000000-0000-4000-8000-000000000001',now(),'SYN'),
('50000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','40000000-0000-4000-8000-000000000002',now(),'SYN');
INSERT INTO mt.object_version(object_id,case_id,org_id,bucket_alias,object_key,version_id,sha256,size_bytes) VALUES
('60000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','synthetic','a','v1',repeat('0',64),1024),
('60000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','synthetic','b','v1',repeat('1',64),1024);
INSERT INTO mt.media_asset(asset_id,case_id,org_id,content_id,source_id,object_id,sha256,mime,size_bytes,kind,mapping_version,state) VALUES
('70000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','50000000-0000-4000-8000-000000000001','40000000-0000-4000-8000-000000000001','60000000-0000-4000-8000-000000000001',repeat('0',64),'image/png',1024,'original','fixture-v1','VALID'),
('70000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','50000000-0000-4000-8000-000000000002','40000000-0000-4000-8000-000000000002','60000000-0000-4000-8000-000000000002',repeat('1',64),'image/png',1024,'original','fixture-v1','VALID');
INSERT INTO mt.analysis_task(task_id,case_id,org_id,asset_id,scene,priority,state,policy_version,modules,report_eligibility) VALUES
('80000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','70000000-0000-4000-8000-000000000001','synthetic','normal','QUEUED','fixture-v1',ARRAY['MEDIA'],'draft_only');
INSERT INTO mt.task_run(task_run_id,case_id,org_id,task_id,run_version,input_sha256,dag_version,policy_version) VALUES
('90000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,repeat('0',64),'fixture-v1','fixture-v1');
INSERT INTO mt.task_result(result_id,case_id,org_id,task_id,run_version,result_version,sha256,policy_version) VALUES
('a0000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,repeat('0',64),'fixture-v1');
INSERT INTO mt.evidence_item(evidence_id,case_id,org_id,task_id,run_version,result_version,asset_id,type,object_id,sha256,captured_at,mapping_version,authorization_version,immutable_state) VALUES
('b0000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,'70000000-0000-4000-8000-000000000001','original','60000000-0000-4000-8000-000000000001',repeat('0',64),now(),'fixture-v1','fixture-v1','RECORDED');
INSERT INTO mt.audit_event(event_id,org_id,case_id,actor_id,action,object_type,outcome,request_id,occurred_at) VALUES
('c0000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','synthetic.test','fixture','allowed','d0000000-0000-4000-8000-000000000001',now());
COMMIT;
DO $$ BEGIN
 IF (SELECT count(*) FROM mt.media_asset)<>2 THEN RAISE EXCEPTION 'seed missing'; END IF;
 RAISE NOTICE 'PASS SQL-001 valid linked synthetic fixtures';
 IF (SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname='mt_runtime') THEN RAISE EXCEPTION 'runtime privilege unsafe'; END IF;
 RAISE NOTICE 'PASS SQL-002 runtime not superuser or BYPASSRLS';
 BEGIN INSERT INTO mt.organizations(org_id,name) VALUES('00000000-0000-4000-8000-000000000001','duplicate');RAISE EXCEPTION 'duplicate accepted';EXCEPTION WHEN unique_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-003 duplicate primary key rejected';
 BEGIN UPDATE mt.analysis_task SET progress=1.1;RAISE EXCEPTION 'progress accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-004 progress range enforced';
 BEGIN UPDATE mt.analysis_task SET state='BOGUS';RAISE EXCEPTION 'state accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-005 unknown task state rejected';
 BEGIN INSERT INTO mt.shot(shot_id,case_id,org_id,asset_id,start_ms,end_ms,mapping_version) VALUES('e0000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','70000000-0000-4000-8000-000000000001',10,5,'v1');RAISE EXCEPTION 'bad range accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-006 reversed time interval rejected';
 BEGIN INSERT INTO mt.shot(shot_id,case_id,org_id,asset_id,start_ms,end_ms,mapping_version) VALUES('e0000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','70000000-0000-4000-8000-000000000002',0,100,'v1');RAISE EXCEPTION 'cross case accepted';EXCEPTION WHEN foreign_key_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-007 cross-case asset relation rejected';
 BEGIN UPDATE mt.media_asset SET sha256=repeat('9',64);RAISE EXCEPTION 'original changed';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-008 original provenance update rejected';
 BEGIN UPDATE mt.evidence_item SET sha256=repeat('9',64);RAISE EXCEPTION 'evidence changed';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-009 evidence update rejected';
 BEGIN DELETE FROM mt.evidence_item;RAISE EXCEPTION 'evidence deleted';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-010 evidence delete rejected';
 BEGIN TRUNCATE mt.evidence_item CASCADE;RAISE EXCEPTION 'evidence truncated';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-011 evidence truncate rejected';
 BEGIN UPDATE mt.audit_event SET action='tamper';RAISE EXCEPTION 'audit changed';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-012 audit update rejected';
 BEGIN DELETE FROM mt.audit_event;RAISE EXCEPTION 'audit deleted';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-013 audit delete rejected';
 BEGIN TRUNCATE mt.audit_event;RAISE EXCEPTION 'audit truncated';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-014 audit truncate rejected';
END $$;
SET ROLE mt_runtime;
SELECT set_config('app.actor_id','',false),set_config('app.org_id','',false);
DO $$ BEGIN IF (SELECT count(*) FROM mt.media_asset)<>0 THEN RAISE EXCEPTION 'no context visible'; END IF;RAISE NOTICE 'PASS SQL-015 missing context default denied';END $$;
SELECT set_config('app.actor_id','10000000-0000-4000-8000-000000000001',false),set_config('app.org_id','00000000-0000-4000-8000-000000000001',false);
DO $$ BEGIN IF (SELECT count(*) FROM mt.media_asset)<>1 THEN RAISE EXCEPTION 'case scope wrong'; END IF;RAISE NOTICE 'PASS SQL-016 valid member sees only authorized case';END $$;
DO $$ BEGIN
 BEGIN INSERT INTO mt.shot(shot_id,case_id,org_id,asset_id,start_ms,end_ms,mapping_version) VALUES('e0000000-0000-4000-8000-000000000003','20000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-000000000001','70000000-0000-4000-8000-000000000002',0,100,'v1');RAISE EXCEPTION 'cross case write accepted';EXCEPTION WHEN insufficient_privilege THEN NULL;END;
 RAISE NOTICE 'PASS SQL-017 unauthorized case insert rejected';
END $$;
RESET ROLE;
UPDATE mt.case_membership SET revoked_at=now();
SET ROLE mt_runtime;
DO $$ BEGIN IF (SELECT count(*) FROM mt.media_asset)<>0 THEN RAISE EXCEPTION 'revocation ineffective'; END IF;RAISE NOTICE 'PASS SQL-018 revoked membership immediately invisible to new query';END $$;
RESET ROLE;
UPDATE mt.case_membership SET revoked_at=NULL;
INSERT INTO mt.approval_request(approval_id,org_id,case_id,object_type,object_id,object_version,run_version,result_version,purpose,policy_version,requested_by,state,reason) VALUES
('f0000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','task','80000000-0000-4000-8000-000000000001',1,1,1,'seal','fixture-v1','10000000-0000-4000-8000-000000000001','REQUESTED','synthetic fixture not real approval');
DO $$ BEGIN
 BEGIN INSERT INTO mt.evidence_package(package_id,case_id,org_id,task_id,run_version,result_version,version,manifest_sha256,approval_id,signature_status,retention_policy_version,state) VALUES('f1000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,1,repeat('0',64),'f0000000-0000-4000-8000-000000000001','mock','fixture-v1','SEALED');RAISE EXCEPTION 'unapproved seal accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-019 pending approval cannot seal';
END $$;
UPDATE mt.approval_request SET state='APPROVED',purpose='report_export';
DO $$ BEGIN
 BEGIN INSERT INTO mt.evidence_package(package_id,case_id,org_id,task_id,run_version,result_version,version,manifest_sha256,approval_id,signature_status,retention_policy_version,state) VALUES('f1000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,1,repeat('0',64),'f0000000-0000-4000-8000-000000000001','mock','fixture-v1','SEALED');RAISE EXCEPTION 'wrong purpose accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-020 approval purpose binding enforced';
END $$;
UPDATE mt.approval_request SET purpose='seal',object_version=2;
DO $$ BEGIN
 BEGIN INSERT INTO mt.evidence_package(package_id,case_id,org_id,task_id,run_version,result_version,version,manifest_sha256,approval_id,signature_status,retention_policy_version,state) VALUES('f1000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,1,repeat('0',64),'f0000000-0000-4000-8000-000000000001','mock','fixture-v1','SEALED');RAISE EXCEPTION 'stale approval accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-021 approval object version binding enforced';
END $$;
UPDATE mt.approval_request SET object_version=1;
INSERT INTO mt.evidence_package(package_id,case_id,org_id,task_id,run_version,result_version,version,manifest_sha256,approval_id,signature_status,retention_policy_version,state) VALUES('f1000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,1,repeat('0',64),'f0000000-0000-4000-8000-000000000001','mock','fixture-v1','SEALED');
DO $$ BEGIN RAISE NOTICE 'PASS SQL-022 matching synthetic approval can insert package';END $$;
INSERT INTO mt.operation_token(token_id,case_id,org_id,approval_id,actor_id,purpose,object_id,object_version,token_sha256,expires_at) VALUES('f2000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','f0000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','seal','80000000-0000-4000-8000-000000000001',1,repeat('3',64),now()+interval '1 hour');
UPDATE mt.operation_token SET consumed_at=now();
DO $$ BEGIN
 BEGIN UPDATE mt.operation_token SET consumed_at=now();RAISE EXCEPTION 'used token accepted';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-023 consumed operation token cannot be reused';
END $$;
DO $$ BEGIN
 BEGIN UPDATE mt.task_result SET sha256=repeat('9',64);RAISE EXCEPTION 'history changed';EXCEPTION WHEN SQLSTATE '55000' THEN NULL;END;
 RAISE NOTICE 'PASS SQL-024 result snapshot immutable';
END $$;
UPDATE mt.approval_request SET run_version=2;
DO $$ BEGIN
 BEGIN INSERT INTO mt.evidence_package(package_id,case_id,org_id,task_id,run_version,result_version,version,manifest_sha256,approval_id,signature_status,retention_policy_version,state) VALUES('f1000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000001','80000000-0000-4000-8000-000000000001',1,1,2,repeat('0',64),'f0000000-0000-4000-8000-000000000001','mock','fixture-v1','SEALED');RAISE EXCEPTION 'wrong run accepted';EXCEPTION WHEN check_violation THEN NULL;END;
 RAISE NOTICE 'PASS SQL-025 approval run binding enforced independently of result version';
END $$;
