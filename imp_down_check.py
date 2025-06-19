import os
import time
import shutil
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 設定
DOWNLOADS_FOLDER = r"C:\Users\momoz\Downloads"
WORK_FOLDER = r"C:\Users\momoz\work"
SCAN_INTERVAL = 3  # スキャン間隔（秒）
DEBUG = True  # デバッグモード

# スクリプト開始時刻（これ以降に作成されたファイルのみ処理対象）
START_TIME = time.time()

# フォルダ準備
if not os.path.exists(WORK_FOLDER):
    os.makedirs(WORK_FOLDER)
    print(f"作業ディレクトリを作成しました: {WORK_FOLDER}")


def is_temp_file(file_path):
    """一時ファイルかどうかを判定"""
    file_name = os.path.basename(file_path)
    return file_name.endswith('.tmp') or file_name.endswith('.crdownload')


def process_file(file_path, existing_files):
    """ファイルを処理してワークフォルダに移動"""
    # 基本的なチェック
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        return False

    # 既存ファイルやディレクトリは対象外
    if file_path in existing_files:
        return False
        
    file_name = os.path.basename(file_path)
    
    # 一時ファイルはスキップ
    if is_temp_file(file_path):
        if DEBUG:
            print(f"一時ファイルのためスキップ: {file_path}")
        return False
    
    try:
        # ファイルが完全にダウンロードされるまで少し待機
        time.sleep(1)
        
        # ファイルが存在し、サイズが0でないことを確認
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
            
        # 移動先のパスを作成（重複回避）
        dest_path = os.path.join(WORK_FOLDER, file_name)
        if os.path.exists(dest_path):
            base_name, extension = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(dest_path):
                new_name = f"{base_name}_{counter}{extension}"
                dest_path = os.path.join(WORK_FOLDER, new_name)
                counter += 1
        
        # ファイルを移動
        if DEBUG:
            print(f"ファイルを移動します: {file_path} -> {dest_path}")
            
        shutil.move(file_path, dest_path)
        print(f"ファイルを移動しました: {file_name} → {dest_path}")
        return True
        
    except PermissionError:
        # ファイルがまだ使用中
        if DEBUG:
            print(f"ファイルにアクセスできません（使用中）: {file_path}")
        return False
    except Exception as e:
        print(f"{file_name}の移動中にエラーが発生しました: {e}")
        return False


class DownloadWatcher:
    """ダウンロードフォルダを監視するクラス"""
    
    def __init__(self, downloads_folder, work_folder):
        """初期化"""
        self.downloads_folder = downloads_folder
        self.work_folder = work_folder
        
        # 既存のファイルリスト（処理対象外）
        self.existing_files = self._get_existing_files()
        print(f"既存のファイル {len(self.existing_files)}個 は処理対象外とします")
        
        # 処理中のファイルを追跡
        self.processing_files = set()
        
        # 観察対象と監視ハンドラーの設定
        self.event_handler = self._create_event_handler()
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.downloads_folder, recursive=False)

    def _get_existing_files(self):
        """既存ファイルのリストを取得"""
        existing = set()
        for filename in os.listdir(self.downloads_folder):
            file_path = os.path.join(self.downloads_folder, filename)
            if os.path.isfile(file_path):
                existing.add(file_path)
        return existing
    
    def _create_event_handler(self):
        """イベントハンドラーを作成"""
        watcher = self
        
        class DownloadHandler(FileSystemEventHandler):
            def on_created(self, event):
                if event.is_directory:
                    return
                watcher._handle_file_event(event.src_path, "作成")
                
            def on_modified(self, event):
                if event.is_directory:
                    return
                watcher._handle_file_event(event.src_path, "変更")
                
            def on_moved(self, event):
                if event.is_directory:
                    return
                # 移動先のファイルを処理
                watcher._handle_file_event(event.dest_path, "移動")
        
        return DownloadHandler()
    
    def _handle_file_event(self, file_path, event_type):
        """ファイルイベントを処理"""
        if file_path in self.processing_files:
            return
            
        if DEBUG:
            print(f"ファイル{event_type}検出: {file_path}")
            
        # 一時ファイルは処理しない
        if is_temp_file(file_path):
            if DEBUG:
                print(f"一時ファイルを検出: {file_path}")
            return
            
        # 処理対象をマークして別スレッドで処理
        self.processing_files.add(file_path)
        threading.Thread(
            target=self._process_in_thread, 
            args=(file_path,), 
            daemon=True
        ).start()
    
    def _process_in_thread(self, file_path):
        """別スレッドでファイル処理を実行"""
        try:
            # ファイルが確実に完了するまで待機
            time.sleep(3)
            process_file(file_path, self.existing_files)
        finally:
            # 処理完了フラグを設定
            self.processing_files.discard(file_path)
    
    def start_periodic_scan(self):
        """定期的なフォルダスキャンを開始"""
        def scanner():
            while True:
                try:
                    time.sleep(SCAN_INTERVAL)
                    self.scan_folder()
                except Exception as e:
                    print(f"スキャン中にエラーが発生: {e}")
        
        scan_thread = threading.Thread(target=scanner, daemon=True)
        scan_thread.start()
    
    def scan_folder(self):
        """フォルダをスキャンして新しいファイルを検出"""
        if DEBUG:
            print("フォルダをスキャン中...")
            
        try:
            # フォルダ内のすべてのファイルをチェック
            for filename in os.listdir(self.downloads_folder):
                file_path = os.path.join(self.downloads_folder, filename)
                
                # 基本的なフィルタリング
                if not os.path.isfile(file_path):
                    continue
                if file_path in self.existing_files:
                    continue
                if file_path in self.processing_files:
                    continue
                if is_temp_file(file_path):
                    continue
                
                # 作成時刻をチェック
                creation_time = os.path.getctime(file_path)
                if creation_time < START_TIME:
                    continue
                
                # 新しいファイルを処理
                if DEBUG:
                    print(f"スキャンで新しいファイルを検出: {file_path}")
                
                self.processing_files.add(file_path)
                threading.Thread(
                    target=self._process_in_thread, 
                    args=(file_path,), 
                    daemon=True
                ).start()
                
        except Exception as e:
            print(f"フォルダスキャン中にエラーが発生しました: {e}")
    
    def start(self):
        """監視を開始"""
        # ファイルシステム監視を開始
        self.observer.start()
        
        # 定期的なスキャンも開始
        self.start_periodic_scan()
        
        print(f"監視中: {self.downloads_folder}")
        print(f"ファイルの移動先: {self.work_folder}")
        print("ダウンロードフォルダの監視を開始しました。停止するにはCtrl+Cを押してください。")
        if DEBUG:
            print("デバッグモード: 有効")
        
        try:
            # メインスレッドを実行し続ける
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            print("ファイル移動プログラムが停止しました。")
        
        self.observer.join()


if __name__ == "__main__":
    # 監視を開始
    watcher = DownloadWatcher(DOWNLOADS_FOLDER, WORK_FOLDER)
    watcher.start()