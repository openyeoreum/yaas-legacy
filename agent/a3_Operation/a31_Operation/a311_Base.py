import os
import json
import sys
sys.path.append("/yaas")

# ======================================================================
# [a311-1] Operation-Base
# ======================================================================
# class: Base
# ======================================================================
class Base:

    # paths 경로
    core_paths_file_path = "/yaas/agent/a2_DataFrame/a22_Core/a221_CorePaths.json"
    solution_tree_paths_file_path = "/yaas/agent/a2_DataFrame/a23_Solution/a231_SolutionTreePaths.json"

    # -----------------------------
    # --- class-init --------------
    # --- class-func: Base 초기화 ---
    def __init__(self, email: str, project_name: str, work: str, *keys: str, solution: str = None, next_solution: str = None, process_number: str = None, process_name: str = None) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 Base 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): yymmdd_프로젝트명
            *keys (str): core_paths_data 또는 solution_paths_data의 연속된 키 값
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
        """
        # attributes 설정
        self.email = email
        self.project_name = project_name
        self.work = work
        self.solution = solution
        self.next_solution = next_solution
        self.process_number = process_number
        self.process_name = process_name
        self.keys = keys
        self.storage_solution_dir_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_{self.solution}"

        # next_solution이 있는 경우 storage_solution_dir_path 변경
        if self.next_solution is not None:
            self.storage_solution_dir_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_{self.solution}({self.next_solution})"

        # core, solution, generation 경로 가져오기
        self.path = self._read_path(self.work, *keys)

    # -------------------------------------
    # --- func-set: load paths file -------
    # --- class-func: core_paths 불러오기 ---
    def _load_core_paths_file(self) -> dict:
        """CorePaths.json 파일을 불러옵니다.

        Returns:
            core_paths (dict): CorePaths.json 파일 내용
        """
        # core_paths.json 파일 불러오기
        with open(self.core_paths_file_path, "r") as f:
            core_paths_dict = json.load(f)
        
        return core_paths_dict

    # --- class-func: solution_paths 불러오기 ---
    def _load_solution_paths_file(self) -> dict:
        """SolutionPaths.json 파일을 불러옵니다.

        Returns:
            solution_paths (dict): SolutionPaths.json 파일 내용
        """
        # solution_paths.json 파일 불러오기
        with open(self.solution_tree_paths_file_path, "r") as f:
            solution_paths_dict = json.load(f)

        # solution에 따른 경로 설정
        if self.solution == "Estimate":
            solution_paths = solution_paths_dict["EstimatePaths"]
        if self.solution == "Collection":
            solution_paths = solution_paths_dict["CollectionPaths"]
        if self.solution == "ScriptGen":
            solution_paths = solution_paths_dict["ScriptGenPaths"]
        if self.solution == "ScriptSegmentation":
            solution_paths = solution_paths_dict["ScriptSegmentationPaths"]
        if self.solution == "ScriptStruction":
            solution_paths = solution_paths_dict["ScriptStructionPaths"]
        if self.solution == "Translation":
            solution_paths = solution_paths_dict["CTranslationPaths"]
        if self.solution == "Textbook":
            solution_paths = solution_paths_dict["TextbookPaths"]
        if self.solution == "Audiobook":
            solution_paths = solution_paths_dict["AudiobookPaths"]
        if self.solution == "Videobook":
            solution_paths = solution_paths_dict["VideobookPaths"]
        if self.solution == "Marketing":
            solution_paths = solution_paths_dict["MarketingPaths"]

        # {self.solution}_paths.json 파일 불러오기
        with open(solution_paths, "r") as f:
            solution_paths_dict = json.load(f)

        return solution_paths_dict

    # --- class-func: generation_paths 불러오기 ---
    def _load_generation_paths_file(self) -> dict:
        """GenerationPaths.json 파일을 불러옵니다.

        Returns:
            generation_paths (dict): GenerationPaths.json 파일 내용
        """

    # ---------------------------------------------
    # --- func-set: read path ---------------------
    # --- class-func: paths_data 가져오고 포맷팅하기 ---
    def _read_path(self, work: str, *keys: str) -> str:
        """work와 _Paths의 키 값을 *keys에 인자로 받은 후, 이를 email, project_name, solution, process_number, process_name, self.solution, self.next_solution, self.storage_solution_dir_path로 포맷팅합니다.

        Args:
            work (str): 'core' 또는 'solution' 또는 'generation' (_load_core_paths_file 또는 _load_solution_paths_file 또는 _load_generation_paths_file 선택)
            *keys (str): core_paths 또는 solution_paths 또는 generation_paths의 연속된 키 값

        Returns:
            formatted_path (str): 포맷팅된 경로
        """
        # paths_dict 가져오기
        if work == 'core':
            paths_dict = self._load_core_paths_file()
        if work == 'solution':
            paths_dict = self._load_solution_paths_file()
        if work == 'generation':
            paths_dict = self._load_generation_paths_file()

        # paths_dict에서 keys에 해당하는 경로 가져오기
        path = paths_dict
        for key in keys:
            path = path[key]

        # 경로 포맷팅
        formatted_path = path.format(
            Email=self.email,
            ProjectName=self.project_name,
            Solution=self.solution,
            ProcessNumber=self.process_number,
            ProcessName=self.process_name,
            NextSolution=self.next_solution,
            StorageSolutionDirPath=self.storage_solution_dir_path
        )

        return formatted_path

if __name__ == "__main__":

    # ------------------
    # --- class-test ---
    email = "yeoreum00128@gmail.com"
    project_name = "250911_오늘도불안한엄마들에게"
    work = "solution"
    key1 = "Storage"
    key2 = "Upload"
    key3 = "DirPath"
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "PT01"
    process_name = "ScriptLoad"

    # 클래스 테스트
    BaseInstance = Base(email, project_name, work, key1,key2, key3, solution=solution, next_solution=next_solution, process_number=process_number, process_name=process_name)
    print(BaseInstance.path)