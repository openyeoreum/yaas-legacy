import os
import json
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a31_Operation.a312_Log import Log

# ======================================================================
# [a313-1] Operation-Base
# ======================================================================
# class: Base
# ======================================================================
class Base(Log):

    # paths 경로
    core_paths_file_path = "/yaas/agent/a2_DataFrame/a22_Core/a221_CorePaths.json"
    solution_tree_paths_file_path = "/yaas/agent/a2_DataFrame/a23_Solution/a231_SolutionTreePaths.json"
    generation_tree_paths_file_path = "/yaas/agent/a2_DataFrame/a24_Generation/a241_GenerationTreePaths.json"

    # -----------------------------
    # --- class-init --------------
    # --- class-func: Base 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 work: str,
                 form_keys: list = None,
                 dir_keys: list = None,
                 file_keys: list = None,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None,
                 idx: int = None,
                 idx_length: int = None) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 Base 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            work (str): "core" 또는 "solution" 또는 "generation"
            _keys (list): core_paths 또는 solution_paths 또는 generation_paths json의 연속된 키 값
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
            idx (int): 솔루션 안에 프로세스 안에 테스크 인덱스 번호로 jpg, wav, mp3 등 file명에 사용
            idx_length (int): idx의 전체 길이
            storage_solution_dir_path (str): 사용자-프로젝트-솔루션 디렉토리 경로
            _path (str): 포맷팅된 경로
        """
        # Log 초기화
        super().__init__(
            email,
            project_name,
            solution = solution,
            next_solution = next_solution,
            process_number = process_number,
            process_name = process_name,
            idx = idx,
            idx_length = idx_length)
        
        # attributes 설정
        self.work = work
        self.form_keys = form_keys if form_keys is not [] else None
        self.dir_keys = dir_keys if dir_keys is not [] else None
        self.file_keys = file_keys if file_keys is not [] else None

        # next_solution 유무에 따른 storage_solution_dir_path 생성
        self.storage_solution_dir_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_{self.solution}"
        if self.next_solution is not None:
            self.storage_solution_dir_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_{self.solution}({self.next_solution})"

        # core, solution, generation의 form, dir, file 경로 가져오기
        self.form_path = None
        self.dir_path = None
        self.file_path = None
        if form_keys is not None:
            self.form_path = self._read_path(self.work, form_keys)
        if dir_keys is not None:
            self.dir_path = self._read_path(self.work, dir_keys)
        if file_keys is not None:
            self.file_path = self._read_path(self.work, file_keys)

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

    # --- class-func: solution_tree_paths 불러오기 ---
    def _load_solution_paths_file(self) -> dict:
        """SolutionTreePaths.json 파일을 불러옵니다.

        Returns:
            solution_tree_paths (dict): SolutionTreePaths.json 파일 내용
        """
        # solution_tree_paths.json 파일 불러오기
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

    # --- class-func: generation_tree_paths 불러오기 ---
    def _load_generation_paths_file(self) -> dict:
        """GenerationTreePaths.json 파일을 불러옵니다.

        Returns:
            generation_tree_paths (dict): GenerationTreePaths.json 파일 내용
        """
        # generation_tree_paths.json 파일 불러오기
        with open(self.generation_tree_paths_file_path, "r") as f:
            generation_paths_dict = json.load(f)
        
        return generation_paths_dict

    # ---------------------------------------------
    # --- func-set: read path ---------------------
    # --- class-func: paths_data 가져오고 포맷팅하기 ---
    def _read_path(self,
                   work: str,
                   keys: list) -> str:
        """work와 _Paths의 키 값을 *keys에 인자로 받은 후, 이를 email, project_name, solution, process_number, process_name, self.solution, self.next_solution, self.storage_solution_dir_path로 포맷팅합니다.

        Args:
            work (str): "core" 또는 "solution" 또는 "generation" (_load_core_paths_file 또는 _load_solution_paths_file 또는 _load_generation_paths_file 선택)
            keys (list): core_paths 또는 solution_paths 또는 generation_paths의 연속된 keys 리스트

        Returns:
            formatted_path (str): 포맷팅된 경로
        """
        # paths_dict 가져오기
        if work == "core":
            paths_dict = self._load_core_paths_file()
        if work == "solution":
            paths_dict = self._load_solution_paths_file()
        if work == "generation":
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
            NextSolution=self.next_solution,
            ProcessNumber=self.process_number,
            ProcessName=self.process_name,
            Idx=self.idx,
            StorageSolutionDirPath=self.storage_solution_dir_path)

        return formatted_path

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"
    work = "solution"
    form_keys = None
    dir_keys = ["Storage", "Upload", "DirPath"]
    file_keys = None
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "PT01"
    process_name = "ScriptLoad"
    idx = None

    # 클래스 테스트
    base = Base(
        email,
        project_name,
        work,
        form_keys=form_keys,
        dir_keys=dir_keys,
        file_keys=file_keys,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name,
        idx=idx)

    dir_path = base.dir_path

    print("Dir Path:", dir_path)