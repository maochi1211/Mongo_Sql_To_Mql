-- 創建 cutdatetransform_record_new 表
CREATE TABLE IF NOT EXISTS cutdatetransform_record_new (
    id SERIAL PRIMARY KEY,  
    driver_id VARCHAR(10) NOT NULL,  
    cutday TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cutdatestarttime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cutdateendtime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    drive_time INT NOT NULL
);

-- **建立索引（這裡正確使用 CREATE INDEX）**
CREATE INDEX idx_driver_id ON cutdatetransform_record_new(driver_id);

-- 創建 track_record3_new 表
CREATE TABLE IF NOT EXISTS track_record3_new (
  id BIGSERIAL PRIMARY KEY,  -- 使用 BIGSERIAL 代替 AUTO_INCREMENT
  real_drive VARCHAR(10) NOT NULL,
  time_day TIMESTAMP NOT NULL DEFAULT NOW(),
  start_time TIMESTAMP NOT NULL DEFAULT NOW(),
  end_time TIMESTAMP NOT NULL DEFAULT NOW(),
  drive_time INTEGER NOT NULL,
  mile DOUBLE PRECISION NOT NULL,
  CONSTRAINT fk_track_record_real_drive
    FOREIGN KEY (real_drive) REFERENCES CutDateTransform_Record_New(driver_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
