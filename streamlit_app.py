import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# --- 1. Supabase 接続設定 ---
# 接続をキャッシュして高速化
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- DB操作関数群 (Supabase版) ---

def get_categories():
    """カテゴリ一覧を取得してDataFrameで返す"""
    response = supabase.table("categories").select("*").order("id").execute()
    df = pd.DataFrame(response.data)
    # データが空の場合でもカラム構造を維持した空DFを返す（エラー防止）
    if df.empty:
        return pd.DataFrame(columns=['id', 'name', 'type', 'color'])
    return df

def add_category(name, type_code, color):
    """カテゴリを追加"""
    data = {"name": name, "type": type_code, "color": color}
    supabase.table("categories").insert(data).execute()

def delete_category(cat_id):
    """カテゴリを削除（itemsはカスケード削除設定済みなら自動で消えるが、念の為明示的に削除も可）"""
    # Supabaseの外部キー設定で on delete cascade にしていれば items の削除は不要ですが
    # ここでは安全のため items -> categories の順で削除コマンドを発行
    supabase.table("items").delete().eq("category_id", cat_id).execute()
    supabase.table("categories").delete().eq("id", cat_id).execute()

def get_items(cat_id):
    """指定カテゴリのアイテムを取得"""
    response = supabase.table("items").select("*").eq("category_id", cat_id).order("id").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        # Map表示などでエラーにならないよう必要なカラムを持つ空DFを返す
        return pd.DataFrame(columns=['id', 'category_id', 'name', 'is_done', 'url', 'target_date', 'lat', 'lon'])
    return df

def add_item(cat_id, name, url=None, target_date=None, lat=None, lon=None):
    """アイテムを追加"""
    # 日付オブジェクトを文字列に変換 (Noneの場合はNoneのまま)
    date_str = target_date.strftime('%Y-%m-%d') if target_date else None
    
    data = {
        "category_id": int(cat_id),
        "name": name,
        "is_done": 0,
        "url": url,
        "target_date": date_str,
        "lat": lat,
        "lon": lon
    }
    supabase.table("items").insert(data).execute()

def update_item_status(item_id, is_done):
    """完了状態を更新"""
    val = 1 if is_done else 0
    supabase.table("items").update({"is_done": val}).eq("id", item_id).execute()

def delete_item(item_id):
    """アイテムを削除"""
    supabase.table("items").delete().eq("id", item_id).execute()

# --- ページ設定 ---
st.set_page_config(page_title="高機能To-Do & Map (Supabase版)", layout="wide")
st.title("🗺️ 行き先マップ付き To-Do アプリ (Cloud DB)")

# --- サイドバー：カテゴリ追加 ---
with st.sidebar:
    st.header("カテゴリ作成")
    with st.form("add_cat_form"):
        new_name = st.text_input("カテゴリ名", placeholder="例：北海道旅行")
        new_type = st.radio("タイプ", ["チェックリスト (買い物等)", "マップ＆リンク (旅行等)"])
        
        # 色選択
        color_options = {
            "🟡 黄 (買い物)": "#fff9c4", 
            "🟢 緑 (旅行/自然)": "#e8f5e9", 
            "🔵 青 (仕事/勉強)": "#e3f2fd", 
            "🔴 赤 (重要)": "#ffcdd2"
        }
        selected_color_label = st.selectbox("テーマカラー", list(color_options.keys()))
        
        if st.form_submit_button("追加"):
            if new_name:
                type_code = "checklist" if "チェックリスト" in new_type else "maplist"
                add_category(new_name, type_code, color_options[selected_color_label])
                st.rerun()

    st.divider()
    st.markdown("※ 緯度経度はGoogleマップ等で右クリックして取得できます")
    st.markdown("Powered by **Supabase**")

# --- メインエリア表示 ---
try:
    categories = get_categories()
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    st.stop()

if categories.empty:
    st.info("👈 サイドバーからカテゴリを追加してください")
else:
    # 2列レイアウトでカードを表示
    cols = st.columns(2)
    
    for index, cat in categories.iterrows():
        col = cols[index % 2]
        
        with col:
            # カード枠のデザイン (背景色はstyle引数などが使えないためMarkdown等で工夫するか、標準のまま)
            # ここではst.containerで枠を表示
            with st.container(border=True):
                # ヘッダー部分
                c_head1, c_head2 = st.columns([4, 1])
                icon = "📝" if cat['type'] == 'checklist' else "🚗"
                c_head1.subheader(f"{icon} {cat['name']}")
                
                # 削除ボタン
                if c_head2.button("🗑️", key=f"del_cat_{cat['id']}"):
                    delete_category(cat['id'])
                    st.rerun()

                # --- アイテム取得 ---
                items = get_items(cat['id'])

                # A. チェックリスト形式（買い物など）
                if cat['type'] == 'checklist':
                    # 追加フォーム
                    with st.form(f"add_check_{cat['id']}", clear_on_submit=True):
                        col_in, col_btn = st.columns([3, 1])
                        new_item_name = col_in.text_input("項目名", label_visibility="collapsed")
                        if col_btn.form_submit_button("追加"):
                            add_item(cat['id'], new_item_name)
                            st.rerun()
                    
                    # リスト表示
                    if not items.empty:
                        for _, item in items.iterrows():
                            # checkboxのkeyを一意にする
                            is_checked = bool(item['is_done'])
                            checked = st.checkbox(item['name'], value=is_checked, key=f"chk_{item['id']}")
                            if checked != is_checked:
                                update_item_status(item['id'], checked)
                                st.rerun()

                # B. マップ＆リンク形式（旅行・ドライブなど）
                elif cat['type'] == 'maplist':
                    # 地図データの準備 (lat/lonがNaNでないものを抽出)
                    map_data = items.dropna(subset=['lat', 'lon'])
                    
                    # 1. 地図表示（データがある場合のみ）
                    if not map_data.empty:
                        st.map(map_data, latitude='lat', longitude='lon', size=20, color='#FF0000')

                    # 2. リスト表示
                    for _, item in items.iterrows():
                        date_label = item['target_date'] if item['target_date'] else '日付未定'
                        with st.expander(f"📍 {item['name']} ({date_label})"):
                            st.write(f"日付: {date_label}")
                            if item['url']:
                                st.link_button("公式サイトを見る", item['url'])
                            
                            # 削除ボタン
                            if st.button("削除", key=f"del_item_{item['id']}"):
                                delete_item(item['id'])
                                st.rerun()

                    # 3. 追加フォーム
                    with st.expander("➕ 新しい行き先を追加"):
                        with st.form(f"add_map_{cat['id']}", clear_on_submit=True):
                            i_name = st.text_input("場所の名前 (例: 富良野ラベンダー畑)")
                            i_date = st.date_input("予定日", datetime.date.today())
                            i_url = st.text_input("URL (Googleマップなど)")
                            
                            c_lat, c_lon = st.columns(2)
                            i_lat = c_lat.number_input("緯度 (Latitude)", value=None, format="%.6f", placeholder="例: 43.418")
                            i_lon = c_lon.number_input("経度 (Longitude)", value=None, format="%.6f", placeholder="例: 142.427")
                            
                            st.caption("※緯度経度を入力すると地図にピンが立ちます")
                            
                            if st.form_submit_button("登録"):
                                # 入力値がNoneの場合のハンドリングは関数側で行う
                                add_item(cat['id'], i_name, i_url, i_date, i_lat, i_lon)
                                st.rerun()
