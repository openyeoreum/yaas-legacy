import os
import shutil
import json
import spacy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter


##################################################
##### PT1 ScriptLoad (업로드 된 스크립트 파일 확인) #####
##################################################
class ScriptLoadProcess:

    # 기본 경로 정의
    ScriptUploadDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload"
    ProjectStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"

    ## ScriptLoad 초기화 ##
    def __init__(self, projectName, email, Solution, AutoTemplate):
        """클래스 초기화"""

        ## 업데이트 정보
        self.email = email
        self.projectName = projectName
        self.Solution = Solution
        self.AutoTemplate = AutoTemplate

        ## Process 설정
        self.ProcessNumber = '1'
        self.ProcessName = "ScriptLoad"

        ## 업로드 스크립트 파일 경로 및 확장자
        self.UploadedScriptFilePath = None
        self.ScriptFileExtension = None

        ## 경로설정
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
        self.PDFLoadFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_P01_PDFLoadFrame({self.Solution}).json")
        self.TXTLoadFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_T01_TXTLoadFrame({self.Solution}).json")

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
                self.UploadedScriptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFileName)

                # 파일명이 다르면 표준화된 이름으로 복사
                if ScriptFiles[0] != ScriptFileName:
                    shutil.copy2(RawScriptFilePath, self.UploadedScriptFilePath)

                # txt 또는 pdf 파일이 존재하면 True
                return True
            
        # txt 또는 pdf 파일이 없으면 False
        return False

    def _CreateLoadFrameFile(self):
        """주어진 정보로 ScriptLoadFrame JSON 파일 생성 및 저장"""
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
        LoadFrame[0]['Completion'] = "Yes"
        LoadFrame[1]['ScriptFilePath'] = self.UploadedScriptFilePath

        with open(LoadFramePath, 'w', encoding = 'utf-8') as LoadFrameFile:
            json.dump(LoadFrame, LoadFrameFile, ensure_ascii = False, indent = 4)

    def _LoadScriptLoadFrame(self):
        """생성된 ScriptLoadFrame JSON 파일 불러오기"""
        # 스크립트 파일 확장자에 따라 적합한 경로 설정
        if os.path.exists(self.PDFLoadFramePath):
            LoadFramePath = self.PDFLoadFramePath
        elif os.path.exists(self.TXTLoadFramePath):
            LoadFramePath = self.TXTLoadFramePath
            
        # LoadFrame JSON 파일 불러오기
        with open(LoadFramePath, 'r', encoding = 'utf-8') as LoadFrameFile:
            LoadFrame = json.load(LoadFrameFile)

        # LoadFrame에서 필요한 정보 반환
        ProjectName = LoadFrame[0]['ProjectName']
        Solution = LoadFrame[0]['Solution']
        AutoTemplate = LoadFrame[0]['AutoTemplate']
        FileExtension = LoadFrame[0]['FileExtension']
        Language = LoadFrame[0]['Language'] if LoadFrame[0]['Language'] != "" else None
        ScriptFilePath = LoadFrame[1]['ScriptFilePath']
            
        return ProjectName, Solution, AutoTemplate, FileExtension, Language, ScriptFilePath

    def Run(self):
        """스크립트 로드 전체 프로세스를 실행하는 메인 메서드"""
        ProcessInfo = f"User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.ProcessName}({self.Solution})"
        print(f"< {ProcessInfo} Update 시작 >")

        # LoadFrame 파일이 이미 존재하는지 확인
        if not self._CheckExistingLoadFrame():

            # 업로드 된 스크립트 파일 여부 확인
            if not self._FindAndProcessScriptFile():
                raise FileNotFoundError(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.UploadScriptFilePath})\n\n")
            else:
                self._CreateLoadFrameFile()
                print(f"[ {ProcessInfo} Update 완료 ]\n")
                return self._LoadScriptLoadFrame()

        else:
            print(f"[ {ProcessInfo} Update는 이미 완료됨 ]\n")
            return self._LoadScriptLoadFrame()

#############################################
##### P2 PDFSplit (PDF 페이지 별 분할) #########
#############################################
class PDFSplitProcess:

    # 기본 경로 정의
    ScriptUploadDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload"
    ProjectStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"

    ## PDFSplit 초기화 ##
    def __init__(self, projectName, email, Solution, AutoTemplate, FileExtension, UploadedScriptFilePath):
        """클래스 초기화"""

        ## 업데이트 정보
        self.projectName = projectName
        self.email = email
        self.Solution = Solution
        self.AutoTemplate = AutoTemplate
        self.ScriptFileExtension = FileExtension
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        ## Process 설정
        self.ProcessNumber = '2'
        self.ProcessName = "PDFSplit"
        
        ## 경로설정
        self._InitializePaths()

    def _InitializePaths(self):
        """프로젝트와 관련된 모든 경로를 초기화"""
        self.PDFSplitDataFramePath = os.path.join(self.ScriptUploadDataFramePath, "a53131_PDF/a53131-02_PDFSplitFrame.json")
        
        self.ScriptFilePath = os.path.join(self.ProjectStoragePath, self.email, self.projectName, f"{self.projectName}_script")
        self.DataFrameScriptPath = os.path.join(self.ScriptFilePath, f"{self.projectName}_dataframe_script_file")
        
        self.SplitPDFDirectoryPath = os.path.join(self.ScriptFilePath, f"{self.projectName}_Script({self.Solution})_{self.ScriptFileExtension}")
        os.makedirs(self.SplitPDFDirectoryPath, exist_ok = True)
        
        self.PDFSplitFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_P02_PDFSplitFrame({self.Solution}).json")

    def _SplitPDF(self):
        """PDF 파일을 페이지별로 분할하고 저장"""
        PageFilePaths = []
        Reader = PdfReader(self.UploadedScriptFilePath)
        TotalPages = len(Reader.pages)
        
        for PageNum in range(TotalPages):
            Writer = PdfWriter()
            Writer.add_page(Reader.pages[PageNum])
            
            OutputFileName = f"{self.projectName}_Script({self.Solution})({PageNum + 1}).{self.ScriptFileExtension}"
            OutputFilePath = os.path.join(self.SplitPDFDirectoryPath, OutputFileName)
            
            with open(OutputFilePath, "wb") as OutputFile:
                Writer.write(OutputFile)
            PageFilePaths.append(OutputFilePath)
            
        return PageFilePaths

    def _CreateSplitFrameFile(self, PageFilePaths):
        """분할된 PDF 정보로 SplitFrame JSON 파일 생성"""
        with open(self.PDFSplitDataFramePath, 'r', encoding='utf-8') as FrameFile:
            SplitFrame = json.load(FrameFile)

        SplitFrame[0]['ProjectName'] = self.projectName
        SplitFrame[0]['Solution'] = self.Solution
        SplitFrame[0]['AutoTemplate'] = self.AutoTemplate
        SplitFrame[0]['InputCount'] = len(PageFilePaths)
        SplitFrame[0]['Completion'] = "Yes"
        
        # 기존 리스트에 페이지별 경로 추가
        for i, Path in enumerate(PageFilePaths):
            SplitFrame[1].append({
                "ScriptId": i + 1,
                "PageFilePath": Path
            })

        with open(self.PDFSplitFramePath, 'w', encoding='utf-8') as OutputJson:
            json.dump(SplitFrame, OutputJson, ensure_ascii=False, indent=4)

    def Run(self):
        """PDF 분할 전체 프로세스 실행"""
        ProcessInfo = f"User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.ProcessName}({self.Solution})"
        print(f"< {ProcessInfo} Update 시작 >")

        if os.path.exists(self.PDFSplitFramePath):
            print(f"[ {ProcessInfo} Update는 이미 완료됨 ]\n")
            return

        PageFilePaths = self._SplitPDF()
        self._CreateSplitFrameFile(PageFilePaths)
        print(f"[ {ProcessInfo} Update 완료 ]\n")


##############################################
##### T2 TXTSplit (TXT 토큰 단위 분할) ##########
##############################################
class TXTSplitProcess:
    ScriptUploadDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload"
    ProjectStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"

    def __init__(self, projectName, email, Solution, AutoTemplate, FileExtension, Language, UploadedScriptFilePath):
        self.projectName = projectName
        self.email = email
        self.Solution = Solution
        self.AutoTemplate = AutoTemplate
        self.ScriptFileExtension = FileExtension
        self.Language = Language if Language else 'en' # 언어 설정이 없으면 영어로 기본값
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        self.ProcessNumber = '2'
        self.ProcessName = "TXTSplit"
        
        self.MaxTokens = 3000

        self._InitializePaths()

    def _InitializePaths(self):
        self.TXTSplitDataFramePath = os.path.join(self.ScriptUploadDataFramePath, "a53132_TXT/a53132-02_TXTSplitFrame.json")
        
        self.ScriptFilePath = os.path.join(self.ProjectStoragePath, self.email, self.projectName, f"{self.projectName}_script")
        self.DataFrameScriptPath = os.path.join(self.ScriptFilePath, f"{self.projectName}_dataframe_script_file")
        
        self.TXTSplitFramePath = os.path.join(self.DataFrameScriptPath, f"{self.email}_{self.projectName}_T02_TXTSplitFrame({self.Solution}).json")

    def _LoadSpacyModel(self):
        """언어에 맞는 Spacy 모델 로드"""
        # 간단한 언어 코드 매핑
        ModelMap = {
            'en': 'en_core_web_sm',
            'ko': 'ko_core_news_sm'
            # 필요에 따라 다른 언어 모델 추가
        }
        ModelName = ModelMap.get(self.Language.lower(), 'en_core_web_sm')
        
        try:
            nlp = spacy.load(ModelName)
        except OSError:
            print(f"Spacy 모델 '{ModelName}'을 찾을 수 없습니다. 다운로드를 시도합니다.")
            spacy.cli.download(ModelName)
            nlp = spacy.load(ModelName)

        # 기존 파이프라인에 사용자 정의 경계 설정 추가
        if "set_custom_boundaries" not in nlp.pipe_names:
            nlp.add_pipe("set_custom_boundaries", before="parser")
        return nlp

    def _SplitTXT(self):
        """TXT 파일을 지정된 토큰 수에 가깝게 문장 묶음으로 분할"""
        nlp = self._LoadSpacyModel()
        
        with open(self.UploadedScriptFilePath, 'r', encoding='utf-8') as f:
            FullText = f.read()

        doc = nlp(FullText)
        Sentences = [s.text for s in doc.sents]
        
        Chunks = []
        CurrentChunkList = []
        
        for sent in Sentences:
            CurrentChunkList.append(sent)
            CurrentText = "".join(CurrentChunkList)
            
            # 토큰 수는 더 빠른 `make_doc`을 사용하여 계산
            TokenCount = len(nlp.make_doc(CurrentText))
            
            if TokenCount >= self.MaxTokens:
                Chunks.append(CurrentText)
                CurrentChunkList = []
                
        # 마지막 남은 문장 묶음 추가
        if CurrentChunkList:
            Chunks.append("".join(CurrentChunkList))
            
        return Chunks

    def _CreateSplitFrameFile(self, TextChunks):
        """분할된 텍스트 정보로 SplitFrame JSON 파일 생성"""
        with open(self.TXTSplitDataFramePath, 'r', encoding='utf-8') as FrameFile:
            SplitFrame = json.load(FrameFile)

        SplitFrame[0]['ProjectName'] = self.projectName
        SplitFrame[0]['Solution'] = self.Solution
        SplitFrame[0]['AutoTemplate'] = self.AutoTemplate
        SplitFrame[0]['Language'] = self.Language
        SplitFrame[0]['InputCount'] = len(TextChunks)
        SplitFrame[0]['Completion'] = "Yes"
        
        for i, Chunk in enumerate(TextChunks):
            SplitFrame[1].append({
                "ScriptId": i + 1,
                "SplitedText": Chunk
            })

        with open(self.TXTSplitFramePath, 'w', encoding='utf-8') as OutputJson:
            json.dump(SplitFrame, OutputJson, ensure_ascii=False, indent=4)

    def Run(self):
        """TXT 분할 전체 프로세스 실행"""
        ProcessInfo = f"User: {self.email} | Project: {self.projectName} | {self.ProcessNumber}_{self.ProcessName}({self.Solution})"
        print(f"< {ProcessInfo} Update 시작 >")

        if os.path.exists(self.TXTSplitFramePath):
            print(f"[ {ProcessInfo} Update는 이미 완료됨 ]\n")
            return

        TextChunks = self._SplitTXT()
        self._CreateSplitFrameFile(TextChunks)
        print(f"[ {ProcessInfo} Update 완료 ]\n")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '250516_업데이트'
    Solution = 'Translation'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################

    # 1. 스크립트 파일 로드
    ScriptLoaderInstance = ScriptLoadProcess(projectName, email, Solution, AutoTemplate)
    ProjectName, Solution, AutoTemplate, FileExtension, Language, ScriptFilePath = ScriptLoaderInstance.Run()
    
    print(f"ProjectName: {ProjectName}, Solution: {Solution}, AutoTemplate: {AutoTemplate}, FileExtension: {FileExtension}, Language: {Language}, ScriptFilePath: {ScriptFilePath}\n")

    # 2. 파일 확장자에 따라 후속 프로세스 실행
    if FileExtension == 'pdf':
        PDFSplitterInstance = PDFSplitProcess(ProjectName, email, Solution, AutoTemplate, FileExtension, ScriptFilePath)
        PDFSplitterInstance.Run()
        
    elif FileExtension == 'txt':
        TXTSplitterInstance = TXTSplitProcess(ProjectName, email, Solution, AutoTemplate, FileExtension, Language, ScriptFilePath)
        TXTSplitterInstance.Run()