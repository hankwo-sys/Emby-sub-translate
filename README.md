# Emby-sub-translate Skill

自動從 Emby 伺服器提取電影字幕，用 Gemini 翻譯成中文，並上傳回伺服器。

## 功能

1. 連接 Emby API 搜尋電影
2. SSH 進入伺服器提取字幕
3. 用 Gemini 翻譯成繁體中文
4. Telegram 確認翻譯品質
5. 上傳中文字幕到 Emby 伺服器

## 配置

在 `~/.openclaw/workspace/skills/emby-subtitle-translator/config.json` 創建配置：

```json
{
  "emby": {
    "host": "154.40.54.28",
    "port": 2095,
    "api_key": "8fb7ec7cc1474955bed3c98789daa36b"
  },
  "ssh": {
    "host": "154.40.54.28",
    "port": 22,
    "user": "root",
    "password": "3eds78fcUs2a39Tk"
  },
  "telegram": {
    "chat_id": "738187802"
  },
  "subtitle": {
    "source_language": "eng",
    "target_language": "chi",
    "batch_size": 120
  }
}
```

## 使用方式

### 搜尋電影
```
搜尋電影 恐懼夜話
搜尋電影 Gaua
```

### 提取並翻譯字幕
```
翻譯字幕 [電影ID]
翻譯字幕 1135189
```

### 指定語言
```
翻譯字幕 [電影ID] 英文
翻譯字幕 [電影ID] eng
```

## 工作流程

1. **搜尋電影** → 獲取電影 ID 和路徑
2. **SSH 連接** → 檢查並安裝 ffmpeg
3. **提取字幕** → 從 MKV 提取指定語言字幕
4. **Gemini 翻譯** → 分批翻譯（每批 120 行）
5. **TG 確認** → 發送翻譯結果給用戶確認
6. **上傳字幕** → SSH 上傳 `.chs.srt` 到電影同目錄

## 輸出

- 翻譯後字幕檔名：`[電影名稱].chs.srt`
- 位置：與電影檔同一目錄
- 格式：SRT（保持時間軸）

## 注意事項

- 需要 Emby API 權限
- 需要 SSH root 權限
- Gemini 翻譯需要時間（約 30-60 分鐘/部電影）
- 建議先測試短片
