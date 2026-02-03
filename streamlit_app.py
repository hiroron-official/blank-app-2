import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime
import requests  # Web API利用のために追加

# --- 1. Supabase 接続設定 ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# --- 2. 外部API活用関数 (Frankfurter API) ---
@st.cache_data(ttl=3600) # 1時間ごとにキャッシュ更新
def get_exchange_rates():
    """Frankfurter APIを用いて為替レートを取得する"""
    # 日本円(JPY)をベースに、米ドル(USD), ユーロ(EUR), 韓国ウォン(KRW)を取得
    url = "https://api.frankfurter.app/latest?from=JPY&to=USD,EUR,KRW"
    try:
        response = requests.get(url)
        response.raise_for_status() # エラーがあれば例外を発生させる
        data = response.json()
        return data.get("rates", {})
    except Exception as e:
        return None

# --- DB操作関数群 ---
def get_categories():
    response = supabase.table("categories").select("*").order("id").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return pd.DataFrame(columns=['id', 'name', 'type', 'color'])
    return df

def add_category(name, type_code, color):
    data = {"name": name, "type": type_code, "color": color}
    supabase.table("categories").insert(data).execute()

def delete_category(cat_id):
    # itemsもカスケード削除される想定、または手動削除
    supabase.table("items").delete().eq("category_id", cat_id).execute()
    supabase.table("categories").delete().eq("id", cat_id).execute()

def get_items(cat_id):
    response = supabase.table("items").select("*").eq("category_id", cat_id).order("id").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return pd.DataFrame(columns=['id', 'category_id', 'name', 'is_done', 'url', 'target_date', 'lat', 'lon'])
    return df

def add_item(cat_id, name, url=None, target_date=None, lat=None, lon=None):
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
    val = 1 if is_done else 0
    supabase.table("items").update({"is_done": val}).eq("id", item_id).execute()

def delete_item(item_id):
    supabase.table("items").delete().eq("id", item_id).execute()

# --- ページ設定 ---
st.set_page_config(page_title="To-Do & Map (API連携版)", layout="wide")
st.title("🗺️ 行き先マップ付き To-Do アプリ")

# --- サイドバー ---
with st.sidebar:
    st.header("カテゴリ作成")
    with st.form("add_cat_form"):
        new_name = st.text_input("カテゴリ名", placeholder="例：北海道旅行")
        new_type = st.radio("タイプ", ["チェックリスト (買い物等)", "マップ＆リンク (旅行等)"])
        
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
    
    # --- ✈️ ここにWeb API機能を追加 ---
    st.subheader("💱 今日の為替レート")
    st.caption("Powered by Frankfurter API")
    
    rates = get_exchange_rates()
    
    if rates:
        st.markdown(f"""
        **1 JPY (日本円) あたり:**
        - 🇺🇸 **{rates.get('USD', 0):.4f}** USD
        - 🇪🇺 **{rates.get('EUR', 0):.4f}** EUR
        - 🇰🇷 **{rates.get('KRW', 0):.2f}** KRW
        """)
        st.info("海外旅行の予算計画に役立ててください！")
    else:
        st.warning("レート情報を取得できませんでした。")

    st.divider()
    st.markdown("※ 緯度経度はGoogleマップ等で右クリックして取得できます")

# --- メインエリア表示 ---
try:
    categories = get_categories()
except Exception as e:
    st.error(f"データベース接続エラー: {e}")
    st.stop()

if categories.empty:
    st.info("👈 サイドバーからカテゴリを追加してください")
else:
    cols = st.columns(2)
    
    for index, cat in categories.iterrows():
        col = cols[index % 2]
        
        with col:
            with st.container(border=True):
                # ヘッダー部分
                c_head1, c_head2 = st.columns([4, 1])
                icon = "📝" if cat['type'] == 'checklist' else "🚗"
                c_head1.subheader(f"{icon} {cat['name']}")
                
                if c_head2.button("🗑️", key=f"del_cat_{cat['id']}"):
                    delete_category(cat['id'])
                    st.rerun()

                items = get_items(cat['id'])

                # A. チェックリスト形式
                if cat['type'] == 'checklist':
                    with st.form(f"add_check_{cat['id']}", clear_on_submit=True):
                        col_in, col_btn = st.columns([3, 1])
                        new_item_name = col_in.text_input("項目名", label_visibility="collapsed")
                        if col_btn.form_submit_button("追加"):
                            add_item(cat['id'], new_item_name)
                            st.rerun()
                    
                    if not items.empty:
                        for _, item in items.iterrows():
                            is_checked = bool(item['is_done'])
                            checked = st.checkbox(item['name'], value=is_checked, key=f"chk_{item['id']}")
                            if checked != is_checked:
                                update_item_status(item['id'], checked)
                                st.rerun()

                # B. マップ＆リンク形式
                elif cat['type'] == 'maplist':
                    map_data = items.dropna(subset=['lat', 'lon'])
                    
                    if not map_data.empty:
                        st.map(map_data, latitude='lat', longitude='lon', size=20, color='#FF0000')

                    for _, item in items.iterrows():
                        date_label = item['target_date'] if item['target_date'] else '日付未定'
                        with st.expander(f"📍 {item['name']} ({date_label})"):
                            st.write(f"日付: {date_label}")
                            if item['url']:
                                st.link_button("公式サイトを見る", item['url'])
                            
                            if st.button("削除", key=f"del_item_{item['id']}"):
                                delete_item(item['id'])
                                st.rerun()

                    with st.expander("➕ 新しい行き先を追加"):
                        with st.form(f"add_map_{cat['id']}", clear_on_submit=True):
                            i_name = st.text_input("場所の名前 (例: 富良野ラベンダー畑)")
                            i_date = st.date_input("予定日", datetime.date.today())
                            i_url = st.text_input("URL (Googleマップなど)")
                            
                            c_lat, c_lon = st.columns(2)
                            i_lat = c_lat.number_input("緯度", value=None, format="%.6f", placeholder="例: 43.418")
                            i_lon = c_lon.number_input("経度", value=None, format="%.6f", placeholder="例: 142.427")
                            
                            st.caption("※緯度経度を入力すると地図にピンが立ちます")
                            
                            if st.form_submit_button("登録"):
                                add_item(cat['id'], i_name, i_url, i_date, i_lat, i_lon)
                                st.rerun()
