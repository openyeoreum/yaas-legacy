import os
import shutil
import json
import spacy
import sys
sys.path.append("/yaas")

from PyPDF2 import PdfReader, PdfWriter


#############################################
##### LoadAgent (업로드 된 스크립트 파일 확인) #####
#############################################
class LoadAgent:

    ## 기본 경로 정의 ##
    StoragePath = "/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage"
    ProjectDataPath = "/yaas/agent/a5_Database/a53_ProjectData"
    PromptDataPath = "/yaas/agent/a5_Database/a54_PromptData"

    ## LoadAgent 초기화 ##
    def __init__(self, InputList, Email, ProjectName, Solution, ProcessNumber, ProcessName, Mode, MessageReview, SubSolution = None, SolutionTag = None):
        """클래스 초기화"""
        # Process 설정
        self.Email = Email
        self.ProjectName = ProjectName
        self.ProcessNumber = ProcessNumber
        self.ProcessName = ProcessName
        self.Solution = Solution
        self.SubSolution = SubSolution
        self.ProcessInfo = f"User: {self.Email} | Solution: {self.Solution}-{self.SubSolution} | Project: {self.ProjectName} | {self.ProcessNumber}_{self.ProcessName}({self.Solution})"
        self.Mode = Mode
        self.MessageReview = MessageReview

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
        self.InputCount, self.DataFrameCompletion = self._ProcessDataFrameCheck()

    ## Solution 및 SubSolution 경로에서 DataFrame 경로 가져오기 ##
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
            print(f"\n\n[ 아래 경로에서 해당 솔루션을 찾을 수 없습니다: {Solution} 또는 {SubSolution} ]\n{DataFramePath}\n\n")
            return None

        # 결정된 최종 디렉터리 내에서 .json 파일 검색
        for Root, Dirs, Files in os.walk(ProjectFrameDirPath):
            for File in Files:
                # 파일 이름에 ProcessNumber와 ProcessName이 포함되어 있는지 확인
                if File.endswith('.json') and f"{self.ProcessNumber}_{self.ProcessName}" in File:
                    return os.path.join(Root, File) # 파일을 찾으면 즉시 경로 반환
        
        # 루프를 모두 순회했으나 파일을 찾지 못한 경우
        print(f"\n\n[ 아래 경로에서 해당 데이터 프레임을 찾을 수 없습니다: {self.ProcessNumber}_{self.ProcessName} ]\n{ProjectFrameDirPath}\n\n")
        return None

    ## 프로세스 DataFrame이 존재하는지 확인하고 InputCount 및 DataFrameCompletion 반환 ##
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
                TranslationEditFrame = json.load(DataFrameJson)
            
            ## InputCount 및 DataFrameCompletion 확인
            NextInputCount = TranslationEditFrame[0]['InputCount'] + 1
            DataFrameCompletion = TranslationEditFrame[0]['Completion']
            
            return NextInputCount, DataFrameCompletion





 

    
    ## Process Count 계산 및 Check ##

    ## Process 진행 ##


if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectNameList = ['250807_PDF테스트', '250807_TXT테스트']
    Solution = 'Translation'
    AutoTemplate = "Yes" # 자동 컴포넌트 체크 여부 (Yes/No)
    #########################################################################