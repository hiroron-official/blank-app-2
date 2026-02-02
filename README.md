# 🗺️ To-Do & Map Pro

位置情報（マップ）とタスク管理を統合した、Streamlit製の高機能To-Doアプリです。
データベースに **Supabase** を採用しており、リロードしてもデータが消えず、クラウド上で永続的に管理・共有が可能です。

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](ここにアプリのURLを貼る)

## ✨ 主な機能

1.  **クラウド同期 (Supabase)**
    * タスクやカテゴリはクラウドデータベースに保存されます。PCやスマホなど、どの端末からアクセスしても最新のデータを閲覧・編集できます。
2.  **2つの管理モード**
    * **チェックリストモード**: 通常の買い物リストやタスク管理に。進捗バーで達成度を可視化。
    * **マップ＆リンクモード**: 旅行の計画や行きたいお店リストに。緯度経度を登録するとGoogle Map上にピンを表示。
3.  **リッチメディア対応**
    * 写真（画像）のアップロード機能。
    * 公式サイトなどのURLリンク管理。
4.  **優先度管理**
    * 「普通」「重要」「激アツ（🔥）」の3段階で優先度を設定可能。

## 🛠️ 使用技術

* **Frontend**: [Streamlit](https://streamlit.io/)
* **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
* **Storage**: Supabase Storage (画像保存用)
* **Language**: Python 3.x

## 🚀 ローカルでの実行方法

このリポジトリをクローンし、以下の手順で設定を行ってください。

### 1. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
