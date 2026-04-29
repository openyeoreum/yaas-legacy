import os

import unicodedata

import json

def ToNFC(text):

    if isinstance(text, str):

        return unicodedata.normalize("NFC", text)

    return text

def ToNFD(text):

    if isinstance(text, str):

        return unicodedata.normalize("NFD", text)

    return text

def MakeOriginalCandidates(original_name):

    return list(set([

        ToNFC(original_name),

        ToNFD(original_name),

    ]))

def ReplaceText(text, original_candidates, new_name):

    if not isinstance(text, str):

        return text

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

    if isinstance(data, list):

        return [

            ReplaceJsonValues(item, original_candidates, new_name)

            for item in data

        ]

    if isinstance(data, str):

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

            print(f"[ JSON 내부 value 변경 ] {json_path}")

    except Exception as e:

        print(f"[ JSON 처리 실패 ] {json_path} | {e}")

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

                    print(f"[ 파일 NFC 변경 ] {old_path} -> {new_path}")

                else:

                    print(f"[ 파일 NFC 건너뜀: 이미 존재 ] {new_path}")

        for folder in dirs:

            new_folder = ToNFC(folder)

            if folder != new_folder:

                old_path = os.path.join(root, folder)

                new_path = os.path.join(root, new_folder)

                if not os.path.exists(new_path):

                    os.rename(old_path, new_path)

                    print(f"[ 폴더 NFC 변경 ] {old_path} -> {new_path}")

                else:

                    print(f"[ 폴더 NFC 건너뜀: 이미 존재 ] {new_path}")

def RenameFiles(storage_root, original_candidates, new_name):

    for root, dirs, files in os.walk(storage_root, topdown=False):

        root_nfc = ToNFC(root)

        for file in files:

            file_nfc = ToNFC(file)

            for candidate in original_candidates:

                candidate_nfc = ToNFC(candidate)

                if candidate_nfc in file_nfc:

                    old_path = os.path.join(root, file)

                    new_filename = file_nfc.replace(candidate_nfc, new_name)

                    new_filename = ToNFC(new_filename)

                    new_path = os.path.join(root_nfc, new_filename)

                    new_path = ToNFC(new_path)

                    if old_path != new_path:

                        if not os.path.exists(new_path):

                            os.rename(old_path, new_path)

                            print(f"[ 파일 이름 변경 ] {old_path} -> {new_path}")

                        else:

                            print(f"[ 파일 이름 건너뜀: 이미 존재 ] {new_path}")

                    break

def RenameFolders(storage_root, original_candidates, new_name):

    for root, dirs, files in os.walk(storage_root, topdown=False):

        root_nfc = ToNFC(root)

        for folder in dirs:

            folder_nfc = ToNFC(folder)

            for candidate in original_candidates:

                candidate_nfc = ToNFC(candidate)

                if candidate_nfc in folder_nfc:

                    old_path = os.path.join(root, folder)

                    new_folder = folder_nfc.replace(candidate_nfc, new_name)

                    new_folder = ToNFC(new_folder)

                    new_path = os.path.join(root_nfc, new_folder)

                    new_path = ToNFC(new_path)

                    if old_path != new_path:

                        if not os.path.exists(new_path):

                            os.rename(old_path, new_path)

                            print(f"[ 폴더 이름 변경 ] {old_path} -> {new_path}")

                        else:

                            print(f"[ 폴더 이름 건너뜀: 이미 존재 ] {new_path}")

                    break

def UpdateJsonFiles(storage_root, original_candidates, new_name):

    for root, dirs, files in os.walk(storage_root):

        for file in files:

            if file.endswith(".json"):

                json_path = os.path.join(root, file)

                UpdateJsonFile(json_path, original_candidates, new_name)

def ProjectRename(email, original_name, new_name):

    email = ToNFC(email)

    new_name = ToNFC(new_name)

    original_candidates = MakeOriginalCandidates(original_name)

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

    print("[ Original Candidates ]")

    for candidate in original_candidates:

        print(candidate)

    print()

    UpdateJsonFiles(storage_root, original_candidates, new_name)

    RenameFiles(storage_root, original_candidates, new_name)

    RenameFolders(storage_root, original_candidates, new_name)

    NormalizeUnicode(storage_root)

    print("\n[ Rename Complete ]\n")

if __name__ == "__main__":

    Email = "yeoreum00128@gmail.com"
    # macOS 붙여넣기 OK (자동 NFC 변환됨)
    OriginalName = "000000_템플릿"

    ########################################################
    ########################################################
    # 아래 변경할 이름 작성
    NewName = "260425_지극히사적인일본"
    ########################################################
    ########################################################

    ProjectRename(Email, OriginalName, NewName)