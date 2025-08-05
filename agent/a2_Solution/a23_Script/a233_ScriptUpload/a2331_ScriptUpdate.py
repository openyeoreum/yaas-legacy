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
class ScriptLoader:

    ## ScriptLoader 초기화 ##
    def __init__(self, ProjectName, Email, Solution, ScriptDataFramePath, ProjectDataFrameScriptCheckPath, Language = "ko", AutoSegmentation = "No"):
        """클래스 초기화 시 필요한 모든 속성을 설정"""
        # 기본 정보 속성
        self.ProjectName = ProjectName
        self.Email = Email
        self.Solution = Solution
        self.AutoSegmentation = AutoSegmentation
        self.Language = Language

        # 경로 관련 속성
        self.ScriptDataFramePath = ScriptDataFramePath
        self.ProjectDataFrameScriptCheckPath = ProjectDataFrameScriptCheckPath
        self.ScriptDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{self.Email}/{self.ProjectName}/{self.ProjectName}_script/{self.ProjectName}_upload_script_file"

        # 최초 업로드 파일 속성
        self.TargetFilePath = None
        self.FileExtension = None
        
        # spaCy 모델 로드
        self.nlp = self._LoadSpacyModel()

    def _FindScriptFile(self):
        """지정된 디렉토리에서 .txt 또는 .pdf 스크립트 파일을 찾아 속성에 저장"""
        AllFiles = os.listdir(self.ScriptDirPath)
        TxtFiles = [File for File in AllFiles if File.lower().endswith(".txt")]
        PdfFiles = [File for File in AllFiles if File.lower().endswith(".pdf")]

        if TxtFiles:
            self.TargetFilePath = os.path.join(self.ScriptDirPath, TxtFiles[0])
            self.FileExtension = ".txt"
        elif PdfFiles:
            self.TargetFilePath = os.path.join(self.ScriptDirPath, PdfFiles[0])
            self.FileExtension = ".pdf"
        
        return self.TargetFilePath is not None

    def _ProcessPdfScript(self):
        """PDF 스크립트 파일 처리"""
        NewFileName = f"{self.ProjectName}_Script({self.Solution}).pdf"
        NewFilePath = os.path.join(self.ScriptDirPath, NewFileName)
        shutil.copy2(self.TargetFilePath, NewFilePath)
        
        PdfSplitDir = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_Script({self.Solution})_pdf")
        os.makedirs(PdfSplitDir, exist_ok=True)

        FileContent = ""
        PageDataList = []
        PdfReaderInstance = PdfReader(self.TargetFilePath)

        for PageNum, Page in enumerate(PdfReaderInstance.pages):
            FileContent += Page.extract_text() or ""
            PdfWriterInstance = PdfWriter()
            PdfWriterInstance.add_page(Page)
            PageFilePath = os.path.join(PdfSplitDir, f"{self.ProjectName}_Script({self.Solution})_{PageNum}.pdf")
            with open(PageFilePath, 'wb') as PageFile:
                PdfWriterInstance.write(PageFile)
            
            PageDataList.append({
                "Page": PageNum + 1,
                "Form": "None",
                "Index": "None",
                "Component": [],
                "Content": PageFilePath
            })

        FileExtensionTag = "pdf(text)" if FileContent.strip() else "pdf(image)"
        self._CreateScriptCheckFile(FileExtensionTag=FileExtensionTag, PageDataList=PageDataList)
        return FileContent

    def _CreateScriptCheckFile(self, FileExtensionTag, PageDataList):
        """주어진 정보로 ScriptCheck JSON 파일 생성 및 저장"""
        DataFrameTemplatePath = os.path.join(self.ScriptDataFramePath, "a5312-00_ScriptCheckFrame.json")
        with open(DataFrameTemplatePath, 'r', encoding='utf-8') as DataFrameTemplateFile:
            ScriptCheckData = json.load(DataFrameTemplateFile)

        ScriptCheckData[0]['ProjectName'] = self.ProjectName
        ScriptCheckData[0]['FileExtension'] = FileExtensionTag
        ScriptCheckData[0]['Solution'] = self.Solution
        ScriptCheckData[0]['AutoSegmentation'] = self.AutoSegmentation
        ScriptCheckData[0]['InputCount'] = len(PageDataList)

        ScriptCheckData[1] = PageDataList

        with open(self.ProjectDataFrameScriptCheckPath, 'w', encoding='utf-8') as ResultFile:
            json.dump(ScriptCheckData, ResultFile, ensure_ascii=False, indent=4)

    def Run(self):
        """스크립트 로드 전체 프로세스를 실행하는 메인 메서드"""
        if os.path.exists(self.ProjectDataFrameScriptCheckPath):
            print("ℹ️ Script check file already exists. Skipping process.")
            return

        if not self._FindScriptFile():
            sys.exit(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.ScriptDirPath})\n\n")

        print(f"Found script file: {os.path.basename(self.TargetFilePath)}")

        if self.FileExtension == ".txt":
            print("Processing as TXT file...")
            self._ProcessTxtScript()
        elif self.FileExtension == ".pdf":
            print("Processing as PDF file...")
            self._ProcessPdfScript()
        
        print("✅ Script loading process complete.")

# class ScriptLoader:

#     ## ScriptLoader 초기화 ##
#     def __init__(self, ProjectName, Email, Solution, ScriptDataFramePath, ProjectDataFrameScriptCheckPath, Language = "ko", AutoSegmentation = "No"):
#         """클래스 초기화 시 필요한 모든 속성을 설정"""
#         # 기본 정보 속성
#         self.ProjectName = ProjectName
#         self.Email = Email
#         self.Solution = Solution
#         self.AutoSegmentation = AutoSegmentation
#         self.Language = Language

#         # 경로 관련 속성
#         self.ScriptDataFramePath = ScriptDataFramePath
#         self.ProjectDataFrameScriptCheckPath = ProjectDataFrameScriptCheckPath
#         self.ScriptDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{self.Email}/{self.ProjectName}/{self.ProjectName}_script/{self.ProjectName}_upload_script_file"

#         # 최초 업로드 파일 속성
#         self.TargetFilePath = None
#         self.FileExtension = None
        
#         # spaCy 모델 로드
#         self.nlp = self._LoadSpacyModel()

#     ## Spacty 모델 로드 ##
#     def _LoadSpacyModel(self):
#         """언어 코드에 맞는 spaCy 모델을 찾아 로드합니다."""
#         ModelMap = {
#             "ko": "ko_core_news_sm",
#             "en": "en_core_web_sm",
#             "zh": "zh_core_web_sm",
#             "ja": "ja_core_news_sm",
#             "fr": "fr_core_news_sm",
#             "de": "de_core_news_sm",
#             "es": "es_core_news_sm",
#         }
#         ModelName = ModelMap.get(self.Language)
#         if not ModelName:
#             raise ValueError(f"지원되지 않는 언어 코드입니다: {self.Language}")
        
#         try:
#             return spacy.load(ModelName)
#         except OSError:
#             print(f"spaCy 모델 '{ModelName}'을 찾을 수 없습니다.")
#             print(f"다음 명령어를 실행하여 모델을 다운로드해주세요: python -m spacy download {ModelName}")
#             sys.exit(1)

#     ## [수정됨] 텍스트 분할 핵심 로직 ##
#     def _SplitTextIntoChunks(self, FullText, ChunkSize = 2000):
#         """
#         spaCy를 사용해 텍스트를 분할합니다.
#         1. 원본 구조(공백, 줄바꿈)를 완벽하게 유지합니다.
#         2. 문장의 끝 또는 줄바꿈 위치에서만 분할합니다.
#         3. 각 청크는 ChunkSize를 넘는 가장 가까운 지점에서 분할됩니다.
#         """
#         # 1. spaCy로 문장 경계 찾기
#         doc = self.nlp(FullText)
#         SentenceBoundaries = {sent.end_char for sent in doc.sents}

#         # 2. 모든 줄바꿈 위치 찾기
#         NewlineBoundaries = {i + 1 for i, char in enumerate(FullText) if char == '\n'}
        
#         # 3. 모든 경계 지점을 합치고 정렬하기
#         AllBoundaries = sorted(list(SentenceBoundaries.union(NewlineBoundaries)))
        
#         PageDataList = []
#         CurrentChunkStart = 0
#         PageIndex = 1

#         # 4. 경계 지점을 순회하며 청크 생성
#         for Boundary in AllBoundaries:
#             # 현재 경계까지의 길이가 ChunkSize를 넘는지 확인
#             if Boundary - CurrentChunkStart >= ChunkSize:
#                 Chunk = FullText[CurrentChunkStart:Boundary]
#                 PageDataList.append({
#                     "Page": PageIndex,
#                     "Form": "None",
#                     "Index": "None",
#                     "Component": [],
#                     "Content": Chunk
#                 })
#                 PageIndex += 1
#                 CurrentChunkStart = Boundary # 다음 청크 시작 위치 업데이트

#         # 5. 마지막 남은 텍스트를 최종 청크로 추가
#         if CurrentChunkStart < len(FullText):
#             FinalChunk = FullText[CurrentChunkStart:]
#             PageDataList.append({
#                 "Page": PageIndex,
#                 "Form": "None",
#                 "Index": "None",
#                 "Component": [],
#                 "Content": FinalChunk
#             })
            
#         return PageDataList

#     def _ProcessTxtScript(self):
#         """TXT 스크립트 파일 처리"""
#         NewFileName = f"{self.ProjectName}_Script({self.Solution}).txt"
#         NewFilePath = os.path.join(self.ScriptDirPath, NewFileName)
#         shutil.copy2(self.TargetFilePath, NewFilePath)

#         with open(self.TargetFilePath, 'r', encoding = 'utf-8') as TxtFile:
#             FileContent = TxtFile.read()
        
#         PageDataList = self._SplitTextIntoChunks(FileContent)
        
#         self._CreateScriptCheckFile(FileExtensionTag = "txt", PageDataList=PageDataList)
#         return FileContent

#     #
#     # --- 이하 _FindScriptFile, _ProcessPdfScript, _CreateScriptCheckFile, Run 메서드는 이전과 동일 ---
#     #

#     def _FindScriptFile(self):
#         """지정된 디렉토리에서 .txt 또는 .pdf 스크립트 파일을 찾아 속성에 저장"""
#         AllFiles = os.listdir(self.ScriptDirPath)
#         TxtFiles = [File for File in AllFiles if File.lower().endswith(".txt")]
#         PdfFiles = [File for File in AllFiles if File.lower().endswith(".pdf")]

#         if TxtFiles:
#             self.TargetFilePath = os.path.join(self.ScriptDirPath, TxtFiles[0])
#             self.FileExtension = ".txt"
#         elif PdfFiles:
#             self.TargetFilePath = os.path.join(self.ScriptDirPath, PdfFiles[0])
#             self.FileExtension = ".pdf"
        
#         return self.TargetFilePath is not None

#     def _ProcessPdfScript(self):
#         """PDF 스크립트 파일 처리"""
#         NewFileName = f"{self.ProjectName}_Script({self.Solution}).pdf"
#         NewFilePath = os.path.join(self.ScriptDirPath, NewFileName)
#         shutil.copy2(self.TargetFilePath, NewFilePath)
        
#         PdfSplitDir = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_Script({self.Solution})_pdf")
#         os.makedirs(PdfSplitDir, exist_ok=True)

#         FileContent = ""
#         PageDataList = []
#         PdfReaderInstance = PdfReader(self.TargetFilePath)

#         for PageNum, Page in enumerate(PdfReaderInstance.pages):
#             FileContent += Page.extract_text() or ""
#             PdfWriterInstance = PdfWriter()
#             PdfWriterInstance.add_page(Page)
#             PageFilePath = os.path.join(PdfSplitDir, f"{self.ProjectName}_Script({self.Solution})_{PageNum}.pdf")
#             with open(PageFilePath, 'wb') as PageFile:
#                 PdfWriterInstance.write(PageFile)
            
#             PageDataList.append({
#                 "Page": PageNum + 1,
#                 "Form": "None",
#                 "Index": "None",
#                 "Component": [],
#                 "Content": PageFilePath
#             })

#         FileExtensionTag = "pdf(text)" if FileContent.strip() else "pdf(image)"
#         self._CreateScriptCheckFile(FileExtensionTag=FileExtensionTag, PageDataList=PageDataList)
#         return FileContent

#     def _CreateScriptCheckFile(self, FileExtensionTag, PageDataList):
#         """주어진 정보로 ScriptCheck JSON 파일 생성 및 저장"""
#         DataFrameTemplatePath = os.path.join(self.ScriptDataFramePath, "a5312-00_ScriptCheckFrame.json")
#         with open(DataFrameTemplatePath, 'r', encoding='utf-8') as DataFrameTemplateFile:
#             ScriptCheckData = json.load(DataFrameTemplateFile)

#         ScriptCheckData[0]['ProjectName'] = self.ProjectName
#         ScriptCheckData[0]['FileExtension'] = FileExtensionTag
#         ScriptCheckData[0]['Solution'] = self.Solution
#         ScriptCheckData[0]['AutoSegmentation'] = self.AutoSegmentation
#         ScriptCheckData[0]['InputCount'] = len(PageDataList)

#         ScriptCheckData[1] = PageDataList

#         with open(self.ProjectDataFrameScriptCheckPath, 'w', encoding='utf-8') as ResultFile:
#             json.dump(ScriptCheckData, ResultFile, ensure_ascii=False, indent=4)

#     def Run(self):
#         """스크립트 로드 전체 프로세스를 실행하는 메인 메서드"""
#         if os.path.exists(self.ProjectDataFrameScriptCheckPath):
#             print("ℹ️ Script check file already exists. Skipping process.")
#             return

#         if not self._FindScriptFile():
#             sys.exit(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.ScriptDirPath})\n\n")

#         print(f"Found script file: {os.path.basename(self.TargetFilePath)}")

#         if self.FileExtension == ".txt":
#             print("Processing as TXT file...")
#             self._ProcessTxtScript()
#         elif self.FileExtension == ".pdf":
#             print("Processing as PDF file...")
#             self._ProcessPdfScript()
        
#         print("✅ Script loading process complete.")

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '250516_업데이트'
    Solution = 'Translation'
    ScriptCheckFramePath = '/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload/a5312-00_ScriptCheckFrame.json'
    ScriptDataFramePath = '/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload'
    ProjectScriptDataFramePath = f'/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_script/{projectName}_dataframe_script_file'
    ProjectDataFrameScriptCheckPath = os.path.join(ProjectScriptDataFramePath, f"{email}_{projectName}_01_ScriptCheckDataFrame({Solution}).json")
    AutoSegmentation = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################