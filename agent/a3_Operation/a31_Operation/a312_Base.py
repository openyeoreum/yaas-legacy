import json
import sys
sys.path.append("/yaas")

from agent.a3_Operation.a31_Operation.a311_Access import Access

# ======================================================================
# [a312-1] Operation-Base
# ======================================================================
# class: Base
# ======================================================================
class Base(Access):

    # path_map 경로
    path_map_path = "/yaas/agent/a2_DataFrame/a21_Operation/a211_PathMap.json"

    # -----------------------------
    # --- class-init --------------
    # --- class-func: Base 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str = None,
                 next_solution: str = None,
                 process_number: str = None,
                 process_name: str = None) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 Base 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
        """
        # Access 초기화
        super().__init__(
            email,
            project_name)

        # attributes 설정       
        self.solution = solution
        self.next_solution = next_solution
        self.process_number = process_number
        self.process_name = process_name

        # next_solution 유무에 따른 storage_solution_dir_path 생성
        self.storage_solution_dir_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_{self.solution}"
        if self.next_solution is not None:
            self.storage_solution_dir_path = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/{self.email}/{self.project_name}/{self.project_name}_{self.solution}({self.next_solution})"

    # -----------------------------------
    # --- func-set: load path map -------
    # --- class-func: path_map 불러오기 ---
    def _load_path_map(self) -> dict:
        """PathMap.json 파일을 불러옵니다.

        Returns:
            path_map_dict (dict): PathMap.json 파일 내용
        """
        # PathMap.json 파일 불러오기
        with open(self.path_map_path, "r") as f:
            path_map_dict = json.load(f)
        
        return path_map_dict

    # --- class-func: path_map에서 path 가져오고 포맷팅하기 ---
    def read_path_map(self,
                      work: str,
                      path_keys: list,
                      idx: int = None) -> str:
        """work와 _Paths의 키 값을 *keys에 인자로 받은 후, 이를 email, project_name, solution, process_number, process_name, self.solution, self.next_solution, self.storage_solution_dir_path로 포맷팅합니다.

        Args:
            work (str): path_map_dict 안에 "Operation" 또는 "Core" 또는 "Solution" 또는 "Generation"
            path_keys (list): "Operation" 또는 "Core" 또는 "Solution" 또는 "Generation"의 연속된 path_keys 리스트
            idx (int): 솔루션 안에 프로세스 안에 테스크 인덱스 번호로 jpg, wav, mp3 등 file명에 사용 (기본값: None)

        Returns:
            formatted_path (str): 포맷팅된 경로
        """
        # path_dict 가져오기
        path_dict = self._load_path_map()[work]

        # path_dict에서 keys에 해당하는 경로 가져오기
        path = path_dict
        for key in path_keys:
            path = path[key]

        # 경로 포맷팅
        formatted_path = path.format(
            Email=self.email,
            ProjectName=self.project_name,
            Solution=self.solution,
            NextSolution=self.next_solution,
            ProcessNumber=self.process_number,
            ProcessName=self.process_name,
            Idx=idx,
            StorageSolutionDirPath=self.storage_solution_dir_path)

        return formatted_path

if __name__ == "__main__":

    # --- class-test ---
    # 인자 설정
    email = "yeoreum00128@gmail.com"
    project_name = "글로벌솔루션여름"
    solution = "ScriptSegmentation"
    next_solution = "Audiobook"
    process_number = "PT01"
    process_name = "ScriptLoad"

    # 클래스 테스트
    base = Base(
        email,
        project_name,
        solution=solution,
        next_solution=next_solution,
        process_number=process_number,
        process_name=process_name)