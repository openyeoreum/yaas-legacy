import os
import shutil
import json
import time
import spacy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter
from agent.a2_Solution.a25_DataFrame.a251_DataCommit.a2511_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse, GOOGLE_LLMresponse, DEEPSEEK_LLMresponse

#############################################
##### LoadAgent (업로드 된 스크립트 파일 확인) #####
#############################################
class LoadAgent:

    ## 기본 경로 정의 ##
    StoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    ProjectDataPath = "/yaas/agent/a5_Database/a53_ProjectData"
    PromptDataPath = "/yaas/agent/a5_Database/a54_PromptData"

    ## LoadAgent 초기화 ##
    def __init__(self, InputList, Email, ProjectName, Solution, ProcessNumber, ProcessName, MainLang = "ko", Model = "OpenAI", Mode = "Master", MessagesReview = "off", SubSolution = None, SolutionTag = None, EditMode = "Auto", OutputsPerInput = 1, InputCountKey = None, IgnoreCountCheck = False, FilterPass = False):
        """클래스 초기화"""
        # Process 설정
        self.Email = Email
        self.ProjectName = ProjectName
        self.ProcessNumber = ProcessNumber
        self.ProcessName = ProcessName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.EditMode = EditMode
        self.ProcessInfo = f"User: {self.Email} | Solution: {self.Solution}-{self.SubSolution} | Project: {self.ProjectName} | Process: {self.ProcessNumber}_{self.ProcessName}({self.Solution})"
        self.MainLang = MainLang
        self.Model = Model
        self.Mode = Mode
        self.MessagesReview = MessagesReview

        # ProjectFrame 경로 설정 (저장된 프로젝트 DataFrame)
        self.SolutionProjectFramePath = self._GetSolutionDataFramePath(self.ProjectDataPath, self.Solution, self.SubSolution)

        # PromptFrame 경로 설정 (저장된 프롬프트 DataFrame)
        self.SolutionPromptFramePath = self._GetSolutionDataFramePath(self.PromptDataPath, self.Solution, self.SubSolution)

        # UserProcess 경로 설정
        self.UserProjectSolutionPath = os.path.join(self.StoragePath, self.Email, self.ProjectName, f"{self.ProjectName}_{self.Solution.lower()}")

        # ProjectDataFrame 경로 설정 (스토리지에 생성되는 프로세스 DataFrame)
        self.DataFrameFileDirPath = os.path.join(self.UserProjectSolutionPath, f"{self.ProjectName}_dataframe_{self.Solution.lower()}_file")

        _SolutionProjectDataFramePath = os.path.join(self.DataFrameFileDirPath, f"{self.Email}_{self.ProjectName}_{self.ProcessNumber}_{ProcessName}.json")
        if SolutionTag:
            self.SolutionProjectDataFramePath = _SolutionProjectDataFramePath.replace('.json', f'({SolutionTag}).json')
        else:
            self.SolutionProjectDataFramePath = _SolutionProjectDataFramePath
        
        # SolutionEdit 경로 설정 (스토리지에 생성되는 최종 Edit)
        self.MasterFileDirPath = os.path.join(self.UserProjectSolutionPath, f"{self.ProjectName}_master_{self.Solution.lower()}_file")
        _SolutionEditPath = os.path.join(self.MasterFileDirPath, f'[{self.ProjectName}_{self.Solution}_Edit].json')
        if SolutionTag:
            self.SolutionEditPath = _SolutionEditPath.replace('.json', f'({SolutionTag}).json')
        else:
            self.SolutionEditPath = _SolutionEditPath

        # InputList 설정
        self.InputList = InputList
        self.TotalInputCount = len(self.InputList)

        # InputCount 및 DataFrameCompletion 설정
        self.InputCount, self.DataFrameCompletion = self._ProcessDataFrameCheck()

        # EditCheck 및 EditCompletion 설정
        self.OutputsPerInput = OutputsPerInput # 출력 배수 설정 (하나의 인풋으로 몇개의 아웃풋이 출력되는지 확인)
        self.InputCountKey = InputCountKey # 입력 수의 기준키 설정 (InputCount의 수가 단순 데이터 리스트의 총 개수랑 맞지 않는 경우)
        self.IgnoreCountCheck = IgnoreCountCheck # 입력 수 체크 안함 (입력의 카운트가 의미가 없는 경우 예시로 IndexDefine 등)
        self.FilterPass = FilterPass # 핃터 오류 3회가 넘어가는 경우 그냥 패스 (에러의 수준이 글자 1000자 중 1자 수준으로 매우 작으나, Response 오류 회수가 너무 빈번한 경우 예시로 TranslationProofreading 등)
        self.EditCheck, self.EditCompletion = self._SolutionEditCheck(OutputsPerInput, InputCountKey, IgnoreCountCheck)

    ## Solution 및 SubSolution 경로에서 DataFrame 경로 가져오기 메서드 ##
    def _GetSolutionDataFramePath(self, DataFramePath, Solution, SubSolution):
        """Solution 및 SubSolution 경로에서 DataFrame을 찾는 메서드"""
        try:
            # Solution이 포함된 첫 번째 디렉터리 찾기
            SolutionDirName = next(Dir for Dir in os.listdir(DataFramePath) 
                                    if Solution in Dir and os.path.isdir(os.path.join(DataFramePath, Dir)))
            SolutionDirPath = os.path.join(DataFramePath, SolutionDirName)

            # SubSolution 값의 유무에 따라 최종 검색 경로를 설정
            if SubSolution:
                # SubSolution이 있을 경우, 한 단계 더 들어감
                SubSolutionDirName = next(Dir for Dir in os.listdir(SolutionDirPath) 
                                            if SubSolution in Dir and os.path.isdir(os.path.join(SolutionDirPath, Dir)))
                ProjectFrameDirPath = os.path.join(SolutionDirPath, SubSolutionDirName)
            else:
                # SubSolution이 None일 경우, Solution 디렉터리가 최종 경로가 됨
                ProjectFrameDirPath = SolutionDirPath

        except StopIteration:
            # 해당하는 디렉터리를 찾지 못한 경우
            raise FileNotFoundError(f"\n\n[ 아래 경로에서 해당 솔루션 데이터 프레임 파일을 찾을 수 없습니다: {Solution} 또는 {SubSolution} ]\n{DataFramePath}\n\n")

        # 결정된 최종 디렉터리 내에서 .json 파일 검색
        for Root, Dirs, Files in os.walk(ProjectFrameDirPath):
            for File in Files:
                # 파일 이름에 ProcessNumber와 ProcessName이 포함되어 있는지 확인
                if File.endswith('.json') and f"{self.ProcessNumber}_{self.ProcessName}" in File:
                    return os.path.join(Root, File) # 파일을 찾으면 즉시 경로 반환
        
        # 루프를 모두 순회했으나 파일을 찾지 못한 경우
        raise FileNotFoundError(f"\n\n[ 아래 경로에서 해당 데이터 프레임 파일을 찾을 수 없습니다: {self.ProcessNumber}_{self.ProcessName} ]\n{ProjectFrameDirPath}\n\n")

    ## 프로세스 DataFrame의 파일, 카운트, 완료 체크 메서드 ##
    def _ProcessDataFrameCheck(self):
        """프로세스 DataFrame이 존재하는지 확인하고, InputCount와 DataFrameCompletion을 반환하는 메서드"""
        # InputCount 및 DataFrameCompletion 초기화
        InputCount = 1
        DataFrameCompletion = 'No'

        # SolutionProjectDataFramePath가 존재하지 않는 경우
        if not os.path.exists(self.SolutionProjectDataFramePath):
            return InputCount, DataFrameCompletion
        else:
            ## Process Edit 불러오기
            with open(self.SolutionProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
                olutionProjectDataFrame = json.load(DataFrameJson)
            
            ## InputCount 및 DataFrameCompletion 확인
            NextInputCount = olutionProjectDataFrame[0]['InputCount'] + 1
            DataFrameCompletion = olutionProjectDataFrame[0]['Completion']
            
            return NextInputCount, DataFrameCompletion

    ## 솔루션 Edit의 파일, 완료 체크 메서드 ##
    def _SolutionEditCheck(self, OutputsPerInput = 1, InputCountKey = None, IgnoreCountCheck = False):
        """프로세스 Edit 및 Completion을 확인하는 메서드"""
        # EditCheck 및 EditCompletion 초기화
        EditCheck = False
        EditCompletion = False

        # SolutionEdit 경로가 존재하는지 확인 후 불러오기
        if os.path.exists(self.SolutionEditPath):
            # '[...Edit].json' 확인
            with open(self.SolutionEditPath, 'r', encoding = 'utf-8') as SolutionEditJson:
                SolutionEdit = json.load(SolutionEditJson)
            
            # 입력 수 체크 안함 (입력의 카운트가 의미가 없는 경우 예시로 IndexDefine 등)
            if IgnoreCountCheck:
                if self.ProcessName in SolutionEdit.keys():
                    EditCheck = True

                    # 'ProcessCompletion' 확인
                    if SolutionEdit[f"{self.ProcessName}Completion"] == 'Completion':
                        EditCompletion = True
            else:
                # 입력 수의 기준키 설정 (InputCount의 수가 단순 데이터 리스트의 총 개수랑 맞지 않는 경우)
                if InputCountKey:
                    if self.ProcessName in SolutionEdit.keys() and SolutionEdit[self.ProcessName][-1][InputCountKey] == self.TotalInputCount * OutputsPerInput:
                        EditCheck = True

                        # 'ProcessCompletion' 확인
                        if SolutionEdit[f"{self.ProcessName}Completion"] == 'Completion':
                            EditCompletion = True
                # 일반적인 입력 수 체크
                else:
                    if self.ProcessName in SolutionEdit and len(SolutionEdit[self.ProcessName]) == self.TotalInputCount * OutputsPerInput:
                        EditCheck = True

                        # 'ProcessCompletion' 확인
                        if SolutionEdit[f"{self.ProcessName}Completion"] == 'Completion':
                            EditCompletion = True
            
        return EditCheck, EditCompletion

    ## ProcessResponse 생성 메서드 ##
    def _ProcessResponse(self, Input, InputCount, CheckCount, memoryCounter = ""):
        """ProcessResponse를 생성하는 메서드"""
        ErrorCount = 0
        while True:
            if self.Model == "OpenAI":
                Response, Usage, Model = OpenAI_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryCounter = memoryCounter, messagesReview = self.MessagesReview)
            elif self.Model == "Anthropic":
                Response, Usage, Model = ANTHROPIC_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryCounter = memoryCounter, messagesReview = self.MessagesReview)
            elif self.Model == "Google":
                Response, Usage, Model = GOOGLE_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryCounter = memoryCounter, messagesReview = self.MessagesReview)
            elif self.Model == "DeepSeek":
                Response, Usage, Model = DEEPSEEK_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryCounter = memoryCounter, messagesReview = self.MessagesReview)

            # 생성된 Respnse Filler 처리
            FilteredResponse = self._ProcessFilter(Response, CheckCount)

            # 필터 에외처리, JSONDecodeError 처리
            if isinstance(FilteredResponse, str):
                print(f"{self.ProcessInfo} | {InputCount}/{self.TotalInputCount} | {FilteredResponse}")
                ErrorCount += 1
                print(f"{self.ProcessInfo} | {InputCount}/{self.TotalInputCount} | "
                    f"오류횟수 {ErrorCount}회, 10초 후 프롬프트 재시도")
                
                ## Error 3회시 해당 프로세스 사용 안함 예외처리
                if self.FilterPass and ErrorCount >= 3:
                    print(f"{self.ProcessInfo} | {InputCount}/{self.TotalInputCount} | ErrorPass 완료")
                    return "ErrorPass"
                
                if ErrorCount >= 10:
                    sys.exit(f"{self.ProcessInfo} | {InputCount}/{self.TotalInputCount} | 오류횟수 {ErrorCount}회 초과, 프롬프트 종료")
                time.sleep(10)
                continue
            
            print(f"{self.ProcessInfo} | {InputCount}/{self.TotalInputCount} | JSONDecode 완료")
            return FilteredResponse

    ##
    def _ProcessFilter(self):
        """"""

    ##
    def _UpdateProcessDataFrame(self):
        """"""

    ##
    def _UpdateSolutionEdit(self):
        """"""

    ##
    def Run(self):
        """프로세스 실행 메서드"""
        if not self.EditCheck:
            if self.DataFrameCompletion == 'No':
                for i in range(self.InputCount - 1, self.TotalInputCount):
                    ## Input 생성
                    inputCount = self.InputList[i]['Id']
                    IndexId = self.InputList[i]['IndexId']
                    Input = self.InputList[i]['Input']
                    
                    ## ProcessResponse 생성
                    ProcessResponse = self._ProcessResponse(self, Input, inputCount, CheckCount, memoryCounter = "")
                    
                    ## DataFrame 저장
                    self._UpdateProcessDataFrame(self.ProjectName, self.MainLang, Translation, TranslationDataFramePath, ProjectDataFrameWordListGenPath, ProcessResponse, self.ProcessName, inputCount, IndexId, self.TotalInputCount)
                    
            ## Edit 저장
            self._UpdateSolutionEdit(ProjectDataFrameWordListGenPath, TranslationEditPath, Process, EditMode)
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update 완료 ]\n")
            
            if EditMode == "Manual":
                sys.exit(f"[ {projectName}_Script_Edit 생성 완료 -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")

        if EditMode == "Manual":
            if EditCheck:
                if not EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {projectName}_Script_Edit -> {Process}: (({Process}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({Process}Completion: Completion))으로 변경 ]\n\n{TranslationEditPath}")
        if EditCompletion:
            print(f"[ User: {email} | Project: {projectName} | {ProcessNumber}_{Process}Update는 이미 완료됨 ]\n")

    
    ## Process Count 계산 및 Check ##

    ## Process 진행 ##


if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectNameList = ['250807_PDF테스트', '250807_TXT테스트']
    Solution = 'Translation'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################

    LoadAgentInstance = LoadAgent(
        InputList = [],
        Email = email,
        ProjectName = projectNameList[0],
        Solution = Solution,
        ProcessNumber = "P01",
        ProcessName = "PDFLoadFrame",
        MainLang = "ko",
        Model = "OpenAI",
        Mode = "Master",
        MessagesReview = "off",
        SubSolution = None,
        SolutionTag = None,
        EditMode = "Auto",
        OutputsPerInput = 1,
        InputCountKey = None,
        IgnoreCountCheck = False,
        FilterPass = False
    )