-- Isolated representative design only. Never apply to the existing PoC or business database.
CREATE SCHEMA isolation_probe;
CREATE ROLE probe_app LOGIN NOSUPERUSER NOBYPASSRLS;
CREATE TABLE isolation_probe.grants (
  subject_id uuid NOT NULL, org_id uuid NOT NULL, case_id uuid NOT NULL,
  can_write boolean NOT NULL DEFAULT false, revoked boolean NOT NULL DEFAULT false,
  PRIMARY KEY(subject_id,org_id,case_id)
);
CREATE TABLE isolation_probe.results (
  id uuid PRIMARY KEY, org_id uuid NOT NULL, case_id uuid NOT NULL,
  task_id uuid NOT NULL, run_version integer NOT NULL CHECK(run_version>0),
  result_version integer NOT NULL CHECK(result_version>0), payload jsonb NOT NULL,
  UNIQUE(org_id,case_id,task_id,run_version,result_version)
);
-- Trusted middleware sets these LOCAL values from verified identity, never from request headers/body.
-- A shared DB login can forge custom settings; this is not an identity provider or SQL-injection defense.
ALTER TABLE isolation_probe.results ENABLE ROW LEVEL SECURITY;
ALTER TABLE isolation_probe.results FORCE ROW LEVEL SECURITY;
CREATE POLICY authorized_read ON isolation_probe.results FOR SELECT TO probe_app USING (
  org_id = nullif(current_setting('mt.org_id',true),'')::uuid AND
  case_id = nullif(current_setting('mt.case_id',true),'')::uuid AND
  EXISTS(SELECT 1 FROM isolation_probe.grants g WHERE
    g.subject_id = nullif(current_setting('mt.subject_id',true),'')::uuid AND
    g.org_id=results.org_id AND g.case_id=results.case_id AND NOT g.revoked)
);
CREATE POLICY authorized_append ON isolation_probe.results FOR INSERT TO probe_app WITH CHECK (
  org_id = nullif(current_setting('mt.org_id',true),'')::uuid AND
  case_id = nullif(current_setting('mt.case_id',true),'')::uuid AND
  EXISTS(SELECT 1 FROM isolation_probe.grants g WHERE
    g.subject_id = nullif(current_setting('mt.subject_id',true),'')::uuid AND
    g.org_id=results.org_id AND g.case_id=results.case_id AND NOT g.revoked AND g.can_write)
);
GRANT USAGE ON SCHEMA isolation_probe TO probe_app;
GRANT SELECT ON isolation_probe.grants TO probe_app;
GRANT SELECT,INSERT ON isolation_probe.results TO probe_app;
