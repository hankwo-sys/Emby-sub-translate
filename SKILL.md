# Emby-sub-translate Skill

## 安裝

1. 複製配置範例：
```bash
cp ~/.openclaw/workspace/skills/emby-subtitle-translator/config.json.example ~/.openclaw/workspace/skills/emby-subtitle-translator/config.json
```

2. 編輯配置：
```bash
nano ~/.openclaw/workspace/skills/emby-subtitle-translator/config.json
```

填入：
- Emby API Key
- SSH 帳號密碼
- Telegram Chat ID

3. 安裝依賴：
```bash
pip3 install requests
```

## 使用方式

### 在對話中直接使用

```
搜尋電影 恐懼夜話
翻譯字幕 1135189
翻譯字幕 1135189 英文
```

### 命令行使用

```bash
python3 ~/.openclaw/workspace/skills/emby-subtitle-translator/emby_subtitle_translator.py "恐懼夜話" eng
```

## 工作流程

```
┌─────────────┐
│  搜尋電影    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  SSH 連接     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 安裝 ffmpeg  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  提取字幕    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Gemini 翻譯  │ (分批處理)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  TG 確認     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  上傳字幕    │
└─────────────┘
```

## 配置說明

### Emby 配置
- `host`: Emby 伺服器 IP
- `port`: Emby 端口（預設 2095）
- `api_key`: Emby API Key

### SSH 配置
- `host`: SSH 伺服器 IP（通常與 Emby 相同）
- `port`: SSH 端口（預設 22）
- `user`: SSH 用戶名（通常 root）
- `password`: SSH 密碼

### Telegram 配置
- `chat_id`: 用於確認的 Telegram Chat ID

### 字幕配置
- `source_language`: 源語言（eng, spa, jpn 等）
- `target_language`: 目標語言（chi, zho 等）
- `batch_size`: Gemini 翻譯批次大小（預設 120 行）

## 輸出

- 翻譯後字幕檔名：`[電影名稱].chs.srt`
- 位置：與電影檔同一目錄
- 格式：SRT（保持原始時間軸）

## 注意事項

1. **需要 sshpass**：
```bash
brew install sshpass  # macOS
apt-get install sshpass  # Linux
```

2. **Gemini 翻譯時間**：
   - 每批 120 行約需 1-2 分鐘
   - 完整電影（2500 行）約需 30-60 分鐘

3. **建議先測試**：
   - 先用短片測試流程
   - 確認翻譯品質後再處理長片

4. **字幕語言代碼**：
   - eng: 英文
   - spa: 西班牙文
   - jpn: 日文
   - kor: 韓文
   - chi/zho: 中文

## 故障排除

### ffmpeg 安裝失敗
```bash
ssh root@your_server "apt-get update && apt-get install -y ffmpeg"
```

### SSH 連接失敗
- 檢查 SSH 密碼是否正確
- 確認 SSH 端口是否開放
- 檢查防火牆設定

### Gemini 翻譯失敗
- 檢查瀏覽器是否登入 Google 帳號
- 確認網路連接正常
- 減少 batch_size 重試

## 作者

由 Luna 為韓佬創建 🌙✨
