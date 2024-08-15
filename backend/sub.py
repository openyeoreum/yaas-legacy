import os
import multiprocessing
import unicodedata
import sys
sys.path.append("/yaas")

### Sub1 : 한글 유니코드 정규화 ###
def NormalizeUnicode(Code = "NFC", StoragePath = "/yaas/storage"):
    for DirPath, DirNames, FileNames in os.walk(StoragePath, topdown = False):
        # 파일 이름 정규화 및 변경
        for filename in FileNames:
            NormalizedFilename = unicodedata.normalize(Code, filename)
            if filename != NormalizedFilename:
                OriginalFilePath = os.path.join(DirPath, filename)
                NewFilePath = os.path.join(DirPath, NormalizedFilename)
                os.rename(OriginalFilePath, NewFilePath)
                if 'AudioBook_Edit' in filename:
                    print(f"[ 파일 이름 {Code} 변경: '{filename}' -> {Code}: '({NormalizedFilename})' ]")

        # 디렉토리 이름 정규화 및 변경
        for dirname in DirNames:
            NormalizedDirname = unicodedata.normalize(Code, dirname)
            if dirname != NormalizedDirname:
                OriginalDirPath = os.path.join(DirPath, dirname)
                NewDirPath = os.path.join(DirPath, NormalizedDirname)
                os.rename(OriginalDirPath, NewDirPath)
                if 'AudioBook_Edit' in filename:
                    print(f"[ 디렉토리 이름 {Code} 변경: '{dirname}' -> {Code}: '({NormalizedDirname})' ]")
                
### Sub2 : 프로젝트명 변경 ###
def ProjectRename(OriginalName, NewName, StoragePath = "/yaas/storage"):
    NFCOriginalName = unicodedata.normalize("NFC", OriginalName)
    NFDOriginalName = unicodedata.normalize("NFD", OriginalName)
    Unicodes = [NFCOriginalName, NFDOriginalName]
    for _OriginalName in Unicodes:
        # 모든 디렉토리와 파일을 거꾸로 순회
        for root, dirs, files in os.walk(StoragePath, topdown = False):
            # 파일 이름 변경
            for name in files:
                if _OriginalName in name:
                    OriginalFilePath = os.path.join(root, name)
                    NewFileName = name.replace(_OriginalName, NewName)
                    NewFilePath = os.path.join(root, NewFileName)
                    os.rename(OriginalFilePath, NewFilePath)
                    print(f"[ 파일 이름 변경: '{OriginalFilePath}' -> '({NewFilePath})' ]")
            
            # 디렉토리 이름 변경
            for name in dirs:
                if _OriginalName in name:
                    OriginalDirPath = os.path.join(root, name)
                    NewDirName = name.replace(_OriginalName, NewName)
                    NewDirPath = os.path.join(root, NewDirName)
                    os.rename(OriginalDirPath, NewDirPath)
                    print(f"[ 디렉토리 이름 변경: '{OriginalDirPath}' -> '({NewDirPath})' ]")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    OriginalName = '240812_룰루레몬스토리'
    NewName = '240812_룰루레몬스토리'
    #########################################################################

    # NormalizeUnicode('NFC')
    ProjectRename(OriginalName, NewName)