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


###################################################
##### PT01 ScriptLoad (업로드 된 스크립트 파일 확인) #####
###################################################
class ScriptLoadProcess:

    ## 기본 경로 정의 ##
    ProjectStoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"

    ## ScriptLoad 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate

        # 업로드 스크립트 파일 경로 및 확장자
        self.UploadedScriptFilePath = None
        self.ScriptFileExtension = None

        # 경로설정
        self._InitializePaths()

        # Process 설정
        self._FindAndProcessScriptFile()
        if self.ScriptFileExtension == 'pdf':
            self.ProcessNumber = 'P01'
            self.ProcessName = "PDFLoad"
        if self.ScriptFileExtension == 'txt':
            self.ProcessNumber = 'T01'
            self.ProcessName = "TXTLoad"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # 출력설정
        self.MessagesReview = MessagesReview

    ## 프로세스 관련 경로 초기화 ##
    def _InitializePaths(self):
        """프로세스와 관련된 모든 경로를 초기화"""
        # project_script 관련 경로
        self.ScriptDirPath = os.path.join(self.ProjectStoragePath, self.Email, self.ProjectName, f"{self.ProjectName}_script")
        self.UploadScriptFilePath = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_upload_script_file")

    ## 스크립트 파일 확장자 확인 및 표준화 메서드 ##
    def _FindAndProcessScriptFile(self):
        """지정된 디렉토리에서 txt 또는 pdf 스크립트 파일을 찾아 표준화된 이름으로 저장"""
        # 디렉토리의 모든 파일을 가져와 .txt 또는 .pdf 파일 탐색
        SupportedExtensions = ['.txt', '.pdf']
        AllFiles = os.listdir(self.UploadScriptFilePath)

        # txt 또는 pdf 파일이 있는 경우 해당 파일을 표준화된 이름으로 저장
        FileExistsError = True
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
                    
                FileExistsError = False

        if FileExistsError:
            # txt 또는 pdf 파일이 없으면 오류메세지 출력
            sys.exit(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.UploadScriptFilePath})\n\n")

    ## InputList 생성 ##
    def _CreateInputList(self):
        """InputList를 생성하는 메서드"""
        # InputList 생성 및 리턴
        InputList = [
            {
                "Id": 1,
                "Input": {
                    "ProjectName": self.ProjectName,
                    "NextSolution": self.NextSolution,
                    "AutoTemplate": self.AutoTemplate,
                    "FileExtension": self.ScriptFileExtension,
                    "UploadedScriptFilePath": self.UploadedScriptFilePath
                },
                "InputFormat": None,
                "ComparisonInput": None
            }
        ]

        return InputList

    ## ScriptLoadProcess 실행 메서드 ##
    def Run(self):
        """스크립트 로드 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        InputList = self._CreateInputList()
        LoadAgentInstance = LoadAgent(InputList, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution)
        SolutionEdit = LoadAgentInstance.Run(Response = "Input")
            
        return SolutionEdit, self.ScriptFileExtension, self.UploadedScriptFilePath, self.UploadScriptFilePath


#################################
#################################
########## PDF Process ##########
#################################
#################################


##############################################
##### P02 PDFMainLangCheck (PDF 언어 체크) #####
##############################################
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

    ## PDF 샘플 이미지 생성 및 라벨 생성 ##
    def _CreatePDFToLabeledSampleJPEG(self, Page, InputId):
        """PDF 페이지에 '자료번호: InputId' 라벨을 추가한 JPEG 파일을 생성"""
        # 페이지 → 이미지
        Pixmap = Page.get_pixmap(dpi = 150)
        PageImg = Image.frombytes("RGB", (Pixmap.width, Pixmap.height), Pixmap.samples)

        # 스케일 기준 및 스케일 팩터
        RefWidth = 1240
        Scale = max(0.5, min(2.5, PageImg.width / RefWidth))

        # 폰트 로딩 (캐시/멤버 재사용 권장)
        FontSize = int(30 * Scale)
        try:
            Font = ImageFont.truetype(self.NotoSansCJKRegular, FontSize)
        except Exception:
            Font = ImageFont.load_default()

        # 라벨 텍스트 및 치수 계산 (최소 폭 보장)
        LabelText = f"자료번호: {InputId}"

        TextBBox = Font.getbbox(LabelText)
        TextW = TextBBox[2] - TextBBox[0]
        TextH = TextBBox[3] - TextBBox[1]

        Padding = int(14 * Scale)
        BorderW = max(2, int(4 * Scale))
        Margin = int(20 * Scale)

        MinWBBox = Font.getbbox("자료번호: 99999")
        MinTextW = (MinWBBox[2] - MinWBBox[0])

        LabelW = max(TextW, MinTextW) + 2 * Padding
        LabelH = TextH + 2 * Padding

        # 라벨 이미지 (반투명 배경 + 얕은 그림자)
        LabelImg = Image.new("RGBA", (LabelW, LabelH), (255, 255, 255, 230))
        Draw = ImageDraw.Draw(LabelImg)

        # 테두리
        Draw.rectangle([(0, 0), (LabelW - 1, LabelH - 1)], outline=(0, 0, 0, 255), width=BorderW)

        # 텍스트 중앙 정렬 + 수직 오프셋(폰트 크기 기준 보정)
        TextX = (LabelW - TextW) // 2
        VerticalOffset = int(-0.3 * FontSize)
        TextY = (LabelH - TextH) // 2 + VerticalOffset
        TextY = max(Padding // 2, min(TextY, LabelH - TextH - Padding // 2))

        ShadowOffset = max(1, int(Scale))
        Draw.text((TextX + ShadowOffset, TextY + ShadowOffset), LabelText, font=Font, fill=(0, 0, 0, 90))
        Draw.text((TextX, TextY), LabelText, font=Font, fill=(0, 0, 0, 255))

        # 합성 위치(상단 중앙) 계산 + 경계 체크
        PosX = (PageImg.width - LabelW) // 2
        PosY = Margin
        PosX = max(0, min(PosX, PageImg.width - LabelW))
        PosY = max(0, min(PosY, PageImg.height - LabelH))

        # 합성 (RGBA → RGB)
        PageImg = PageImg.convert("RGBA")
        PageImg.alpha_composite(LabelImg, dest=(PosX, PosY))
        PageImg = PageImg.convert("RGB")

        # 디렉터리 보장 및 저장 옵션
        os.makedirs(self.SampleScriptJPEGDirPath, exist_ok=True)
        OutputFilename = f"{self.ProjectName}_Script({self.NextSolution})({InputId}).jpeg"
        OutputPath = os.path.join(self.SampleScriptJPEGDirPath, OutputFilename)

        PageImg.save(
            OutputPath,
            "JPEG",
            quality = 92,
            optimize = True,
            progressive = True,
            subsampling = 1  # 4:2:2에 해당
        )

        return OutputPath

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
            OutputFilePath = self._CreatePDFToLabeledSampleJPEG(Page, InputId)

            InputList[0]["Input"].append(OutputFilePath)

        PdfDocument.close()

        return InputList

    ## PDFMainLangCheckProcess 실행 ##
    def Run(self):
        """PDF 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        InputList = self._CreateInputList()
        LoadAgentInstance = LoadAgent(InputList, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution)
        SolutionEdit = LoadAgentInstance.Run()

        # MainLang 추출
        MainLang = SolutionEdit[self.ProcessName][0]["MainLang"]

        return SolutionEdit, MainLang


##########################################
##### P03 PDFSplit (PDF 페이지 별 분할) #####
##########################################
class PDFSplitProcess:

    ## PDFSplit 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, FileExtension, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.ScriptFileExtension = FileExtension
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        # Process 설정
        self.ProcessNumber = 'P03'
        self.ProcessName = "PDFSplit"
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
        self.SplitScriptPDFDirPath = os.path.join(self.UploadScriptFilePath, f"{self.ProjectName}_SplitScript({self.NextSolution})_{self.ScriptFileExtension}")
        os.makedirs(self.SplitScriptPDFDirPath, exist_ok = True)

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

    ## InputList 생성 ##
    def _CreateInputList(self):
        """InputList를 생성하는 메서드"""
        # PDF 파일을 페이지별로 분할 및 저장
        PageFilePaths = self._SplitPDF()
        
        # InputList 생성 및 리턴
        InputList = []
        for i, Path in enumerate(PageFilePaths):
            InputList.append(
                {
                    "Id": i + 1,
                    "Input": {
                        "ScriptId": i + 1,
                        "PageFilePath": Path
                    },
                    "InputFormat": None,
                    "ComparisonInput": None
                }
            )

        return InputList

    ## PDFSplitProcess 실행 ##
    def Run(self):
        """PDF 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        InputList = self._CreateInputList()
        LoadAgentInstance = LoadAgent(InputList, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution)
        SolutionEdit = LoadAgentInstance.Run(Response = "Input")
        
        return SolutionEdit


####################################################
##### #P04 PDFFormCheck (PDF 파일 페이지 형식 체크) #####
####################################################
class PDFFormCheck:

    ## PDFFormCheck 초기화 ##
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
        self.ScriptJPEGDirPath = os.path.join(self.UploadScriptFilePath, f"{self.ProjectName}_Script({self.NextSolution})_jpeg")
        os.makedirs(self.ScriptJPEGDirPath, exist_ok = True)
        self.FontDirPath = "/usr/share/fonts/"
        self.NotoSansCJKRegular = os.path.join(self.FontDirPath, "opentype/noto/NotoSansCJK-Regular.ttc")

    ## PDF 이미지 생성 및 라벨 생성 ##
    def _CreatePDFToLabeledJPEGs(self, PDFDoc):
        """PDF 전체 페이지를 순회하며 '자료번호: 페이지번호' 라벨을 추가한 JPEG 파일을 생성"""

        OutputPathList = []

        # 페이지 번호는 1부터 시작 (보통 사람이 보는 페이지 넘버링과 일치)
        for PageNumber in range(len(PDFDoc)):
            Page = PDFDoc[PageNumber]

            # 페이지 → 이미지
            Pixmap = Page.get_pixmap(dpi =150)
            PageImg = Image.frombytes("RGB", (Pixmap.width, Pixmap.height), Pixmap.samples)

            # 스케일 기준
            RefWidth = 1240
            Scale = max(0.5, min(2.5, PageImg.width / RefWidth))

            # 폰트
            FontSize = int(30 * Scale)
            try:
                Font = ImageFont.truetype(self.NotoSansCJKRegular, FontSize)
            except Exception:
                Font = ImageFont.load_default()

            # 라벨 텍스트
            LabelText = f"자료번호: {PageNumber + 1}"
            TextBBox = Font.getbbox(LabelText)
            TextW = TextBBox[2] - TextBBox[0]
            TextH = TextBBox[3] - TextBBox[1]

            Padding = int(14 * Scale)
            BorderW = max(2, int(4 * Scale))
            Margin = int(20 * Scale)

            # 최소 폭 보장
            MinWBBox = Font.getbbox("자료번호: 99999")
            MinTextW = MinWBBox[2] - MinWBBox[0]

            LabelW = max(TextW, MinTextW) + 2 * Padding
            LabelH = TextH + 2 * Padding

            # 라벨 이미지
            LabelImg = Image.new("RGBA", (LabelW, LabelH), (255, 255, 255, 230))
            Draw = ImageDraw.Draw(LabelImg)

            Draw.rectangle([(0, 0), (LabelW - 1, LabelH - 1)], outline=(0, 0, 0, 255), width=BorderW)

            TextX = (LabelW - TextW) // 2
            VerticalOffset = int(-0.3 * FontSize)
            TextY = (LabelH - TextH) // 2 + VerticalOffset
            TextY = max(Padding // 2, min(TextY, LabelH - TextH - Padding // 2))

            ShadowOffset = max(1, int(Scale))
            Draw.text((TextX + ShadowOffset, TextY + ShadowOffset), LabelText, font=Font, fill=(0, 0, 0, 90))
            Draw.text((TextX, TextY), LabelText, font=Font, fill=(0, 0, 0, 255))

            # 합성 위치
            PosX = (PageImg.width - LabelW) // 2
            PosY = Margin
            PosX = max(0, min(PosX, PageImg.width - LabelW))
            PosY = max(0, min(PosY, PageImg.height - LabelH))

            PageImg = PageImg.convert("RGBA")
            PageImg.alpha_composite(LabelImg, dest=(PosX, PosY))
            PageImg = PageImg.convert("RGB")

            # 저장
            os.makedirs(self.ScriptJPEGDirPath, exist_ok=True)
            OutputFilename = f"{self.ProjectName}_Script({self.NextSolution})({PageNumber + 1}).jpeg"
            OutputPath = os.path.join(self.ScriptJPEGDirPath, OutputFilename)

            PageImg.save(
                OutputPath,
                "JPEG",
                quality = 92,
                optimize = True,
                progressive = True,
                subsampling = 1
            )

            OutputPathList.append(OutputPath)

        return OutputPathList

    ## InputList 생성 ##
    def _CreateInputList(self):
        """InputList를 생성하는 메서드"""
        # SampleScriptJPEGDirPath에 ScriptJPEG 파일이 5개 존재하면 그대로 유지
        if os.path.exists(self.ScriptJPEGDirPath):
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

#################################
#################################
########## TXT Process ##########
#################################
#################################


##############################################
##### T02 TXTMainLangCheck (TXT 언어 체크) #####
##############################################
class TXTMainLangCheckProcess:

    ## TXTMainLangCheck 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, UploadedScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # Process 설정
        self.ProcessNumber = "T02"
        self.ProcessName = "TXTMainLangCheck"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # 출력설정
        self.MessagesReview = MessagesReview

    ## TXT 샘플 생성 ##
    def _CreateTXTToSampleText(self, FullText):
        """텍스트 파일에서 3개의 샘플 텍스트를 추출하여 하나의 문자열로 반환하는 메서드"""
        FullTextLength = len(FullText)
        sampleTextLength = 1000

        # 세그먼트 길이 결정: 텍스트가 1000자 미만이면 가능한 길이로 줄임
        SampleTextLength = sampleTextLength if FullTextLength >= sampleTextLength else FullTextLength

        SampleTextList = []
        if FullTextLength == 0:
            # 내용이 비어있다면 빈 문자열 3개
            SampleTextList = ["", "", ""]
        elif FullTextLength >= SampleTextLength * 3:
            # 3,000자 이상이면 서로 겹치지 않게 3구간을 무작위로 선택
            # 후보 시작 인덱스
            CandidateSampleList = list(range(0, FullTextLength - SampleTextLength + 1))
            random.shuffle(CandidateSampleList)

            Starts = []
            for s in CandidateSampleList:
                # 기존에 선택된 구간과 겹치는지 검사
                overlaps = any(not (s + SampleTextLength <= t or t + SampleTextLength <= s) for t in Starts)
                if not overlaps:
                    Starts.append(s)
                    if len(Starts) == 3:
                        break

            # 혹시 예외적으로 겹치지 않는 3개를 못 찾으면(매우 드묾) 겹침 허용으로 전환
            if len(Starts) < 3:
                Starts = [random.randint(0, FullTextLength - SampleTextLength) for _ in range(3)]

            Starts.sort()
            SampleTextList = [FullText[s:s + SampleTextLength] for s in Starts]

        elif FullTextLength >= SampleTextLength:
            # 1,000자 이상 3,000자 미만이면 겹침을 허용해 3구간을 선택
            MaxStart = max(0, FullTextLength - SampleTextLength)
            Starts = [random.randint(0, MaxStart) for _ in range(3)]
            SampleTextList = [FullText[s:s + SampleTextLength] for s in Starts]
        else:
            # 1,000자 미만이면 텍스트 전체를 각 세그먼트로 사용
            SampleTextList = [FullText, FullText, FullText]

        # "1구간문구 ... 2구간문구 ... 3구간문구" 형태로 합치기
        SampleText = f"{SampleTextList[0]} ... {SampleTextList[1]} ... {SampleTextList[2]}"

        return SampleText

    ## InputList 생성 ##
    def _CreateInputList(self):
        """InputList를 생성하는 메서드"""
        # 업로드된 스크립트 파일 읽기
        with open(self.UploadedScriptFilePath, 'r', encoding = 'utf-8') as f:
            FullText = f.read()

        InputList = [
            {
                "Id": 1,
                "Input": self._CreateTXTToSampleText(FullText),
                "InputFormat": "text",
                "ComparisonInput": None
            }
        ]

        return InputList

    ## TXTMainLangCheckProcess 실행 ##
    def Run(self):
        """TXT 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        InputList = self._CreateInputList()
        LoadAgentInstance = LoadAgent(InputList, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution)
        SolutionEdit = LoadAgentInstance.Run()

        # MainLang 추출
        MainLang = SolutionEdit[self.ProcessName][0]["MainLang"]

        return SolutionEdit, MainLang


##########################################
##### T03 TXTSplit (TXT 토큰 단위 분할) #####
##########################################
class TXTSplitProcess:

    ## TXTSplit 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, FileExtension, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview, BaseTokens = 3000):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.ScriptFileExtension = FileExtension
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        # Process 설정
        self.ProcessNumber = 'T03'
        self.ProcessName = "TXTSplit"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"
        
        # 언어별 MaxTokens 설정
        self.MainLang = MainLang
        self.BaseTokens = BaseTokens
        self.MaxTokens = self._DetermineMaxTokens()

        # 경로설정
        self.UploadScriptFilePath = UploadScriptFilePath
        
        # 출력설정
        self.MessagesReview = MessagesReview

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

    ## InputList 생성 ##
    def _CreateInputList(self):
        """InputList를 생성하는 메서드"""
        # PDF 파일을 페이지별로 분할 및 저장
        TXTChunks = self._SplitTXT()
        
        # InputList 생성 및 리턴
        InputList = []
        for i, TXTChunk in enumerate(TXTChunks):
            InputList.append(
                {
                    "Id": i + 1,
                    "Input": {
                        "ScriptId": i + 1,
                        "SplitedText": TXTChunk
                    },
                    "InputFormat": None,
                    "ComparisonInput": None
                }
            )

        return InputList

    ## TXTSplitProcess 실행 ##
    def Run(self):
        """TXT 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        InputList = self._CreateInputList()
        LoadAgentInstance = LoadAgent(InputList, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution)
        SolutionEdit = LoadAgentInstance.Run(Response = "Input")
        
        return SolutionEdit


################################
##### Process 진행 및 업데이트 #####
################################
## ScriptSegmentation 프롬프트 요청 및 결과물 Json화
def ScriptSegmentationProcessUpdate(projectName, email, NextSolution, AutoTemplate, MessagesReview = "on"):
    ## 솔루션 정의
    Solution = 'Script'
    SubSolution = 'ScriptSegmentation'
    
    ## PT01 통합: (PDF)ScriptLoad (업로드 된 스크립트 파일 확인)
    ScriptLoadInstance = ScriptLoadProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MessagesReview)
    SolutionEdit, ScriptFileExtension, UploadedScriptFilePath, UploadScriptFilePath = ScriptLoadInstance.Run()

    ## 파일 확장자에 따라 후속 프로세스 실행
    if ScriptFileExtension == 'pdf':

        ## P02 PDFMainLangCheck (PDF 언어 체크)
        PDFMainLangCheckProcessInstance = PDFMainLangCheckProcess(email, projectName, Solution, SubSolution, NextSolution, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit, MainLang = PDFMainLangCheckProcessInstance.Run()

        # #P03 PDFSplit (PDF 파일 페이지 분할)
        PDFSplitterInstance = PDFSplitProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, ScriptFileExtension, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit = PDFSplitterInstance.Run()
        
    elif ScriptFileExtension == 'txt':

        # T02 TXTMainLangCheck (TXT 언어 체크)
        TXTMainLangCheckInstance = TXTMainLangCheckProcess(email, projectName, Solution, SubSolution, NextSolution, UploadedScriptFilePath, MessagesReview)
        SolutionEdit, MainLang = TXTMainLangCheckInstance.Run()

        # T03 TXTSplit (텍스트 파일 지정 토큰수 분할)
        TXTSplitterInstance = TXTSplitProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, ScriptFileExtension, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview, BaseTokens = 3000)
        SolutionEdit = TXTSplitterInstance.Run()

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = 'yeoreum00128@gmail.com'
    projectName = '250807_TXT테스트'
    Solution = 'Script'
    SubSolution = 'ScriptSegmentation'
    NextSolution = 'Translation'
    AutoTemplate = "on" # 자동 컴포넌트 체크 여부 (on/off)
    MessagesReview = "on"
    #########################################################################