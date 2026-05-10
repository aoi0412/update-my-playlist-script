import os
import sys

# プロジェクトのルートディレクトリをパスに追加（モジュール読み込みのため）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.database import SessionLocal
from backend.services.download_service import DownloadService
from backend.db.models import DownloadHistory, Track

def main():
    print("データベースに接続し、既存の曲を一括で更新します...")
    db = SessionLocal()
    service = DownloadService(db)
    
    # ダウンロードが完了している履歴をすべて取得
    histories = db.query(DownloadHistory).filter(DownloadHistory.status == "completed").all()
    
    print(f"合計 {len(histories)} 件のダウンロード済みファイルが見つかりました。処理を開始します...")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for history in histories:
        # ファイルが存在しない場合はスキップ
        if not history.file_path or not os.path.exists(history.file_path):
            skip_count += 1
            continue
            
        # 紐づくトラック情報を取得
        track = db.query(Track).filter(Track.id == history.track_id).first()
        if not track or not track.artist:
            skip_count += 1
            continue
            
        try:
            # download_service に実装したタグ上書き処理を呼び出す
            service._apply_multivalue_tags(history.file_path, track.artist)
            success_count += 1
        except Exception as e:
            print(f"エラー: {history.file_path} の処理中に問題が発生しました - {e}")
            error_count += 1
            
    print(f"\n処理が完了しました！")
    print(f"✅ 成功: {success_count} 件")
    print(f"⏭ スキップ (ファイルなし等): {skip_count} 件")
    print(f"❌ エラー: {error_count} 件")
    
    db.close()

if __name__ == "__main__":
    main()
