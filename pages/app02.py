import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta, time # Import time
from dotenv import load_dotenv
import os
import pandas as pd
import traceback

st.set_page_config(layout="wide")
# ... (讀取 .env, 環境變數顯示, MongoDB 連線 部分不變, 確保 main_collection 和 target_collection 都獲取) ...
# ========== 讀取 .env ==========
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
db_name = "DEMO02"
main_collection_name = os.getenv("MONGO_COLLECTION", "cutdatetransformRecordNew")
target_collection_name = "trackRecord3New"

# ========== DEBUG：環境變數顯示 ==========
st.sidebar.subheader("🔍 環境變數檢查")
st.sidebar.write(f"DB Name: `{db_name}`")
st.sidebar.write(f"主 Collection Name: `{main_collection_name}`")
st.sidebar.write(f"目標 Collection Name: `{target_collection_name}`")

# ========== MongoDB 連線 ==========
try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    st.sidebar.success("✅ 成功連線 MongoDB")
    db = client[db_name]
    main_collection = db[main_collection_name]
    target_collection = db[target_collection_name]
    st.sidebar.write(f"`{main_collection_name}` Doc 數量: {main_collection.estimated_document_count()}")
    st.sidebar.write(f"`{target_collection_name}` Doc 數量: {target_collection.estimated_document_count()}")
except Exception as e:
    st.sidebar.error(f"❌ 無法連線 MongoDB 或選擇集合: {e}")
    st.sidebar.code(traceback.format_exc())
    st.error("應用程式無法啟動：無法連接到資料庫。請檢查側邊欄的錯誤訊息。")
    st.stop()

# ========== 工具函數 ==========

# --- 修改日期範圍函數，以匹配 cutday 的篩選邏輯 ---
def get_cutday_range_for_pipeline(end_date, past_days=7):
    """
    計算用於篩選 cutday 的日期範圍。
    返回 7 天週期的第一天 00:00:00 (inclusive) 和
    最後一天之後那天 00:00:00 (exclusive)。
    """
    # end_date 是用戶選擇的日期
    last_day_start = datetime.combine(end_date, time.min) # 最後一天 00:00:00
    # 第一天 = 最後一天 - (7 - 1) 天
    first_day_start = last_day_start - timedelta(days=past_days - 1)
    # 結束邊界 = 最後一天 + 1 天
    day_after_last_start = last_day_start + timedelta(days=1)

    st.sidebar.write(f"Cutday 篩選範圍: >= {first_day_start}, < {day_after_last_start}")
    return first_day_start, day_after_last_start

# get_all_driver_ids 函數保持不變，從主集合獲取 ID
def get_all_driver_ids(collection_to_get_ids_from):
    """從指定集合獲取所有不重複的 driverId (確保是字串)"""
    st.sidebar.write(f"從 `{collection_to_get_ids_from.name}` 獲取初始 Driver IDs...")
    try:
        ids = collection_to_get_ids_from.distinct("driverId")
        valid_ids = [str(id_val) for id_val in ids if id_val is not None and str(id_val).strip() != ""]
        st.sidebar.write(f"📋 取得的有效 driverId 數量：{len(valid_ids)}")
        if not valid_ids:
             st.sidebar.warning("未能從主集合獲取任何有效的 driverId。")
        return valid_ids
    except Exception as e:
        st.sidebar.error(f"❌ 獲取 driverId 時出錯: {e}")
        st.sidebar.code(traceback.format_exc())
        return []

# --- 新的 Pipeline 生成函數 (V3) ---
def get_aggregation_pipeline_v3(driver_ids, start_of_first_day, start_of_day_after_last):
    """
    生成新的聚合管道，從主集合開始，並使用帶條件的 $lookup。
    """
    pipeline = [
      {
        "$match": {
          "driverId": { "$in": driver_ids },
          "cutday": {
            "$gte": start_of_first_day,
            "$lt": start_of_day_after_last
          }
        }
      },
      {
        "$lookup": {
          "from": target_collection_name, # Use variable for target collection name
          "let": {
            "lookup_driverId": "$driverId",
            "lookup_startOfDay": "$cutday",
            "lookup_endOfDayExclusive": { "$add": [ "$cutday", 86400000 ] }
          },
          "pipeline": [
            {
              "$match": {
                "$expr": {
                  "$and": [
                    { "$eq": [ "$realDrive", "$$lookup_driverId" ] },
                    { "$gte": [ "$startTime", "$$lookup_startOfDay" ] },
                    { "$lt": [ "$startTime", "$$lookup_endOfDayExclusive" ] }
                  ]
                }
              }
            },
            { "$project": { "_id": 0, "driveTime": 1 } }
          ],
          "as": "dailyMatchedTracks"
        }
      },
      # Unwind results - adjust if you need to keep drivers with 0 time
      { "$unwind": "$dailyMatchedTracks" },
      {
        "$group": {
          "_id": "$driverId",
          "totalDriveTime": { "$sum": "$dailyMatchedTracks.driveTime" }
        }
      },
      {
        "$project": { "_id": 0, "driverId": "$_id", "totalDriveTime": 1 }
      }
    ]
    return pipeline

# --- 新的查詢函數 (V3) ---
def query_drive_time_v3(collection_to_start_from, driver_ids_list, end_date, past_days=7):
    """
    在主集合上執行新的聚合查詢 (V3 Pipeline)。
    """
    if not driver_ids_list:
         st.warning("沒有提供 driver ID 進行查詢。")
         return [], []

    # 使用新的日期範圍函數
    start_of_first_day, start_of_day_after_last = get_cutday_range_for_pipeline(end_date, past_days)
    # 使用新的 pipeline 生成函數
    pipeline = get_aggregation_pipeline_v3(driver_ids_list, start_of_first_day, start_of_day_after_last)

    st.write(f"⏳ 正在主集合 `{collection_to_start_from.name}` 上執行聚合查詢 (V3)...")
    st.write(f"查詢條件: {len(driver_ids_list)} 個司機, 結束日期: {end_date.strftime('%Y-%m-%d')} (含前 {past_days} 天)")

    try:
        # 在主集合上執行 aggregate
        result = list(collection_to_start_from.aggregate(pipeline))
        st.success(f"✅ 查詢完成，聚合結果包含 {len(result)} 筆記錄。")
        return result, pipeline
    except Exception as e:
        st.error(f"❌ 在主集合執行聚合時發生錯誤 (V3)：{e}")
        st.code(traceback.format_exc())
        return [], pipeline

# --- show_results_lazy_table 函數理論上不需大改，因為輸出格式預期一致 ---
# 但為確保，我們還是用之前更新過的版本
def show_results_lazy_table(results, key_prefix="lazy", batch_size=10):
    """分批顯示為 DataFrame 表格 + lazy load (處理 $project 後的欄位名)"""
    if not results:
        st.info("ℹ️ 查無符合條件的資料可供顯示。")
        return

    key = f"{key_prefix}_visible_count"
    if key not in st.session_state:
        st.session_state[key] = batch_size

    visible_count = st.session_state.get(key, batch_size)
    visible_count = min(visible_count, len(results))
    to_show = results[:visible_count]

    if not to_show:
        st.info("ℹ️ 沒有更多資料可載入。")
    else:
        df = pd.DataFrame(to_show)
        # 因為 pipeline 最後用了 $project，結果應該直接有 "driverId"
        if 'driverId' not in df.columns and '_id' in df.columns:
             # 保留以防 $project 被移除
             df.rename(columns={"_id": "driverId"}, inplace=True)
        elif 'driverId' not in df.columns and '_id' not in df.columns:
             st.warning("⚠️ 聚合結果缺少 '_id' 或 'driverId' 欄位。")

        sortable_columns = [col for col in ["driverId", "totalDriveTime"] if col in df.columns]

        if sortable_columns:
            sort_col = st.selectbox(
                "🔽 選擇排序欄位", sortable_columns, key=f"{key_prefix}_sort_col", index=0
            )
            sort_order = st.radio(
                "排序方式", ["升冪", "降冪"], horizontal=True, key=f"{key_prefix}_sort_order"
            )
            ascending = sort_order == "升冪"
            try:
                 df.sort_values(by=sort_col, ascending=ascending, inplace=True)
                 st.dataframe(df.reset_index(drop=True), use_container_width=True)
            except Exception as e:
                 st.error(f"排序時出錯: {e}")
                 st.dataframe(df.reset_index(drop=True), use_container_width=True)
        else:
             st.warning("DataFrame 中缺少可排序欄位 ('driverId', 'totalDriveTime')。")
             st.dataframe(df.reset_index(drop=True), use_container_width=True)

    if visible_count < len(results):
        if st.button("➕ 載入更多", key=f"{key_prefix}_load_more_button"):
            st.session_state[key] = visible_count + batch_size
            st.rerun()

# ========== Streamlit UI ==========

st.title("🚗 駕駛工時查詢系統 v4 (按日歸屬)")

tab1, tab2 = st.tabs(["查詢全部司機", "查詢特定司機"])

# --- Tab 1: Query All Drivers ---
with tab1:
    st.header("查詢全部司機工時")
    date_tab1 = st.date_input(
        "📅 請選擇查詢**結束**日期（將查詢此日期及之前的 6 天，共 7 天）",
        value=datetime(2023, 10, 11), # 更新預設日期以匹配範例
        key="date_tab1_v4",
        help="例如選擇 10/11，將查詢 10/5 00:00:00 至 10/11 23:59:59 的數據，並按日歸屬加總"
    )

    SESSION_KEY_RESULTS_T1 = "tab1_results_v4"
    SESSION_KEY_PIPELINE_T1 = "tab1_pipeline_v4"
    SESSION_KEY_DATE_T1 = "tab1_date_v4"

    if st.button("🔄 開始查詢全部司機 (按日歸屬)", key="button_tab1_v4", type="primary"):
        if SESSION_KEY_RESULTS_T1 in st.session_state: del st.session_state[SESSION_KEY_RESULTS_T1]
        if SESSION_KEY_PIPELINE_T1 in st.session_state: del st.session_state[SESSION_KEY_PIPELINE_T1]
        st.session_state[SESSION_KEY_DATE_T1] = date_tab1

        with st.spinner("⚙️ 正在獲取司機列表並執行聚合查詢 (V3 Pipeline)..."):
            # 1. Get driver IDs from the main collection
            all_driver_ids = get_all_driver_ids(main_collection)
            if all_driver_ids:
                # 2. Run the NEW query function (V3) on the MAIN collection
                results, pipeline = query_drive_time_v3(
                    main_collection, # 查詢從主集合開始
                    all_driver_ids,
                    date_tab1,
                    past_days=7
                )
                st.session_state[SESSION_KEY_RESULTS_T1] = results
                st.session_state[SESSION_KEY_PIPELINE_T1] = pipeline
            else:
                 st.error("無法獲取任何司機 ID，查詢中止。")

    st.markdown("---")
    st.subheader("📊 查詢結果")

    if SESSION_KEY_RESULTS_T1 in st.session_state and st.session_state.get(SESSION_KEY_DATE_T1) == date_tab1:
        results_to_display = st.session_state[SESSION_KEY_RESULTS_T1]
        pipeline_to_display = st.session_state[SESSION_KEY_PIPELINE_T1]

        if results_to_display:
            st.success(f"查詢成功！共計算出 {len(results_to_display)} 位司機在此期間的總工時。")
            # 使用 show_results_lazy_table 顯示
            show_results_lazy_table(results_to_display, key_prefix="tab1_lazy_v4")

            with st.expander("🛠️ 查看執行的 MongoDB 查詢語法 (MQL V3)"):
                st.json(pipeline_to_display)
        else:
            st.info(f"ℹ️ 在 {date_tab1.strftime('%Y-%m-%d')} 及之前的 6 天內，未能計算出任何司機的工時記錄 (可能無匹配數據)。")
            with st.expander("🛠️ 查看執行的 MongoDB 查詢語法 (MQL V3)"):
                 st.json(pipeline_to_display)
    elif SESSION_KEY_DATE_T1 not in st.session_state or st.session_state.get(SESSION_KEY_DATE_T1) != date_tab1:
         st.info("請點擊 '開始查詢全部司機' 按鈕以載入數據。")


# --- Tab 2: Query Specific Driver ---
with tab2:
    st.header("查詢特定司機工時")
    date_tab2 = st.date_input(
        "📅 請選擇查詢**結束**日期（含前七天）", key="date_tab2_v4",
        value=datetime(2023, 10, 11),
        help="例如選擇 10/11，將查詢 10/5 00:00:00 至 10/11 23:59:59 的數據，並按日歸屬加總"
    )
    driver_id_input_t2 = st.text_input("🆔 請輸入司機 ID (例如: 6423)", key="driverId_tab2_v4")

    if st.button("🔍 查詢該司機工時 (按日歸屬)", key="button_tab2_v4"):
        driver_id = driver_id_input_t2.strip()
        if driver_id:
            with st.spinner(f"⚙️ 正在查詢司機 {driver_id} 的資料 (V3 Pipeline)..."):
                # Use the NEW query function (V3) on the MAIN collection
                results, pipeline = query_drive_time_v3(
                    main_collection, # 查詢從主集合開始
                    [str(driver_id)], # Pass ID as a list of strings
                    date_tab2,
                    past_days=7
                )

            st.markdown("---")
            st.subheader(f"📊 司機 {driver_id} 的查詢結果")

            if results:
                # 結果應該只有一條記錄 (或沒有)
                df = pd.DataFrame(results)
                # $project 應該已經處理了欄位名
                if 'driverId' not in df.columns and '_id' in df.columns:
                     df.rename(columns={"_id": "driverId"}, inplace=True) # Fallback rename
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"查無司機 {driver_id} 在 {date_tab2.strftime('%Y-%m-%d')} 及之前的 6 天內的工時資料 (按日歸屬計算)。")

            with st.expander("🛠️ 查看執行的 MongoDB 查詢語法 (MQL V3)"):
                st.json(pipeline)
        else:
            st.error("⚠️ 請輸入有效的司機 ID。")