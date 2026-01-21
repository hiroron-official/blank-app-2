import streamlit as st
import pandas as pd
import sqlite3
import datetime

# --- 1. データベース設定 (SQLite) ---
def init_db():
    conn = sqlite3.connect('todo_app.db', check_same_thread=False)
    c = conn.cursor()
    
    # カテゴリ管理テーブル
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, type TEXT, color TEXT)''')
    
    # アイテム管理テーブル（日付、緯度経度カラムを追加）
    c.execute('''CREATE TABLE IF NOT EXISTS items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, category_id INTEGER, 
                  name TEXT, is_done INTEGER, url TEXT, 
                  target_date TEXT, lat REAL, lon REAL)''')
    conn.commit()
    return conn

conn = init_db()

# --- DB操作関数群 ---
def get_categories():
    return pd.read_sql("SELECT * FROM categories", conn)

def add_category(name, type, color):
    c = conn.cursor()
    c.execute("INSERT INTO categories (name, type, color) VALUES (?, ?, ?)", (name, type, color))
    conn.commit()

def delete_category(cat_id):
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE category_id = ?", (cat_id,)) # 紐づくアイテムも削除
    c.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()

def get_items(cat_id):
    return pd.read_sql("SELECT * FROM items WHERE category_id = ?", conn, params=(cat_id,))

def add_item(cat_id, name, url=None, target_date=None, lat=None, lon=None):
    c = conn.cursor()
    # 日付オブジェクトを文字列に変換
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

# --- ページ設定 ---
st.set_page_config(page_title="高機能To-Do & Map", layout="wide")
st.title("🗺️ 行き先マップ付き To-Do アプリ")

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

# --- メインエリア表示 ---
categories = get_categories()

if categories.empty:
    st.info("👈 サイドバーからカテゴリを追加してください")
else:
    # 2列レイアウトでカードを表示
    cols = st.columns(2)
    
    for index, cat in categories.iterrows():
        col = cols[index % 2]
        
        with col:
            # カード枠のデザイン
            with st.container(border=True):
                # ヘッダー部分
                c_head1, c_head2 = st.columns([4, 1])
                icon = "📝" if cat['type'] == 'checklist' else "🚗"
                c_head1.subheader(f"{icon} {cat['name']}")
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
                            checked = st.checkbox(item['name'], value=bool(item['is_done']), key=f"chk_{item['id']}")
                            if checked != bool(item['is_done']):
                                update_item_status(item['id'], checked)
                                st.rerun()

                # B. マップ＆リンク形式（旅行・ドライブなど）
                elif cat['type'] == 'maplist':
                    # 地図データの準備
                    map_data = items.dropna(subset=['lat', 'lon'])
                    
                    # 1. 地図表示（データがある場合のみ）
                    if not map_data.empty:
                        st.map(map_data, latitude='lat', longitude='lon', size=20, color='#FF0000')

                    # 2. リスト表示
                    for _, item in items.iterrows():
                        with st.expander(f"📍 {item['name']} ({item['target_date'] or '日付未定'})"):
                            st.write(f"日付: {item['target_date']}")
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
                                add_item(cat['id'], i_name, i_url, i_date, i_lat, i_lon)
                                st.rerun()
