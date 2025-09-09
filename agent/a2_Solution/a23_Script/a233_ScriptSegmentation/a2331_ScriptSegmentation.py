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
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.Model = Model
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # 업로드 스크립트 파일 확장자
        self.FileExtension = None

        # 경로설정
        self.UploadScriptFilePath = UploadScriptFilePath
        self._InitializePaths()

        # Process 설정
        self._FindAndProcessScriptFile()
        if self.FileExtension == 'pdf':
            self.ProcessNumber = 'P01'
            self.ProcessName = "PDFLoad"
        if self.FileExtension == 'txt':
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
                self.FileExtension = Extension[1:]
                ScriptFileName = f"{self.ProjectName}_Script({self.NextSolution}).{self.FileExtension}"
                self.UploadedScriptFilePath = os.path.join(self.UploadScriptFilePath, ScriptFileName)

                # 파일명이 다르면 표준화된 이름으로 복사
                if ScriptFiles[0] != ScriptFileName:
                    shutil.copy2(RawUploadedScriptFilePath, self.UploadedScriptFilePath)
                    
                FileExistsError = False

        if FileExistsError:
            # txt 또는 pdf 파일이 없으면 오류메세지 출력
            sys.exit(f"\n\n[ 원고 파일(txt, pdf)을 아래 경로에 복사해주세요. ]\n({self.UploadScriptFilePath})\n\n")

    ## 프로세스 정보 Inputs 생성 ##
    def _CreateProcessInfoToInputs(self):
        """ProcessInfo를 생성해서 list 형태로 반환 """
        Inputs = {
            "ProjectName": self.ProjectName,
            "NextSolution": self.NextSolution,
            "AutoTemplate": self.AutoTemplate,
            "FileExtension": self.FileExtension,
            "UploadedScriptFilePath": self.UploadedScriptFilePath
        }

        return [Inputs], [""]

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## ScriptLoadProcess 실행 메서드 ##
    def Run(self):
        """스크립트 로드 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateProcessInfoToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit, self.FileExtension, self.UploadedScriptFilePath, self.UploadScriptFilePath


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
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.Model = Model
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
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
    def _CreatePDFToLabeledSampleJPEGs(self, Page, InputId):
        """PDF 페이지에 '자료번호: InputId' 라벨을 추가한 JPEG 파일을 생성"""
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

    ## 라벨 샘플 경로의 Inputs 생성 ##
    def _CreateLabeledSamplePathToInputs(self):
        """샘플 입력을 생성해서 list 형태로 반환"""
        # 폴더에 JPEG가 5개 이상 있으면 그대로 사용
        if os.path.exists(self.SampleScriptJPEGDirPath):
            ScriptJpegs = sorted(
                f for f in os.listdir(self.SampleScriptJPEGDirPath)
                if f.lower().endswith(".jpeg")
            )
            if len(ScriptJpegs) >= 5:
                Inputs = [
                    os.path.join(self.SampleScriptJPEGDirPath, fn)
                    for fn in ScriptJpegs
                ]
                return [Inputs], [""]

        # 없으면 PDF에서 5페이지 뽑아 라벨 JPEG 생성
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        TotalPages = len(PdfDocument)

        if TotalPages < 5:
            Selected = random.choices(range(TotalPages), k = 5)
        else:
            Selected = random.sample(range(TotalPages), 5)

        os.makedirs(self.SampleScriptJPEGDirPath, exist_ok=True)

        Inputs = []
        for InputId, PageIdx in enumerate(Selected, 1):
            page = PdfDocument.load_page(PageIdx)
            OutPath = self._CreatePDFToLabeledSampleJPEGs(page, InputId)
            Inputs.append(OutPath)

        PdfDocument.close()

        return [Inputs], [""]

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## PDFMainLangCheckProcess 실행 ##
    def Run(self):
        """PDF 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateLabeledSamplePathToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        # MainLang 추출
        MainLang = SolutionEdit[self.ProcessName][0]["MainLang"]

        return SolutionEdit, MainLang


##############################################################
##### P03 PDFLayoutCheck (PDF 인쇄 파일 형식인 단면, 양면 체크) #####
##############################################################
class PDFLayoutCheckProcess:

    ## PDFLayoutCheck 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.Model = Model
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # Process 설정
        self.ProcessNumber = "P03"
        self.ProcessName = "PDFLayoutCheck"
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

    ## PDF 라벨 샘플 이미지 Inputs 생성 ##
    def _LoadPDFToLabeledSampleJPEGToInputs(self):
        """SampleScriptJPEGDirPath에 저장된 JPEG 파일 경로를 리스트로 반환"""
        # SampleScriptJPEGDirPath에 ScriptJPEG 파일 5개 파일명 추출
        ScriptJPEGFiles = sorted([FileName for FileName in os.listdir(self.SampleScriptJPEGDirPath) if FileName.lower().endswith('.jpeg')])

        # SampleScriptJPEGDirPath에 JPEG 파일 5개 경로 Inputs 생성 및 리턴
        Inputs = []
        for FileName in ScriptJPEGFiles:
            FilePath = os.path.join(self.SampleScriptJPEGDirPath, FileName)
            Inputs.append(FilePath)

        return [Inputs], [""]

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## PDFLayoutCheckProcess 실행 ##
    def Run(self):
        """PDF 인쇄 파일 형식인 단면, 양면 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._LoadPDFToLabeledSampleJPEGToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


#####################################################
##### P04 PDFResize (PDF 파일 가로 재단) #####
#####################################################
class PDFResizeProcess:

    ## PDFResize 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.Model = Model
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # Process 설정
        self.ProcessNumber = "P04"
        self.ProcessName = "PDFResize"
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
        self.TrimScriptJPEGDirPath = os.path.join(self.UploadScriptFilePath, f"{self.ProjectName}_TrimScript({self.NextSolution})_jpeg")
        os.makedirs(self.TrimScriptJPEGDirPath, exist_ok = True)
        self.FontDirPath = "/usr/share/fonts/"
        self.NotoSansCJKRegular = os.path.join(self.FontDirPath, "opentype/noto/NotoSansCJK-Regular.ttc")

    ## PDF 방향별 보조선 샘플 이미지 생성 ##
    def _CreatePDFToTrimLineJPEGs(self, Page, InputId):
        """PDF 페이지에서 보조선 샘플 이미지를 생성"""
        Pixmap = Page.get_pixmap(dpi=150)
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
        self.IntervalRatio = 0.03  # 간격 비율 (전체 크기에 대한 비율)
        LineWidth          = max(1, int(2 * Scale))
        IntervalY          = max(1, int(BaseImg.height * self.IntervalRatio))
        IntervalX          = max(1, int(BaseImg.width  * self.IntervalRatio))
        NumberPad          = int(3 * Scale)
        NumberBaselineLift = int(2 * Scale)
        RoundedRadius      = max(2, int(6 * Scale))
        LabelGap           = int(8 * Scale)    # 라벨과 선 사이 간격
        ExtraMargin        = int(15 * Scale)   # 추가 여유

        CircledNums = ["","①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩"]

        Padding = int(14 * Scale)
        BorderW = max(2, int(4 * Scale))

        if self.MainLang == "ko":
            DirLabelMap = {"Left":"자료방향: 좌","Right":"자료방향: 우","Up":"자료방향: 위","Down":"자료방향: 아래"}
            MultiDirSuffix = "네방향"
        else:
            DirLabelMap = {"Left":"Direction: Left","Right":"Direction: Right","Up":"Direction: Up","Down":"Direction: Down"}
            MultiDirSuffix = "FourDirections"

        FilenameSuffix = {"Left":"Left","Right":"Right","Up":"Up","Down":"Down"}

        # 방향별 색상 매핑
        DirectionColors = {
            "Left":  (255,   0,   0),  # 빨강
            "Right": (  0,   0, 255),  # 파랑
            "Up":    (  0, 128,   0),  # 녹색(가독성 위해 약간 어둡게)
            "Down":  (255, 215,   0),  # 노랑(골드 톤으로 가독성↑)
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

        def DrawTextWithWhiteBgCenter(
            Draw, CenterXY, Text, Font, Pad=NumberPad, Rounded=True, BaselineLift=0, text_fill="red"
        ):
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
            # 텍스트 크기 산출
            TextBBox = LabelFont.getbbox(LabelText)
            Tw = TextBBox[2] - TextBBox[0]
            Th = TextBBox[3] - TextBBox[1]
            LabelW = Tw + 2*Padding
            LabelH = Th + 2*Padding
            LabelImg = Image.new("RGB", (LabelW, LabelH), "white")
            LDraw = ImageDraw.Draw(LabelImg)
            # 외곽선
            LDraw.rectangle([(0,0),(LabelW-1,LabelH-1)], outline="black", width=BorderW)
            # 중앙 정렬 (세로 살짝 올림)
            Tx = (LabelW - Tw)//2
            Ty = (LabelH - Th)//2 + int(-0.3 * LabelFontSize)
            Ty = max(Padding//2, min(Ty, LabelH - Th - Padding//2))
            LDraw.text((Tx, Ty), LabelText, font=LabelFont, fill="black")
            return LabelImg

        def DrawDirection(Img, Direction, Color):
            Draw = ImageDraw.Draw(Img)
            ImgCx = Img.width // 2
            ImgCy = Img.height // 2

            if Direction == "Up":
                for i in range(1, 11):
                    y = i * IntervalY
                    Draw.line([(0, y), (Img.width, y)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(
                        Draw, (ImgCx, y), CircledNums[i], NumberFont,
                        Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color
                    )

            elif Direction == "Down":
                for i in range(1, 11):
                    y = Img.height - (i * IntervalY)
                    Draw.line([(0, y), (Img.width, y)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(
                        Draw, (ImgCx, y), CircledNums[i], NumberFont,
                        Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color
                    )

            elif Direction == "Left":
                for i in range(1, 11):
                    x = i * IntervalX
                    Draw.line([(x, 0), (x, Img.height)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(
                        Draw, (x, ImgCy), CircledNums[i], NumberFont,
                        Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color
                    )

            elif Direction == "Right":
                for i in range(1, 11):
                    x = Img.width - (i * IntervalX)
                    Draw.line([(x, 0), (x, Img.height)], fill=Color, width=LineWidth)
                    DrawTextWithWhiteBgCenter(
                        Draw, (x, ImgCy), CircledNums[i], NumberFont,
                        Pad=NumberPad, Rounded=True, BaselineLift=NumberBaselineLift, text_fill=Color
                    )

        def SaveImage(Img, SuffixText):
            OutName = f"{self.ProjectName}_HTrimScript({self.NextSolution})({InputId})({SuffixText}).jpeg"
            OutPath = os.path.join(self.TrimScriptJPEGDirPath, OutName)
            Img.save(OutPath, "JPEG", quality=92, optimize=True, progressive=True, subsampling=1)
            return OutPath

        OutputPaths = []

        if self.ResponseMethod == "Prompt":
            # 방향별로 개별 저장 + 중앙 라벨 (각 방향 색상 적용)
            for DirKey in ["Left", "Right", "Up", "Down"]:
                Img = BaseImg.copy()
                DrawDirection(Img, DirKey, DirectionColors[DirKey])
                # 중앙 라벨
                CenterLabel = MakeLabelImage(DirLabelMap[DirKey])
                Px = (Img.width - CenterLabel.width)//2
                Py = (Img.height - CenterLabel.height)//2
                Img.paste(CenterLabel, (Px, Py))
                OutPath = SaveImage(Img, FilenameSuffix[DirKey])
                OutputPaths.append(OutPath)
        if self.ResponseMethod == "Manual":
            # 한 장에 4방향 모두 + 라벨 4개 '안쪽' 배치 (선과 절대 겹치지 않도록), 방향별 색 적용
            Img = BaseImg.copy()
            for DirKey in ["Left", "Right", "Up", "Down"]:
                DrawDirection(Img, DirKey, DirectionColors[DirKey])

            # ---- 라벨 위치 계산 (⑩번째 선 기준) ----
            LabelInnerOffset = LabelGap + LineWidth + NumberPad + ExtraMargin  # 선/숫자와 라벨 간 충분한 이격

            # Up: y = 10*IntervalY → 그 "아래(안쪽)"에 라벨, 180°
            up_y10 = 10 * IntervalY
            up_label = MakeLabelImage(DirLabelMap["Up"]).rotate(180, expand=True)
            up_px = (Img.width - up_label.width) // 2
            up_py = up_y10 + LabelInnerOffset
            up_py = min(max(0, up_py), Img.height - up_label.height)
            Img.paste(up_label, (up_px, up_py))

            # Down: y = Img.height - 10*IntervalY → 그 "위(안쪽)"에 라벨, 0°
            down_y10 = Img.height - 10 * IntervalY
            down_label = MakeLabelImage(DirLabelMap["Down"])
            down_px = (Img.width - down_label.width) // 2
            down_py = down_y10 - LabelInnerOffset - down_label.height
            down_py = min(max(0, down_py), Img.height - down_label.height)
            Img.paste(down_label, (down_px, down_py))

            # Left: x = 10*IntervalX → 그 "오른쪽(안쪽)"에 라벨, 270°
            left_x10 = 10 * IntervalX
            left_label = MakeLabelImage(DirLabelMap["Left"]).rotate(270, expand=True)
            left_px = left_x10 + LabelInnerOffset
            left_px = min(max(0, left_px), Img.width - left_label.width)
            left_py = (Img.height - left_label.height) // 2
            Img.paste(left_label, (left_px, left_py))

            # Right: x = Img.width - 10*IntervalX → 그 "왼쪽(안쪽)"에 라벨, 90°
            right_x10 = Img.width - 10 * IntervalX
            right_label = MakeLabelImage(DirLabelMap["Right"]).rotate(90, expand=True)
            right_px = right_x10 - LabelInnerOffset - right_label.width
            right_px = min(max(0, right_px), Img.width - right_label.width)
            right_py = (Img.height - right_label.height) // 2
            Img.paste(right_label, (right_px, right_py))

            OutPath = SaveImage(Img, MultiDirSuffix)
            OutputPaths.append(OutPath)
        
        return OutputPaths

    ## 방향별 보조선 샘플 이미지 Inputs 생성 ##
    def _CreateTrimLineJPEGToInputs(self):
        """PDF에서 최대 10개 페이지를 뽑아 각 페이지마다 방향별 보조선 샘플 이미지 4개 생성"""
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
                            "CropLineDirection": "Up",
                            "BodyCropLineNumber": 0
                        },
                        {
                            "CropLineDirection": "Down",
                            "BodyCropLineNumber": 0
                        }
                    ]
                ]
            ComparisonInputs = [""]
            for InputId, PageIndex in enumerate(SelectedPageIndices, 1):
                page = PdfDocument.load_page(PageIndex)
                OutputPaths = self._CreatePDFToTrimLineJPEGs(page, InputId)
            
        PdfDocument.close()

        return Inputs, ComparisonInputs

    ## Output을 통한 PDF 재단 ##
    def _CreateOutputToPDFCrop(self, SolutionEditProcess):
        """Response 결과에 따른 PDF를 재단"""
        # SolutionEditProcess값 중 가장 빈도가 높은 값 구하기
        LeftNumberList = []
        RightNumberList = []
        UpNumberList = []
        DownNumberList = []
        for SolutionEditProcessDic in SolutionEditProcess:
            for SolutionEditProcessDicItem in SolutionEditProcessDic:
                CropLineDirection = SolutionEditProcessDicItem['CropLineDirection']
                if CropLineDirection == 'Left':
                    LeftNumberList.append(SolutionEditProcessDicItem["BodyCropLineNumber"])
                elif CropLineDirection == 'Right':
                    RightNumberList.append(SolutionEditProcessDicItem["BodyCropLineNumber"])
                elif CropLineDirection == 'Up':
                    UpNumberList.append(SolutionEditProcessDicItem["BodyCropLineNumber"])
                elif CropLineDirection == 'Down':
                    DownNumberList.append(SolutionEditProcessDicItem["BodyCropLineNumber"])

        LeftNumber = max(set(LeftNumberList), key=LeftNumberList.count)
        RightNumber = max(set(RightNumberList), key=RightNumberList.count)
        UpNumber = max(set(UpNumberList), key=UpNumberList.count)
        DownNumber = max(set(DownNumberList), key=DownNumberList.count)

        # PDF 재단
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        for PdfPage in PdfDocument:
            rect = PdfPage.rect
            w, h = rect.width, rect.height

            dx = w * self.IntervalRatio
            dy = h * self.IntervalRatio

            left = rect.x0 + (LeftNumber * dx)
            right = rect.x1 - (RightNumber * dx)
            top = rect.y0 + (UpNumber * dy)
            bottom = rect.y1 - (DownNumber * dy)

            # 좌표 유효성 보정 (경계 안쪽으로 클램프)
            left = max(rect.x0, min(left, rect.x1))
            right = max(rect.x0, min(right, rect.x1))
            top = max(rect.y0, min(top, rect.y1))
            bottom = max(rect.y0, min(bottom, rect.y1))
            CropRect = fitz.Rect(left, top, right, bottom)

            # 항상 적용
            PdfPage.set_cropbox(CropRect)
            PdfPage.set_mediabox(CropRect)

        # 같은 경로에 덮어쓰기 저장
        PdfDocument.save(self.UploadedScriptFilePath, garbage=4, deflate=True)
        PdfDocument.close()

    ## PDFResizeProcess 실행 ##
    def Run(self):
        """PDF 가로 재단 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateTrimLineJPEGToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutputToPDFCrop(), MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


##########################################
##### P05 PDFSplit (PDF 페이지 별 분할) #####
##########################################
class PDFSplitProcess:

    ## PDFSplit 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        # Process 설정
        self.ProcessNumber = 'P05'
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
        self.SplitScriptPDFDirPath = os.path.join(self.UploadScriptFilePath, f"{self.ProjectName}_Script({self.NextSolution})_pdf")
        os.makedirs(self.SplitScriptPDFDirPath, exist_ok = True)

    ## PDF 파일을 페이지별로 분할 및 저장 및 Inputs 생성 ##
    def _SplitPDFToInputs(self):
        """PDF 파일을 페이지별로 분할하고 저장"""
        # PDF 파일 읽고 총 페이지 수 계산
        Reader = PdfReader(self.UploadedScriptFilePath)
        TotalPages = len(Reader.pages)
        
        # 각 페이지를 개별 PDF 파일로 저장 및 Inputs 생성
        Inputs = []
        ComparisonInputs = []
        for PageNum in range(TotalPages):
            Writer = PdfWriter()
            Writer.add_page(Reader.pages[PageNum])
            
            OutputFileName = f"{self.ProjectName}_Script({self.NextSolution})({PageNum + 1}).pdf"
            OutputFilePath = os.path.join(self.SplitScriptPDFDirPath, OutputFileName)
            
            # 페이지별 PDF 파일 저장
            with open(OutputFilePath, "wb") as OutputFile:
                Writer.write(OutputFile)
            # 페이지별 파일 경로를 리스트에 추가
            Inputs.append(
                {
                    "ScriptId": PageNum + 1,
                    "PageFilePath": OutputFilePath
                }
            )
            ComparisonInputs.append("")

        return Inputs, ComparisonInputs

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## PDFSplitProcess 실행 ##
    def Run(self):
        """PDF 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._SplitPDFToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


####################################################
##### #P06 PDFFormCheck (PDF 파일 페이지 형식 체크) #####
####################################################
class PDFFormCheckProcess:

    ## PDFFormCheck 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.Model = Model
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # Process 설정
        self.ProcessNumber = "P06"
        self.ProcessName = "PDFFormCheck"
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

    ## 라벨된 JPEG 경로의 Inputs 생성 ##
    def _CreateLabeledJPEGsToInputs(self):
        """라벨된 JPEG 경로 목록을 기반으로, 5개를 선택하여 리스트를 반환"""
        # PdfDocument 열어서 라벨 JPEG 생성 후 경로 리스트 확보
        PdfDocument = fitz.open(self.UploadedScriptFilePath)
        OutputPathList = self._CreatePDFToLabeledJPEGs(PdfDocument)  # list[str]
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

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## PDFFormCheckProcess 실행 ##
    def Run(self):
        """PDF 페이지 형식 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateLabeledJPEGsToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit

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
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.Model = Model
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.UploadedScriptFilePath = UploadedScriptFilePath

        # Process 설정
        self.ProcessNumber = "T02"
        self.ProcessName = "TXTMainLangCheck"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # 출력설정
        self.MessagesReview = MessagesReview

    ## TXT 샘플 생성 ##
    def _CreateTXTToSampleTextToInputs(self):
        """텍스트 파일에서 3개의 샘플 텍스트를 추출하여 하나의 문자열로 반환하는 메서드"""
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

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## TXTMainLangCheckProcess 실행 ##
    def Run(self):
        """TXT 언어 체크 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._CreateTXTToSampleTextToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        # MainLang 추출
        MainLang = SolutionEdit[self.ProcessName][0]["MainLang"]

        return SolutionEdit, MainLang


##########################################
##### T03 TXTSplit (TXT 토큰 단위 분할) #####
##########################################
class TXTSplitProcess:

    ## TXTSplit 초기화 ##
    def __init__(self, Email, ProjectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview):
        """클래스 초기화"""
        # 업데이트 정보
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.AutoTemplate = AutoTemplate
        self.MainLang = MainLang
        self.ResponseMethod = ResponseMethod
        self.EditMode = "Auto"
        if self.ResponseMethod == "Manual":
            self.EditMode = self.ResponseMethod
        self.UploadedScriptFilePath = UploadedScriptFilePath
        
        # Process 설정
        self.ProcessNumber = 'T03'
        self.ProcessName = "TXTSplit"
        self.ProcessInfo = f"User: {self.Email} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"
        
        # 언어별 MaxTokens 설정
        self.MainLang = MainLang
        self.BaseTokens = 3000
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

    ## TXT 파일을 지정된 토큰 수에 가깝게 문장 묶음으로 분할 및 Inputs 생성 ##
    def _SplitTXTToInputs(self):
        """TXT 파일을 지정된 글자 수(공백 포함)에 가깝게 문장 묶음으로 분할 (공백/줄바꿈 유지)"""
        # Spacy 모델 로드
        nlp = self._LoadSpacyModel()
        
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

    ## Output을 통한 ... ##
    def _CreateOutput(self):
        return None

    ## TXTSplitProcess 실행 ##
    def Run(self):
        """TXT 분할 전체 프로세스 실행"""
        print(f"< {self.ProcessInfo} Update 시작 >")
        LoadAgentInstance = LoadAgent(self._SplitTXTToInputs(), self.Email, self.ProjectName, self.Solution, self.ProcessNumber, self.ProcessName, MainLang = self.MainLang, Model = self.Model, ResponseMethod = self.ResponseMethod, OutpitFunc = self._CreateOutput, MessagesReview = self.MessagesReview, SubSolution = self.SubSolution, NextSolution = self.NextSolution, EditMode = self.EditMode, AutoTemplate = self.AutoTemplate)
        SolutionEdit = LoadAgentInstance.Run()

        return SolutionEdit


################################
##### Process 진행 및 업데이트 #####
################################
## ScriptSegmentation 프롬프트 요청 및 결과물 Json화
def ScriptSegmentationProcessUpdate(projectName, email, NextSolution, AutoTemplate, MessagesReview = "on"):
    ## 솔루션 정의
    Solution = "Script"
    SubSolution = "ScriptSegmentation"
    MainLang = "ko"
    Model = "OpenAI"
    ResponseMethod = "Prompt"
    
    ## PT01 통합: (PDF)ScriptLoad (업로드 된 스크립트 파일 확인)
    ScriptLoadInstance = ScriptLoadProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, "Algorithm", None, None, MessagesReview)
    SolutionEdit, FileExtension, UploadedScriptFilePath, UploadScriptFilePath = ScriptLoadInstance.Run()

    ## 파일 확장자에 따라 후속 프로세스 실행
    if FileExtension == 'pdf':

        ## P02 PDFMainLangCheck (PDF 언어 체크)
        PDFMainLangCheckProcessInstance = PDFMainLangCheckProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit, MainLang = PDFMainLangCheckProcessInstance.Run()
        
        ## P03 PDFLayoutCheck (PDF 인쇄 파일 형식인 단면, 양면 체크) <- 여기서 페이지 분할 동시 진행
        PDFLayoutCheckInstance = PDFLayoutCheckProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit = PDFLayoutCheckInstance.Run()
        
        ## P04 PDFResize (PDF 파일 재단)
        PDFResizeInstance = PDFResizeProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, "Google", "Manual", UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit = PDFResizeInstance.Run()
        
        ## P05 PDFSplit (PDF 파일 페이지 분할)
        PDFSplitterInstance = PDFSplitProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, "Algorithm", UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit = PDFSplitterInstance.Run()

        ## P06 PDFFormCheck (PDF 파일 페이지 형식 체크)
        PDFFormCheckInstance = PDFFormCheckProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, "Google", ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit = PDFFormCheckInstance.Run()
        
    elif FileExtension == 'txt':

        # T02 TXTMainLangCheck (TXT 언어 체크)
        TXTMainLangCheckInstance = TXTMainLangCheckProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, ResponseMethod, UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
        SolutionEdit, MainLang = TXTMainLangCheckInstance.Run()

        # T03 TXTSplit (텍스트 파일 지정 토큰수 분할)
        TXTSplitterInstance = TXTSplitProcess(email, projectName, Solution, SubSolution, NextSolution, AutoTemplate, MainLang, Model, "Algorithm", UploadedScriptFilePath, UploadScriptFilePath, MessagesReview)
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