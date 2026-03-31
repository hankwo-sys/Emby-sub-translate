# Emby-sub-translate Skill

## 安裝

1. 克隆倉庫：
```bash
git clone https://github.com/hankwo-sys/Emby-sub-translate.git
cd Emby-sub-translate
```

2. 創建配置文件：
```bash
cp config.json.example config.json
nano config.json
```

3. 編輯配置：
```json
{
  "emby": {
    "host": "請填入 Emby 伺服器 IP",
    "port": 2095,
    "api_key": "請填入 Emby API Key"
  },
  "ssh": {
    "host": "請填入 SSH 伺服器 IP",
    "port": 22,
    "user": "root",
    "password": "請填入 SSH 密碼"
  },
  "telegram": {
    "chat_id": "請填入 Telegram Chat ID"
  },
  "subtitle": {
    "source_language": "eng",
    "target_language": "chi",
    "batch_size": 120
  }
}
```

⚠️ **安全警告：**
- `config.json` 包含敏感資訊，已加入 `.gitignore`
- 不要手動上傳 `config.json` 到 GitHub
- 不要將密碼提交到版本控制

## 使用方式

### 在對話中使用
```
搜尋電影 恐懼夜話
翻譯字幕 1135189
翻譯字幕 1135189 英文
```

### 命令行使用
```bash
python3 emby_subtitle_translator.py "恐懼夜話" eng
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
│ DeepSeek 翻譯 │ (分批處理，瀏覽器操作)
└──────┬──────┘
       │
       ▼
│ 📊 每15分鐘進度報告 │
       │
       ▼
┌─────────────┐
│  合併字幕    │
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
- `batch_size`: DeepSeek 翻譯批次大小（預設 120 行）

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

2. **DeepSeek 翻譯時間**：
   - 每批 120 行約需 30 秒 - 1 分鐘
   - 完整電影（2500 行）約需 15-20 分鐘

3. **翻譯進度報告**：
   - 每 15 分鐘自動向 Telegram 發送進度報告
   - 報告包含：已完成批次、剩餘批次、預計完成時間
   - 確保長時間翻譯任務時用戶能掌握進度

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

### DeepSeek 翻譯失敗
- 檢查瀏覽器是否已開啟 DeepSeek 頁面 (https://chat.deepseek.com)
- 確認網路連接正常
- 減少 batch_size 重試

## 作者

由 Luna 為韓佬創建 🌙✨
