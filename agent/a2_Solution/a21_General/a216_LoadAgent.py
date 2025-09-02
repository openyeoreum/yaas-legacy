import os
import re
import shutil
import json
import time
import spacy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter
from agent.a2_Solution.a21_General.a215_LoadLLM import OpenAI_LLMresponse, ANTHROPIC_LLMresponse, GOOGLE_LLMresponse, DEEPSEEK_LLMresponse

#############################################
##### LoadAgent (업로드 된 스크립트 파일 확인) #####
#############################################
class LoadAgent:

    ## 기본 경로 정의 ##
    StoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    ProjectDataPath = "/yaas/agent/a5_Database/a53_ProjectData"
    PromptDataPath = "/yaas/agent/a5_Database/a54_PromptData"

    ## LoadAgent 초기화 ##
    def __init__(self, InputList, Email, ProjectName, Solution, ProcessNumber, ProcessName, MainLang = "ko", Model = "OpenAI", Mode = "Master", MessagesReview = "off", SubSolution = None, NextSolution = None, EditMode = "Auto", AutoTemplate = "on", OutputsPerInput = 1, InputCountKey = None, IgnoreCountCheck = False, FilterPass = False):
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
        if MainLang.lower() == "ko":
            self.MainLangTag = "ko"
        else:
            self.MainLangTag = "global"
        self.Model = Model
        self.Mode = Mode
        self.MessagesReview = MessagesReview
        self.EditMode = EditMode
        self.AutoTemplate = AutoTemplate
        self.ProcessInfo = f"User: {self.Email} | Solution: {self.Solution}-{self.SubSolution} | Project: {self.ProjectName} | Process: {self.ProcessNumber}_{self.ProcessName}({self.NextSolution})"

        # ProjectFrame 경로 설정 (저장된 프로젝트 DataFrame)
        self.SolutionProjectFramePath = self._GetSolutionDataFramePath("ProjectFrame", self.ProjectDataPath)

        # PromptFrame 경로 설정 (저장된 프롬프트 DataFrame)
        self.SolutionPromptFramePath = self._GetSolutionDataFramePath("PromptFrame", self.PromptDataPath)
        # PromptFrame, ResponseStructure 설정
        with open(self.SolutionPromptFramePath, 'r', encoding = 'utf-8') as PromptJson:
            self.SolutionPromptFrame = json.load(PromptJson)
        self.ResponseStructure = self.SolutionPromptFrame["OutputStructure"]

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
                ProjectFrameDirPath = os.path.join(SolutionDirPath, SubSolutionDirName)
            else:
                # SubSolution이 None일 경우, Solution 디렉터리가 최종 경로가 됨
                ProjectFrameDirPath = SolutionDirPath

        except StopIteration:
            # 해당하는 디렉터리를 찾지 못한 경우
            raise FileNotFoundError(f"\n\n[ 아래 경로에서 해당 솔루션 데이터 프레임 파일을 찾을 수 없습니다: {self.Solution} 또는 {self.SubSolution} ]\n{DataFramePath}\n\n")

        # 결정된 최종 디렉터리 내에서 .json 파일 검색
        FileEndName = ".json"

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
            # Process Edit 불러오기
            with open(self.SolutionProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
                SolutionProjectDataFrame = json.load(DataFrameJson)

            # InputCount 및 DataFrameCompletion 확인
            NextInputCount = SolutionProjectDataFrame[0]['InputCount'] + 1
            DataFrameCompletion = SolutionProjectDataFrame[0]['Completion']

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
    def _ProcessResponse(self, Input, InputCount, InputFormat = "text", memoryNote = ""):
        """ProcessResponse를 생성하는 메서드"""
        ErrorCount = 0
        while True:
            if self.Model == "OpenAI":
                Response, Usage, Model = OpenAI_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, inputFormat = InputFormat, mainLang = self.MainLang, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)
            elif self.Model == "Anthropic":
                Response, Usage, Model = ANTHROPIC_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, inputFormat = InputFormat, mainLang = self.MainLang, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)
            elif self.Model == "Google":
                Response, Usage, Model = GOOGLE_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, inputFormat = InputFormat, mainLang = self.MainLang, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)
            elif self.Model == "DeepSeek":
                Response, Usage, Model = DEEPSEEK_LLMresponse(self.ProjectName, self.Email, self.ProcessName, Input, InputCount, inputFormat = InputFormat, mainLang = self.MainLang, Mode = self.Mode, Input2 = "", MemoryNote = memoryNote, messagesReview = self.MessagesReview)

            # 생성된 Respnse Filler 처리
            FilteredResponse = self._ProcessFilter(Response, Input)

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
    def _ProcessFilter(self, Response, Input):
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
        def FilterFunc(FilteredResponse, ResponseStructureDict, Input):
            Value = FilteredResponse[ResponseStructureDict["Key"]]
            for ValueCheckDict in ResponseStructureDict["ValueCheckList"]:
                ValueCheck = ValueCheckDict["ValueCheck"]
                ValueCheckItem = [item.strip() for item in ValueCheckDict['ValueCheckItem'].split(",")]

                # Filter4-1: 벨류가 리스트인 경우 객관식 답의 범주 체크 (ValueCheckItem: 객관식 답의 범주 리스트)
                if ValueCheck == "listDataAnswerRangeCheck":
                    for value in Value:
                        if value not in ValueCheckItem:
                            return f"{self.ProcessInfo} | ListDataAnswerRangeCheckError: ({value}) 항목은 ({ValueCheckItem})에 포함되지 않습니다"

                # Filter4-2: 벨류가 리스트인 경우 꼭 포함되어야할 데이터 체크 (ValueCheckItem: 포함되어야할 데이터 리스트)
                if ValueCheck == "listDataInclusionCheck":
                    for CheckItem in ValueCheckItem:
                        if CheckItem not in Value:
                            return f"{self.ProcessInfo} | ListDataInclusionCheckError: ({value}) 항목에 ({CheckItem}) 항목이 포함되어야 합니다"

                # Filter4-3: 벨류가 리스트인 경우 꼭 포함되지 말아야할 데이터 체크 (ValueCheckItem: 포함되지 말아야할 데이터 리스트)
                if ValueCheck == "listDataExclusionCheck":
                    for CheckItem in ValueCheckItem:
                        if CheckItem in Value:
                            return f"{self.ProcessInfo} | ListDataExclusionCheckError: ({CheckItem}) 항목이 포함되어서는 안됩니다"

                # Filter4-4: 벨류가 리스트인 경우 리스트의 길이 체크 (ValueCheckItem: 리스트의 길이 [정수])
                if ValueCheck == "listDataLengthCheck":
                    if len(Value) != int(ValueCheckItem[0]):
                        return f"{self.ProcessInfo} | ListDataLengthCheckError: ({Value}) 의 개수는 ({ValueCheckItem[0]}) 개가 되어야 합니다."
                
                # Filter4-5: 벨류가 리스트인 경우 리스트 길이의 범위 체크 (ValueCheckItem: 리스트의 길이 범위 [최소, 최대])
                if ValueCheck == "listDataRangeCheck":
                    if not (int(ValueCheckItem[0]) <= len(Value) <= int(ValueCheckItem[1])):
                        return f"{self.ProcessInfo} | ListDataRangeCheckError: ({Value}) 의 개수는 ({ValueCheckItem[0]}) 개 이상 ({ValueCheckItem[1]}) 개 이하여야 합니다."

                # 벨류가 문자인 경우 객관식 답의 범주 체크 (ValueCheckItem: 객관식 답의 범주 리스트)
                if ValueCheck == "strDataAnswerRangeCheck":
                    if Value not in ValueCheckItem:
                        return f"{self.ProcessInfo} | StrDataAnswerRangeCheckError: ({Value}) 항목은 ({ValueCheckItem})에 포함되지 않습니다"

                # 벨류가 문자인 경우 꼭 포함되어야할 문자 체크 (ValueCheckItem: 포함되어야할 문자 리스트)
                if ValueCheck == "strDataInclusionCheck":
                    for CheckItem in ValueCheckItem:
                        if CheckItem not in Value:
                            return f"{self.ProcessInfo} | StrDataInclusionCheckError: ({CheckItem}) 항목이 ({Value})에 포함되어야 합니다"
                
                # 벨류가 문자인 경우 꼭 포함되지 말아야할 문자 체크 (ValueCheckItem: 포함되지 말아야할 문자 리스트)
                if ValueCheck == "strDataExclusionCheck":
                    for CheckItem in ValueCheckItem:
                        if CheckItem in Value:
                            return f"{self.ProcessInfo} | StrDataExclusionCheckError: ({CheckItem}) 항목이 포함되어서는 안됩니다"

                # 벨류가 문자인 경우 문자 일치 여부 체크 (ValueCheckItem: Input에서 비교 대상의 dict Key, ex: ComparisonInput)
                if ValueCheck == "strDataSameCheck":
                    if Value != Input[ValueCheckItem[0]]:
                        return f"{self.ProcessInfo} | StrDataSameCheckError: ({ResponseStructureDict['Key']}) 와 (Input[{[ValueCheckItem[0]]}]) 는 일치해야 합니다\n\n({Value})\n\n({Input[ValueCheckItem[0]]})"

                # 벨류가 문자인 경우 특수문자 및 공백제외 문자 일치 여부 체크 (ValueCheckItem: Input에서 비교 대상의 dict Key, ex: ComparisonInput)
                if ValueCheck == "strCleanDataSameCheck":
                    if re.sub(r'\W+', '', Value, flags = re.UNICODE) != re.sub(r'\W+', '', Input[ValueCheckItem[0]], flags = re.UNICODE):
                        return f"{self.ProcessInfo} | StrCleanDataSameCheckError: ({ResponseStructureDict['Key']}) 와 (Input[{[ValueCheckItem[0]]}]) 는 일치해야 합니다\n\n({Value})\n\n({Input[ValueCheckItem[0]]})"

                # 벨류가 문자인 경우 문자열 길이 일치 여부 체크 (ValueCheckItem: Input에서 비교 대상의 dict Key, ex: ComparisonInput)
                if ValueCheck == "strDataLengthCheck":
                    ValueLength = len(Value)
                    InputLength = len(Input[ValueCheckItem[0]])
                    if ValueLength != InputLength:
                        return f"{self.ProcessInfo} | StrDataLengthCheckError: ({ResponseStructureDict['Key']} Length: {ValueLength}) 와 (Input[{[ValueCheckItem[0]]}] Length: {InputLength}) 는 길이는 일치해야 합니다"

                # 벨류가 문자인 경우 특수문자 및 공백제외 문자열 길이 일치 여부 체크 (ValueCheckItem: Input에서 비교 대상의 dict Key, ex: ComparisonInput)
                if ValueCheck == "strCleanDataLengthCheck":
                    CleanValueLength = len(re.sub(r'\W+', '', Value, flags=re.UNICODE))
                    CleanInputLength = len(re.sub(r'\W+', '', Input[ValueCheckItem[0]], flags=re.UNICODE))
                    if CleanValueLength != CleanInputLength:
                        return f"{self.ProcessInfo} | StrCleanDataLengthCheckError: ({ResponseStructureDict['Key']} Length: {CleanValueLength}) 와 (Input[{[ValueCheckItem[0]]}] Length: {CleanInputLength}) 는 길이는 일치해야 합니다"

                # 벨류가 문자인 경우 문자열 길이의 범위 체크 (ValueCheckItem: 문자열의 길이 범위 [최소, 최대])
                if ValueCheck == "strDataRangeCheck":
                    ValueLength = len(Value)
                    if not (int(ValueCheckItem[0]) <= ValueLength <= int(ValueCheckItem[1])):
                        return f"{self.ProcessInfo} | StrDataRangeCheckError: ({ResponseStructureDict['Key']} Length: {ValueLength}) 는 ({ValueCheckItem[0]}) 이상 ({ValueCheckItem[1]}) 이하여야 합니다"

                # 벨류가 문자인 경우 문자열 처음과 끝에 존재해야하는 필수 문자 체크 (ValueCheckItem: 문자열 처음과 끝에 존재해야하는 문자 리스트 [시작 문자, 끝 문자], 시작 문자 또는 끝 문자중 존재하지 않는 부분은 빈문자 ""로 작성)
                if ValueCheck == "strDataStartEndInclusionCheck":
                    StartWordLength = len(ValueCheckItem[0])
                    EndWordLength = len(ValueCheckItem[1])
                    if ValueCheckItem[0] not in Value[0:StartWordLength + 10] or ValueCheckItem[1] not in Value[-EndWordLength - 10:-1]:
                        return f"{self.ProcessInfo} | StrDataStartEndInclusionCheckError: ({ResponseStructureDict['Key']}) 는 ({ValueCheckItem[0]}) 로 시작하고 ({ValueCheckItem[1]}) 로 끝나야 합니다"

                # 벨류가 문자인 경우 문자열 처음과 끝에 존재하지 말아야할 문자 체크 (ValueCheckItem: 문자열 처음과 끝에 존재하지 말아야할 문자 리스트 [시작 문자, 끝 문자], 시작 문자 또는 끝 문자중 존재하지 않는 부분은 빈문자 ""로 작성)
                if ValueCheck == "strDataStartEndExclusionCheck":
                    if ValueCheckItem[0] == "":
                        ValueCheckItem[0] = "(포@함-방$지_문^구#)"
                    if ValueCheckItem[1] == "":
                        ValueCheckItem[1] = "(포@함-방$지_문^구#)"
                    StartWordLength = len(ValueCheckItem[0])
                    EndWordLength = len(ValueCheckItem[1])
                    if ValueCheckItem[0] in Value[0:StartWordLength + 10] or ValueCheckItem[1] in Value[-EndWordLength - 10:-1]:
                        return f"{self.ProcessInfo} | StrDataStartEndExclusionCheckError: ({ResponseStructureDict['Key']}) 는 ({ValueCheckItem[0]}) 로 시작하고 ({ValueCheckItem[1]}) 로 끝나지 않아야 합니다"

                # 벨류가 문자인 경우 주요 언어 체크
                if ValueCheck == "strMainLangCheck":
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
        FilteredResponse = KeyCheck(FilteredResponse, self.ResponseStructure)
        if isinstance(FilteredResponse, str):
            return FilteredResponse
               
        # Error1-3: Main-FilterFunc
        FilteredResponse = FilterFunc(FilteredResponse, self.ResponseStructure, Input)
        if isinstance(FilteredResponse, str):
            return FilteredResponse
        
        # Error2: SubCheck
        # Main-ValueType이 dict인 경우
        if self.ResponseStructure["ValueType"] == "dict":
            SubFilteredResponse = FilteredResponse[self.ResponseStructure["Key"]]
            for i in range(len(self.ResponseStructure["Value"])):

                # Error2-2: Sub-KeyCheck
                SubFilteredResponse = KeyCheck(SubFilteredResponse, self.ResponseStructure["Value"][i])
                if isinstance(SubFilteredResponse, str):
                    return SubFilteredResponse

                # Error2-3: Sub-FilterFunc
                SubFilteredResponse = FilterFunc(SubFilteredResponse, self.ResponseStructure["Value"][i], Input)
                if isinstance(SubFilteredResponse, str):
                    return SubFilteredResponse
        
        # Main-ValueType이 list인 경우
        if self.ResponseStructure["ValueType"] == "list":
            for SubFilteredResponse in FilteredResponse["Key"]:
                for i in range(len(self.ResponseStructure["Value"])):

                    # Error2-2: Sub-KeyCheck
                    SubFilteredResponse = KeyCheck(SubFilteredResponse, self.ResponseStructure["Value"][i])
                    if isinstance(SubFilteredResponse, str):
                        return SubFilteredResponse

                    # Error2-3: Sub-FilterFunc
                    SubFilteredResponse = FilterFunc(SubFilteredResponse, self.ResponseStructure["Value"][i], Input)
                    if isinstance(SubFilteredResponse, str):
                        return SubFilteredResponse
        
        # 모든 조건을 만족하면 필터링된 응답 반환
        return FilteredResponse[self.ResponseStructure["Key"]]

    ## ProcessDataFrame 업데이트 메서드 ##
    def _UpdateProcessDataFrame(self, InputCount, Response):
        """Response에 따라 ProcessDataFrame을 업데이트하는 메서드"""
        ## SolutionProjectDataFrame 불러오기
        if os.path.exists(self.SolutionProjectDataFramePath):
            with open(self.SolutionProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
                SolutionProcessDataFrame = json.load(DataFrameJson)
        else:
            with open(self.SolutionProjectFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
                SolutionProcessDataFrame = json.load(DataFrameJson)[self.MainLangTag]
        ## SolutionProcessInfo 데이터 업데이트
        SolutionProcessInfo = SolutionProcessDataFrame[0].copy()
        for key, ValueExpression in SolutionProcessInfo.items():
            if key in ['InputCount', 'Completion']:
                continue

            ActualValue = ValueExpression
            if isinstance(ValueExpression, str) and ValueExpression.startswith("eval(") and ValueExpression.endswith(")"):
                # "eval("와 ")" 부분을 제외한 안쪽 코드만 추출
                CodeToEval = ValueExpression[5:-1]
                ActualValue = eval(CodeToEval)
            
            SolutionProcessDataFrame[0][key] = ActualValue


        ## SolutionProcessData 데이터 업데이트
        SolutionProcessData = SolutionProcessDataFrame[1][0].copy()
        for key, ValueExpression in SolutionProcessData.items():

            ActualValue = ValueExpression
            if isinstance(ValueExpression, str) and ValueExpression.startswith("eval(") and ValueExpression.endswith(")"):
                # "eval("와 ")" 부분을 제외한 안쪽 코드만 추출
                CodeToEval = ValueExpression[5:-1]
                ActualValue = eval(CodeToEval)

            SolutionProcessData[key] = ActualValue

        ## SolutionProcessDataFrame 데이터 프레임 업데이트
        SolutionProcessDataFrame[1].append(SolutionProcessData)
        
        ## SolutionProjectDataFrame ProcessCount 및 Completion 업데이트
        SolutionProcessDataFrame[0]['InputCount'] = InputCount
        if InputCount == self.TotalInputCount:
            SolutionProcessDataFrame[0]['Completion'] = 'Yes'
            
        ## SolutionProjectDataFrame 저장
        with open(self.SolutionProjectDataFramePath, 'w', encoding = 'utf-8') as DataFrameJson:
            json.dump(SolutionProcessDataFrame, DataFrameJson, indent = 4, ensure_ascii = False)

    ## SolutionEdit 업데이트 메서드 ##
    def _UpdateSolutionEdit(self):
        """SolutionEdit을 업데이트하는 메서드"""
        ## SolutionProjectDataFrame 불러온 뒤 Completion 확인
        with open(self.SolutionProjectDataFramePath, 'r', encoding = 'utf-8') as DataFrameJson:
            SolutionProjectDataFrame = json.load(DataFrameJson)
        if SolutionProjectDataFrame[0]['Completion'] == 'Yes':
            ## SolutionEdit이 존재할때
            if os.path.exists(self.SolutionEditPath):
                with open(self.SolutionEditPath, 'r', encoding = 'utf-8') as SolutionEditJson:
                    SolutionEdit = json.load(SolutionEditJson)
            ## SolutionEdit이 존재 안할때
            else:
                SolutionEdit = {}
            ## TranslationEdit 업데이트
            SolutionEdit[self.ProcessName] = []
            if self.EditMode == "Manual":
                SolutionEdit[f"{self.ProcessName}Completion"] = '완료 후 Completion'
            elif self.EditMode == "Auto":
                SolutionEdit[f"{self.ProcessName}Completion"] = 'Completion'
            SolutionProjectDataList = SolutionProjectDataFrame[1]
            for i in range(1, len(SolutionProjectDataList)):
                SolutionProjectData = SolutionProjectDataList[i]
                SolutionEdit[self.ProcessName].append(SolutionProjectData)

            ## Process에서 추가 데이터가 존재하는 경우 예외 저장
            if len(SolutionProjectDataFrame) > 2:
                for i, AdditionalData in enumerate(SolutionProjectDataFrame[2:], start = 1):
                    AdditionalKey = f"{self.ProcessName}AdditionalData{i}"
                    SolutionEdit[AdditionalKey] = AdditionalData

            ## SolutionEdit 저장
            with open(self.SolutionEditPath, 'w', encoding = 'utf-8') as SolutionEditJson:
                json.dump(SolutionEdit, SolutionEditJson, indent = 4, ensure_ascii = False)

    ## SolutionEdit 불러오기 메서드 ##
    def _LoadEdit(self):
        """SolutionEdit 불러오기 메서드"""
        if os.path.exists(self.SolutionEditPath):
            with open(self.SolutionEditPath, 'r', encoding = 'utf-8') as SolutionEditJson:
                SolutionEdit = json.load(SolutionEditJson)
        return SolutionEdit

    ## Response 생성 및 프로세스 실행 메서드 ##
    def Run(self, Response = "Response"):
        """프로세스 실행 메서드"""
        if not self.EditCheck:
            if self.DataFrameCompletion == 'No':
                for i in range(self.InputCount - 1, self.TotalInputCount):
                    ## Input 생성
                    inputCount = self.InputList[i]['Id']
                    Input = self.InputList[i]['Input']
                    InputFormat = self.InputList[i]['InputFormat']

                    if Response == "Response":
                        ## ProcessResponse 생성
                        ProcessResponse = self._ProcessResponse(Input, inputCount, InputFormat = InputFormat)
                    if Response == "Input":
                        ProcessResponse = Input

                    ## DataFrame 저장
                    self._UpdateProcessDataFrame(inputCount, ProcessResponse)

            ## Edit 저장
            self._UpdateSolutionEdit()
            print(f"[ {self.ProcessInfo}Update 완료 ]\n")

            if self.EditMode == "Manual":
                sys.exit(f"[ {self.ProjectName}_Script_Edit 생성 완료 -> {self.ProcessName}: (({self.ProcessName}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({self.ProcessName}Completion: Completion))으로 변경 ]\n\n{self.SolutionEditPath}")

        if self.EditMode == "Manual":
            if self.EditCheck:
                if not self.EditCompletion:
                    ### 필요시 이부분에서 RestructureProcessDic 후 다시 저장 필요 ###
                    sys.exit(f"[ {self.ProjectName}_Script_Edit -> {self.ProcessName}: (({self.ProcessName}))을 검수한 뒤 직접 수정, 수정사항이 없을 시 (({self.ProcessName}Completion: Completion))으로 변경 ]\n\n{self.SolutionEditPath}")
        if self.EditCompletion:
            print(f"[ {self.ProcessInfo}Update는 이미 완료됨 ]\n")

        ## Edit 불러오기
        return self._LoadEdit()

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    Email = "yeoreum00128@gmail.com"
    ProjectNameList = ['250807_PDF테스트', '250807_TXT테스트']
    Solution = 'Script'
    SubSolution = 'ScriptSegmentation'
    ProcessNumber = 'T02'
    ProcessName = 'TXTMainLangCheck'
    NextSolution = 'Translation'
    MessagesReview = 'on'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################