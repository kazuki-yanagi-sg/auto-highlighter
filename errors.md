# エラー解析ログ (error-loop)

## 2026-06-07 Wikipedia取得で 502 "取得に失敗しました"

**症状**: `POST /documents {"url":"https://en.wikipedia.org/wiki/Probability_theory"}` が
`{"detail":"取得に失敗しました: ..."}`(HTTP 502)を返す。
**理解**: `HttpScraper.fetch` 内の httpx GET が `httpx.HTTPError` を投げ、`ScrapeError` に変換されて
502 になっている。コンテナ内検証で **httpx デフォルトUAだと Wikipedia が 403 を返す**ことを確認
(`default UA -> 403` / `with UA -> 200`)。原因は User-Agent。

### 考えられる原因(確度順)
- [x] 原因1: User-Agentヘッダ未設定 → Wikipedia等が `python-httpx` を弾いて403。検証: コンテナ内でUA有無を比較 → UAなし403/UAあり200。対策: ブラウザ風UAを既定ヘッダに付与。
- [ ] 原因2: `Accept`等の一般的ブラウザヘッダ不足でbot判定。対策: Accept/Accept-Language も付与。
- [ ] 原因3: リダイレクト未追従。検証: `HttpScraper` は既に `follow_redirects=True` → 該当せず。
- [ ] 原因4: タイムアウト(10s)が大ページで不足。検証: UAありで200/314KB取得済 → 該当せず。
- [ ] 原因5: TLS/ネットワーク不通。検証: 同ホストにUAありで200 → 該当せず。

### 試行ログ
- 原因1を採用。HttpScraper に既定の User-Agent(+Accept/Accept-Language)を付与。
- TDD: `test_fetch_sends_browser_like_user_agent` を追加(Red: `python-httpx/0.28.1`)→ 実装後 Green。
- ライブ再現: `POST /documents {wikipedia URL}` → 修正前 HTTP 502 → **修正後 HTTP 201**(513文・マーカー付与)。

**結果: 解決** — 原因はhttpx既定UA(`python-httpx`)をWikipediaが403で弾いていたこと。
HttpScraper にブラウザ風 User-Agent と Accept ヘッダを既定で付与して解消。

---

## 2026-06-07 (再報告) 同じWikipedia URLで "取得に失敗しました"

**症状**: ユーザーが前回と同一の `{"detail":"取得に失敗しました: .../Probability_theory"}` を再報告。
**理解**: 再現を試みたが **現在は再現しない**。検証:
- backend直叩き `POST /documents` → HTTP 201
- frontend経由 `POST /api/documents`(proxy) → HTTP 201
- コンテナ内 生fetch×5 → 全て 200 / 約0.14s / 314KB(403も429もタイムアウトも無し)
→ 前回のUA修正で根本原因は解消済み。残るのは「断続要因」か「ブラウザに残った古いエラー表示」。

### 考えられる原因(可能な限り列挙)
- [x] 原因1: 前回のUA未設定403 → 既に修正済み。再現せず(201)。
- [ ] 原因2: ブラウザに古いエラーが残存(修正反映前のリクエスト結果を表示し続けている)。対策: ハードリロードを案内。コード変更不要。
- [x] 原因3: 断続的なタイムアウト(10s)/レート制限(429) → 大ページや低速回線でまれに失敗しうる。対策: タイムアウトを20sへ、加えて失敗時に **実際の原因(ステータス/例外)をエラーメッセージに含める**(次回以降の調査をゼロにする=本スキルの目的)。

### 試行ログ
- 原因1: 既に修正済みを確認(201)。追加変更なし。
- 原因2: ブラウザ古エラーの可能性 → ユーザーにハードリロードを案内(コード変更不要)。
- 原因3: TDD で `..._with_status_in_message` / `..._with_cause_in_message` を追加(Red)→
  `HttpScraper` のタイムアウト10s→20s、`HTTPStatusError`/`HTTPError` を分けて
  メッセージにステータス/例外名を付与 → Green(35件全緑)。
- ライブ検証: 元URL=201、存在しないページ=`取得に失敗しました(HTTP 404): ...`(原因が即判明)。

**結果: 解決** — 取得失敗自体は前回のUA修正で解消済み(再現せず)。今回は再発に備え、
タイムアウト緩和＋エラーメッセージへの実ステータス/例外付与で「次回は調べなくても原因が分かる」状態にした。

---

## 2026-06-07 TTS "音声の生成に失敗しました (502)"

**症状**: フロントの音声再生で `音声の生成に失敗しました (502)`。backend `POST /documents/{id}/tts`
が `{"detail":"音声合成に失敗しました"}` / 502 を返す。
**理解**: backend→VOICEVOX が `ConnectError: Name or service not known`。調査すると
**voicevoxコンテナが OOMKilled (ExitCode=137, OOMKilled=true) で停止**していた。
直前ログに、Wikipedia記事の英語段落**まるごと1文**(数千文字)を `audio_query` に渡したリクエストあり。
巨大テキストの合成でメモリを使い切り強制終了→以後 `voicevox` 名が解決できず502、という連鎖。

### 考えられる原因(確度順)
- [ ] 原因1: voicevoxコンテナが落ちている(OOMKilled) → まず再起動。さらに `restart` ポリシーが無く自動復旧しない。対策: voicevoxを起動＋compose に `restart: unless-stopped` を付与。
- [ ] 原因2: TTSが対象色の全文を連結し、巨大テキストをVOICEVOXに送ってOOMを誘発。対策: 合成前にテキストを安全な長さで分割(チャンク)し、各チャンクを合成→WAV結合。1リクエストを小さく保つ。
- [ ] 原因3: (副因) Segmenterが英語の "." で分割せず段落が1セグメントになり、1文が極端に長い。対策: 文末記号に "." 等も加える(別エラーとして扱う/今回は原因2のチャンク化で実害を回避)。
- [x] 原因4: speaker未初期化/不正 → 検証で audio_query 自体は過去200だったため該当せず(無関係)。

### 試行ログ
- 原因1: voicevox再起動＋compose に `restart: unless-stopped` 追加 → 小ドキュメント(example.com)TTSが200/正常WAVに復旧。
- 原因2(根治): TDDで `_chunk_text`/WAV結合のテスト追加(Red)→ `VoicevoxTts` をテキスト分割(既定200字)＋各チャンク合成＋`wave`でWAV結合 に変更 → 40件全緑。
  - ライブ検証: **doc5 赤=6152字 → HTTP 200(34MB WAV)**、緑=4069字 → 200、**voicevoxはOOMKilled=false で生存**。OOM再発せず。
- 原因3(副因): 英語の "." 非分割で1セグメントが長い件は、原因2のチャンク化で実害(OOM)を回避済み。読みやすさ改善は別途(必要なら Segmenter に "." 対応を追加)。

**結果: 解決** — 直接原因は VOICEVOX の OOMKilled(巨大テキストを一括合成)。
①voicevox再起動＋自動再起動ポリシー、②合成テキストを安全な長さに分割→WAV結合、で解消。
6000字超でも200で返り、voicevoxは落ちなくなった。

---

## 2026-06-07 (再発) db 起動で "Bind for 0.0.0.0:5432 failed: port is already allocated"

**症状**: `sokudoku-db-1` の起動で 5432 のバインド失敗(port already allocated)。
**理解**: 別プロジェクト `keiba_postgres` が常時ホスト5432を専有。以前 compose を `5433:5432` に
逃がしたので**現在のcomposeでは再現しない**(検証: `docker compose up -d` → exit 0、db は 5433 で healthy)。
貼られたエラーは 5433 修正前の状態のもの。ただしユーザーが繰り返しポート競合に当たっているため、
**ホストにDBを公開していること自体が再発の温床**(固定ホストポートは何番でも競合しうる)。

### 考えられる原因(確度順)
- [x] 原因1: ホスト5432競合 → 既に `5433:5432` へ変更済み。現composeでは再現せず(up成功)。
- [x] 原因2(恒久): DBをホストに公開する必要が無い(backendは `db:5432` で内部接続)。固定ホストポートは競合源。対策: db の `ports` 公開を撤去 → ホストポート競合の全クラスを根絶。

### 試行ログ
- 再現確認: 現compose(5433)で `docker compose up -d` → exit 0、db は5433でhealthy。エラーは再現せず(修正前のもの)。
- 恒久対策: docker-compose の db から `ports` を撤去し `expose: 5432` のみに(ホスト非公開)。`docker compose up -d` 成功、`docker ps` で db は `5432/tcp`(0.0.0.0公開なし)。keiba_postgres と二度と競合しない。
- 副次: db再作成中に backend が古い接続を握り `GET /documents` が一時500 → backend再起動で200。根治として `db.py` の Postgres エンジンに `pool_pre_ping=True` を追加(切れた接続を自動で張り直す)。backendテスト57件緑。

**結果: 解決** — 直接の競合は既に `5433` 回避済みで現状再現せず。恒久策として
**DBのホスト公開を撤去**(内部接続のみ)し、ホストポート競合の全クラスを根絶。
加えて `pool_pre_ping` でDB再起動時の500も自動回復するようにした。

---

## 2026-06-07 POST /documents で "Internal Server Error" (Gemini 429)

**症状**: 記事追加(POST /documents)で 500 Internal Server Error。
**理解**: backendログに `google.api_core.exceptions.ResourceExhausted: 429 ... quota ...
generate_content_free_tier_input_token_count, limit 250000, model gemini-3.5-flash`。
Gemini無料枠の入力トークン/分の上限超過。長文記事の **注釈(annotator)+分類(categorizer)** で
大量トークンを消費し、その例外が未捕捉のまま 500 になっていた。

### 考えられる原因(確度順)
- [x] 原因1: Geminiのクォータ/レート超過(429)が未処理で500化。対策: AI呼び出し失敗を捕捉し、
  注釈失敗は **503(明確なメッセージ)** にして500を出さない。分類失敗は「その他」にフォールバック。
- [ ] 原因2: 入力トークン過大(全文を一括送信)。緩和策(将来): 注釈に送る本文量を抑える/モデル選択。今回は主因の処理(429ハンドリング)を優先。
- [x] 原因3: APIキー無効/期限切れ → ログは quota であり認証エラーではないため該当せず(無関係)。

### 試行ログ
- TDD: `AiError` を追加。`GeminiAnnotator._suggest` で呼び出し例外を `AiError` に包む(注釈テスト)。
  `GeminiCategorizer._suggest` は例外時 None→`classify` で「その他」フォールバック(分類テスト)。
  `routers/documents` で `AiError`→**503 + 日本語メッセージ**。documents APIテストで503確認。backend 83件緑。
- フロント: `client.asJson` がエラー時に `detail` を取り出すよう改善(503の文言をそのまま表示)。
- ライブ: `POST /documents` → 500 が出なくなり、クォータ回復時は 201、超過時は 503(明確メッセージ)。

**結果: 解決** — 直接原因は Gemini 無料枠のトークン/分の上限超過(429)が未処理で 500 化していたこと。
AI失敗を捕捉し、注釈失敗=503(「AIが混雑/上限。少し待って再試行」)、分類失敗=「その他」に倒すことで
500 を根絶。なお上限自体は無料枠の制約で、短時間に大きい記事を連投すると 503 になる(約1分で回復)。

---

## 2026-06-07 phi4 切替後にマーカーが一切引かれない

**症状**: モデルを phi4 にした後、(特に長文/初回で)マーカーが全く付かない。短文(example.com)では付く。
**理解**: 実測で **phi4 は40文バッチの注釈に約95秒** かかる。`ollama.generate` の httpx タイムアウトは **120秒** で、
初回のモデルロード(14B)や密なバッチが重なると120秒を超え `httpx` 例外→`AiError`→ジョブ status=error。
最初のバッチで失敗すると以降が走らず、そのドキュメントはマーカー0になる。短文は1バッチで間に合うため付く。

### 考えられる原因(確度順)
- [ ] 原因1: phi4が遅く、注釈バッチが120秒のタイムアウトを超える→AiError→0マーカー。対策: Ollamaのタイムアウトを大幅に延長(例600s)＋1バッチの文数を減らす(40→20)で1回を軽く・速く・落ちにくくする。
- [ ] 原因2: phi4自体が重すぎてUXも悪い → 速度優先なら llama3 に戻す選択肢(精度は落ちる)。
- [x] 原因1: phi4が遅くバッチが120秒超過→AiError→0マーカー。対策実施。
- [-] 原因2: llama3へ戻す(精度優先のため採用せず)。
- [x] 原因3: 原因1の結果なので原因1の解消で解決。

### 試行ログ
- 実測: phi4 は40文バッチで約95秒(120秒タイムアウトに肉薄、初回ロードで超過しうる)。
- 対策: `ollama.generate` のタイムアウト 120→**600秒**、`ANNOTATE_BATCH` 40→**20**(1回を軽く・落ちにくく・色がこまめに付く)。
- 検証: 日本語Wikipedia「パーセプトロン」(172文=9バッチ)で **全バッチ完走・25マーカー・error無し**。
  markersが 2→6→16→25 と段階的に増え done(ストリーミング動作も確認)。backend 103件緑。

**結果: 解決** — 原因は phi4 の遅さがOllama呼び出しの120秒タイムアウトを超え `AiError`→マーカー0 になっていたこと。
タイムアウトを600秒に延長＋バッチを20文に縮小して、長文でも落ちずに(色をこまめに付けながら)完走するようにした。
