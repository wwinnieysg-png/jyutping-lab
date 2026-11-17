# 粵音修正所 v0.4.1 · 開放字庫整合版

今次版本仍然使用 v0.3 嘅霧藍色、粉彩浮球同簡潔無陰影 UI，並保留 **查字、同音字、詞例、釋義、粵拼複製、講稿修正、書面語轉口語**。

**已移除** MiniMax 測試成功／失敗回饋及「我的修正」功能。無 Firebase、無帳戶、無網站後端。

## 使用 GitHub 網頁手動架設（初學者版）

1. 下載 ZIP 並解壓。若你已經有一個網站 Repo，先備份現有內容；**不要將 ZIP 壓縮檔直接上傳當作網站**。
2. 打開 github.com，進入要部署嘅 Repository，確認分支係 `main`。新建 Repository 可選 **Public**；如果用免費方案，GitHub Pages 需要公開 Repository。
3. 於 **Code → Add file → Upload files**，將解壓後資料夾**裡面**嘅網站檔案拖到上傳畫面。要見到根目錄有 `index.html`、`styles.css`、`app.js`、`dictionary.js`、`build_dictionary.py`、`custom-words.csv` 同 `assets/`。
4. **務必檢查 `.github/workflows/deploy.yml` 有冇上傳。** 有些檔案總管會隱藏點開頭資料夾。若上傳後欠缺 workflow，於 Repo 用 **Add file → Create new file**，檔名完整填 `.github/workflows/deploy.yml`，然後將下載包內同名檔案內容貼入並 Commit。
5. 輸入 Commit message（例如 `Deploy Jyutping Studio v0.4.1`），提交到 `main`。若保護分支要求 Pull Request，先合併至 `main`。
6. 開 **Settings → Pages → Build and deployment → Source**，揀 **GitHub Actions**。呢個版本唔適合選 `Deploy from a branch`，因為要先用 Python 下載、編譯字庫。
7. 去 **Actions**，找到 `Build Cantonese dictionary and deploy GitHub Pages`。提交到 main 會自動觸發；想手動啟動就揀 **Run workflow → main → Run workflow**。
8. 留意 workflow 每步是否成功：`Download open-source dictionaries and compile indexes`、`Validate generated data`、`Deploy to GitHub Pages`。顯示綠色剔號，回 **Settings → Pages** 開啟網站網址。
9. 正式網址通常係 `https://<GitHub帳號>.github.io/<Repo名稱>/`。如果你用個人網站特別指定嘅 `username.github.io` Repo，網址會係根目錄。若已有自訂 domain，使用原有設定。

**如果 Actions 報錯**：點入紅色失敗步驟，複製最尾段錯誤文字檢查；最常見係 workflow 未上傳、來源下載失敗、字庫資料格式改變、部署權限不足。不要只見到網站首頁就假設完整字庫已建置，請檢查搜尋區域有冇顯示實際漢字及詞條數目。

**日後補字**：編輯根目錄 `custom-words.csv`，選 `Commit changes`。`main` 有新提交時會重新建置，亦可喺 Actions 手動執行。

## ⚠️ 重要：字庫如何安裝？

呢個 ZIP 包含 **完整下載／整理字庫嘅程式碼**，並未隨檔夾附未下載嘅 GitHub 字庫。原因係本次製作環境未能將 GitHub 原始檔直接下載落 ZIP。請按以下其中一個方法執行，完整資料就會由 GitHub 原始倉庫取得。

### 方法 A：GitHub Actions（推薦，唔使喺自己電腦裝工具）

1. 建立新 GitHub Repository，或者將 ZIP 解壓後所有檔案上傳到現有 Repository 嘅 `main` 分支。**連同 `.github/workflows/deploy.yml` 呢個隱藏資料夾一齊上傳**。建議用 GitHub Desktop 或 `git` 以免遺漏隱藏資料夾。
2. 進入 Repository → `Settings` → `Pages` → `Build and deployment`，將 Source 選為 **GitHub Actions**。
3. 去 `Actions` 頁，打開 **Build Cantonese dictionary and deploy GitHub Pages**，選 **Run workflow**。首次上傳到 `main` 分支亦會自動觸發。
4. Workflow 會：下載 Rime Cantonese 及 KFCD YYZD、讀取 `custom-words.csv`、合併字音同詞例、輸出 `data/*.json`、再部署到 GitHub Pages。
5. 喺 `Actions` 日誌確認匯入數量，部署完成後打開 Pages 網址。正常會見到搜尋欄上方載有實際漢字及詞條數目，唔再係「示範資料」。

GitHub Pages Source 設為 **GitHub Actions**，唔係 Deploy from a branch。請確保 GitHub Action 權限同 Pages 功能喺 repo 設定下已啟用。

**日後要更新詞庫**：編輯 `custom-words.csv` 並提交到 `main`，Actions 會重新生成字庫並發佈。來源更新後可以手動 Run workflow。

### 方法 B：自己電腦建置

安裝 Python 3.10+ 同 Git，喺資料夾執行：

```bash
python build_dictionary.py
python -m http.server 8000
```

用瀏覽器打開 `http://localhost:8000`。首次執行需要網路下載資料，之後網站讀取本地 `data/*.json`，查字毋須再連外部字庫服務。

可以執行 `python build_dictionary.py --no-phrases`，暫時不匯入較大型 phrase 來源以減少資料體積，但仍保留 chars + words。

**純預覽**：開啟 `preview.html`，無需安裝，只包括少量示範字詞。此檔未夾帶全量字庫。亦可直接開啟 `index.html` 作示範，但本機 file:// 受瀏覽器安全限制，唔會載入分散 JSON。

## 開發者補充字詞

用 Excel 打開根目錄 `custom-words.csv`（UTF-8），每行填一項：

| 字詞 | 粵拼 | 解釋 | 詞例 | 類別 |
| --- | --- | --- | --- | --- |
| 行街 | haang4 gaai1 | 逛街 | | 粵語口語 |

- **字詞**：單字或整詞，建議繁體。
- **粵拼**：香港語言學學會 1–6 聲調，例如 `haang4 gaai1`，每個字對應一個音節，以空格隔開。
- **解釋**：可留空；唔會喺網站由 AI 自動填意思。
- **詞例**：可留空；多個詞例用頓號 `、` 分隔。
- **類別**：方便人工整理，目前唔用作搜尋排序。

目前 `custom-words.csv` 已預先加入數個示範詞條供你修改；內容係開發者自訂，並非官方字典嘅權威解釋。

建置時會將相同字音／詞語音節去重。不同讀音會保留，開發者補充亦會標示來源；請留意多音字嘅語境差異。

## 資料與授權

- **Rime Cantonese**，由 Cantonese Computational Linguistics Infrastructure Development Workgroup (@CanCLID) 維護。主體資料 CC BY 4.0。專案：https://github.com/rime/rime-cantonese 。本版本匯入 `jyut6ping3.chars.dict.yaml`、`jyut6ping3.words.dict.yaml`、`jyut6ping3.phrase.dict.yaml`，**唔匯入**另循 ODbL 授權嘅 maps 檔。
- **開放粵語字典 KFCD YYZD**，© 2009–2020 開放詞典，CC BY 3.0。專案：https://github.com/kfcd/yyzd 。使用該倉庫嘅粵拼 TSV 資料；語義與詞例來自該資料。原著資料已重新排版、去重及與其他來源合併。
- **custom-words.csv**：本網站嘅開發者補充詞，與公共來源分開管理。

請保留網站關於頁面、呢份 README 同上述來源／授權連結，以符合署名條款。

## 架構

```text
index.html / styles.css / app.js / dictionary.js
assets/                 # 粉彩浮球（原版素材）
custom-words.csv        # 開發者補充詞語，可用 Excel 修改
build_dictionary.py     # Python 合併及建立索引工具
test_builder.py         # 離線格式及合併測試
.github/workflows/deploy.yml  # GitHub Actions 自動部署

data/manifest.json     # 建置後產生，實際數量和版本
    characters.json     # 漢字與所有已收錄讀音
    words-00.json…words-31.json # 按首字分片的詞語索引
```

網站查字時只載入一次漢字索引；輸入完整詞語時再按首字載入詞語分片，減少手機起始流量。網站內嘅原字讀音不能代替語音學人工校對；第三方 TTS 是否接受 `(hang4)` 格式應另行測試。

## 開發檢查

- `node --check app.js`
- `python test_builder.py`
- HTML5 語義化、響應式排版。
- 嚴格無 `box-shadow`、無漸層背景、圓角不大過 2px。

本版本係逐步改良嘅開發原型；**GitHub Actions 尚未在你嘅實際 repository 執行驗證**，部署遇到來源格式更改應參考 Actions 錯誤日誌再修正。
