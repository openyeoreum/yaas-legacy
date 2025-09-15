import os
import fitz
import random
import shutil
import json
import math
import spacy
import sys
sys.path.append("/yaas")

from PIL import Image, ImageDraw, ImageFont, ImageChops
from PyPDF2 import PdfReader, PdfWriter
from agent.a2_Solution.a22_Operation.a226_LoadAgent import LoadAgent


#############################################
##### Solution: PT00 ScriptSegmentation #####
#############################################
class ScriptSegmentationSolution:

    Solution = "Script"
    SubSolution = "ScriptSegmentation"
    StoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"


    ## [Method] Init: ScriptSegmentation 초기화 ##
    def __init__(self, Email, ProjectName, ProcessNumber, ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.ProcessNumber = ProcessNumber
        self.ProcessName = ProcessName
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.Model = Model
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.MixedScriptFileDirPath = MixedScriptFileDirPath
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # 업로드 스크립트 파일 확장자
        self.FileExtension = None

        # Edit 설정
        self.SolutionEdit = SolutionEdit

        # 응답 출력설정
        self.MessagesReview = MessagesReview

        # MixedScriptFileDir 경로
        self.ScriptDirPath = os.path.join(self.StoragePath, self.Email, self.ProjectName, f"{self.ProjectName}_script")
        self.MixedScriptFileDirPath = os.path.join(self.ScriptDirPath, f"{self.ProjectName}_mixed_script_file")

        # P02, P03: 랜덤 샘플 jpeg 5개, 경로 및 디렉토리 생성
        self.SampleScriptJPEGDirPath = os.path.join(self.MixedScriptFileDirPath, f"{self.ProjectName}_SampleScript({self.NextSolution})_jpeg")
        os.makedirs(self.SampleScriptJPEGDirPath, exist_ok = True)

        # P04: 리사이즈 보조선 샘플 jpeg 10개, 경로 및 디렉토리 생성
        self.TrimSampleScriptJPEGDirPath = os.path.join(self.MixedScriptFileDirPath, f"{self.ProjectName}_TrimSampleScript({self.NextSolution})_jpeg")
        os.makedirs(self.TrimSampleScriptJPEGDirPath, exist_ok = True)

        # P05: 경로 및 디렉토리 생성
        self.SplitScriptPDFDirPath = os.path.join(self.MixedScriptFileDirPath, f"{self.ProjectName}_Script({self.NextSolution})_pdf")
        os.makedirs(self.SplitScriptPDFDirPath, exist_ok = True)

        # P05: 경로 및 디렉토리 생성
        self.ResizeSplitScriptPDFDirPath = os.path.join(self.MixedScriptFileDirPath, f"{self.ProjectName}_ResizeScript({self.NextSolution})_pdf")
        os.makedirs(self.ResizeSplitScriptPDFDirPath, exist_ok = True)

        # P06: 경로 및 디렉토리 생성
        self.ScriptJPEGDirPath = os.path.join(self.MixedScriptFileDirPath, f"{self.ProjectName}_Script({self.NextSolution})_jpeg")
        os.makedirs(self.ScriptJPEGDirPath, exist_ok = True)

        # 폰트 경로
        self.FontDirPath = "/usr/share/fonts/"
        self.NotoSansCJKRegular = os.path.join(self.FontDirPath, "opentype/noto/NotoSansCJK-Regular.ttc")

        # 로그 출력정보 및 경로 설정
        self.ProcessInfo = self._ProcessInfo()


    ## [Method]: 출력정보 설정 ##
    def _ProcessInfo(self):
        """ProcessInfo를 생성해서 출력 정보 설정"""
        return f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"


    ## [AbstractMethod] InputsPreprocess: ... 전처리 메서드 ##
    def _InputsPreprocess(self):
        """... 전처리 메서드"""
        pass


    ## [AbstractMethod] Inputs: ... Inputs 생성 ##
    def _Create_Inputs(self):
        """... Inputs 생성"""
        # Inputs 초기화
        return [], []


    ## [AbstractMethod] ResponsePostprocess: ... Output 메서드 ##
    def _ResponsePostprocess(self, SolutionEditProcess):
        """Output을 통한 ..."""
        # Output 스위치
        return True


    ## [AbstractMethod] Output: ... Output 메서드 ##
    def _CreateOutput(self, SolutionEditProcess):
        """Output을 통한 ..."""
        # Output 스위치
        return True


############################################################
##### Process: PT01 ScriptLoad (업로드 된 스크립트 파일 확인) #####
############################################################
class ScriptLoadProcess(ScriptSegmentationSolution):

    ProcessNumber = "PT01"
    ProcessName = "ScriptLoad"


    ## Init: ScriptLoad 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## InputsPreprocess: 스크립트 파일 확장자 확인 및 표준화 전처리 메서드 ##
    def _InputsPreprocessNormalizedScriptFile(self):
        """지정된 디렉토리에서 txt 또는 pdf 스크립트 파일을 찾아 표준화된 이름으로 저장 전처리 메서드"""
        FileExistsError = True

        SupportedExtensions = ['.txt', '.pdf']
        AllFiles = os.listdir(self.MixedScriptFileDirPath)
        for Extension in SupportedExtensions:
            ScriptFiles = [File for File in AllFiles if File.lower().endswith(Extension)]
            if ScriptFiles:
                RawUploadedScriptFilePath = os.path.join(self.MixedScriptFileDirPath, ScriptFiles[0])
                self.FileExtension = Extension[1:]
                ScriptFileName = f"{self.ProjectName}_Script({self.NextSolution}).{self.FileExtension}"
                self.UploadedScriptFilePath = os.path.join(self.MixedScriptFileDirPath, ScriptFileName)

                # 파일명이 다르면 표준화된 이름으로 복사 (기존 파일이 존재하면 복사하지 않음)
                if not os.path.exists(self.UploadedScriptFilePath):
                    if ScriptFiles[0] != ScriptFileName:
                        shutil.copy2(RawUploadedScriptFilePath, self.UploadedScriptFilePath)
                    
                FileExistsError = False

        if FileExistsError:
            # txt 또는 pdf 파일이 없으면 오류메세지 출력
            sys.exit(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.MixedScriptFileDirPath})\n\n")


    ## Inputs: 솔루션 정보 Inputs 생성 메서드 ##
    def _CreateSolutionInfoToInputs(self):
        """솔루션 정보 Inputs 생성 메서드"""
        # 스크립트 파일 확장자 확인 및 표준화
        self._InputsPreprocessNormalizedScriptFile()

        # Inputs 생성
        Inputs = {
            "ProjectName": self.ProjectName,
            "NextSolution": self.NextSolution,
            "AutoTemplate": self.AutoTemplate,
            "FileExtension": self.FileExtension,
            "UploadedScriptFilePath": self.UploadedScriptFilePath
        }

        return [Inputs], [""]


    ## Run: ScriptLoadProcess 실행 ##
    def Run(self):
        """스크립트 로드 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateSolutionInfoToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        # SolutionEdit 추출
        FileExtension = SolutionEdit[self.ProcessName][0]["FileExtension"]
        UploadedScriptFilePath = SolutionEdit[self.ProcessName][0]["UploadedScriptFilePath"]

        return SolutionEdit, FileExtension, UploadedScriptFilePath, self.MixedScriptFileDirPath


#################################
#################################
########## PDF Process ##########
#################################
#################################


#######################################################
##### Process: P02 PDFMainLangCheck (PDF 언어 체크) #####
#######################################################
class PDFMainLangCheckProcess(ScriptSegmentationSolution):

    ProcessNumber = "P02"
    ProcessName = "PDFMainLangCheck"


    ## Init: PDFMainLangCheck 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## InputsPreprocess: PDF 샘플 이미지 생성 및 라벨 생성 전처리 메서드 ##
    def _InputsPreprocessLabeledSampleJPEGs(self, Page, InputId):
        """PDF 페이지에 '자료번호: InputId' 라벨을 추가한 JPEG 파일을 생성 전처리 메서드 """
        # 페이지 → 이미지
        Pixmap = Page.get_pixmap(dpi = 150)
        PageImg = Image.frombytes("RGB", (Pixmap.width, Pixmap.height), Pixmap.samples)

        # 스케일 기준 및 스케일 팩터
        RefWidth = 1240
        Scale = max(0.5, min(2.5, PageImg.width / RefWidth))

        # 폰트 로딩
        FontSize = int(30 * Scale)
        try:
            Font = ImageFont.truetype(self.NotoSansCJKRegular, FontSize)
        except Exception:
            Font = ImageFont.load_default()

        # 라벨 텍스트 및 치수
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

        # 라벨 이미지 (흰색 불투명 배경, RGB)
        LabelImg = Image.new("RGB", (LabelW, LabelH), "white")
        Draw = ImageDraw.Draw(LabelImg)

        # 테두리
        Draw.rectangle([(0, 0), (LabelW - 1, LabelH - 1)], outline="black", width=BorderW)

        # 텍스트 중앙 정렬 + 수직 오프셋(그림자 없음)
        TextX = (LabelW - TextW) // 2
        VerticalOffset = int(-0.3 * FontSize)  # 필요시 0 ~ -0.3*FontSize 내에서 조정
        TextY = (LabelH - TextH) // 2 + VerticalOffset
        TextY = max(Padding // 2, min(TextY, LabelH - TextH - Padding // 2))

        Draw.text((TextX, TextY), LabelText, font=Font, fill="black")

        # 합성 위치(상단 중앙)
        PosX = (PageImg.width - LabelW) // 2
        PosY = Margin
        PosX = max(0, min(PosX, PageImg.width - LabelW))
        PosY = max(0, min(PosY, PageImg.height - LabelH))

        # 불투명 라벨은 paste로 합성 (alpha_composite 사용 금지)
        if LabelImg.mode != "RGB":
            LabelImg = LabelImg.convert("RGB")
        # PageImg는 이미 RGB
        PageImg.paste(LabelImg, (PosX, PosY))

        # 디렉터리 저장
        OutputFilename = f"{self.ProjectName}_Script({self.NextSolution})({InputId}).jpeg"
        OutputPath = os.path.join(self.SampleScriptJPEGDirPath, OutputFilename)

        PageImg.save(
            OutputPath,
            "JPEG",
            quality = 92,
            optimize = True,
            progressive = True,
            subsampling = 1
        )

        return OutputPath


    ## Inputs: 라벨 샘플 경로의 Inputs 생성 메서드 ##
    def _CreateLabeledSamplePathToInputs(self):
        """샘플 입력을 생성해서 list 형태로 반환, 앞 5페이지와 전체 랜덤 5페이지를 합쳐 총 10개의 샘플 Inputs 생성 메서드"""
        # 폴더에 JPEG가 10개 이상 있으면 그대로 사용
        if os.path.exists(self.SampleScriptJPEGDirPath):
            ScriptJpegs = sorted(
                f for f in os.listdir(self.SampleScriptJPEGDirPath)
                if f.lower().endswith(".jpeg")
            )
            if len(ScriptJpegs) >= 10:
                Inputs = [
                    os.path.join(self.SampleScriptJPEGDirPath, fn)
                    for fn in ScriptJpegs
                ]
                return [Inputs], [""]

        # 없으면 PDF에서 10페이지를 선정하여 라벨 JPEG 생성
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        TotalPages = len(PdfDocument)
        os.makedirs(self.SampleScriptJPEGDirPath, exist_ok=True)

        SelectedPages = set()
        TargetCount = min(10, TotalPages) # 목표 개수는 최대 10개 또는 전체 페이지 수

        # 1. 가장 앞에서부터 5페이지 선택 (문서가 5페이지 미만일 경우 가능한 페이지만큼 선택)
        front_pages = range(min(5, TotalPages))
        SelectedPages.update(front_pages)

        # 2. 목표 개수(10개)에 도달할 때까지 나머지 페이지 중에서 랜덤으로 추가
        #    중복을 피하기 위해 아직 선택되지 않은 페이지들 중에서 선택
        if len(SelectedPages) < TargetCount:
            remaining_pool = [Page for Page in range(TotalPages) if Page not in SelectedPages]
            NumToAdd = TargetCount - len(SelectedPages)
            
            # 만약 풀에 있는 페이지 수보다 더 많이 뽑아야 하는 경우를 대비 (실제로는 발생하지 않음)
            NumToSample = min(NumToAdd, len(remaining_pool))

            randomly_added_pages = random.sample(remaining_pool, k = NumToSample)
            SelectedPages.update(randomly_added_pages)

        # 최종 선택된 페이지 인덱스를 정렬
        Selected = sorted(list(SelectedPages))

        Inputs = []
        for InputId, PageIdx in enumerate(Selected, 1):
            page = PdfDocument.load_page(PageIdx)
            OutPath = self._InputsPreprocessLabeledSampleJPEGs(page, InputId)
            Inputs.append(OutPath)

        PdfDocument.close()

        return [Inputs], [""]


    ## Run: PDFMainLangCheckProcess 실행 ##
    def Run(self):
        """PDF 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateLabeledSamplePathToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        # SolutionEdit 추출
        MainLang = SolutionEdit[self.ProcessName][0]["MainLang"]

        return SolutionEdit, MainLang


#######################################################################
##### Process: P03 PDFLayoutCheck (PDF 인쇄 파일 형식인 단면, 양면 체크) #####
#######################################################################
class PDFLayoutCheckProcess(ScriptSegmentationSolution):

    ProcessNumber = "P03"
    ProcessName = "PDFLayoutCheck"


    ## Init: PDFLayoutCheck 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## Inputs: PDF 라벨 샘플 이미지 Inputs 생성 메서드##
    def _LoadPDFToLabeledSampleJPEGToInputs(self):
        """SampleScriptJPEGDirPath에 저장된 JPEG 파일 경로를 리스트로 Inputs 생성 메서드"""
        # SampleScriptJPEGDirPath에 ScriptJPEG 파일 10개 파일명 추출
        ScriptJPEGFiles = sorted([FileName for FileName in os.listdir(self.SampleScriptJPEGDirPath) if FileName.lower().endswith('.jpeg')])

        # SampleScriptJPEGDirPath에 JPEG 파일 10개 경로 Inputs 생성 및 리턴
        Inputs = []
        for FileName in ScriptJPEGFiles:
            FilePath = os.path.join(self.SampleScriptJPEGDirPath, FileName)
            Inputs.append(FilePath)

        return [Inputs], [""]


    ## Output: Output을 통한 PDF 레이아웃 조정 ##
    def _CreateOutputToAdjustedLayoutPDF(self, SolutionEditProcess):
        """Output을 통한 PDF 레이아웃 조정 메서드"""
        # PDFLayout Check (최소 한 페이지라도 Spread면 수행)
        AdjustedLayout = False
        for SolutionEditProcessDic in SolutionEditProcess[0]:
            if SolutionEditProcessDic.get('Size') == 'Spread':
                AdjustedLayout = True
                break
            
        # 레이아웃 조정이 필요한 경우
        if AdjustedLayout:

            # 1) PDF 열기
            PdfDocument = fitz.open(self.UploadedScriptFilePath)
            BackUpPdfDocumentPath = self.UploadedScriptFilePath.replace(".pdf", "_backup.pdf")

            if len(PdfDocument) == 0:
                PdfDocument.close()
                return True

            # 2) 모든 페이지 가로폭 수집
            Widths = []
            for Page in PdfDocument:
                R = Page.rect  # mediabox 기준
                W = float(R.width)
                Widths.append(W)

            # 숫자 안정화용 반올림 기반 고유 폭
            UniqueWidths = sorted(set(round(w, 3) for w in Widths))

            # 3) 혼합본(단면+스프레드) 가정에서 x, y 추정 조건 확인
            #    - 단면 폭(가장 작은 폭) = 2x + y = w_s
            #    - 스프레드 폭(가장 큰 폭) = 2x + 2y = w_l
            #    - w_s > w_l/2  이면  x > 0  (재단영역 존재)
            UseXYTrim = False
            XTrim = 0.0
            SingleWidth = min(Widths)
            SpreadThreshold = 1.5 - 1e-6  # fallback용

            if len(UniqueWidths) >= 2:
                SmallW = min(UniqueWidths)
                LargeW = max(UniqueWidths)
                if SmallW > (LargeW / 2.0) + 1e-6:
                    # y = w_l - w_s, x = w_s - w_l/2
                    YContent = LargeW - SmallW
                    XTrim = SmallW - (LargeW / 2.0)
                    if XTrim < 0:
                        XTrim = 0.0
                    UseXYTrim = XTrim > 0.0
                # 단면 기준 폭은 혼합본에서 가장 작은 가로폭
                SingleWidth = SmallW

            # 4) 결과 PDF 생성
            AdjustedLayoutPdfDocument = fitz.open()

            # 다시 처음부터 순회 (PyMuPDF는 재순회 가능)
            for PageIndex, Page in enumerate(PdfDocument):
                Rect = Page.rect
                W, H = float(Rect.width), float(Rect.height)

                # 기본 스프레드 판정 (fallback 겸용)
                IsSpread = (W / SingleWidth) >= SpreadThreshold

                # 우선 재단(x) 적용
                if UseXYTrim and XTrim > 0.0:
                    # 상하좌우 x 만큼 크롭 (클램프)
                    Left   = max(Rect.x0, Rect.x0 + XTrim)
                    Right  = min(Rect.x1, Rect.x1 - XTrim)
                    Top    = max(Rect.y0, Rect.y0 + XTrim)
                    Bottom = min(Rect.y1, Rect.y1 - XTrim)

                    # 역전 방지 (너무 큰 x로 인해 폭/높이가 0 이하가 되지 않도록 최소폭 2pt 보장)
                    if Right - Left < 2:
                        MidX = (Rect.x0 + Rect.x1) / 2.0
                        Left, Right = MidX - 1, MidX + 1
                    if Bottom - Top < 2:
                        MidY = (Rect.y0 + Rect.y1) / 2.0
                        Top, Bottom = MidY - 1, MidY + 1

                    CropRect = fitz.Rect(Left, Top, Right, Bottom)
                else:
                    # 재단 미적용 시 원본 박스 사용
                    CropRect = Rect

                # 재단 후 박스의 폭/높이
                CW = float(CropRect.width)
                CH = float(CropRect.height)

                if IsSpread:
                    # 재단 후 좌/우 절반 분할 (가로 절반)
                    HalfW = CW / 2.0

                    # 좌측(앞페이지)
                    LeftClip = fitz.Rect(CropRect.x0, CropRect.y0, CropRect.x0 + HalfW, CropRect.y1)
                    LeftPage = AdjustedLayoutPdfDocument.new_page(width=HalfW, height=CH)
                    LeftPage.show_pdf_page(LeftPage.rect, PdfDocument, Page.number, clip=LeftClip)

                    # 우측(뒷페이지)
                    RightClip = fitz.Rect(CropRect.x0 + HalfW, CropRect.y0, CropRect.x1, CropRect.y1)
                    RightPage = AdjustedLayoutPdfDocument.new_page(width=HalfW, height=CH)
                    RightPage.show_pdf_page(RightPage.rect, PdfDocument, Page.number, clip=RightClip)
                else:
                    # 단면 페이지: x 재단만 적용한 채로 그대로 복사
                    NewPage = AdjustedLayoutPdfDocument.new_page(width=CW, height=CH)
                    NewPage.show_pdf_page(NewPage.rect, PdfDocument, Page.number, clip=CropRect)

            # 5) 저장 및 교체
            AdjustedLayoutPdfDocument.save(BackUpPdfDocumentPath, garbage=4, deflate=True)
            AdjustedLayoutPdfDocument.close()
            PdfDocument.close()

            os.remove(self.UploadedScriptFilePath)
            shutil.move(BackUpPdfDocumentPath, self.UploadedScriptFilePath)

        # Output 스위치
        return True


    ## Run: PDFLayoutCheckProcess 실행 ##
    def Run(self):
        """PDF 인쇄 파일 형식인 단면, 양면 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._LoadPDFToLabeledSampleJPEGToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


###################################################
##### Process: P04 PDFResize (PDF 파일 가로 재단) #####
###################################################
class PDFResizeProcess(ScriptSegmentationSolution):

    ProcessNumber = "P04"
    ProcessName = "PDFResize"


    ## Init: PDFResize 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## InputsPreprocess: PDF 방향별 보조선 샘플 이미지 생성 전처리 메서드 ##
    def _InputsPreprocessPDFToTrimLineJPEGs(self, Page, InputId):
        """PDF 페이지에서 보조선 샘플 이미지를 생성 생성 전처리 메서드 """
        Pixmap = Page.get_pixmap(dpi = 150)
        BaseImg = Image.frombytes("RGB", (Pixmap.width, Pixmap.height), Pixmap.samples)

        RefWidth = 1240
        Scale = max(0.5, min(2.5, BaseImg.width / RefWidth))

        # 폰트 크기
        LabelFontSize  = int(30 * Scale)
        NumberFontSize = max(14, int(26 * Scale))

        # 폰트 로딩
        try:
            LabelFont  = ImageFont.truetype(self.NotoSansCJKRegular, LabelFontSize)
            NumberFont = ImageFont.truetype(self.NotoSansCJKRegular, NumberFontSize)
        except Exception:
            LabelFont  = ImageFont.load_default()
            NumberFont = ImageFont.load_default()

        # 공통 스타일
        self.IntervalRatio = 0.03  # 간격 비율
        LineWidth          = max(1, int(2 * Scale))
        IntervalY          = max(1, int(BaseImg.height * self.IntervalRatio))
        IntervalX          = max(1, int(BaseImg.width  * self.IntervalRatio))
        NumberPad          = int(3 * Scale)
        NumberBaselineLift = int(2 * Scale)
        RoundedRadius      = max(2, int(6 * Scale))
        LabelGap           = int(8 * Scale)
        ExtraMargin        = int(15 * Scale)

        CircledNums = ["","①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩"]

        Padding = int(14 * Scale)
        BorderW = max(2, int(4 * Scale))

        if self.MainLang == "ko":
            DirLabelMap = {"Left":"자료방향: 좌","Right":"자료방향: 우","Top":"자료방향: 위","Bottom":"자료방향: 아래"}
            MultiDirSuffix = "네방향"
        else:
            DirLabelMap = {"Left":"Direction: Left","Right":"Direction: Right","Top":"Direction: Top","Bottom":"Direction: Bottom"}
            MultiDirSuffix = "FourDirections"

        FilenameSuffix = {"Left":"Left","Right":"Right","Top":"Top","Bottom":"Bottom"}

        # 방향별 색상
        DirectionColors = {
            "Left": (255, 0, 0),     # 빨강
            "Right": (0, 0, 255),    # 파랑
            "Top": (0, 128, 0),      # 녹색
            "Bottom": (128, 0, 128), # 보라
        }

        def DrawTextWithWhiteBg(Draw, XY, Text, Font, Pad=NumberPad, Rounded=True, text_fill="red"):
            X, Y = XY
            try:
                L, T, R, B = Draw.textbbox((X, Y), Text, font=Font)
            except Exception:
                Est = Font.getbbox(Text)
                L, T, R, B = X, Y, X + (Est[2]-Est[0]), Y + (Est[3]-Est[1])
            if Rounded and hasattr(Draw, "rounded_rectangle"):
                Draw.rounded_rectangle([(L-Pad, T-Pad), (R+Pad, B+Pad)], radius=RoundedRadius, fill="white")
            else:
                Draw.rectangle([(L-Pad, T-Pad), (R+Pad, B+Pad)], fill="white")
            Draw.text((X, Y), Text, font=Font, fill=text_fill)

        def DrawTextWithWhiteBgCenter(Draw, CenterXY, Text, Font, Pad=NumberPad, Rounded=True, BaselineLift=0, text_fill="red"):
            Cx, Cy = CenterXY
            try:
                Est = Draw.textbbox((0,0), Text, font=Font)
                Tw, Th = Est[2]-Est[0], Est[3]-Est[1]
            except Exception:
                Est = Font.getbbox(Text)
                Tw, Th = Est[2]-Est[0], Est[3]-Est[1]
            Tx = int(Cx - Tw/2)
            Ty = int(Cy - Th/2 - BaselineLift)
            DrawTextWithWhiteBg(Draw, (Tx, Ty), Text, Font, Pad=Pad, Rounded=Rounded, text_fill=text_fill)

        # 라벨 이미지를 만들어(테두리 포함) 회전 후 붙이는 헬퍼
        def MakeLabelImage(LabelText):
            TextBBox = LabelFont.getbbox(LabelText)
            Tw = TextBBox[2] - TextBBox[0]
            Th = TextBBox[3] - TextBBox[1]
            LabelW = Tw + 2*Padding
            LabelH = Th + 2*Padding
            LabelImg = Image.new("RGB", (LabelW, LabelH), "white")
            LDraw = ImageDraw.Draw(LabelImg)
            LDraw.rectangle([(0,0),(LabelW-1,LabelH-1)], outline="black", width=BorderW)
            Tx = (LabelW - Tw)//2
            Ty = (LabelH - Th)//2 + int(-0.3 * LabelFontSize)  # 살짝 위로
            Ty = max(Padding//2, min(Ty, LabelH - Th - Padding//2))
            LDraw.text((Tx, Ty), LabelText, font=LabelFont, fill="black")
            return LabelImg

        def DrawDirection(Img, Direction, Color):
            Draw = ImageDraw.Draw(Img)
            ImgCx = Img.width // 2
            ImgCy = Img.height // 2

            if Direction == "Top":
                for i in range(1, 11):
                    y = i * IntervalY
                    Draw.line([(0, y), (Img.width, y)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(Draw, (ImgCx, y), CircledNums[i], NumberFont,
                                            Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color)
            elif Direction == "Bottom":
                for i in range(1, 11):
                    y = Img.height - (i * IntervalY)
                    Draw.line([(0, y), (Img.width, y)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(Draw, (ImgCx, y), CircledNums[i], NumberFont,
                                            Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color)
            elif Direction == "Left":
                for i in range(1, 11):
                    x = i * IntervalX
                    Draw.line([(x, 0), (x, Img.height)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(Draw, (x, ImgCy), CircledNums[i], NumberFont,
                                            Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color)
            elif Direction == "Right":
                for i in range(1, 11):
                    x = Img.width - (i * IntervalX)
                    Draw.line([(x, 0), (x, Img.height)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(Draw, (x, ImgCy), CircledNums[i], NumberFont,
                                            Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color)

        def SaveImage(Img, SuffixText, input_id=None):
            use_id = InputId if input_id is None else input_id
            OutName = f"{self.ProjectName}_Script({self.NextSolution})({use_id})({SuffixText}).jpeg"
            OutPath = os.path.join(self.TrimSampleScriptJPEGDirPath, OutName)
            Img.save(OutPath, "JPEG", quality=92, optimize=True, progressive=True, subsampling=1)
            return OutPath

        OutputPaths = []

        if self.ResponseMethod == "Prompt":
            # 방향별로 개별 저장 + 중앙 라벨
            for DirKey in ["Left", "Right", "Top", "Bottom"]:
                Img = BaseImg.copy()
                DrawDirection(Img, DirKey, DirectionColors[DirKey])
                CenterLabel = MakeLabelImage(DirLabelMap[DirKey])
                Px = (Img.width - CenterLabel.width)//2
                Py = (Img.height - CenterLabel.height)//2
                Img.paste(CenterLabel, (Px, Py))
                OutPath = SaveImage(Img, FilenameSuffix[DirKey])
                OutputPaths.append(OutPath)

        if self.ResponseMethod == "Manual":
            # 1) 4방향 'RGB(흰 배경)' 레이어 생성 (투명처리 없음)
            layer_dict = {}
            for DirKey in ["Left", "Right", "Top", "Bottom"]:
                layer = Image.new("RGB", (BaseImg.width, BaseImg.height), "white")
                DrawDirection(layer, DirKey, DirectionColors[DirKey])
                layer_dict[DirKey] = layer  # 그대로 RGB 보관

            # 2) BaseImg와 각 레이어를 곱하기(Multiply)로 합성
            merged_rgb = BaseImg.convert("RGB")
            for DirKey in ["Left", "Right", "Top", "Bottom"]:
                merged_rgb = ImageChops.multiply(merged_rgb, layer_dict[DirKey])

            # 3) 라벨은 별도 캔버스(RGBA)에 배치 후, 최종 이미지 위에 알파 합성
            label_canvas = Image.new("RGBA", (BaseImg.width, BaseImg.height), (255, 255, 255, 0))
            LabelInnerOffset = LabelGap + LineWidth + NumberPad + ExtraMargin

            # Top
            up_y10 = 10 * IntervalY
            up_label = MakeLabelImage(DirLabelMap["Top"]).rotate(180, expand=True)
            up_px = (BaseImg.width - up_label.width) // 2
            up_py = min(max(0, up_y10 + LabelInnerOffset), BaseImg.height - up_label.height)
            label_canvas.paste(up_label.convert("RGBA"), (up_px, up_py))

            # Bottom
            down_y10 = BaseImg.height - 10 * IntervalY
            down_label = MakeLabelImage(DirLabelMap["Bottom"])
            down_px = (BaseImg.width - down_label.width) // 2
            down_py = min(max(0, down_y10 - LabelInnerOffset - down_label.height), BaseImg.height - down_label.height)
            label_canvas.paste(down_label.convert("RGBA"), (down_px, down_py))

            # Left
            left_x10 = 10 * IntervalX
            left_label = MakeLabelImage(DirLabelMap["Left"]).rotate(270, expand=True)
            left_px = min(max(0, left_x10 + LabelInnerOffset), BaseImg.width - left_label.width)
            left_py = (BaseImg.height - left_label.height) // 2
            label_canvas.paste(left_label.convert("RGBA"), (left_px, left_py))

            # Right
            right_x10 = BaseImg.width - 10 * IntervalX
            right_label = MakeLabelImage(DirLabelMap["Right"]).rotate(90, expand=True)
            right_px = min(max(0, right_x10 - LabelInnerOffset - right_label.width), BaseImg.width - right_label.width)
            right_py = (BaseImg.height - right_label.height) // 2
            label_canvas.paste(right_label.convert("RGBA"), (right_px, right_py))

            # 4) 라벨을 merged_rgb 위에 합성
            final_rgba = merged_rgb.convert("RGBA")
            final_rgba = Image.alpha_composite(final_rgba, label_canvas)
            final_rgb = final_rgba.convert("RGB")

            # 저장: ({InputId})(네방향).jpeg -> OutputPaths에 포함
            OutPath = SaveImage(final_rgb, MultiDirSuffix)
            OutputPaths.append(OutPath)

            # 저장: (multiply)(네방향).jpeg -> 누적 Multiply 저장 (OutputPaths에는 포함 X)
            zero_name = f"{self.ProjectName}_Script({self.NextSolution})(multiply)({MultiDirSuffix}).jpeg"
            zero_path = os.path.join(self.TrimSampleScriptJPEGDirPath, zero_name)

            # 파일이 이미 있으면 불러와서 곱하기 누적, 없으면 이번 결과로 시작
            if os.path.exists(zero_path):
                try:
                    prev = Image.open(zero_path).convert("RGB")
                    # 흰색은 항등(255)이라 누적될수록 공통된 요소만 진해짐
                    accum = ImageChops.multiply(prev, final_rgb)
                except Exception:
                    # 문제가 있으면 이번 결과를 그대로 사용
                    accum = final_rgb
            else:
                accum = final_rgb

            # 덮어쓰기 저장 (누적본 유지)
            accum.save(zero_path, "JPEG", quality=92, optimize=True, progressive=True, subsampling=1)
            # OutputPaths.append(zero_path)

        return OutputPaths


    ## Inputs: 방향별 보조선 샘플 이미지 Inputs 생성 메서드 ##
    def _CreateTrimLineJPEGToInputs(self):
        """PDF에서 최대 10개 페이지를 뽑아 각 페이지마다 방향별 보조선 샘플 이미지 4개 Inputs 생성 메서드"""
        # PDF 열기
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        TotalPages = len(PdfDocument)

        # 총 페이지가 10 미만이면 중복 포함 선택, 아니면 10개 샘플
        K = 10
        if TotalPages < K:
            SelectedPageIndices = random.choices(range(TotalPages), k = K)
        else:
            SelectedPageIndices = random.sample(range(TotalPages), K)

        if self.ResponseMethod == "Prompt":
            # 각 페이지별로 출력물 생성 → 하나의 Input
            Inputs = []
            ComparisonInputs = []
            for InputId, PageIndex in enumerate(SelectedPageIndices, 1):
                page = PdfDocument.load_page(PageIndex)
                OutputPaths = self._CreatePDFToTrimLineJPEGs(page, InputId)  # list[str] 기대
                Inputs.append(OutputPaths)
                ComparisonInputs.append("")
                
        if self.ResponseMethod == "Manual":
            if self.MainLang == "ko":
                Inputs = [
                    [
                        {
                            "재단선방향": "좌",
                            "본문재단선번호": 0
                        },
                        {
                            "재단선방향": "우",
                            "본문재단선번호": 0
                        },
                        {
                            "재단선방향": "위",
                            "본문재단선번호": 0
                        },
                        {
                            "재단선방향": "아래",
                            "본문재단선번호": 0
                        }
                    ]
                ]
            else:
                Inputs = [
                    [
                        {
                            "CropLineDirection": "Left",
                            "BodyCropLineNumber": 0
                        },
                        {
                            "CropLineDirection": "Right",
                            "BodyCropLineNumber": 0
                        },
                        {
                            "CropLineDirection": "Top",
                            "BodyCropLineNumber": 0
                        },
                        {
                            "CropLineDirection": "Bottom",
                            "BodyCropLineNumber": 0
                        }
                    ]
                ]
            ComparisonInputs = [""]
            for InputId, PageIndex in enumerate(SelectedPageIndices, 1):
                page = PdfDocument.load_page(PageIndex)
                OutputPaths = self._InputsPreprocessPDFToTrimLineJPEGs(page, InputId)
            
        PdfDocument.close()

        return Inputs, ComparisonInputs


    ## Output: Output을 통한 PDF 본문 재단 ##
    def _CreateOutputToResizedPDF(self, SolutionEditProcess):
        """Output을 통한 PDF를 재단 메서드"""
        # 1) 다수결로 방향별 선택 숫자 결정
        LeftNumberList, RightNumberList, TopNumberList, BottomNumberList = [], [], [], []
        for SolutionEditProcessDic in SolutionEditProcess:
            for item in SolutionEditProcessDic:
                d = item['CropLineDirection']
                n = item['BodyCropLineNumber']
                if d == 'Left':
                    LeftNumberList.append(n)
                elif d == 'Right':
                    RightNumberList.append(n)
                elif d == 'Top':
                    TopNumberList.append(n)
                elif d == 'Bottom':
                    BottomNumberList.append(n)

        LeftNumber   = max(set(LeftNumberList), key = LeftNumberList.count)
        RightNumber  = max(set(RightNumberList), key = RightNumberList.count)
        TopNumber    = max(set(TopNumberList), key = TopNumberList.count)
        BottomNumber = max(set(BottomNumberList), key = BottomNumberList.count)

        # 2) 공통 비율 (이미지 생성과 동일)
        interval_ratio = getattr(self, "IntervalRatio", 0.03)  # 이미지 코드에서 세팅한 값과 동일해야 함

        # 3) PDF 열기
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        ResizePdfDocumentPath = self.UploadedScriptFilePath.replace(".pdf", "_Resize.pdf")

        # 회전에 따른 "시각 방향 -> PDF 엣지" 매핑
        # rot는 0, 90, 180, 270 중 하나
        def _edge_map(rot_deg):
            # 반환값: { 'left': 시각적으로 어느 방향의 숫자를 쓸지,
            #           'right': ...,
            #           'top': ...,
            #           'bottom': ... }
            # 예) rot=90이면 화면의 'Top' 간격이 PDF의 'Left' 엣지 간격으로 적용됨
            if rot_deg == 0:
                return {'left': 'Left', 'right': 'Right', 'top': 'Top', 'bottom': 'Bottom'}
            elif rot_deg == 90:
                return {'left': 'Top', 'right': 'Bottom', 'top': 'Right', 'bottom': 'Left'}
            elif rot_deg == 180:
                return {'left': 'Right', 'right': 'Left', 'top': 'Bottom', 'bottom': 'Top'}
            elif rot_deg == 270:
                return {'left': 'Bottom', 'right': 'Top', 'top': 'Left', 'bottom': 'Right'}
            else:
                # 예외적으로 다른 값이면 회전 없다고 간주
                return {'left': 'Left', 'right': 'Right', 'top': 'Top', 'bottom': 'Bottom'}

        # 시각 방향 숫자 → 값 조회 헬퍼
        dir_to_num = {
            'Left': LeftNumber,
            'Right': RightNumber,
            'Top': TopNumber,
            'Bottom': BottomNumber
        }

        for page in PdfDocument:
            rect = page.rect
            w, h = rect.width, rect.height

            # 페이지 회전 각도
            try:
                rot = int(page.rotation) % 360
            except Exception:
                rot = 0

            m = _edge_map(rot)  # 회전 보정 매핑

            # 4) 각 엣지별 오프셋 계산
            #    - left/right는 너비 w를 기준으로, top/bottom은 높이 h를 기준으로
            left_offset   = dir_to_num[m['left']]   * interval_ratio * w
            right_offset  = dir_to_num[m['right']]  * interval_ratio * w
            top_offset    = dir_to_num[m['bottom']] * interval_ratio * h
            bottom_offset = dir_to_num[m['top']]    * interval_ratio * h

            # 5) 최종 크롭 박스 계산
            left   = rect.x0 + left_offset
            right  = rect.x1 - right_offset
            top    = rect.y0 + top_offset
            bottom = rect.y1 - bottom_offset

            # 유효 범위로 클램프 + 뒤집힘 방지
            left   = max(rect.x0, min(left, rect.x1))
            right  = max(rect.x0, min(right, rect.x1))
            top    = max(rect.y0, min(top, rect.y1))
            bottom = max(rect.y0, min(bottom, rect.y1))

            # 혹시라도 역전된 경우 보정
            if right <= left:
                mid = (rect.x0 + rect.x1) / 2.0
                left, right = mid - 1, mid + 1  # 최소 폭 2pt 보장
            if bottom <= top:
                mid = (rect.y0 + rect.y1) / 2.0
                top, bottom = mid - 1, mid + 1  # 최소 높이 2pt 보장

            CropRect = fitz.Rect(left, top, right, bottom)

            # 6) 크롭 적용
            page.set_cropbox(CropRect)
            page.set_mediabox(CropRect)

        # 7) 저장
        PdfDocument.save(ResizePdfDocumentPath, garbage = 4, deflate = True)
        PdfDocument.close()

        return True


    ## Run: PDFResizeProcess 실행 ##
    def Run(self):
        """PDF 가로 재단 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateTrimLineJPEGToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutputToResizedPDF, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


###################################################
##### Process: P05 PDFSplit (PDF 페이지 별 분할) #####
###################################################
class PDFSplitProcess(ScriptSegmentationSolution):

    ProcessNumber = "P05"
    ProcessName = "PDFSplit"


    ## Init: PDFSplit 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## Inputs: PDF 파일을 페이지별로 분할 및 저장 및 Inputs 생성 메서드 ##
    def _SplitPDFToInputs(self):
        """PDF 파일을 페이지별로 분할하고 저장 및 Inputs 생성 메서드 """
        # PDF 파일 읽고 총 페이지 수 계산
        PdfDocument = PdfReader(self.UploadedScriptFilePath)
        ResizePDFPath = self.UploadedScriptFilePath.replace(f"_Script({self.NextSolution}).pdf", f"_ResizeScript({self.NextSolution}).pdf")
        ResizePdfDocument = PdfReader(ResizePDFPath)
        TotalPages = len(PdfDocument.pages)

        # 각 페이지를 개별 PDF 파일로 저장 및 Inputs 생성
        Inputs = []
        ComparisonInputs = []
        for PageNum in range(TotalPages):
            # 페이지별 PDF 분할
            Writer = PdfWriter()
            Writer.add_page(PdfDocument.pages[PageNum])
            OutputFileName = f"{self.ProjectName}_Script({self.NextSolution})({PageNum + 1}).pdf"
            OutputFilePath = os.path.join(self.SplitScriptPDFDirPath, OutputFileName)

            # 페이지별 PDF 파일 저장
            with open(OutputFilePath, "wb") as OutputFile:
                Writer.write(OutputFile)

            # 페이지별 Resize PDF 분할
            ResizeWriter = PdfWriter()
            ResizeWriter.add_page(ResizePdfDocument.pages[PageNum])
            ResizeOutputFileName = f"{self.ProjectName}_Script({self.NextSolution})({PageNum + 1}).pdf"
            ResizeOutputFilePath = os.path.join(self.ResizeSplitScriptPDFDirPath, ResizeOutputFileName)

            # 페이지별 Resize PDF 파일 저장
            with open(ResizeOutputFilePath, "wb") as ResizeOutputFile:
                ResizeWriter.write(ResizeOutputFile)
            
            # 페이지별 파일 경로를 리스트에 추가
            Inputs.append(
                {
                    "ScriptId": PageNum + 1,
                    "PageFilePath": OutputFilePath,
                    "ResizePageFilePath": ResizeOutputFilePath
                }
            )
            ComparisonInputs.append("")

        return Inputs, ComparisonInputs


    ## Run: PDFSplitProcess 실행 ##
    def Run(self):
        """PDF 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._SplitPDFToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


############################################################
##### Process: P06 PDFFormCheck (PDF 파일 페이지 형식 체크) #####
############################################################
class PDFFormCheckProcess(ScriptSegmentationSolution):

    ProcessNumber = "P06"
    ProcessName = "PDFFormCheck"


    ## Init: PDFFormCheck 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## InputsPreprocess: PDF 이미지 생성 및 라벨 생성 전처리 메서드 ##
    def _InputsPreprocessPDFToLabeledJPEGs(self, PDFDoc):
        """PDF 전체 페이지를 순회하며 '자료번호: 페이지번호' 라벨을 추가한 JPEG 파일 생성 전처리 메서드"""
        OutputPathList = []

        for PageNumber in range(len(PDFDoc)):
            Page = PDFDoc[PageNumber]

            # 페이지 → 이미지
            Pixmap = Page.get_pixmap(dpi = 150)
            PageImg = Image.frombytes("RGB", (Pixmap.width, Pixmap.height), Pixmap.samples)

            # 스케일
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

            MinWBBox = Font.getbbox("자료번호: 99999")
            MinTextW = MinWBBox[2] - MinWBBox[0]

            LabelW = max(TextW, MinTextW) + 2 * Padding
            LabelH = TextH + 2 * Padding

            # 라벨 이미지 (흰색 불투명 배경, RGB)
            LabelImg = Image.new("RGB", (LabelW, LabelH), "white")
            Draw = ImageDraw.Draw(LabelImg)

            # 테두리
            Draw.rectangle([(0, 0), (LabelW - 1, LabelH - 1)], outline="black", width=BorderW)

            # 텍스트 중앙 정렬 + 수직 오프셋(그림자 없음)
            TextX = (LabelW - TextW) // 2
            VerticalOffset = int(-0.3 * FontSize)
            TextY = (LabelH - TextH) // 2 + VerticalOffset
            TextY = max(Padding // 2, min(TextY, LabelH - TextH - Padding // 2))

            Draw.text((TextX, TextY), LabelText, font=Font, fill="black")

            # 합성 위치(상단 중앙)
            PosX = (PageImg.width - LabelW) // 2
            PosY = Margin
            PosX = max(0, min(PosX, PageImg.width - LabelW))
            PosY = max(0, min(PosY, PageImg.height - LabelH))

            # 불투명 라벨은 paste 사용
            if LabelImg.mode != "RGB":
                LabelImg = LabelImg.convert("RGB")
            PageImg.paste(LabelImg, (PosX, PosY))

            # 저장
            OutputFilename = f"{self.ProjectName}_Script({self.NextSolution})({PageNumber + 1}).jpeg"
            OutputPath = os.path.join(self.ScriptJPEGDirPath, OutputFilename)

            PageImg.save(
                OutputPath,
                "JPEG",
                quality=92,
                optimize=True,
                progressive=True,
                subsampling=1
            )

            OutputPathList.append(OutputPath)

        return OutputPathList


    ## Inputs: 라벨된 JPEG 경로의 Inputs 생성 메서드 ##
    def _CreateLabeledJPEGsToInputs(self):
        """라벨된 JPEG 경로 목록을 기반으로, 5개를 선택하여 리스트 Inputs 생성 메서드"""
        # PdfDocument 열어서 라벨 JPEG 생성 후 경로 리스트 확보
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        OutputPathList = self._InputsPreprocessPDFToLabeledJPEGs(PdfDocument)
        PdfDocument.close()

        # 2칸씩 건너뛰며 시작점을 잡고, 매번 5개를 원형으로 선택
        OutputPathLength = len(OutputPathList)
        Inputs = []
        ComparisonInputs = []
        for start in range(0, OutputPathLength, 2):
            Indexes = [(start + k) % OutputPathLength for k in range(5)]
            inputPaths = [OutputPathList[i] for i in Indexes]
            Inputs.append(inputPaths)
            
            OutputPathNums = [idx + 1 for idx in Indexes]
            OutputPathNumsStr = ", ".join(str(idx) for idx in OutputPathNums)
            ComparisonInputs.append(OutputPathNumsStr)

        return Inputs, ComparisonInputs


    ## ResponsePostprocess: ##


    ## Run: PDFFormCheckProcess 실행 ##
    def Run(self):
        """PDF 페이지 형식 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateLabeledJPEGsToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


###########################################################
##### Process: P07 PDFIndexGen (PDF 파일 목차 데이터 형성) #####
###########################################################
class PDFIndexGenProcess(ScriptSegmentationSolution):

    ProcessNumber = "P07"
    ProcessName = "PDFIndexGen"


    ## Init: PDFIndexGen 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## InputsPreprocess: 생성된 라벨 선별 ##

######################################################################
##### Process: P08 PDFIndexMatching (PDF 파일 목차와 본문 속 목차 매칭) #####
######################################################################
# class PDFFormCheckProcess(ScriptSegmentationSolution):


#####################################################################################
##### Process: P09 PDFBodyCaptionComponentCheck (PDF 파일 페이지별 Body 구성요소 체크) #####
#####################################################################################
# class PDFFormCheckProcess(ScriptSegmentationSolution):


#################################
#################################
########## TXT Process ##########
#################################
#################################


#######################################################
##### Process: T02 TXTMainLangCheck (TXT 언어 체크) #####
#######################################################
class TXTMainLangCheckProcess(ScriptSegmentationSolution):

    ProcessNumber = "T02"
    ProcessName = "TXTMainLangCheck"


    ## Init: TXTMainLangCheck 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## Inputs: TXT 샘플 Inputs 생성 메서드 ##
    def _CreateTXTToSampleTextToInputs(self):
        """텍스트 파일에서 3개의 샘플 텍스트를 추출하여 하나의 문자열로 반환하는 Inputs 생성 메서드"""
        # 업로드된 스크립트 파일 읽기
        with open(self.UploadedScriptFilePath, 'r', encoding = 'utf-8') as f:
            FullText = f.read()

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
        Inputs = f"{SampleTextList[0]} ... {SampleTextList[1]} ... {SampleTextList[2]}"

        return [Inputs], [""]


    ## Run: TXTMainLangCheckProcess 실행 ##
    def Run(self):
        """TXT 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateTXTToSampleTextToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        # MainLang 추출
        MainLang = SolutionEdit[self.ProcessName][0]["MainLang"]

        return SolutionEdit, MainLang


###################################################
##### Process: T03 TXTSplit (TXT 토큰 단위 분할) #####
###################################################
class TXTSplitProcess(ScriptSegmentationSolution):

    ProcessNumber = "T03"
    ProcessName = "TXTSplit"


    ## Init: TXTSplit 초기화 ##
    def __init__(self, Email, ProjectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview):
        """솔루션 상속 및 프로세스 초기화"""
        super().__init__(Email, ProjectName, self.ProcessNumber, self.ProcessName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)


    ## InputsPreprocess1: 언어별 MaxTokens 전처리 메서드 ##
    def _InputsPreprocessDetermineMaxTokens(self):
        """언어에 따라 적절한 MaxTokens 값을 결정 전처리 메서드"""       
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
        self.MaxTokens = int(3000 * Ratio)


    ## InputsPreprocess2: Spacy 모델 로드 및 사용자 정의 경계 설정 전처리 메서드 ##
    def _InputsPreprocessLoadSpacyModel(self):
        """언어에 맞는 Spacy 모델 로드 및 사용자 정의 경계 설정 전처리 메서드"""
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


    ## Inputs: TXT 파일을 지정된 토큰 수에 가깝게 문장 묶음으로 분할 및 Inputs 생성 메서드 ##
    def _SplitTXTToInputs(self):
        """TXT 파일을 지정된 글자 수(공백 포함)에 가깝게 문장 묶음으로 분할 및 Inputs 생성 메서드"""
        # 언어별 MaxTokens 결정
        self._InputsPreprocessDetermineMaxTokens()
        # Spacy 모델 로드
        nlp = self._InputsPreprocessLoadSpacyModel()
        
        # 업로드된 스크립트 파일 읽기
        with open(self.UploadedScriptFilePath, 'r', encoding = 'utf-8') as f:
            FullText = f.read()

        Doc = nlp(FullText)
        
        # 문장의 원본 텍스트와 마지막 토큰 뒤의 공백/줄바꿈을 합쳐서 리스트 생성
        Sentences = [s.text + s[-1].whitespace_ for s in Doc.sents]
        
        CurrentTXTChunkList = []
        Inputs = []
        ComparisonInputs = []
        for i, Sent in enumerate(Sentences):
            CurrentTXTChunkList.append(Sent)
            CurrentText = "".join(CurrentTXTChunkList)
            
            # 토큰 수 계산 대신, 공백을 포함한 글자 수를 계산합니다.
            CharCount = len(CurrentText)
            
            # 글자 수가 MaxTokens를 초과하면 분할합니다.
            if CharCount >= self.MaxTokens:
                Inputs.append(
                    {
                        "ScriptId": i + 1,
                        "SplitedText": CurrentText
                    }
                )
                CurrentTXTChunkList = []
                ComparisonInputs.append("")
                
        # 마지막 남은 문장 묶음 추가
        if CurrentTXTChunkList:
            Inputs.append(
                {
                    "ScriptId": len(Inputs) + 1,
                    "SplitedText": "".join(CurrentTXTChunkList)
                }
            )
            ComparisonInputs.append("")

        return Inputs, ComparisonInputs


    ## Run: TXTSplitProcess 실행 ##
    def Run(self):
        """TXT 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._SplitTXTToInputs, self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutputFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit



########################################################
##### SolutionRun: ScriptSegmentation Solution 진행 #####
########################################################
def ScriptSegmentationProcessUpdate(projectName, email, NextSolution, AutoTemplate, MessagesReview = "on"):
    ## 기본 인자 정의
    MainLang = "ko"
    Model = "OpenAI"
    ResponseMethod = "Prompt"
    
    ## PT01 통합: ScriptLoad (업로드 된 스크립트 파일 확인)
    ScriptLoadInstance = ScriptLoadProcess(email, projectName, NextSolution, AutoTemplate, MainLang, Model, "Algorithm", None, None, None, MessagesReview)
    SolutionEdit, FileExtension, UploadedScriptFilePath, MixedScriptFileDirPath = ScriptLoadInstance.Run()

    # 파일 확장자에 따라 후속 프로세스 실행
    if FileExtension == 'pdf':

        ## P02 PDFMainLangCheck (PDF 언어 체크)
        PDFMainLangCheckProcessInstance = PDFMainLangCheckProcess(email, projectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
        SolutionEdit, MainLang = PDFMainLangCheckProcessInstance.Run()
        
        ## P03 PDFLayoutCheck (PDF 인쇄 파일 형식인 단면, 양면 체크) <- 여기서 페이지 분할 동시 진행
        PDFLayoutCheckInstance = PDFLayoutCheckProcess(email, projectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
        SolutionEdit = PDFLayoutCheckInstance.Run()
        
        ## P04 PDFResize (PDF 파일 재단)
        PDFResizeInstance = PDFResizeProcess(email, projectName, NextSolution, AutoTemplate, MainLang, "Google", "Manual", MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
        SolutionEdit = PDFResizeInstance.Run()
        
        ## P05 PDFSplit (PDF 파일 페이지 분할)
        PDFSplitterInstance = PDFSplitProcess(email, projectName, NextSolution, AutoTemplate, MainLang, Model, "Algorithm", MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
        SolutionEdit = PDFSplitterInstance.Run()

        ## P06 PDFFormCheck (PDF 파일 페이지 형식 체크)
        PDFFormCheckInstance = PDFFormCheckProcess(email, projectName, NextSolution, AutoTemplate, MainLang, "Google", ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
        SolutionEdit = PDFFormCheckInstance.Run()
        
    elif FileExtension == 'txt':

        ## T02 TXTMainLangCheck (TXT 언어 체크)
        TXTMainLangCheckInstance = TXTMainLangCheckProcess(email, projectName, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
        SolutionEdit, MainLang = TXTMainLangCheckInstance.Run()

        ## T03 TXTSplit (텍스트 파일 지정 토큰수 분할)
        TXTSplitterInstance = TXTSplitProcess(email, projectName, NextSolution, AutoTemplate, MainLang, Model, "Algorithm", MixedScriptFileDirPath, UploadedScriptFilePath, SolutionEdit, MessagesReview)
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