ALTER TABLE mt.upload_session ADD COLUMN duplicate_of uuid;
ALTER TABLE mt.upload_session ADD CONSTRAINT upload_duplicate_same_case
    FOREIGN KEY(case_id,duplicate_of) REFERENCES mt.media_asset(case_id,asset_id);
COMMENT ON COLUMN mt.upload_session.duplicate_of IS '同案件重复资产引用；仅在完整摘要/媒体校验成功后登记，读取仍核验当前案件权限；NULL表示未确定重复。';
