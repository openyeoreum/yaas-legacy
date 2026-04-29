import os
import unicodedata
import sys
import json

sys.path.append("/yaas")


### Sub1 : 한글 유니코드 정규화 ###
def NormalizeUnicode(Code="NFC", StoragePath="/yaas/storage"):
    for DirPath, DirNames, FileNames in os.walk(StoragePath, topdown=False):

        # 파일 이름 정규화 및 변경
        for filename in FileNames:
            NormalizedFilename = unicodedata.normalize(Code, filename)

            if filename != NormalizedFilename:
                OriginalFilePath = os.path.join(DirPath, filename)
                NewFilePath = os.path.join(DirPath, NormalizedFilename)

                os.rename(OriginalFilePath, NewFilePath)

                if "AudioBook_Edit" in filename:
                    print(f"[ 파일 이름 {Code} 변경: '{filename}' -> '{NormalizedFilename}' ]")

        # 디렉토리 이름 정규화 및 변경
        for dirname in DirNames:
            NormalizedDirname = unicodedata.normalize(Code, dirname)

            if dirname != NormalizedDirname:
                OriginalDirPath = os.path.join(DirPath, dirname)
                NewDirPath = os.path.join(DirPath, NormalizedDirname)

                os.rename(OriginalDirPath, NewDirPath)

                if "AudioBook_Edit" in dirname:
                    print(f"[ 디렉토리 이름 {Code} 변경: '{dirname}' -> '{NormalizedDirname}' ]")


### Sub2 : 프로젝트명 변경 ###
def ProjectRename(OriginalName, NewName, StoragePath="/yaas/storage"):
    NFCOriginalName = unicodedata.normalize("NFC", OriginalName)
    NFDOriginalName = unicodedata.normalize("NFD", OriginalName)

    Unicodes = [NFCOriginalName, NFDOriginalName]

    for _OriginalName in Unicodes:

        # 모든 디렉토리와 파일을 거꾸로 순회
        for root, dirs, files in os.walk(StoragePath, topdown=False):

            # 파일 이름 변경
            for name in files:
                if _OriginalName in name:
                    OriginalFilePath = os.path.join(root, name)
                    NewFileName = name.replace(_OriginalName, NewName)
                    NewFilePath = os.path.join(root, NewFileName)

                    os.rename(OriginalFilePath, NewFilePath)

                    print(f"[ 파일 이름 변경: '{OriginalFilePath}' -> '{NewFilePath}' ]")

            # 디렉토리 이름 변경
            for name in dirs:
                if _OriginalName in name:
                    OriginalDirPath = os.path.join(root, name)
                    NewDirName = name.replace(_OriginalName, NewName)
                    NewDirPath = os.path.join(root, NewDirName)

                    os.rename(OriginalDirPath, NewDirPath)

                    print(f"[ 디렉토리 이름 변경: '{OriginalDirPath}' -> '{NewDirPath}' ]")

        # 핵심 추가:
        # StoragePath 자체가 OriginalName을 포함하고 있는 경우,
        # os.walk 내부에서는 root 자기 자신이 dirs에 포함되지 않으므로 별도로 변경해야 함
        StorageBaseName = os.path.basename(StoragePath)
        StorageParentPath = os.path.dirname(StoragePath)

        if _OriginalName in StorageBaseName:
            NewStorageBaseName = StorageBaseName.replace(_OriginalName, NewName)
            NewStoragePath = os.path.join(StorageParentPath, NewStorageBaseName)

            os.rename(StoragePath, NewStoragePath)

            print(f"[ 최상위 디렉토리 이름 변경: '{StoragePath}' -> '{NewStoragePath}' ]")

            # 이후 ConfigPath 계산을 위해 StoragePath 갱신
            StoragePath = NewStoragePath

    # Config ProjectName 이름 변경
    ConfigPath = os.path.join(
        StoragePath,
        "s1_Yeoreum",
        "s12_UserStorage",
        "s123_Storage",
        NewName,
        f"{NewName}_config.json"
    )

    if os.path.exists(ConfigPath):
        with open(ConfigPath, "r", encoding="utf-8") as ConfigJson:
            ConfigData = json.load(ConfigJson)

        ConfigData["ProjectName"] = NewName

        with open(ConfigPath, "w", encoding="utf-8") as ConfigJson:
            json.dump(ConfigData, ConfigJson, ensure_ascii=False, indent=4)

        print(f"[ Config ProjectName 이름 변경: '{ConfigPath}' -> '{NewName}' ]")


if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    OriginalName = "000000_템플릿"
    NewName = "260425_지극히사적인일본"
    #########################################################################

    # NormalizeUnicode("NFC")
    ProjectRename(OriginalName, NewName)