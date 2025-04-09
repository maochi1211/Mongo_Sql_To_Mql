import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pandas as pd

# ========== 讀取 .env ==========
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGO_DB")
collection_name = os.getenv("MONGO_COLLECTION")

# ========== DEBUG：環境變數顯示 ==========
st.sidebar.subheader("🔍 環境變數檢查")
st.sidebar.write("DB Name:", db_name)
st.sidebar.write("Collection:", collection_name)

# ========== MongoDB 連線 ==========
try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) # Add timeout
    client.admin.command('ping')
    st.sidebar.success("✅ 成功連線 MongoDB")
except Exception as e:
    st.sidebar.error(f"❌ 無法連線 MongoDB: {e}")
    st.stop()

db = client[db_name]
collection = db[collection_name]

# ========== 工具函數 ==========
def get_date_range(date, past_days=7):
    end_of_day = datetime.combine(date, datetime.max.time())
    start_of_day = end_of_day - timedelta(days=past_days - 1)
    start_of_day = datetime.combine(start_of_day.date(), datetime.min.time())
    return start_of_day, end_of_day

def get_all_driver_ids():
    try:
        ids = collection.distinct("driverId")
        st.sidebar.write("📋 取得的 driverId 數量：", len(ids))
        return [str(id) for id in ids if id is not None] # Filter out None if necessary
    except Exception as e:
        st.sidebar.error(f"❌ 取得 driverId 時發生錯誤: {e}")
        return []


def get_aggregation_pipeline(driver_ids, start_of_day, end_of_day):
    # Convert driver_ids to appropriate type if they are stored as numbers in DB
    # Example: try converting to int if that's the storage type
    processed_driver_ids = []
    for driver_id in driver_ids:
        try:
           # Change this based on how driverId is stored in your MongoDB
           # If it's stored as string, no conversion needed:
           processed_driver_ids.append(driver_id)
           # If it's stored as integer:
           # processed_driver_ids.append(int(driver_id))
           # If it's stored as ObjectId:
           # from bson import ObjectId
           # processed_driver_ids.append(ObjectId(driver_id))
        except ValueError:
           st.warning(f"無法處理的 driverId 格式: {driver_id}")


    return [
        # Ensure driverId type matches the database storage type
        {"$match": {"driverId": {"$in": processed_driver_ids}}},
        {"$unwind": "$trackRecord3News"},
        {"$match": {
            "trackRecord3News.startTime": {"$gte": start_of_day, "$lt": end_of_day}
        }},
        {"$group": {
            "_id": "$driverId",
            "totalDriveTime": {"$sum": "$trackRecord3News.driveTime"}
        }}
    ]

def query_drive_time(driver_ids, date, past_days=7):
    start_of_day, end_of_day = get_date_range(date, past_days)
    pipeline = get_aggregation_pipeline(driver_ids, start_of_day, end_of_day)
    st.write("執行查詢中...") # Add user feedback
    try:
        result = list(collection.aggregate(pipeline))
        st.write(f"查詢完成，找到 {len(result)} 筆結果。") # Add user feedback
        return result, pipeline
    except Exception as e:
        st.error(f"❌ 執行聚合時發生錯誤：{e}")
        return [], pipeline

# 分批顯示為 DataFrame 表格 + lazy load
def show_results_lazy_table(results, key_prefix="lazy", batch_size=10):
    # --- FIX: Check if results list is empty first ---
    if not results:
        st.info("ℹ️ 查無符合條件的資料。")
        return # Exit the function if there's no data

    key = f"{key_prefix}_visible_count"
    if key not in st.session_state:
        st.session_state[key] = batch_size

    visible_count = st.session_state[key]
    # Ensure visible_count doesn't exceed results length unnecessarily
    visible_count = min(visible_count, len(results))
    to_show = results[:visible_count]

    # --- FIX: Check if the slice 'to_show' has data before creating DataFrame ---
    if not to_show:
         # This might happen if visible_count somehow becomes 0 or negative,
         # or if results was non-empty but became empty (less likely here)
         st.info("ℹ️ 沒有更多資料可載入。") # Or handle appropriately
         # Still show the button potentially, if more data exists beyond visible_count
    else:
        # --- Create DataFrame only if 'to_show' is not empty ---
        df = pd.DataFrame(to_show)

        # Rename the column - this should be safe now as df is not empty
        # and aggregation guarantees _id if results are present.
        df.rename(columns={"_id": "driverId"}, inplace=True)

        # --- FIX: Get column options from the actual DataFrame ---
        sortable_columns = [col for col in ["driverId", "totalDriveTime"] if col in df.columns]
        if not sortable_columns:
             st.warning("⚠️ DataFrame 中沒有可排序的欄位 ('driverId', 'totalDriveTime')。")
             st.dataframe(df.reset_index(drop=True), use_container_width=True) # Display anyway
             # Skip sorting if no sortable columns found
        else:
             default_sort_col = sortable_columns[0]
             sort_col = st.selectbox("🔽 選擇排序欄位", sortable_columns, index=sortable_columns.index(default_sort_col), key=f"{key_prefix}_sort_col")
             sort_order = st.radio("排序方式", ["升冪", "降冪"], horizontal=True, key=f"{key_prefix}_sort_order")
             ascending = sort_order == "升冪"
             df.sort_values(by=sort_col, ascending=ascending, inplace=True)
             st.dataframe(df.reset_index(drop=True), use_container_width=True)


    # --- Load More Button Logic ---
    if visible_count < len(results):
        if st.button("➕ 載入更多", key=f"{key_prefix}_load_more_button"):
            st.session_state[key] += batch_size
            st.rerun() # --- FIX: Add rerun to refresh the table view ---

# ========== Streamlit UI ==========
st.title("🚗 駕駛工時查詢系統")

tab1, tab2 = st.tabs(["查詢全部司機", "查詢特定司機"])

with tab1:
    # Use a unique key for the date input in this tab
    date_tab1 = st.date_input("📅 請選擇查詢日期（含前七天）", value=datetime(2023, 10, 7), key="date_tab1")

    # State management specific to tab1
    session_key_results = "tab1_last_results"
    session_key_pipeline = "tab1_last_pipeline"
    session_key_date = "tab1_last_query_date"
    session_key_lazy_count = "tab1_lazy_visible_count"

    # Reset lazy count if date changes
    if session_key_lazy_count in st.session_state and st.session_state.get(session_key_date) != date_tab1:
        st.session_state[session_key_lazy_count] = 10 # Reset to initial batch size
        # Clear old results when date changes
        if session_key_results in st.session_state:
             del st.session_state[session_key_results]
        if session_key_pipeline in st.session_state:
             del st.session_state[session_key_pipeline]

    if st.button("查詢全部司機工時", key="button_tab1"):
        st.session_state[session_key_lazy_count] = 10 # Reset count on new query
        st.session_state[session_key_date] = date_tab1
        with st.spinner("正在查詢所有司機資料..."): # Add spinner
            all_driver_ids = get_all_driver_ids()
            if all_driver_ids: # Only query if IDs were found
                 results, pipeline = query_drive_time(all_driver_ids, date_tab1)
                 st.session_state[session_key_results] = results
                 st.session_state[session_key_pipeline] = pipeline
            else:
                 st.error("無法獲取任何司機 ID，請檢查 MongoDB 連線或資料。")
                 # Clear previous results if driver IDs couldn't be fetched
                 if session_key_results in st.session_state:
                      del st.session_state[session_key_results]
                 if session_key_pipeline in st.session_state:
                      del st.session_state[session_key_pipeline]


    # Display results if they exist in session state for tab1
    if session_key_results in st.session_state:
        st.subheader("🛠 MongoDB 查詢語法")
        st.json(st.session_state[session_key_pipeline])

        st.subheader(f"📊 查詢結果（共 {len(st.session_state[session_key_results])} 筆）")
        # Pass the specific session state results and a unique key prefix for lazy loading
        show_results_lazy_table(st.session_state[session_key_results], key_prefix="tab1_lazy")
    # Add a message if query was run but found nothing
    elif session_key_date in st.session_state and session_key_date == date_tab1 and session_key_results not in st.session_state :
         st.info("ℹ️ 在此日期範圍內查無任何司機的工時記錄。")


with tab2:
    # Use unique keys for widgets in this tab
    date_tab2 = st.date_input("📅 請選擇查詢日期（含前七天）", key="date_tab2", value=datetime(2023, 10, 7))
    driver_id_input = st.text_input("請輸入司機ID，例如 65", key="driverId_tab2")

    if st.button("查詢該司機工時", key="button_tab2"):
        driver_id = driver_id_input.strip()
        if driver_id:
            with st.spinner(f"正在查詢司機 {driver_id} 的資料..."): # Add spinner
                # Note: query_drive_time expects a list of IDs
                results, pipeline = query_drive_time([driver_id], date_tab2)

                st.subheader("🛠 MongoDB 查詢語法")
                st.json(pipeline)

                if results:
                    df = pd.DataFrame(results)
                    df.rename(columns={"_id": "driverId"}, inplace=True)
                    st.dataframe(df)
                else:
                    st.warning(f"查無司機 {driver_id} 在此日期範圍內的工時資料。")
        else:
            st.error("請輸入司機ID。")