# 🗺️ 行き先マップ付き To-Do アプリ (Web API連携版)

StreamlitとSupabaseを使用して作成した、位置情報（マップ）も扱えるクラウド対応のTo-Doアプリです。
Frankfurter APIと連携し、旅行計画に役立つ**リアルタイムの為替レート**を表示する機能も搭載しています。

## URL

このURLで試すことができます（スリープ状態のときは青色の起動ボタンを押してください）：  
https://blank-app-cih34ssp36.streamlit.app/


## ✨ 主な機能

1.  **クラウドデータ保存 (Supabase)**
    * SQLiteなどの簡易DBとは異なり、Supabase（PostgreSQL）にデータを保存するため、どの端末からアクセスしても同じデータを閲覧・編集できます。
2.  **Web API連携 (New!)**
    * **Frankfurter API** を使用して、現在の為替レート（USD, EUR, KRW）をサイドバーにリアルタイム表示します。海外旅行の計画時に便利です。
3.  **2つのリスト形式**
    * **📝 チェックリスト**: 通常の買い物やタスク管理用。
    * **🚗 マップ＆リンク**: 旅行計画用。URLを登録することでいつでも旅行先の情報を見れます。
4.  **カテゴリ管理**
    * 用途に合わせてカテゴリを作成し、テーマカラーを設定できます。

## 🛠️ 使用技術

* **Frontend**: [Streamlit](https://streamlit.io/)
* **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
* **Web API**: [Frankfurter API](https://frankfurter.dev/) (Currency Data)
* **Language**: Python 3.x

## 🚀 ローカルでの実行方法

このリポジトリをクローンし、以下の手順で設定を行ってください。

### 1. 依存ライブラリのインストール
Web APIを利用するために `requests` ライブラリが必要です。
```bash
pip install -r requirements.txt
