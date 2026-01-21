import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- 1. データベース設定 ---
def init_db():
    conn = sqlite3.connect('todo_app_simple.db', check_same_thread=False)
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

# --- UI設定 ---
st.set_page_config(page_title="To-Do & Map", layout="wide")
st.title("🗺️ 行き先マップ付き To-Do (シンプル版)")

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

                # B. マップ＆リンク（手動入力版）
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
                            
                            if st.button("削除", key=f"del_i_{item['id']}"):
                                delete_item(item['id'])
                                st.rerun()

                    # 追加フォーム（手動入力）
                    st.markdown("---")
                    with st.form(f"add_map_{cat['id']}", clear_on_submit=True):
                        st.caption("行き先の登録")
                        i_name = st.text_input("名前 (例: 清水寺)")
                        i_date = st.date_input("予定日", datetime.date.today())
                        i_url = st.text_input("URL (任意)")
                        
                        c_lat, c_lon = st.columns(2)
                        i_lat = c_lat.number_input("緯度 (Googleマップで右クリック)", value=None, format="%.6f")
                        i_lon = c_lon.number_input("経度", value=None, format="%.6f")

                        if st.form_submit_button("登録"):
                            if i_name:
                                add_item(cat['id'], i_name, i_url, i_date, i_lat, i_lon)
                                st.rerun()
