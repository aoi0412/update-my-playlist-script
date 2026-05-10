import os
import sys
import re

# プロジェクトのルートディレクトリをパスに追加（モジュール読み込みのため）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
os.chdir(project_root)

def fix_file(file_path):
    try:
        import mutagen
        from mutagen.id3 import ID3, TPE1, TPE2
    except ImportError:
        print("mutagen is not installed.")
        return False

    if not file_path.lower().endswith('.mp3'):
        return False
        
    try:
        audio = ID3(file_path)
    except Exception as e:
        return False

    changed = False
    
    # 1. TPE1 (アーティスト) のチェックと書き換え
    if "TPE1" in audio:
        artist_text = str(audio["TPE1"].text[0])
        artists_list = [a.strip() for a in re.split(r',|\s+&\s+', artist_text) if a.strip()]
        if len(artists_list) > 1:
            joined = " / ".join(artists_list)
            audio.add(TPE1(encoding=3, text=[joined]))
            changed = True
            
    # 2. TPE2 (アルバムアーティスト) もNavidromeの表示に影響するため同様に書き換える
    if "TPE2" in audio:
        album_artist_text = str(audio["TPE2"].text[0])
        artists_list = [a.strip() for a in re.split(r',|\s+&\s+', album_artist_text) if a.strip()]
        if len(artists_list) > 1:
            joined = " / ".join(artists_list)
            audio.add(TPE2(encoding=3, text=[joined]))
            changed = True

    if changed:
        audio.save(file_path, v2_version=3)
        return True
    return False

def main():
    print("データベースを使わず、MP3ファイルのタグを直接読み込んで更新します...")
    
    # data/downloads 以下のすべてのmp3ファイルを検索（サブディレクトリも含む）
    mp3_files = []
    for root, dirs, files in os.walk("data/downloads"):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
                
    print(f"合計 {len(mp3_files)} 件のMP3ファイルが見つかりました。処理を開始します...")
    
    success_count = 0
    
    for file_path in mp3_files:
        try:
            if fix_file(file_path):
                success_count += 1
                print(f"🔄 更新: {file_path}")
        except Exception as e:
            print(f"❌ エラー ({file_path}): {e}")
            
    print(f"\n処理が完了しました！")
    print(f"✅ 実際にタグが上書きされたファイル: {success_count} 件")

if __name__ == "__main__":
    main()
