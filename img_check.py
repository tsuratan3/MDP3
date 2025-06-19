import os
import glob
import time
import shutil
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DLF = r""
SSF = r""
BUPS = r"C:\BackUp_Pictures"
INTERVAL = 3
DEBUG =True
SST = time.time()

#フォルダ準備
if not os.path.exists(BUPS):
    os.makedirs(BUPS)
    print(f"作業ディレクトリを作成：{BUPS}")

def _reguler_name_dl():
    dp = os.path.join(os.environ['USERPROFILE'], 'Downloads')
    return dp

def _reguler_name_oss():
    osp = os.path.join(os.environ['USERPROFILE'], 'OneDrive', '画像', 'スクリーンショット')
    return osp

def _reguler_name_ss():
    sp = os.path.join(os.environ['USERPROFILE'], '画像', 'スクリーンショット')
    return sp

def is_temp_file(file_path):
    """一時ファイルかどうか判定"""
    file_name = os.path.basename(file_path)
    return file_name.endswith(".tmp") or file_name.endswith(".crdownload")

def is_picture_file(file_path):
    """画像ファイル(.jpgまたは.jpeg)かどうか判定"""
    return file_path.lower().endswith(".jpg") or file_path.lower().endswith(".jpeg") or file_path.lower().endswith(".png")

def process_file(file_path, ep):
    """ファイルを処理してワークフォルダに移動"""
    #基本的なチェック
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        return False
    
    #既存ファイルやディレクトリは対象外
    if file_path in ep:
        return False
    
    file_name = os.path.basename(file_path)

    #一時ファイルはスキップ
    if is_temp_file(file_path):
        if DEBUG:
            print(f"一時ファイルのためスキップ：{file_path}")
        return False
    
    if not is_picture_file(file_path):
        if DEBUG:
            print(f"画像ファイル以外はスキップ：{file_path}")
        return False
    
    try:
        #ファイルが完全にダウンロードされるまで少し待機
        time.sleep(1)

        #ファイルが存在し、サイズが0でないことを確認
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
        
        #移動先のパスを作成（重複回避）
        dp = os.path.join(BUPS, file_name)
        if os.path.exists(dp):
            bn, extension = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(dp):
                nn = f"{bn}_{counter}_{extension}"
                dp = os.path.join(BUPS, nn)
                counter += 1
        
        #ファイルを移動
        if DEBUG:
            print(f"ファイルに移動します：{file_path} → {dp}")
        
        shutil.move(file_path, dp)
        print(f"ファイルを移動しました：{file_path} → {dp}")
        return True
    
    except PermissionError:
        #ファイルがまだ使用中
        if DEBUG:
            print(f"ファイルにアクセスできません（使用中）：{file_path}")
        return False
    except Exception as e:
        print(f"{file_name}の移動中にエラーが発生しました：{e}")
        return False
    

class DownLoadGurding:
    """ダウンロードフォルダを監視するクラス"""
    def __init__(self, dlf, ssf, bups):
        """初期化"""
        self.dlf = dlf
        self.bups = bups
        self.ssf = ssf
        #既存のファイルリスト（処理対象外）
        self.ep = self._get_existing_pic()
        print(f"既存のファイル{len(self.ep)}個は処理対象外とします")

        #処理中のファイルを追跡
        self.pf = set()

        #観察対象と監視ハンドラーの設定
        self.eh = self._create_event_handler()
        self.observer = Observer()
        self.observer.schedule(self.eh,self.dlf,recursive=False)
        self.observer.schedule(self.eh,self.ssf,recursive=False)

    def _get_existing_pic(self):
        """既存ファイルのリストを取得"""
        existing = set()
        for filename in os.listdir(self.dlf):
            file_path = os.path.join(self.dlf, filename)
            if os.path.isfile(file_path):
                existing.add(file_path)
        return existing
    
    def _create_event_handler(self):
        """イベントハンドラーを作成"""
        gurd = self

        class DownloadHandler(FileSystemEventHandler):
            def on_created(self,event):
                if event.is_directory:
                    return
                gurd._handle_file_event(event.src_path,"作成")

            # def on_modified(self,event):
            #     if event.is_directory:
            #         return
            #     gurd._handle_file_event(event.src_path,"変更")

            # def on_moved(self,event):
            #     if event.is_directory:
            #         return
            #     #移動先のファイルを処理
            #     gurd._handle_file_event(event.src_path,"移動")

        return DownloadHandler()

    def _handle_file_event(self, file_path,et):
        """ファイルイベントを処理"""
        if file_path in self.pf:
            return
        if is_picture_file(file_path):
            if DEBUG:
                print(f"画像ファイル{et}検出：{file_path}")
    
        #一時ファイルは処理しない
        if is_temp_file(file_path):
            if DEBUG:
                print(f"一時ファイルを検出：{file_path}")
            return
        
        #処理対象をマークして別スレッドで処理
        self.pf.add(file_path)
        threading.Thread(
            target = self._process_in_thread,
            args = (file_path,),
            daemon = True
        ).start()

    def _process_in_thread(self, file_path):
        """別スレッドでファイル処理を実行"""
        try:
            #ファイルが確実に完了するまで待機
            time.sleep(3)
            process_file(file_path, self.ep)
        finally:
            #処理完了フラグを設定
            self.pf.discard(file_path)
    
    def start_periodic_scan(self):
        """定期的なフォルダスキャンを開始"""
        def scanner():
            while True:
                try:
                    time.sleep(INTERVAL)
                    self.scan_folder()
                except Exception as e:
                    print(f"スキャン中にエラーが発生：{e}")
        st = threading.Thread(target=scanner, daemon=True)
        st.start()

    def scan_folder(self):
        """フォルダをスキャンして新しいファイルを検出"""
        if DEBUG:
            print("フォルダをスキャン中…")
        
        try:
            #フォルダ内の全てのファイルをチェック
            for filename in os.listdir(self.dlf):
                file_path = os.path.join(self.dlf, filename)

                #基本的なフィルタリング
                if not os.path.isfile(file_path):
                    continue
                if file_path in self.ep:
                    continue
                if file_path in self.pf:
                    continue
                if is_temp_file(file_path):
                    continue
                if not is_picture_file(file_path):
                    continue

                #作成時刻をチェック
                ctime = os.path.getctime(file_path)
                if ctime < SST:
                    continue

                #新しいファイルを処理
                if DEBUG:
                    print(f"スキャンで新しいファイルを検出：{file_path}")

                self.pf.add(file_path)
                threading.Thread(
                    target=self._process_in_thread,
                    args=(file_path,),
                    daemon=True
                ).start()

        except Exception as e:
            print(f"フォルダをスキャン中にエラーが発生しました：{e}")

        try:
            #フォルダ内の全てのファイルをチェック
            for filename in os.listdir(self.ssf):
                file_path = os.path.join(self.ssf, filename)

                #基本的なフィルタリング
                if not os.path.isfile(file_path):
                    continue
                if file_path in self.ep:
                    continue
                if file_path in self.pf:
                    continue
                if is_temp_file(file_path):
                    continue
                if not is_picture_file(file_path):
                    continue

                #作成時刻をチェック
                ctime = os.path.getctime(file_path)
                if ctime < SST:
                    continue

                #新しいファイルを処理
                if DEBUG:
                    print(f"スキャンで新しいファイルを検出：{file_path}")

                self.pf.add(file_path)
                threading.Thread(
                    target=self._process_in_thread,
                    args=(file_path,),
                    daemon=True
                ).start()

        except Exception as e:
            print(f"フォルダをスキャン中にエラーが発生しました：{e}")

    def start(self):
        """監視を開始"""
        #ファイルシステム監視を開始
        self.observer.start()

        #定期的なスキャンも開始
        self.start_periodic_scan()

        print(f"監視中：{self.dlf}")
        print(f"監視中：{self.ssf}")
        print(f"ファイルの移動先：{self.bups}")
        print("ダウンロードフォルダとスクリーンショットフォルダの監視を開始しました。停止するにはCtrl+Cを押してください。")
        if DEBUG:
            print("デバッグモード：有効")
        try:
            #メインスレッドを実行し続ける
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            print("ファイル移動プログラムが停止しました。")
        
        self.observer.join()


if __name__ == "__main__":
    #監視を開始
    osp = _reguler_name_oss()
    sp = _reguler_name_ss()
    if not os.path.exists(osp):
        SSF = _reguler_name_ss()
        print(f"SP：{sp}")
    else:
        SSF = _reguler_name_oss()
        print(f"OSP：{osp}")
    DLF = _reguler_name_dl()
    print(f"{DLF},{SSF}")
    if os.path.exists(DLF) and os.path.exists(SSF):
        Gurding_Program = DownLoadGurding(DLF, SSF, BUPS)
        Gurding_Program.start()
    else:
        print("パス設定が正しくされていません。")