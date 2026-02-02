import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time

# --- 1. Supabaseへの接続設定 ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. データベース操作関数 ---

def get_data():
    """Supabaseから全データを取得してDataFrame化"""
    response = supabase.table("todos").select("*").order("id", desc=True).execute()
    df = pd.DataFrame(response.data)
    # データが空の場合の列定義（エラー回避用）
    if df.empty:
        df = pd.DataFrame(columns=["id", "task", "latitude", "longitude", "is_done", "created_at"])
    return df

def handle_changes():
    """データエディタの変更内容をSupabaseに反映するコールバック関数"""
    changes = st.session_state.editor_changes
    # 現在の画面上のデータ（変更前の状態を知るために必要）
    current_df = st.session_state.current_df

    # 1. 削除された行の処理 (deleted_rows)
    # changes['deleted_rows'] には削除された行のインデックス番号のリストが入っています
    if changes["deleted_rows"]:
        for index in changes["deleted_rows"]:
            # 削除対象のIDを取得
            if 0 <= index < len(current_df):
                row_id = int(current_df.iloc[index]["id"])
                supabase.table("todos").delete().eq("id", row_id).execute()
                st.toast(f"ID:{row_id} を削除しました🗑️")

    # 2. 追加された行の処理 (added_rows)
    # changes['added_rows'] には {追加された行のデータ} のリストが入っています
    if changes["added_rows"]:
        for row in changes["added_rows"]:
            # 必須項目が空でないか簡易チェック（空ならデフォルト値や無視など）
            # ここでは task があれば登録するようにします
            if "task" in row and row["task"]:
                # latitude/longitude が入力されてなければデフォルト値を入れる等の処理も可
                new_data = {
                    "task": row.get("task"),
                    "latitude": row.get("latitude", 35.6812), # デフォルト東京駅
                    "longitude": row.get("longitude", 139.7671),
                    "is_done": row.get("is_done", False)
                }
                supabase.table("todos").insert(new_data).execute()
                st.toast("新しいタスクを追加しました✨")

    # 3. 編集された行の処理 (edited_rows)
    # changes['edited_rows'] は {インデックス: {変更された列: 新しい値}} の辞書です
    if changes["edited_rows"]:
        for index, updates in changes["edited_rows"].items():
            index = int(index)
            if 0 <= index < len(current_df):
                row_id = int(current_df.iloc[index]["id"])
                # Supabaseを更新
                supabase.table("todos").update(updates).eq("id", row_id).execute()
                st.toast(f"ID:{row_id} を更新しました✏️")

# --- 3. アプリケーション UI ---
st.set_page_config(page_title="Table Editor ToDo", layout="wide")
st.title("⚡️ Supabase Table Editor アプリ")
st.caption("下の表をExcelのように直接編集できます。変更は自動保存されます。")

# データのロード（初回またはリロード時）
if 'current_df' not in st.session_state:
    st.session_state.current_df = get_data()

# データを再取得ボタン（同期ズレ用）
if st.button("🔄 最新データを読み込む"):
    st.session_state.current_df = get_data()
    st.rerun()

# 画面レイアウト：左にテーブル、右にマップ
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📋 データ編集")
    # --- データエディタの表示 ---
    edited_df = st.data_editor(
        st.session_state.current_df,
        key="editor_changes",          # 変更検知用のキー
        on_change=handle_changes,      # 変更があったら実行する関数
        num_rows="dynamic",            # 行の追加・削除を許可
        height=500,
        use_container_width=True,
        # 列ごとの設定（IDは編集不可にするなど）
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "task": st.column_config.TextColumn("タスク名", required=True),
            "latitude": st.column_config.NumberColumn("緯度", format="%.4f"),
            "longitude": st.column_config.NumberColumn("経度", format="%.4f"),
            "is_done": st.column_config.CheckboxColumn("完了"),
            "created_at": st.column_config.DatetimeColumn("作成日時", disabled=True, format="YYYY/MM/DD HH:mm"),
        },
        # どの列を表示するか（created_atなどは隠してもよい）
        column_order=["is_done", "task", "latitude", "longitude", "id"]
    )
    
    # 処理が終わった後、session_stateのデータを最新にしてリロードしないと
    # 「変更前のデータ」と「DB」がズレてしまうため、ここでリロード判定
    if st.session_state.editor_changes["edited_rows"] or \
       st.session_state.editor_changes["added_rows"] or \
       st.session_state.editor_changes["deleted_rows"]:
        # 少し待ってからリロード（Toastを表示させるため）
        time.sleep(1)
        st.session_state.current_df = get_data()
        st.rerun()

with col2:
    st.subheader("🗺️ リアルタイムマップ")
    # 完了していないタスクのみマップに表示
    # データエディタで編集中（edited_df）の内容を反映
    active_tasks = edited_df[edited_df['is_done'] == False].copy()
    
    if not active_tasks.empty:
        # map用に列名をリネーム
        map_data = active_tasks.rename(columns={"latitude": "lat", "longitude": "lon"})
        # 緯度経度がNaN（空）のデータを除外
        map_data = map_data.dropna(subset=['lat', 'lon'])
        st.map(map_data)
        
        # タスクリスト（マップ下の補助表示）
        st.write("**📍 マップ上のタスク:**")
        for i, row in active_tasks.iterrows():
            st.markdown(f"- {row['task']}")
    else:
        st.info("マップに表示する未完了タスクはありません。")
