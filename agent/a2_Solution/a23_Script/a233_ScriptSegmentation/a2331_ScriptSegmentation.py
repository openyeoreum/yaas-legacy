import os
import fitz
import random
import shutil
import json
import spacy
import sys
sys.path.append("/yaas")

from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfReader, PdfWriter
from agent.a2_Solution.a21_General.a216_LoadAgent import LoadAgent


##################################################
##### PT1 ScriptLoad (업로드 된 스크립트 파일 확인) #####
##################################################
class ScriptLoadProcess:

    ## 기본 경로 정의 ##
    ScriptSegmentationDataFramePath = "/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptSegmentation"
    ScriptSegmentationPromptPath = "/yaas/agent/a5_Database/a54_PromptData/a542_ScriptPrompt/a5423_ScriptSegmentationPrompt"
    ProjectStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"

    ## ScriptLoad 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate

        # Process 설정
        self.ProcessNumber = 'PT01'
        self.ProcessName = "ScriptLoad"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # 업로드 스크립트 파일 경로 및 확장자
        self.UploadedScriptFilePath = None
        self.ScriptFileExtension = None

        # 경로설정
        self._InitializePaths()

    ## 프로세스 관련 경로 초기화 ##
    def _InitializePaths(self):
        """프로세스와 관련된 모든 경로를 초기화"""
        # DataFrame 원본 경로
        self.PDFLoadDataFramePath = os.path.join(self.ScriptSegmentationDataFramePath, "a53131-P01_PDFLoadFrame.json")
        self.TXTLoadDataFramePath = os.path.join(self.ScriptSegmentationDataFramePath, "a53132-T01_TXTLoadFrame.json")

        # project_script 관련 경로
        self.ScriptDirPath = os.path.join(self.ProjectStoragePath, self.Email, self.ProjectName, f"{self.ProjectName}_script")
        self.UploadScriptFilePath = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_upload_script_file")
        self.DataFrameScriptFilePath = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_dataframe_script_file")
        self.MasterScriptFilePath = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_master_script_file")

        # 최종 생성될 LoadFrame 파일 경로
        self.PDFLoadFramePath = os.path.join(self.DataFrameScriptFilePath, f"{self.Email}_{self.ProjectName}_P01_PDFLoadFrame({self.NextSolution}).json")
        self.TXTLoadFramePath = os.path.join(self.DataFrameScriptFilePath, f"{self.Email}_{self.ProjectName}_T01_TXTLoadFrame({self.NextSolution}).json")

    ## LoadFrame 파일 생성 확인 메서드 ##
    def _CheckExistingLoadFrame(self):
        """PDFLoadFrame 또는 TXTLoadFrame 파일이 존재하는지 확인"""
        return os.path.exists(self.PDFLoadFramePath) or os.path.exists(self.TXTLoadFramePath)

    ## 스크립트 파일 확장자 확인 및 표준화 메서드 ##
    def _FindAndProcessScriptFile(self):
        """지정된 디렉토리에서 txt 또는 pdf 스크립트 파일을 찾아 표준화된 이름으로 저장"""
        # 디렉토리의 모든 파일을 가져와 .txt 또는 .pdf 파일 탐색
        SupportedExtensions = ['.txt', '.pdf']
        AllFiles = os.listdir(self.UploadScriptFilePath)

        # txt 또는 pdf 파일이 있는 경우 해당 파일을 표준화된 이름으로 저장
        for Extension in SupportedExtensions:
            ScriptFiles = [File for File in AllFiles if File.lower().endswith(Extension)]
            if ScriptFiles:
                RawUploadedScriptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFiles[0])
                self.ScriptFileExtension = Extension[1:]
                ScriptFileName = f"{self.ProjectName}_Script({self.NextSolution}).{self.ScriptFileExtension}"
                self.UploadedScriptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFileName)

                # 파일명이 다르면 표준화된 이름으로 복사
                if ScriptFiles[0] != ScriptFileName:
                    shutil.copy2(RawUploadedScriptFilePath, self.UploadedScriptFilePath)

                # txt 또는 pdf 파일이 존재하면 True
                return True
            
        # txt 또는 pdf 파일이 없으면 False
        return False

    ## LoadFrame 생성 및 저장 메서드 ##
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

        LoadFrame[0]['ProjectName'] = self.ProjectName
        LoadFrame[0]['NextSolution'] = self.NextSolution
        LoadFrame[0]['AutoTemplate'] = self.AutoTemplate
        LoadFrame[0]['FileExtension'] = self.ScriptFileExtension
        LoadFrame[0]['Completion'] = "Yes"
        LoadFrame[1]['UploadedScriptFilePath'] = self.UploadedScriptFilePath

        with open(LoadFramePath, 'w', encoding = 'utf-8') as LoadFrameFile:
            json.dump(LoadFrame, LoadFrameFile, ensure_ascii = False, indent = 4)

    ## ScriptLoadProcess 실행 메서드 ##
    def Run(self):
        """스크립트 로드 전체 프로세스를 실행하는 메인 메서드"""
        print(f"< {self.ProcessInfo} Update 시작 >")

        # LoadFrame 파일이 이미 존재하는지 확인
        if not self._CheckExistingLoadFrame():

            # 업로드 된 스크립트 파일 여부 확인
            if not self._FindAndProcessScriptFile():
                raise FileNotFoundError(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.UploadScriptFilePath})\n\n")
            else:
                self._CreateLoadFrameFile()
                print(f"[ {self.ProcessInfo} Update 완료 ]\n")

        else:
            print(f"[ {self.ProcessInfo} Update는 이미 완료됨 ]\n")

    ## LoadFrame 불러오기 메서드 ##
    def LoadScriptLoadFrame(self):
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
        FileExtension = LoadFrame[0]['FileExtension']
        MainLang = LoadFrame[0]['MainLang'] if LoadFrame[0]['MainLang'] != "" else None
        UploadedScriptFilePath = LoadFrame[1]['UploadedScriptFilePath']
            
        return FileExtension, MainLang, UploadedScriptFilePath

    ## LoadFrame 불러오기 메서드 ##
    def LoadScriptSegmentationPath(self):
        """생성된 ScriptLoadFrame JSON 파일 불러오기"""
            
        return self.ScriptSegmentationDataFramePath, self.ScriptSegmentationPromptPath, self.UploadScriptFilePath, self.DataFrameScriptFilePath, self.MasterScriptFilePath

#############################################
##### P2 PDFMainLangCheck (PDF 언어 체크) #####
#############################################
class PDFMainLangCheckProcess:

    ## PDFMainLangCheck 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # Process 설정
        self.ProcessNumber = "P02"
        self.ProcessName = "PDFMainLangCheck"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # 경로설정
        self.UploadScriptFilePath = UploadScriptFilePath
        self._InitializePaths()

        # 출력설정
        self.MessagesReview = MessagesReview

    ## 프로세스 관련 경로 초기화 ##
    def _InitializePaths(self):
        """프로세스와 관련된 모든 경로를 초기화"""
        # SplitedPDF 경로 및 디렉토리 생성
        self.SampleScriptJPEGDirPath = os.path.join(self.UploadScriptFilePath, f"{self.ProjectName}_SampleScript({self.NextSolution})_jpeg")
        os.makedirs(self.SampleScriptJPEGDirPath, exist_ok = True)
        self.FontDirPath = "/usr/share/fonts/"
        self.NotoSansCJKRegular = os.path.join(self.FontDirPath, "opentype/noto/NotoSansCJK-Regular.ttc")

    ## PDF 이미지 생성 및 라벨 생성 ##
    def _CreatePDFToLabeledSmapleJPEG(self, Page, InputId):
        """PDF 페이지를 받아 라벨을 추가한 뒤, 이미지 파일로 저장하고 경로를 반환하는 메서드"""
        # 페이지를 고해상도 이미지로 변환
        Pixmap = Page.get_pixmap(dpi = 150)
        PageImage = Image.frombytes("RGB", [Pixmap.width, Pixmap.height], Pixmap.samples)

        # "자료번호: n" 라벨 이미지 생성
        LabelText = f"자료번호: {InputId}"
        Font = ImageFont.truetype(self.NotoSansCJKRegular, 30)

        # 페이지 번호가 3~5자리가 되어도 너비가 충분하도록 최대 너비 기준으로 계산
        PlaceholderText = "자료번호: 99999"
        PlaceholderBbox = Font.getbbox(PlaceholderText)
        TextWidth = PlaceholderBbox[2] - PlaceholderBbox[0]
        
        TextBbox = Font.getbbox(LabelText)
        TextHeight = TextBbox[3] - TextBbox[1]
        
        # 라벨 이미지의 여백(Padding)을 포함한 크기 계산
        Padding = 15  # 좌우 여백을 조금 더 주어 넉넉하게 설정
        LabelWidth = TextWidth + 2 * Padding
        LabelHeight = TextHeight + 2 * Padding
        
        # 하얀 배경의 라벨 이미지 생성
        LabelImage = Image.new('RGB', (LabelWidth, LabelHeight), 'white')
        Draw = ImageDraw.Draw(LabelImage)
        
        # 검은색 테두리 그리기
        Draw.rectangle([(0, 0), (LabelWidth - 1, LabelHeight - 1)], outline = 'black', width = 4)
        
        # 요구사항 1: 페이지 높이에 비례하여 텍스트 세로 위치 자동 조정
        BaseHeight = 1754  # 기준 높이
        BaseVerticalOffset = -8  # 기준 높이에서의 조정값
        VerticalTextOffset = int((BaseVerticalOffset / BaseHeight) * PageImage.height)
        
        # 텍스트를 라벨의 중앙에 위치시키기 위한 x좌표 계산
        # (라벨 전체 너비 - 실제 텍스트 너비) / 2
        text_x_position = (LabelWidth - (TextBbox[2] - TextBbox[0])) // 2
        
        # 검은색 텍스트 추가 (조정된 위치 적용)
        Draw.text((text_x_position, Padding + VerticalTextOffset), LabelText, font=Font, fill = 'black')
        
        # 원본 페이지 이미지의 중앙 상단에 라벨 이미지 합성
        Margin = 20
        Position = ((PageImage.width - LabelWidth) // 2, Margin)
        PageImage.paste(LabelImage, Position)

        # 해당 이미지 파일을 지정된 디렉토리에 저장
        OutputFilename = f"{self.ProjectName}_Script({self.NextSolution})({InputId}).jpeg"
        OutputFilePath = os.path.join(self.SampleScriptJPEGDirPath, OutputFilename)
        PageImage.save(OutputFilePath, 'JPEG')
        
        return OutputFilePath

    ## InputList 생성 ##
    def _CreateInputList(self):
        """InputList를 생성하는 메서드"""
        # SampleScriptJPEGDirPath에 ScriptJPEG 파일이 5개 존재하면 그대로 유지
        if os.path.exists(self.SampleScriptJPEGDirPath):
            # SampleScriptJPEGDirPath에서 모든 JPEG 파일을 가져와 정렬
            ScriptJPEGFiles = sorted([
                FileName for FileName in os.listdir(self.SampleScriptJPEGDirPath)
                if FileName.lower().endswith('.jpeg')
            ])

            # SampleScriptJPEGDirPath에 JPEG 파일이 5개 이상 있는 경우는 InputList 생성 및 리턴
            if len(ScriptJPEGFiles) >= 5:
                InputList = [
                    {
                        "Id": 1,
                        "Input": [],
                        "InputFormat": "jpeg",
                        "ComparisonInput": None
                    }
                ]
                for InputId, FileName in enumerate(ScriptJPEGFiles, 1):
                    FilePath = os.path.join(self.SampleScriptJPEGDirPath, FileName)
                    InputList[0]["Input"].append(FilePath)
                return InputList

        # PDF 파일 불러오기 및 랜덤으로 5개 페이지 선택
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        TotalPages = len(PdfDocument)
        if TotalPages < 5:
            SelectedPageIndices = range(TotalPages)
        else:
            SelectedPageIndices = random.sample(range(TotalPages), 5)

        # InputList 생성
        InputList = [
            {
                "Id": 1,
                "Input": [],
                "InputFormat": "jpeg",
                "ComparisonInput": None
            }
        ]
        for InputId, PageIndex in enumerate(SelectedPageIndices, 1):
            Page = PdfDocument.load_page(PageIndex)
            # PDF 이미지 생성 및 라벨 생성
            OutputFilePath = self._CreatePDFToLabeledSmapleJPEG(Page, InputId)

            InputList[0]["Input"].append(OutputFilePath)

        PdfDocument.close()

        return InputList

    ## PDFMainLangCheckProcess 실행 ##
    def Run(self):
        """PDF 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        InputList = self._CreateInputList()
        LoadAgentInstance = LoadAgent(InputList, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution)
        LoadAgentInstance.Run()

#########################################
##### P3 PDFSplit (PDF 페이지 별 분할) #####
#########################################
class PDFSplitProcess:

    ## PDFSplit 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, FileExtension, UploadedScriptFilePath, UploadScriptFilePath, ScriptSegmentationDataFramePath, DataFrameScriptFilePath):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.ScriptFileExtension = FileExtension
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        # Process 설정
        self.ProcessNumber = '3'
        self.ProcessName = "PDFSplit"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"
        
        # 경로설정
        self.UploadScriptFilePath = UploadScriptFilePath
        self.ScriptSegmentationDataFramePath = ScriptSegmentationDataFramePath
        self.DataFrameScriptFilePath = DataFrameScriptFilePath
        self._InitializePaths()

    ## 프로세스 관련 경로 초기화 ##
    def _InitializePaths(self):
        """프로세스와 관련된 모든 경로를 초기화"""
        # DataFrame 원본 경로
        self.PDFSplitDataFramePath = os.path.join(self.ScriptSegmentationDataFramePath, "a53131-P03_PDFSplitFrame.json")

        # 최종 생성될 SplitFrame 파일 경로
        self.PDFSplitFramePath = os.path.join(self.DataFrameScriptFilePath, f"{self.Email}_{self.ProjectName}_P03_PDFSplitFrame({self.NextSolution}).json")

        # SplitedPDF 경로 및 디렉토리 생성
        self.SplitScriptPDFDirPath = os.path.join(self.UploadScriptFilePath, f"{self.ProjectName}_SplitScript({self.NextSolution})_{self.ScriptFileExtension}")
        os.makedirs(self.SplitScriptPDFDirPath, exist_ok = True)
        
    ## PDFSplitFrame 파일 생성 확인 ##
    def _CheckExistingSplitFrame(self):
        """PDFSplitFrame 파일이 이미 존재하는지 확인"""
        return os.path.exists(self.PDFSplitFramePath)

    ## PDF 파일을 페이지별로 분할 및 저장 ##
    def _SplitPDF(self):
        """PDF 파일을 페이지별로 분할하고 저장"""
        # PDF 파일 읽고 총 페이지 수 계산
        PageFilePaths = []
        Reader = PdfReader(self.UploadedScriptFilePath)
        TotalPages = len(Reader.pages)
        
        # 각 페이지를 개별 PDF 파일로 저장
        for PageNum in range(TotalPages):
            Writer = PdfWriter()
            Writer.add_page(Reader.pages[PageNum])
            
            OutputFileName = f"{self.ProjectName}_Script({self.NextSolution})({PageNum + 1}).{self.ScriptFileExtension}"
            OutputFilePath = os.path.join(self.SplitScriptPDFDirPath, OutputFileName)
            
            # 페이지별 PDF 파일 저장
            with open(OutputFilePath, "wb") as OutputFile:
                Writer.write(OutputFile)
            # 페이지별 파일 경로를 리스트에 추가
            PageFilePaths.append(OutputFilePath)
            
        return PageFilePaths

    ## SplitFrame 생성 및 저장 ##
    def _CreateSplitFrameFile(self, PageFilePaths):
        """분할된 PDF 정보로 SplitFrame JSON 파일 생성"""
        # SplitFrame JSON 파일 생성
        with open(self.PDFSplitDataFramePath, 'r', encoding = 'utf-8') as FrameFile:
            SplitFrame = json.load(FrameFile)

        SplitFrame[0]['ProjectName'] = self.ProjectName
        SplitFrame[0]['NextSolution'] = self.NextSolution
        SplitFrame[0]['AutoTemplate'] = self.AutoTemplate
        SplitFrame[0]['MainLang'] = self.MainLang
        SplitFrame[0]['InputCount'] = len(PageFilePaths)
        SplitFrame[0]['Completion'] = "Yes"
        
        # 기존 리스트에 페이지별 경로 추가
        for i, Path in enumerate(PageFilePaths):
            PageFilePathDic = SplitFrame[1][0].copy()
            PageFilePathDic['ScriptId'] = i + 1
            PageFilePathDic['PageFilePath'] = Path
            # 페이지별 경로를 SplitFrame에 추가
            SplitFrame[1].append(PageFilePathDic)

        with open(self.PDFSplitFramePath, 'w', encoding = 'utf-8') as OutputJson:
            json.dump(SplitFrame, OutputJson, ensure_ascii = False, indent = 4)

    ## PDFSplitProcess 실행 ##
    def Run(self):
        """PDF 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")

        # PDFSplitFrame 파일이 이미 존재하는지 확인
        if not self._CheckExistingSplitFrame():
            PageFilePaths = self._SplitPDF()
            self._CreateSplitFrameFile(PageFilePaths)
            print(f"[ {self.ProcessInfo} Update 완료 ]\n")
        else:
            print(f"[ {self.ProcessInfo} Update는 이미 완료됨 ]\n")


#########################################
##### T3 TXTSplit (TXT 토큰 단위 분할) #####
#########################################
class TXTSplitProcess:

    ## TXTSplit 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, FileExtension, UploadedScriptFilePath, ScriptSegmentationDataFramePath, DataFrameScriptFilePath, BaseTokens = 3000):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.ScriptFileExtension = FileExtension
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        # Process 설정
        self.ProcessNumber = '3'
        self.ProcessName = "TXTSplit"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"
        
        # 언어별 MaxTokens 설정
        self.MainLang = MainLang
        self.BaseTokens = BaseTokens
        self.MaxTokens = self._DetermineMaxTokens()

        # 경로설정
        self.ScriptSegmentationDataFramePath = ScriptSegmentationDataFramePath
        self.DataFrameScriptFilePath = DataFrameScriptFilePath
        self._InitializePaths()

    ## 언어별 MaxTokens ##
    def _DetermineMaxTokens(self):
        """언어에 따라 적절한 MaxTokens 값을 결정"""       
        # 언어별 토큰 비율 (한국어 대비)
        TokenRatios = {
            'ko': 1.0,      # 한국어 (기준)
            'en': 1.8,      # 영어
            'de': 2.1,      # 독일어
            'fr': 2.0,      # 프랑스어
            'es': 2.0,      # 스페인어
            'zh': 0.9,      # 중국어
            'ja': 1.2,      # 일본어
            'it': 2.0,      # 이탈리아어
            'pt': 2.0,      # 포르투갈어
            'nl': 2.1,      # 네덜란드어
            'sv': 1.8,      # 스웨덴어
            'no': 1.8,      # 노르웨이어
            'da': 1.9,      # 덴마크어
            'pl': 2.1,      # 폴란드어
        }

        # 언어 코드에 해당하는 비율 적용, 없으면 기본값(1.0) 사용
        Ratio = TokenRatios.get(self.MainLang.lower(), 1.0)

        return int(self.BaseTokens * Ratio)

    ## 프로세스 관련 경로 초기화 ##
    def _InitializePaths(self):
        """프로세스와 관련된 모든 경로를 초기화"""
        # DataFrame 원본 경로
        self.TXTSplitDataFramePath = os.path.join(self.ScriptSegmentationDataFramePath, "a53132-T03_TXTSplitFrame.json")

        # 최종 생성될 SplitFrame 파일 경로
        self.TXTSplitFramePath = os.path.join(self.DataFrameScriptFilePath, f"{self.Email}_{self.ProjectName}_T03_TXTSplitFrame({self.NextSolution}).json")

    ## TXTSplitFrame 파일 생성 확인 ##
    def _CheckExistingSplitFrame(self):
        """TXTSplitFrame 파일이 이미 존재하는지 확인"""
        return os.path.exists(self.TXTSplitFramePath)
    
    ## Spacy 모델 로드 및 사용자 정의 경계 설정 ##
    def _LoadSpacyModel(self):
        """언어에 맞는 Spacy 모델 로드"""
        # 언어 코드 매핑
        ModelMap = {
            'ko': 'ko_core_news_sm',      # 한국어
            'en': 'en_core_web_sm',       # 영어
            'de': 'de_core_news_sm',      # 독일어
            'fr': 'fr_core_news_sm',      # 프랑스어
            'es': 'es_core_news_sm',      # 스페인어
            'zh': 'zh_core_web_sm',       # 중국어
            'ja': 'ja_core_news_sm',      # 일본어
            'it': 'it_core_news_sm',      # 이탈리아어
            'pt': 'pt_core_news_sm',      # 포르투갈어
            'nl': 'nl_core_news_sm',      # 네덜란드어
            'sv': 'sv_core_news_sm',      # 스웨덴어
            'no': 'nb_core_news_sm',      # 노르웨이어
            'da': 'da_core_news_sm',      # 덴마크어
            'pl': 'pl_core_news_sm',      # 폴란드어
        }

        # 언어에 맞는 모델 이름 가져오기, 기본값은 한국어 모델
        ModelName = ModelMap.get(self.MainLang.lower(), 'ko_core_news_sm')
        
        try:
            nlp = spacy.load(ModelName)
        except OSError:
            print(f"[ Download: Spacy 모델 '{ModelName}'을 찾을 수 없습니다. 다운로드를 시도합니다. ]")
            spacy.cli.download(ModelName)
            nlp = spacy.load(ModelName)

        return nlp

    ## TXT 파일을 지정된 토큰 수에 가깝게 문장 묶음으로 분할 ##
    def _SplitTXT(self):
        """TXT 파일을 지정된 글자 수(공백 포함)에 가깝게 문장 묶음으로 분할 (공백/줄바꿈 유지)"""
        # Spacy 모델 로드
        nlp = self._LoadSpacyModel()
        
        # 업로드된 스크립트 파일 읽기
        with open(self.UploadedScriptFilePath, 'r', encoding = 'utf-8') as f:
            FullText = f.read()

        Doc = nlp(FullText)
        
        # 문장의 원본 텍스트와 마지막 토큰 뒤의 공백/줄바꿈을 합쳐서 리스트 생성
        Sentences = [s.text + s[-1].whitespace_ for s in Doc.sents]
        
        TXTChunks = []
        CurrentTXTChunkList = []
        
        for Sent in Sentences:
            CurrentTXTChunkList.append(Sent)
            CurrentText = "".join(CurrentTXTChunkList)
            
            # 토큰 수 계산 대신, 공백을 포함한 글자 수를 계산합니다.
            CharCount = len(CurrentText)
            
            # 글자 수가 MaxTokens를 초과하면 분할합니다.
            if CharCount >= self.MaxTokens:
                TXTChunks.append(CurrentText)
                CurrentTXTChunkList = []
                
        # 마지막 남은 문장 묶음 추가
        if CurrentTXTChunkList:
            TXTChunks.append("".join(CurrentTXTChunkList))
            
        return TXTChunks

    ## SplitFrame 생성 및 저장 ##
    def _CreateSplitFrameFile(self, TXTChunks):
        """분할된 텍스트 정보로 SplitFrame JSON 파일 생성"""
        # SplitFrame JSON 파일 생성
        with open(self.TXTSplitDataFramePath, 'r', encoding = 'utf-8') as FrameFile:
            SplitFrame = json.load(FrameFile)

        SplitFrame[0]['ProjectName'] = self.ProjectName
        SplitFrame[0]['NextSolution'] = self.NextSolution
        SplitFrame[0]['AutoTemplate'] = self.AutoTemplate
        SplitFrame[0]['MainLang'] = self.MainLang
        SplitFrame[0]['InputCount'] = len(TXTChunks)
        SplitFrame[0]['Completion'] = "Yes"
        
        for i, TXTChunk in enumerate(TXTChunks):
            SplitedTextDic = SplitFrame[1][0].copy()
            SplitedTextDic['ScriptId'] = i + 1
            SplitedTextDic['SplitedText'] = TXTChunk
            # 페이지별 텍스트를 SplitFrame에 추가
            SplitFrame[1].append(SplitedTextDic)

        with open(self.TXTSplitFramePath, 'w', encoding = 'utf-8') as OutputJson:
            json.dump(SplitFrame, OutputJson, ensure_ascii = False, indent = 4)

    def Run(self):
        """TXT 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")

        # TXTSplitFrame 파일이 이미 존재하는지 확인
        if not self._CheckExistingSplitFrame():
            TXTChunks = self._SplitTXT()
            self._CreateSplitFrameFile(TXTChunks)
            print(f"[ {self.ProcessInfo} Update 완료 ]\n")
        else:
            print(f"[ {self.ProcessInfo} Update는 이미 완료됨 ]\n")



if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    Email = "yeoreum00128@gmail.com"
    ProjectNameList = ['250807_PDF테스트', '250807_TXT테스트']
    Solution = 'Script'
    SubSolution = 'ScriptSegmentation'
    NextSolution = 'Translation'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    MessagesReview = "on"
    #########################################################################

    for ProjectName in ProjectNameList:
        # PT01 통합: (PDF)ScriptLoad (업로드 된 스크립트 파일 확인)
        ScriptLoadInstance = ScriptLoadProcess(Email, ProjectName, NextSolution, AutoTemplate)
        ScriptLoadInstance.Run()
        FileExtension, MainLang, UploadedScriptFilePath = ScriptLoadInstance.LoadScriptLoadFrame()
        ScriptSegmentationDataFramePath, ScriptSegmentationPromptPath, UploadScriptFilePath, DataFrameScriptFilePath, MasterScriptFilePath = ScriptLoadInstance.LoadScriptSegmentationPath()

        # 파일 확장자에 따라 후속 프로세스 실행
        if FileExtension == 'pdf':
            # P02 PDFMainLangCheck (PDF 언어 체크)
            PDFMainLangCheckProcessInstance = PDFMainLangCheckProcess(Email, ProjectName, Solution, SubSolution, NextSolution, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
            PDFMainLangCheckProcessInstance.Run()

            # #P03 PDFSplit (PDF 파일 페이지 분할)
            PDFSplitterInstance = PDFSplitProcess(Email, ProjectName, NextSolution, AutoTemplate, "ko", FileExtension, UploadedScriptFilePath, UploadScriptFilePath, ScriptSegmentationDataFramePath, DataFrameScriptFilePath)
            PDFSplitterInstance.Run()
            
        elif FileExtension == 'txt':
            # T02 TXTMainLangCheck (TXT 언어 체크)

            # T03 TXTSplit (텍스트 파일 지정 토큰수 분할)
            TXTSplitterInstance = TXTSplitProcess(Email, ProjectName, NextSolution, AutoTemplate, "ko", FileExtension, UploadedScriptFilePath, ScriptSegmentationDataFramePath, DataFrameScriptFilePath)
            TXTSplitterInstance.Run()