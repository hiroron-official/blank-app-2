import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="カラフルTo-Do", layout="wide")

# --- データ構造の定義（セッションで管理） ---
if 'todos' not in st.session_state:
    st.session_state.todos = [
        {
            "id": 1,
            "category": "買い物",
            "color": "#fff9c4",  # 薄い黄色
            "items": [
                {"name": "牛乳", "done": False},
                {"name": "トイレットペーパー", "done": True},
            ],
            "type": "checklist"  # チェックリスト形式
        },
        {
            "id": 2,
            "category": "ドライブ計画",
            "color": "#e8f5e9",  # 薄い緑
            "items": [
                {"name": "海ほたる", "url": "https://www.umihotaru.com/"},
                {"name": "木更津アウトレット", "url": "https://mitsui-shopping-park.com/mop/kisarazu/"},
            ],
            "type": "linklist"  # リンク集形式
        }
    ]

st.title("🎨 カテゴリ別 To-Do & メモ")

# --- 新規カテゴリ追加エリア ---
with st.expander("＋ 新しいカテゴリを追加"):
    with st.form("add_category"):
        new_cat_name = st.text_input("カテゴリ名（例：仕事、読書リスト）")
        new_cat_type = st.selectbox("タイプ", ["チェックリスト（買い物など）", "リンク集（旅行など）"])
        # 色選び
        color_map = {"黄色 (買い物)": "#fff9c4", "緑 (旅行)": "#e8f5e9", "青 (仕事)": "#e3f2fd", "赤 (重要)": "#ffcdd2"}
        selected_color_name = st.selectbox("色", list(color_map.keys()))
        
        if st.form_submit_button("作成"):
            new_id = len(st.session_state.todos) + 1
            type_code = "checklist" if "チェックリスト" in new_cat_type else "linklist"
            st.session_state.todos.append({
                "id": new_id,
                "category": new_cat_name,
                "color": color_map[selected_color_name],
                "items": [],
                "type": type_code
            })
            st.rerun()

st.divider()

# --- メイン表示エリア（2列表示） ---
cols = st.columns(2)  # 2列のカラムを作成

for i, todo in enumerate(st.session_state.todos):
    # 列を交互に割り当て
    col = cols[i % 2]
    
    with col:
        # カード風の背景色をつけるためのコンテナ
        container = st.container(border=True)
        
        # 背景色をCSSで適用（Streamlitの標準機能では背景色は変えにくいためMarkdownハックを使用）
        # ※簡易的な実装として、今回は枠線(border=True)と絵文字で色を表現します
        
        color_icon = "🟡" if "fff9c4" in todo['color'] else "🟢" if "e8f5e9" in todo['color'] else "🔵" if "e3f2fd" in todo['color'] else "🔴"
        
        container.subheader(f"{color_icon} {todo['category']}")
        
        # --- タイプごとの表示処理 ---
        
        # A. 買い物リスト（チェックボックス式）
        if todo['type'] == 'checklist':
            # アイテム追加
            c1, c2 = container.columns([3, 1])
            new_item = c1.text_input(f"追加", key=f"input_{todo['id']}", label_visibility="collapsed", placeholder="項目を追加...")
            if c2.button("＋", key=f"btn_add_{todo['id']}"):
                if new_item:
                    todo['items'].append({"name": new_item, "done": False})
                    st.rerun()
            
            # リスト表示
            for idx, item in enumerate(todo['items']):
                is_checked = container.checkbox(item['name'], value=item['done'], key=f"chk_{todo['id']}_{idx}")
                # 状態更新
                todo['items'][idx]['done'] = is_checked

        # B. ドライブ/リンク集（URL付きリスト）
        elif todo['type'] == 'linklist':
            # アイテム追加
            with container.expander("行き先を追加"):
                l_name = st.text_input("場所の名前", key=f"lname_{todo['id']}")
                l_url = st.text_input("URL", key=f"lurl_{todo['id']}")
                if st.button("追加", key=f"lbtn_{todo['id']}"):
                    if l_name:
                        todo['items'].append({"name": l_name, "url": l_url})
                        st.rerun()
            
            # リスト表示
            for item in todo['items']:
                container.markdown(f"📍 **{item['name']}**")
                if item.get('url'):
                    container.link_button(f"🔗 {item['name']} の詳細を見る", item['url'])
                else:
                    container.caption("URLなし")
        
        # 削除ボタン（右下に配置）
        if container.button("削除", key=f"del_cat_{todo['id']}"):
            st.session_state.todos.pop(i)
            st.rerun()
