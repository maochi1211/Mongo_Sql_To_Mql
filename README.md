## Demo SQL to MQL 
### 給定日期，找到各司機在此日期的前七天實際工時。
#### 
- 在 PostgreSQL 中，原儲存成兩張 Table 並且執行 2~3 個 Qeury 完成任務。
- 在 Mongo DB 中，可以合併儲存成一個 Collection，用一個 Aggregate 完成。
### =========
## 步驟
1. 創建一個容器化的 PostgreSQL 資料庫並 Insert 模擬資料
2. 用 Mongo DB Relational Migrator 搬遷資料至 Mongo Atlas
3. Mongo Shell 執行查詢 JS 腳本


### =========

## 環境與資料準備 

Docker Version: 4.25.0
Mongo DB Relational Migrator Version: 1.11.0
PostgreSQL Version : 17.2
Mongo Atlas Version: 8.0.4
