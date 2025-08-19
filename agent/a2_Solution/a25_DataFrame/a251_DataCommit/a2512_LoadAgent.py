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
    def __init__(self, InputList, Email, ProjectName, Solution, ProcessNumber, ProcessName, MainLang = "ko", Model = "OpenAI", Mode = "Master", MessagesReview = "off", SubSolution = None, NextSolution = None, EditMode = "Auto", OutputsPerInput = 1, InputCountKey = None, IgnoreCountCheck = False, FilterPass = False):
        """클래스 초기화"""
        # Process 설정
        self.Email = Email
        self.ProjectName = ProjectName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.NextSolution = NextSolution
        self.ProcessNumber = ProcessNumber
        self.ProcessName = ProcessName
        self.MainLang = MainLang
        self.Model = Model
        self.Mode = Mode
        self.MessagesReview = MessagesReview
        self.EditMode = EditMode
        self.ProcessInfo = f"User: {self.Email} | Solution: {self.Solution}-{self.SubSolution} | Project: {self.ProjectName} | Process: {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # ProjectFrame 경로 설정 (저장된 프로젝트 DataFrame)
        self.SolutionProjectFramePath = self._GetSolutionDataFramePath("ProjectFrame", self.ProjectDataPath)

        # PromptFrame 경로 설정 (저장된 프롬프트 DataFrame)
        self.SolutionPromptFramePath = self._GetSolutionDataFramePath("PromptFrame", self.PromptDataPath)

        # UserProcess 경로 설정
        self.UserProjectSolutionPath = os.path.join(self.StoragePath, self.Email, self.ProjectName, f"{self.ProjectName}_{self.Solution.lower()}")

        # ProjectDataFrame 경로 설정 (스토리지에 생성되는 프로세스 DataFrame)
        self.DataFrameFileDirPath = os.path.join(self.UserProjectSolutionPath, f"{self.ProjectName}_dataframe_{self.Solution.lower()}_file")

        _SolutionProjectDataFramePath = os.path.join(self.DataFrameFileDirPath, f"{self.Email}_{self.ProjectName}_{self.ProcessNumber}_{ProcessName}.json")
        if self.NextSolution:
            self.SolutionProjectDataFramePath = _SolutionProjectDataFramePath.replace('.json', f'({self.NextSolution}).json')
        else:
            self.SolutionProjectDataFramePath = _SolutionProjectDataFramePath
        
        # SolutionEdit 경로 설정 (스토리지에 생성되는 최종 Edit)
        self.MasterFileDirPath = os.path.join(self.UserProjectSolutionPath, f"{self.ProjectName}_master_{self.Solution.lower()}_file")
        _SolutionEditPath = os.path.join(self.MasterFileDirPath, f'[{self.ProjectName}_{self.Solution}_Edit].json')
        if self.NextSolution:
            self.SolutionEditPath = _SolutionEditPath.replace('.json', f'({self.NextSolution}).json')
        else:
            self.SolutionEditPath = _SolutionEditPath

        # InputList 설정
        self.CheckCount = 0
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
    def _GetSolutionDataFramePath(self, DataFrameType, DataFramePath):
        """Solution 및 SubSolution 경로에서 DataFrame을 찾는 메서드"""
        try:
            # Solution이 포함된 첫 번째 디렉터리 찾기
            SolutionDirName = next(Dir for Dir in os.listdir(DataFramePath) 
                                    if self.Solution in Dir and os.path.isdir(os.path.join(DataFramePath, Dir)))
            SolutionDirPath = os.path.join(DataFramePath, SolutionDirName)

            # SubSolution 값의 유무에 따라 최종 검색 경로를 설정
            if self.SubSolution:
                # SubSolution이 있을 경우, 한 단계 더 들어감
                SubSolutionDirName = next(Dir for Dir in os.listdir(SolutionDirPath) 
                                            if self.SubSolution in Dir and os.path.isdir(os.path.join(SolutionDirPath, Dir)))
                print(f"SubSolutionDirName: {SubSolutionDirName}")
                ProjectFrameDirPath = os.path.join(SolutionDirPath, SubSolutionDirName)
            else:
                # SubSolution이 None일 경우, Solution 디렉터리가 최종 경로가 됨
                ProjectFrameDirPath = SolutionDirPath

        except StopIteration:
            # 해당하는 디렉터리를 찾지 못한 경우
            raise FileNotFoundError(f"\n\n[ 아래 경로에서 해당 솔루션 데이터 프레임 파일을 찾을 수 없습니다: {self.Solution} 또는 {self.SubSolution} ]\n{DataFramePath}\n\n")

        # 결정된 최종 디렉터리 내에서 .json 파일 검색
        if DataFrameType == "ProjectFrame":
            FileEndName = ".json"
        elif DataFrameType == "PromptFrame":
            if self.MainLang == "ko":
                FileEndName = "(ko).json"
            else:
                FileEndName = "(global).json"

        for Root, Dirs, Files in os.walk(ProjectFrameDirPath):
            for File in Files:
                # 파일 이름에 ProcessNumber와 ProcessName이 포함되어 있는지 확인
                if File.endswith(FileEndName) and f"{self.ProcessNumber}_{self.ProcessName}" in File:
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
    def _ProcessResponse(self, Input, InputCount, memoryNote = ""):
        """ProcessResponse를 생성하는 메서드"""
        ErrorCount = 0
        while True:
            if self.Model == "OpenAI":
                Response, Usage, Model = OpenAI_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)
            elif self.Model == "Anthropic":
                Response, Usage, Model = ANTHROPIC_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)
            elif self.Model == "Google":
                Response, Usage, Model = GOOGLE_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)
            elif self.Model == "DeepSeek":
                Response, Usage, Model = DEEPSEEK_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)

            # 생성된 Respnse Filler 처리
            FilteredResponse = self._ProcessFilter(Response, self.CheckCount)

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

    ## ProcessFilter 메서드 ##
    def _ProcessFilter(self, Response, ResponseStructure):
        """프로세스 응답에 대한 필터 메서드"""
        # Filter1: JsonLoad
        def JsonLoad(Response):
            try:
                FilteredResponse = json.loads(Response)
                return FilteredResponse
            except json.JSONDecodeError:
                return f"{self.ProcessInfo} | JsonLoadError: 응답 형식이 (Json)이 아닙니다"

        # Filter2: Preprocessing
        ## Preprocessing도 FilterFunc에 포함시킬지 고민

        # Filter3: KeyCheck
        def KeyCheck(FilteredResponse, ResponseStructureDict):
            # TypeMap 정의 및 매핑
            TypeMap = {
                "int": int,
                "str": str,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict
            }
            ValueType = TypeMap.get(ResponseStructureDict['ValueType'])

            if FilteredResponse and ResponseStructureDict['Key'] in FilteredResponse:
                # 문자열 형태의 숫자를 int로 변환
                if ValueType == int and isinstance(FilteredResponse[ResponseStructureDict['Key']], str):
                    if FilteredResponse[ResponseStructureDict['Key']].isdigit() or (FilteredResponse[ResponseStructureDict['Key']].startswith('-') and FilteredResponse[ResponseStructureDict['Key']][1:].isdigit()):
                        try:
                            FilteredResponse[ResponseStructureDict['Key']] = int(FilteredResponse[ResponseStructureDict['Key']])
                        except ValueError:
                            return f"{self.ProcessInfo} | KeyTypeError: ({ResponseStructureDict['Key']}) 키의 데이터 타입이 ({ValueType})가 아닙니다"

                if isinstance(FilteredResponse[ResponseStructureDict['Key']], ValueType):
                    return FilteredResponse
                else:
                    return f"{self.ProcessInfo} | KeyTypeError: ({ResponseStructureDict['Key']}) 키의 데이터 타입이 ({ValueType})가 아닙니다"
            else:
                return f"{self.ProcessInfo} | KeyCheckError: ({ResponseStructureDict['Key']}) 키가 누락되었습니다"

        # Filter4: FilterFunc
        def FilterFunc(FilteredResponse, ResponseStructureDict):
            Value = FilteredResponse[ResponseStructureDict["Key"]]
            for ValueCheckDict in ResponseStructureDict["ValueCheckList"]:
                ValueCheck = ValueCheckDict["ValueCheck"]
                ValueCheckItem = [item.strip() for item in ValueCheckDict['ValueCheckItem'].split(",")]

                # Filter4-1: 벨류가 리스트인 경우 객관식 답의 범주 체크
                if ValueCheck == "listDataAnswerRangeCheck":
                    for value in Value:
                        if value not in ValueCheckItem:
                            return f"{self.ProcessInfo} | ListDataAnswerRangeCheckError: ({value}) 항목은 ({ValueCheckItem})에 포함되지 않습니다"

                # Filter4-2: 벨류가 리스트인 경우 꼭 포함되어야할 데이터 체크
                if ValueCheck == "listDataInclusionCheck":
                    for CheckItem in ValueCheckItem:
                        if CheckItem not in Value:
                            return f"{self.ProcessInfo} | ListDataInclusionCheckError: ({value}) 항목에 ({CheckItem}) 항목이 포함되어야 합니다"

                # Filter4-3: 벨류가 리스트인 경우 꼭 포함되지 말아야할 데이터 체크
                if ValueCheck == "listDataExclusionCheck":
                    for CheckItem in ValueCheckItem:
                        if CheckItem in Value:
                            return f"{self.ProcessInfo} | ListDataExclusionCheckError: ({CheckItem}) 항목이 포함되어서는 안됩니다"

                # Filter4-4: 벨류가 리스트인 경우 리스트의 길이 체크
                if ValueCheck == "listDataLengthCheck":
                    if len(Value) != int(ValueCheckItem[0]):
                        return f"{self.ProcessInfo} | ListDataLengthCheckError: ({Value}) 의 개수는 ({ValueCheckItem[0]}) 개가 되어야 합니다."
                
                # Filter4-5: 벨류가 리스트인 경우 리스트 길이의 범위 체크
                if ValueCheck == "listDataRangeCheck":
                    if not (int(ValueCheckItem[0]) <= len(Value) <= int(ValueCheckItem[1])):
                        return f"{self.ProcessInfo} | ListDataRangeCheckError: ({Value}) 의 개수는 ({ValueCheckItem[0]}) 개 이상 ({ValueCheckItem[1]}) 개 이하이어야 합니다."

                # 벨류가 문자인 경우 객관식 답의 범주 체크
                if ValueCheck == "strDataAnswerRangeCheck":
                    if Value not in ValueCheckItem:
                        return f"{self.ProcessInfo} | StrDataAnswerRangeCheckError: ({Value}) 항목은 ({ValueCheckItem})에 포함되지 않습니다"

                # 벨류가 문자인 경우 꼭 포함되어야할 문자 체크
                if ValueCheck == "strDataInclusionCheck":
                    return FilteredResponse
                
                # 벨류가 문자인 경우 꼭 포함되지 말아야할 문자 체크
                if ValueCheck == "strDataExclusionCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 문자 일치 여부 체크
                if ValueCheck == "strDataSameCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 특수문자 및 공백제외 문자 일치 여부 체크
                if ValueCheck == "strCleanDataSameCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 문자열 길이 일치 여부 체크
                if ValueCheck == "strDataLengthCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 특수문자 및 공백제외 문자열 길이 일치 여부 체크
                if ValueCheck == "strCleanDataLengthCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 문자열 길이의 범위 체크
                if ValueCheck == "strDataRangeCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 문자열 처음과 끝에 존재해야하는 필수 문자 체크
                if ValueCheck == "strDataStartEndCheck":
                    return FilteredResponse

                # 벨류가 문자인 경우 주요 언어 체크
                if ValueCheck == "strLanguageCheck":
                    return FilteredResponse

                # 벨류가 숫자인 경우 수의 범위 체크
                if ValueCheck == "intDataRangeCheck":
                    return FilteredResponse

            # 벨류가 숫자인 경우 수 일치 여부 체크
                if ValueCheck == "intDataSameCheck":
                    return FilteredResponse
                
            return FilteredResponse

        """ResponseStructure에 맞는 필터 실행"""
        # Error1: MainCheck
        # Error1-1: JsonLoad
        FilteredResponse = JsonLoad(Response)
        if isinstance(FilteredResponse, str):
            return FilteredResponse
        
        # Error1-2: Main-KeyCheck
        FilteredResponse = KeyCheck(FilteredResponse, ResponseStructure)
        if isinstance(FilteredResponse, str):
            return FilteredResponse
               
        # Error1-3: Main-FilterFunc
        FilteredResponse = FilterFunc(FilteredResponse, ResponseStructure)
        if isinstance(FilteredResponse, str):
            return FilteredResponse
        
        # Error2: SubCheck
        # Main-ValueType이 dict인 경우
        if ResponseStructure["ValueType"] == "dict":
            SubFilteredResponse = FilteredResponse[ResponseStructure["Key"]]
            for i in range(len(ResponseStructure["Value"])):

                # Error2-2: Sub-KeyCheck
                SubFilteredResponse = KeyCheck(SubFilteredResponse, ResponseStructure["Value"][i])
                if isinstance(SubFilteredResponse, str):
                    return SubFilteredResponse

                # Error2-3: Sub-FilterFunc
                SubFilteredResponse = FilterFunc(SubFilteredResponse, ResponseStructure["Value"][i])
                if isinstance(SubFilteredResponse, str):
                    return SubFilteredResponse
        
        # Main-ValueType이 list인 경우
        if ResponseStructure["ValueType"] == "list":
            for SubFilteredResponse in FilteredResponse["Key"]:
                for i in range(len(ResponseStructure["Value"])):

                    # Error2-2: Sub-KeyCheck
                    SubFilteredResponse = KeyCheck(SubFilteredResponse, ResponseStructure["Value"][i])
                    if isinstance(SubFilteredResponse, str):
                        return SubFilteredResponse

                    # Error2-3: Sub-FilterFunc
                    SubFilteredResponse = FilterFunc(SubFilteredResponse, ResponseStructure["Value"][i])
                    if isinstance(SubFilteredResponse, str):
                        return SubFilteredResponse
        
        # 모든 조건을 만족하면 필터링된 응답 반환
        return FilteredResponse[ResponseStructure["Key"]]

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
                    ProcessResponse = self._ProcessResponse(self, Input, inputCount, memoryNote = "")
                    
                    ## DataFrame 저장
                    self._UpdateProcessDataFrame(self.ProjectName, self.MainLang, Translation, TranslationDataFramePath, ProjectDataFrameWordListGenPath, ProcessResponse, self.ProcessName, inputCount, IndexId, self.TotalInputCount)
                    
            ## Edit 저장
            self._UpdateSolutionEdit(ProjectDataFrameWordListGenPath, TranslationEditPath, Process, EditMode)
            print(f"[ {self.ProcessInfo}Update 완료 ]\n")
            
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
    Email = "yeoreum00128@gmail.com"
    ProjectNameList = ['250807_PDF테스트', '250807_TXT테스트']
    Solution = 'Script'
    SubSolution = 'ScriptUpload'
    ProcessNumber = 'T02'
    ProcessName = 'TXTLanguageCheck'
    NextSolution = 'Translation'
    MessagesReview = 'on'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################
    with open('/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/yeoreum00128@gmail.com/250807_TXT테스트/250807_TXT테스트_script/250807_TXT테스트_dataframe_script_file/yeoreum00128@gmail.com_250807_TXT테스트_T03_TXTSplitFrame(Translation).json', 'r', encoding = 'utf-8') as LoadDataFrameFile:
        LoadFrame = json.load(LoadDataFrameFile)
        InputList = []
        for Input in LoadFrame[1][1:]:
            InputList.append(Input['SplitedText'])

    LoadAgentInstance = LoadAgent(InputList, Email, ProjectNameList[0], Solution, ProcessNumber, ProcessName, MessagesReview = MessagesReview, SubSolution = SubSolution, NextSolution = NextSolution)
    
    Response = """
    {
        "언어": {
            "태그": ["koo", "ja", "lo"]
        }
    }
    """
    ResponseStructure = {
        "Key": "언어",
        "ValueType": "dict",
        "ValueCheckList": [{"ValueCheck": "", "ValueCheckItem": ""}],
        "Value": [
            {
                "Key": "태그",
                "ValueType": "list",
                "ValueCheckList": [{"ValueCheck": "listDataRangeCheck",
                "ValueCheckItem": "1, 2"}],
                "Value": ""
            }
        ]
    }

    FilteredResponse = LoadAgentInstance._ProcessFilter(Response, ResponseStructure)

    print(f"FilteredResponse: {FilteredResponse}")