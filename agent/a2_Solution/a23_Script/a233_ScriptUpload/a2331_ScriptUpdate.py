import os
import shutil
import json
import spacy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter

################################################
##### ScriptLoader (업로드 된 스크립트 파일 확인) #####
################################################
class ScriptLoadProcess:

    ## ScriptLoader 초기화 ##
    def __init__(self, projectName, email, Solution, AutoTemplate):
        """클래스 초기화 시 필요한 정보"""

        # 업데이트 정보
        self.email = email
        self.projectName = projectName
        self.Solution = Solution
        self.AutoTemplate = AutoTemplate

        ## Process 설정
        self.ProcessNumber = '1'
        self.Process = "ScriptLoad"

        # 업로드 스크립트 파일 경로 및 확장자
        self.UploadedSciptFilePath = None
        self.ScriptFileExtension = None

        # DataFrame 경로
        self.PDFLoadDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload/a53131_PDF/a53131-01_PDFLoadFrame.json"
        self.TXTLoadDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload/a53132_TXT/a53132-01_TXTLoadFrame.json"

        # project_script 경로
        self.ScriptFilePath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{self.email}/{self.projectName}/{self.projectName}_script"
        self.UploadScriptFilePath = os.path.join(self.ScriptFilePath, f"{self.projectName}_upload_script_file")
        self.DataFrameScriptPath = os.path.join(self.ScriptFilePath, f"{self.projectName}_dataframe_script_file")
        self.PDFLoadFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_01_PDFLoadFrame({self.Solution}).json")
        self.TXTLoadFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_01_TXTLoadFrame({self.Solution}).json")

    def _CheckExistingLoadFrame(self):
        """PDFLoadFrame 또는 TXTLoadFrame 파일이 존재하는지 확인"""
        return os.path.exists(self.PDFLoadFramePath) or os.path.exists(self.TXTLoadFramePath)

    def _FindAndProcessScriptFile(self):
        """지정된 디렉토리에서 txt 또는 pdf 스크립트 파일을 찾아 표준화된 이름으로 저장"""
        # 디렉토리의 모든 파일을 가져와 .txt 또는 .pdf 파일 탐색
        AllFiles = os.listdir(self.UploadScriptFilePath)
        TxtFiles = [File for File in AllFiles if File.lower().endswith(".txt")]
        PdfFiles = [File for File in AllFiles if File.lower().endswith(".pdf")]

        # txt 또는 pdf 파일이 있는 경우 해당 파일을 표준화된 이름으로 저장
        if TxtFiles:
            original_file_path = os.path.join(self.UploadScriptFilePath, TxtFiles[0])
            self.ScriptFileExtension = "txt"
            ScriptFileName = f"{self.projectName}_Script({self.Solution}).{self.ScriptFileExtension}"
            self.UploadedSciptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFileName)
            
            # 파일명이 다르면 표준화된 이름으로 복사
            if TxtFiles[0] != ScriptFileName:
                shutil.copy2(original_file_path, self.UploadedSciptFilePath)
                
        elif PdfFiles:
            original_file_path = os.path.join(self.UploadScriptFilePath, PdfFiles[0])
            self.ScriptFileExtension = "pdf"
            ScriptFileName = f"{self.projectName}_Script({self.Solution}).{self.ScriptFileExtension}"
            self.UploadedSciptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFileName)
            
            # 파일명이 다르면 표준화된 이름으로 복사
            if PdfFiles[0] != ScriptFileName:
                shutil.copy2(original_file_path, self.UploadedSciptFilePath)

        return self.UploadedSciptFilePath is not None

    def _CreateLoadFrameFile(self):
        """주어진 정보로 ScriptCheck JSON 파일 생성 및 저장"""
        # 스크립트 파일 확장자에 따라 적합한 경로 설정
        if self.ScriptFileExtension == "pdf":
            LoadDataFramePath = os.path.join(self.PDFLoadDataFramePath)
            LoadFramePath = self.PDFLoadFramePath
        elif self.ScriptFileExtension == "txt":
            LoadDataFramePath = os.path.join(self.TXTLoadDataFramePath)
            LoadFramePath = self.TXTLoadFramePath

        # LoadFrame JSON 파일 생성
        with open(LoadDataFramePath, 'r', encoding = 'utf-8') as LoadDataFrameFile:
            LoadFrame = json.load(LoadDataFrameFile)

        LoadFrame[0]['ProjectName'] = self.projectName
        LoadFrame[0]['Solution'] = self.Solution
        LoadFrame[0]['AutoTemplate'] = self.AutoTemplate
        LoadFrame[0]['FileExtension'] = self.ScriptFileExtension

        with open(LoadFramePath, 'w', encoding='utf-8') as LoadFrameFile:
            json.dump(LoadFrame, LoadFrameFile, ensure_ascii = False, indent = 4)

    def Run(self):
        """스크립트 로드 전체 프로세스를 실행하는 메인 메서드"""
        print(f"< User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.Process}({self.Solution})Update 시작 >")

        # LoadFrame 파일이 이미 존재하는지 확인
        if not self._CheckExistingLoadFrame():

            # 업로드 된 스크립트 파일 여부 확인
            if not self._FindAndProcessScriptFile():
                sys.exit(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.ScriptDirPath})\n\n")
            else:
                self._CreateLoadFrameFile()
                print(f"[ User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.Process}({self.Solution})Update 완료 ]\n")

        else:
            print(f"[ User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.Process}({self.Solution})Update는 이미 완료됨 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '250516_업데이트'
    Solution = 'Translation'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################

    ScriptLoaderInstance = ScriptLoadProcess(projectName, email, Solution, AutoTemplate)
    ScriptLoaderInstance.Run()