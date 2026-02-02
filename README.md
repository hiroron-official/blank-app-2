# 🗺️ 行き先マップ付き To-Do アプリ (Supabase版)

StreamlitとSupabaseを使用して作成した、位置情報（マップ）も扱えるTo-Doリストアプリです。
データベースに **Supabase** を採用しているため、アプリを再起動してもデータが消えず、クラウド上で永続的に管理できます。


https://blank-app-cih34ssp36.streamlit.app/

## ✨ 主な機能

1.  **クラウドデータ保存**
    * SQLiteなどの簡易DBとは異なり、Supabase（PostgreSQL）にデータを保存するため、どの端末からアクセスしても同じデータを閲覧・編集できます。
2.  **カテゴリ管理**
    * 「北海道旅行」「週末の買い物」など、用途に合わせてカテゴリを作成可能。
    * カテゴリごとにテーマカラーを設定できます。
3.  **2つのリスト形式**
    * **📝 チェックリスト**: 通常の買い物やタスク管理用。
    * **🚗 マップ＆リンク**: 旅行計画用。緯度経度を登録すると、地図上にピンが表示されます。

## 🛠️ 使用技術

* **Frontend**: [Streamlit](https://streamlit.io/)
* **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
* **Language**: Python 3.x

## 🚀 ローカルでの実行方法

このリポジトリをクローンし、以下の手順で設定を行ってください。

### 1. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
