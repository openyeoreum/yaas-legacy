import os
import unicodedata
import json


############################
# Unicode Helper
############################

def ToNFC(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFC", text)
    return text


def ToNFD(text):
    if isinstance(text, str):
        return unicodedata.normalize("NFD", text)
    return text


############################
# JSON 내부 value 변경
############################

def ReplaceText(text, original_candidates, new_name):

    if not isinstance(text, str):
        return text

    text = ToNFC(text)

    for original in original_candidates:
        text = text.replace(ToNFC(original), new_name)
        text = text.replace(ToNFD(original), new_name)

    return ToNFC(text)


def ReplaceJsonValues(data, original_candidates, new_name):

    if isinstance(data, dict):
        return {
            key: ReplaceJsonValues(value, original_candidates, new_name)
            for key, value in data.items()
        }

    elif isinstance(data, list):
        return [
            ReplaceJsonValues(item, original_candidates, new_name)
            for item in data
        ]

    elif isinstance(data, str):
        return ReplaceText(data, original_candidates, new_name)

    return data


def UpdateJsonFile(json_path, original_candidates, new_name):

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        new_data = ReplaceJsonValues(data, original_candidates, new_name)

        if new_data != data:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)

            print(f"[ JSON 내부 변경 완료 ] {json_path}")

    except Exception as e:
        print(f"[ JSON 변경 실패 ] {json_path} | {e}")


############################
# Unicode Normalize 전체 수행
############################

def NormalizeUnicode(storage_path):

    storage_path = ToNFC(storage_path)

    for root, dirs, files in os.walk(storage_path, topdown=False):

        for file in files:

            new_file = ToNFC(file)

            if file != new_file:

                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_file)

                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)

        for folder in dirs:

            new_folder = ToNFC(folder)

            if folder != new_folder:

                old_path = os.path.join(root, folder)
                new_path = os.path.join(root, new_folder)

                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)


############################
# Rename Core
############################

def ProjectRename(email, original_name, new_name):

    email = ToNFC(email)
    original_name = ToNFC(original_name)
    new_name = ToNFC(new_name)

    storage_root = os.path.join(
        "/yaas/storage",
        "s1_Yeoreum",
        "s12_UserStorage",
        "s123_Storage",
        email
    )

    storage_root = ToNFC(storage_root)

    print("\n[ Rename Root ]")
    print(storage_root)
    print()

    original_candidates = [
        ToNFC(original_name),
        ToNFD(original_name)
    ]

    ############################
    # Step1 JSON 내부 변경
    ############################

    for root, dirs, files in os.walk(storage_root):

        for file in files:

            if file.endswith(".json"):

                json_path = os.path.join(root, file)

                UpdateJsonFile(
                    json_path,
                    original_candidates,
                    new_name
                )

    ############################
    # Step2 파일명 변경
    ############################

    for root, dirs, files in os.walk(storage_root, topdown=False):

        for file in files:

            file_nfc = ToNFC(file)

            for candidate in original_candidates:

                if candidate in file_nfc:

                    old_path = os.path.join(root, file)

                    new_filename = file_nfc.replace(candidate, new_name)

                    new_path = os.path.join(root, new_filename)

                    if old_path != new_path:

                        if not os.path.exists(new_path):

                            os.rename(old_path, new_path)

                            print(f"[ 파일 변경 ]")
                            print(old_path)
                            print(" → ")
                            print(new_path)
                            print()

    ############################
    # Step3 폴더명 변경
    ############################

    for root, dirs, files in os.walk(storage_root, topdown=False):

        for folder in dirs:

            folder_nfc = ToNFC(folder)

            for candidate in original_candidates:

                if candidate in folder_nfc:

                    old_path = os.path.join(root, folder)

                    new_folder = folder_nfc.replace(candidate, new_name)

                    new_path = os.path.join(root, new_folder)

                    if old_path != new_path:

                        if not os.path.exists(new_path):

                            os.rename(old_path, new_path)

                            print(f"[ 폴더 변경 ]")
                            print(old_path)
                            print(" → ")
                            print(new_path)
                            print()

    ############################
    # Step4 NFC 최종 정리
    ############################

    NormalizeUnicode(storage_root)

    print("\n[ Rename Complete ]\n")


############################
# Run
############################

if __name__ == "__main__":

    Email = "yeoreum00128@gmail.com"
    # macOS 붙여넣기 OK (자동 NFC 변환됨)
    OriginalName = "000000_템플릿"

    ########################################################
    # 아래 변경할 이름 작성
    NewName = "260425_지극히사적인일본"
    ########################################################

    ProjectRename(Email, OriginalName, NewName)