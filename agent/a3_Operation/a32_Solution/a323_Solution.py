import os
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a32_Solution.a322_Agent import Agent

# ======================================================================
# [a333-1] Operation-Solution
# ======================================================================
# class: Solution
# ======================================================================
class Solution(Agent):

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
    def _CreateInputs(self):
        """... Inputs 생성"""
        # Inputs 초기화
        return [], []


    ## [AbstractMethod] PreprocessResponse: ... Response 전처리 메서드 ##
    def _PreprocessResponse(self):
        """Response 전처리 메서드"""
        pass


    ## [AbstractMethod] ResponsePostprocess: ... Output 메서드 ##
    def _PostprocessResponse(self, SolutionEditProcess):
        """Output을 통한 ..."""
        # Output 스위치
        return True


    ## [AbstractMethod] Output: ... Output 메서드 ##
    def _CreateOutput(self, SolutionEditProcess):
        """Output을 통한 ..."""
        # Output 스위치
        return True