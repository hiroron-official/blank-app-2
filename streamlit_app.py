import streamlit as st
import pandas as pd
import sqlite3
import datetime
from duckduckgo_search import DDGS
from geopy.geocoders import Nominatim

# --- 1. データベース設定 ---
def init_db():
    conn = sqlite3.connect('todo_app_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, color TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, 
                  name TEXT, is_done INTEGER, url TEXT, 
                  target_date TEXT, lat REAL, lon REAL)''')
    conn.commit()
    return conn

conn = init_db()

# --- DB操作関数 ---
def get_categories():
    return pd.read_sql("SELECT * FROM categories", conn)

def add_category(name, type, color):
    c = conn.cursor()
    c.execute("INSERT INTO categories (name, type, color) VALUES (?, ?, ?)", (name, type, color))
    conn.commit()

def delete_category(cat_id):
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE category_id = ?", (cat_id,))
    c.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()

def get_items(cat_id):
    return pd.read_sql("SELECT * FROM items WHERE category_id = ?", conn, params=(cat_id,))

def add_item(cat_id, name, url=None, target_date=None, lat=None, lon=None):
    c = conn.cursor()
    date_str = target_date.strftime('%Y-%m-%d') if target_date else None
    c.execute('''INSERT INTO items (category_id, name, is_done, url, target_date, lat, lon) 
                 VALUES (?, ?, 0, ?, ?, ?, ?)''', 
              (cat_id, name, url, date_str, lat, lon))
    conn.commit()

def update_item_status(item_id, is_done):
    c = conn.cursor()
    val = 1 if is_done else 0
    c.execute("UPDATE items SET is_done = ? WHERE id = ?", (val, item_id))
    conn.commit()

def delete_item(item_id):
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()

# --- 🔍 自動検索ロジック (ここが新機能) ---
def search_place_info(query):
    """地名からURLと緯度経度を検索する"""
    url = None
    lat = None
    lon = None

    # 1. URL検索 (DuckDuckGo)
    try:
        with DDGS() as ddgs:
            # 日本語優先で検索し、最初の結果を取得
            results = list(ddgs.text(f"{query} 公式", region='jp-jp', max_results=1))
            if results:
                url = results[0]['href']
    except Exception as e:
        print(f"Search Error: {e}")

    # 2. 緯度経度検索 (Nominatim / OpenStreetMap)
    try:
        geolocator = Nominatim(user_agent="streamlit_todo_app")
        location = geolocator.geocode(query)
        if location:
            lat = location.latitude
            lon = location.longitude
    except Exception as e:
        print(f"Geo Error: {e}")

    return url, lat, lon

# --- UI設定 ---
st.set_page_config(page_title="自動検索To-Do", layout="wide")
st.title("🤖 自動検索付き 行き先マップ")

# サイドバー
with st.sidebar:
    st.header("カテゴリ作成")
    with st.form("add_cat_form"):
        new_name = st.text_input("カテゴリ名", placeholder="例：京都旅行")
        new_type = st.radio("タイプ", ["チェックリスト", "マップ＆リンク"])
        color_options = {"🟡 黄": "#fff9c4", "🟢 緑": "#e8f5e9", "🔵 青": "#e3f2fd", "🔴 赤": "#ffcdd2"}
        selected_color_label = st.selectbox("色", list(color_options.keys()))
        
        if st.form_submit_button("追加"):
            if new_name:
                t_code = "checklist" if "チェックリスト" in new_type else "maplist"
                add_category(new_name, t_code, color_options[selected_color_label])
                st.rerun()

# メイン表示
categories = get_categories()

if not categories.empty:
    cols = st.columns(2)
    for index, cat in categories.iterrows():
        col = cols[index % 2]
        with col:
            with st.container(border=True):
                # ヘッダー
                c1, c2 = st.columns([4, 1])
                c1.subheader(f"{'📝' if cat['type']=='checklist' else '🚗'} {cat['name']}")
                if c2.button("🗑️", key=f"del_{cat['id']}"):
                    delete_category(cat['id'])
                    st.rerun()

                items = get_items(cat['id'])

                # A. チェックリスト
                if cat['type'] == 'checklist':
                    with st.form(f"f_{cat['id']}", clear_on_submit=True):
                        col_in, col_btn = st.columns([3,1])
                        nm = col_in.text_input("項目", label_visibility="collapsed")
                        if col_btn.form_submit_button("追加"):
                            add_item(cat['id'], nm)
                            st.rerun()
                    for _, item in items.iterrows():
                        chk = st.checkbox(item['name'], value=bool(item['is_done']), key=f"c_{item['id']}")
                        if chk != bool(item['is_done']):
                            update_item_status(item['id'], chk)
                            st.rerun()

                # B. マップ＆リンク（自動検索付き）
                elif cat['type'] == 'maplist':
                    # 地図表示
                    map_data = items.dropna(subset=['lat', 'lon'])
                    if not map_data.empty:
                        st.map(map_data, latitude='lat', longitude='lon', size=20, color='#FF0000')

                    # リスト表示
                    for _, item in items.iterrows():
                        with st.expander(f"📍 {item['name']}"):
                            if item['url']:
                                st.link_button(f"🔗 公式サイト: {item['url']}", item['url'])
                            else:
                                st.caption("URLなし")
                            
                            if st.button("削除", key=f"del_i_{item['id']}"):
                                delete_item(item['id'])
                                st.rerun()

                    # 追加フォーム
                    st.markdown("---")
                    st.caption("👇 名前だけ入力して「自動検索＆登録」を押すと、URLと地図を自動取得します")
                    
                    with st.form(f"add_map_{cat['id']}", clear_on_submit=True):
                        i_name = st.text_input("行き先の名前 (例: 清水寺, USJ)")
                        i_date = st.date_input("予定日", datetime.date.today())
                        
                        # 手動入力欄（アコーディオンで隠す）
                        with st.expander("手動でURLや座標を入れる場合は開く"):
                            i_url = st.text_input("URL (任意)")
                            c_lat, c_lon = st.columns(2)
                            i_lat = c_lat.number_input("緯度", value=None, format="%.6f")
                            i_lon = c_lon.number_input("経度", value=None, format="%.6f")

                        if st.form_submit_button("✨ 自動検索＆登録"):
                            if i_name:
                                # 手動入力がない場合は検索を実行
                                final_url = i_url
                                final_lat = i_lat
                                final_lon = i_lon

                                # 検索実行の判定
                                needs_search = (not final_url) or (final_lat is None)
                                
                                if needs_search:
                                    with st.spinner(f"🔍 '{i_name}' を検索中..."):
                                        s_url, s_lat, s_lon = search_place_info(i_name)
                                        # 空欄箇所のみ検索結果で埋める
                                        if not final_url: final_url = s_url
                                        if final_lat is None: final_lat = s_lat
                                        if final_lon is None: final_lon = s_lon
                                
                                add_item(cat['id'], i_name, final_url, i_date, final_lat, final_lon)
                                st.rerun()
