-- Append-only event facts must identify an existing fixed task run.
-- No state transition policy, history rewriting or runtime adoption is implied.
ALTER TABLE mt.task_event ADD CONSTRAINT task_event_run_identity_fk
    FOREIGN KEY (case_id,task_id,run_version)
    REFERENCES mt.task_run(case_id,task_id,run_version) NOT VALID;

ALTER TABLE mt.task_event ADD CONSTRAINT task_event_from_state_check
    CHECK (from_state IS NULL OR from_state IN (
        'CREATED','QUEUED','RUNNING','WAIT_REVIEW','REVIEWING','SUCCEEDED',
        'FAILED','RETURNED','CANCEL_REQUESTED','CANCELLED','ARCHIVED'
    )) NOT VALID;

ALTER TABLE mt.task_event ADD CONSTRAINT task_event_to_state_check
    CHECK (to_state IN (
        'CREATED','QUEUED','RUNNING','WAIT_REVIEW','REVIEWING','SUCCEEDED',
        'FAILED','RETURNED','CANCEL_REQUESTED','CANCELLED','ARCHIVED'
    )) NOT VALID;

-- The migration runner commits the complete upgrade and ledger together.
-- Invalid historical rows abort it; never manufacture runs or edit old facts.
ALTER TABLE mt.task_event VALIDATE CONSTRAINT task_event_run_identity_fk;
ALTER TABLE mt.task_event VALIDATE CONSTRAINT task_event_from_state_check;
ALTER TABLE mt.task_event VALIDATE CONSTRAINT task_event_to_state_check;
