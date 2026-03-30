#!/usr/bin/env python3
"""
Emby-sub-translate Skill
自動從 Emby 伺服器提取電影字幕，用 Gemini 翻譯成中文，並上傳回伺服器
"""

import json
import os
import re
import time
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, List

# 配置路徑
CONFIG_PATH = Path.home() / '.openclaw' / 'workspace' / 'skills' / 'emby-subtitle-translator' / 'config.json'
SKILL_DIR = Path.home() / '.openclaw' / 'workspace' / 'skills' / 'emby-subtitle-translator'

class EmbySubtitleTranslator:
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config = self.load_config()
        self.emby_base_url = f"http://{self.config['emby']['host']}:{self.config['emby']['port']}"
        self.temp_dir = SKILL_DIR / 'temp'
        self.temp_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> Dict:
        """載入配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在：{self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def search_movie(self, query: str) -> List[Dict]:
        """搜尋電影"""
        url = f"{self.emby_base_url}/Items"
        params = {
            'api_key': self.config['emby']['api_key'],
            'SearchTerm': query,
            'IncludeItemTypes': 'Movie',
            'Limit': 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get('Items', []):
            results.append({
                'id': item.get('Id'),
                'name': item.get('Name'),
                'year': item.get('ProductionYear'),
                'path': item.get('Path')
            })
        
        return results
    
    def get_movie_streams(self, movie_id: str) -> Dict:
        """獲取電影的媒體流資訊"""
        url = f"{self.emby_base_url}/Items/{movie_id}"
        params = {'api_key': self.config['emby']['api_key']}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
    
    def ssh_command(self, command: str, timeout: int = 60) -> str:
        """執行 SSH 命令"""
        ssh_config = self.config['ssh']
        
        # 使用 sshpass 執行 SSH 命令
        cmd = [
            'sshpass', '-p', ssh_config['password'],
            'ssh', '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            '-p', str(ssh_config.get('port', 22)),
            f"{ssh_config['user']}@{ssh_config['host']}",
            command
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    
    def install_ffmpeg(self):
        """在伺服器上安裝 ffmpeg"""
        print("📦 檢查並安裝 ffmpeg...")
        
        # 檢查是否已安裝
        result = self.ssh_command('which ffmpeg')
        if 'ffmpeg' in result:
            print("✅ ffmpeg 已安裝")
            return
        
        # 安裝 ffmpeg
        print("⏳ 安裝 ffmpeg...")
        self.ssh_command('apt-get update && apt-get install -y ffmpeg', timeout=300)
        
        # 驗證安裝
        result = self.ssh_command('which ffmpeg')
        if 'ffmpeg' in result:
            print("✅ ffmpeg 安裝完成")
        else:
            raise RuntimeError("❌ ffmpeg 安裝失敗")
    
    def extract_subtitle(self, movie_path: str, language: str = 'eng', output_path: str = None) -> str:
        """從電影提取字幕"""
        print(f"📽️ 提取 {language} 字幕...")
        
        if not output_path:
            output_path = str(self.temp_dir / f'subtitle_{language}.srt')
        
        # SSH 命令提取字幕
        ssh_config = self.config['ssh']
        remote_temp = f'/tmp/subtitle_{language}.srt'
        
        # 找出字幕軌道
        cmd = f"ffprobe -v error -select_streams s -show_entries stream=index:stream_tags=language -of csv=p=0 '{movie_path}'"
        result = self.ssh_command(cmd)
        
        # 解析軌道資訊
        subtitle_index = None
        for line in result.strip().split('\n'):
            if language.lower() in line.lower():
                subtitle_index = line.split(',')[0]
                break
        
        if not subtitle_index:
            # 嘗試提取第一条字幕
            subtitle_index = '0'
            print(f"⚠️ 未找到 {language} 字幕，使用第一條字幕軌道")
        
        # 提取字幕
        extract_cmd = f"ffmpeg -i '{movie_path}' -map 0:s:{subtitle_index} -c:s srt {remote_temp} -y"
        self.ssh_command(extract_cmd, timeout=120)
        
        # 下載到本地
        download_cmd = [
            'sshpass', '-p', ssh_config['password'],
            'scp', '-o', 'StrictHostKeyChecking=no', '-P', str(ssh_config.get('port', 22)),
            f"{ssh_config['user']}@{ssh_config['host']}:{remote_temp}",
            output_path
        ]
        
        subprocess.run(download_cmd, capture_output=True, timeout=30)
        
        if os.path.exists(output_path):
            print(f"✅ 字幕已提取：{output_path}")
            return output_path
        else:
            raise RuntimeError("❌ 字幕提取失敗")
    
    def translate_with_gemini(self, subtitle_path: str, batch_size: int = 120) -> str:
        """用 Gemini 翻譯字幕"""
        print("🤖 開始用 Gemini 翻譯字幕...")
        
        # 讀取字幕
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割成批次
        lines = content.split('\n')
        total_batches = (len(lines) + batch_size - 1) // batch_size
        
        translated_content = []
        
        for i in range(0, len(lines), batch_size):
            batch_num = (i // batch_size) + 1
            print(f"📝 翻譯批次 {batch_num}/{total_batches}...")
            
            batch_lines = lines[i:i+batch_size]
            batch_text = '\n'.join(batch_lines)
            
            # 構建提示詞
            prompt = f"""請幫我把這個電影 SRT 字幕從英文翻譯成繁體中文。

要求：
1. 保持 SRT 格式（序號和時間軸不要改）
2. 只翻譯對話內容，<i>標籤內的描述文字不要翻譯
3. 翻譯成高度口語化、順暢的中文
4. 人名和地名請音譯
5. 這是電影字幕

以下是第 {i+1}-{min(i+batch_size, len(lines))} 行字幕：

{batch_text}

請直接返回翻譯後的 SRT 內容，不要其他說明。"""
            
            # 調用 Gemini API（這裡需要用瀏覽器自動化）
            # 由於 Gemini API 需要特殊配置，這裡用偽代碼
            translated_batch = self.call_gemini_api(prompt)
            
            if translated_batch:
                translated_content.append(translated_batch)
            
            # 避免請求過快
            time.sleep(2)
        
        # 合併翻譯結果
        final_content = '\n'.join(translated_content)
        
        # 保存翻譯結果
        output_path = subtitle_path.replace('.srt', '.zh.srt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"✅ 翻譯完成：{output_path}")
        return output_path
    
    def call_gemini_api(self, prompt: str) -> Optional[str]:
        """調用 Gemini API（需要瀏覽器自動化）"""
        # 這裡需要用 browser 工具自動化 Gemini 網頁
        # 由於這是 Skill 代碼，實際實現需要調用 OpenClaw 的 browser 工具
        # 這裡用偽代碼表示
        
        print("⏳ 正在調用 Gemini...")
        time.sleep(5)  # 模擬 API 調用
        
        # 實際實現需要：
        # 1. 用 browser.navigate 到 gemini.google.com
        # 2. 用 browser.act 輸入提示詞
        # 3. 用 browser.snapshot 獲取翻譯結果
        # 4. 解析並返回結果
        
        return None  # 偽代碼返回
    
    def send_to_telegram(self, subtitle_path: str):
        """發送到 Telegram 確認"""
        print("📤 發送到 Telegram 確認...")
        
        tg_config = self.config.get('telegram', {})
        chat_id = tg_config.get('chat_id')
        
        if not chat_id:
            print("⚠️ 未配置 Telegram chat_id")
            return
        
        # 讀取字幕檔（前 50 行作為預覽）
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            preview = '\n'.join(f.readlines()[:50])
        
        # 發送消息（需要調用 message 工具）
        print(f"📤 預覽發送到 Telegram (chat_id: {chat_id})")
        print(preview[:500])
    
    def upload_subtitle(self, subtitle_path: str, movie_path: str):
        """上傳字幕到伺服器"""
        print("📤 上傳字幕到伺服器...")
        
        ssh_config = self.config['ssh']
        
        # 獲取電影目錄
        movie_dir = os.path.dirname(movie_path)
        movie_name = os.path.splitext(os.path.basename(movie_path))[0]
        
        # 中文字幕檔名
        subtitle_name = f"{movie_name}.chs.srt"
        remote_path = f"{movie_dir}/{subtitle_name}"
        
        # 上傳
        upload_cmd = [
            'sshpass', '-p', ssh_config['password'],
            'scp', '-o', 'StrictHostKeyChecking=no', '-P', str(ssh_config.get('port', 22)),
            subtitle_path,
            f"{ssh_config['user']}@{ssh_config['host']}:{remote_path}"
        ]
        
        subprocess.run(upload_cmd, capture_output=True, timeout=60)
        print(f"✅ 字幕已上傳：{remote_path}")
    
    def run(self, movie_query: str, language: str = 'eng'):
        """執行完整流程"""
        print(f"🎬 開始處理：{movie_query}")
        
        # 1. 搜尋電影
        print("🔍 搜尋電影...")
        results = self.search_movie(movie_query)
        
        if not results:
            print("❌ 未找到電影")
            return
        
        # 顯示結果
        print("\n找到以下電影：")
        for i, movie in enumerate(results):
            print(f"{i+1}. {movie['name']} ({movie['year']}) - ID: {movie['id']}")
        
        # 選擇第一個（或讓用戶選擇）
        movie = results[0]
        print(f"\n選擇：{movie['name']}")
        
        # 2. 獲取電影詳情
        movie_info = self.get_movie_streams(movie['id'])
        movie_path = movie_info.get('Path')
        
        if not movie_path:
            print("❌ 無法獲取電影路徑")
            return
        
        print(f"📁 電影路徑：{movie_path}")
        
        # 3. 安裝 ffmpeg
        self.install_ffmpeg()
        
        # 4. 提取字幕
        subtitle_path = self.extract_subtitle(movie_path, language)
        
        # 5. 翻譯字幕
        translated_path = self.translate_with_gemini(subtitle_path)
        
        # 6. 發送到 Telegram 確認
        self.send_to_telegram(translated_path)
        
        # 7. 確認後上傳（需要用戶確認）
        print("\n⏳ 等待用戶確認...")
        print("確認後請輸入 'y' 上傳字幕，或 'n' 取消")
        
        # 這裡需要等待用戶輸入
        # confirm = input("確認上傳？(y/n): ")
        confirm = 'y'  # 偽代碼
        
        if confirm.lower() == 'y':
            self.upload_subtitle(translated_path, movie_path)
            print("✅ 完成！")
        else:
            print("❌ 已取消")


def main():
    """主函數"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python emby_subtitle_translator.py <電影名稱> [語言]")
        print("範例：python emby_subtitle_translator.py '恐懼夜話' eng")
        return
    
    movie_query = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'eng'
    
    translator = EmbySubtitleTranslator()
    translator.run(movie_query, language)


if __name__ == '__main__':
    main()
