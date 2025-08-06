import os
import shutil
import json
import logging
import spacy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter

# 로깅 설정
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')

##################################################
##### PT1 ScriptLoad (업로드 된 스크립트 파일 확인) #####
##################################################
class ScriptLoadProcess:

    # 기본 경로 상수 정의
    ScriptUploadDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload"
    ProjectStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"

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
        self.ProcessName = "ScriptLoad"

        # 업로드 스크립트 파일 경로 및 확장자
        self.UploadedSciptFilePath = None
        self.ScriptFileExtension = None

        # 경로설정
        self._InitializePaths()

    def _InitializePaths(self):
        """프로젝트와 관련된 모든 경로를 초기화"""
        # DataFrame 원본 경로
        self.PDFLoadDataFramePath = os.path.join(self.ScriptUploadDataFramePath, "a53131_PDF/a53131-01_PDFLoadFrame.json")
        self.TXTLoadDataFramePath = os.path.join(self.ScriptUploadDataFramePath, "a53132_TXT/a53132-01_TXTLoadFrame.json")

        # project_script 관련 경로
        self.ScriptFilePath = os.path.join(self.ProjectStoragePath, self.email, self.projectName, f"{self.projectName}_script")
        self.UploadScriptFilePath = os.path.join(self.ScriptFilePath, f"{self.projectName}_upload_script_file")
        self.DataFrameScriptPath = os.path.join(self.ScriptFilePath, f"{self.projectName}_dataframe_script_file")

        # 최종 생성될 LoadFrame 파일 경로
        self.PDFLoadFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_01_PDFLoadFrame({self.Solution}).json")
        self.TXTLoadFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_01_TXTLoadFrame({self.Solution}).json")

    def _CheckExistingLoadFrame(self):
        """PDFLoadFrame 또는 TXTLoadFrame 파일이 존재하는지 확인"""
        return os.path.exists(self.PDFLoadFramePath) or os.path.exists(self.TXTLoadFramePath)

    def _FindAndProcessScriptFile(self):
        """지정된 디렉토리에서 txt 또는 pdf 스크립트 파일을 찾아 표준화된 이름으로 저장"""
        # 디렉토리의 모든 파일을 가져와 .txt 또는 .pdf 파일 탐색
        SupportedExtensions = ['.txt', '.pdf']
        AllFiles = os.listdir(self.UploadScriptFilePath)

        # txt 또는 pdf 파일이 있는 경우 해당 파일을 표준화된 이름으로 저장
        for Extension in SupportedExtensions:
            ScriptFiles = [File for File in AllFiles if File.lower().endswith(Extension)]
            if ScriptFiles:
                RawScriptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFiles[0])
                self.ScriptFileExtension = Extension[1:]
                ScriptFileName = f"{self.projectName}_Script({self.Solution}).{self.ScriptFileExtension}"
                self.UploadedSciptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFileName)

                # 파일명이 다르면 표준화된 이름으로 복사
                if ScriptFiles[0] != ScriptFileName:
                    shutil.copy2(RawScriptFilePath, self.UploadedSciptFilePath)

                # txt 또는 pdf 파일이 존재하면 True
                return True
            
        # txt 또는 pdf 파일이 없으면 False
        return False

    def _CreateLoadFrameFile(self):
        """주어진 정보로 ScriptCheck JSON 파일 생성 및 저장"""
        # 스크립트 파일 확장자에 따라 적합한 경로 설정
        if self.ScriptFileExtension == "pdf":
            LoadDataFramePath = self.PDFLoadDataFramePath
            LoadFramePath = self.PDFLoadFramePath
        elif self.ScriptFileExtension == "txt":
            LoadDataFramePath = self.TXTLoadDataFramePath
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
        ProcessInfo = f"User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.ProcessName}({self.Solution})"
        logging.info(f"< {ProcessInfo} Update 시작 >")

        # LoadFrame 파일이 이미 존재하는지 확인
        if not self._CheckExistingLoadFrame():

            # 업로드 된 스크립트 파일 여부 확인
            if not self._FindAndProcessScriptFile():
                raise FileNotFoundError(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.ScriptDirPath})\n\n")
            else:
                self._CreateLoadFrameFile()
                logging.info(f"[ {ProcessInfo} Update 완료 ]\n")

        else:
            logging.info(f"[ {ProcessInfo} Update는 이미 완료됨 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '250516_업데이트'
    Solution = 'Translation'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################

    ScriptLoaderInstance = ScriptLoadProcess(projectName, email, Solution, AutoTemplate)
    ScriptLoaderInstance.Run()