import os
import shutil
from PIL import Image
import piexif

BUPS = r"C:\BackUp_Pictures"
def compress_and_save_image(path):
    try:
        img = Image.open(path).convert("RGBA")

        # PNG透過→白背景JPEG
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        else:
            img = img.convert("RGB")

        # サイズ調整
        max_length = 1920
        w, h = img.size
        if max(w, h) > max_length:
            ratio = max_length / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        # Exif削除
        exif_bytes = piexif.dump({})

        # JPEGで上書き保存
        img.save(path, "JPEG", quality=80, exif=exif_bytes)

        print(f"圧縮成功：{path}")
        return path

    except Exception as e:
        print(f"圧縮エラー：{e}")
        return None


def get_latest_images(directory, limit=1): 
	# ここの値で実行枚数指定/新しい順にn枚圧縮
    valid_exts = [".jpg", ".jpeg", ".png"]
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.splitext(f)[1].lower() in valid_exts
    ]
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:limit]


def main():
    folder = BUPS
    latest_images = get_latest_images(folder)
    print(f"{latest_images}が入っています")

    for original_path in latest_images:
        name, _ = os.path.splitext(os.path.basename(original_path))
        copy_path = os.path.join(folder, f"{name}.jpg")

        try:
            shutil.copy2(original_path, copy_path)
            os.remove(original_path)
            compress_and_save_image(copy_path)
        except Exception as e:
            print(f"{original_path} の圧縮失敗：{e}")


if __name__ == "__main__":
    main()
