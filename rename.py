import os

def rename(base_path, old_str, new_str):
    for root, dirs, files in os.walk(base_path, topdown=False):
        # 파일 이름 변경
        for filename in files:
            if old_str in filename:
                old_path = os.path.join(root, filename)
                new_filename = filename.replace(old_str, new_str)
                new_path = os.path.join(root, new_filename)
                os.rename(old_path, new_path)
                print(f"파일 이름 변경: {old_path} -> {new_path}")

        # 디렉토리 이름 변경
        for dirname in dirs:
            if old_str in dirname:
                old_path = os.path.join(root, dirname)
                new_dirname = dirname.replace(old_str, new_str)
                new_path = os.path.join(root, new_dirname)
                os.rename(old_path, new_path)
                print(f"디렉토리 이름 변경: {old_path} -> {new_path}")

# 실행
if __name__ == "__main__":
    base_dir = "/yaas/agent/a2_Solution/a21_Operation"
    old_str = "a21"
    new_str = "a22"
    rename(base_dir, old_str, new_str)