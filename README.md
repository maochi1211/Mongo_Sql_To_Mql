## Demo SQL to MQL 
- 教學文:https://hackmd.io/lEVqH0rQQoyKRkDZFWd1uA?view

### 給定日期，找到各司機在此日期前七天的實際工時。
#### 
- 原先在 PostgreSQL 中，存成兩張 Table 且執行 2~3 個 Qeury 完成查詢。
- 轉至 Mongo DB 中，合併存成一個 Collection，用一個 Aggregate 完成查詢。
### =========
## 步驟
1. 創建一個容器化的 PostgreSQL 資料庫並 Insert 模擬資料
2. 用 Mongo DB Relational Migrator 搬遷資料至 Mongo Atlas
3. Mongo Shell 執行查詢 JS 腳本


### =========

## 環境與資料準備 

- Docker Version: 4.25.0
- Mongo DB Relational Migrator Version: 1.11.0
- PostgreSQL Version : 17.2
- Mongo Atlas Version: 8.0.4
