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

    # ---------------------------------
    # --- class-init ------------------
    # --- class-func: Solution 초기화 ---
    def __init__(self,
                 email: str,
                 project_name: str,
                 solution: str,
                 next_solution: str,
                 process_number: str,
                 process_name: str) -> None:
        """사용자-프로젝트의 Operation에 통합 Solution 기능을 셋팅하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): 프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Audiobook, Translation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
        """
        # Agent 초기화
        super().__init__(
            email,
            project_name,
            solution,
            next_solution,
            process_number,
            process_name)

    # --- class-func: solution 디렉토리 생성 ---
    def _make_solution_dir(self):
        pass

    # # --- class-func: solution 디렉토리 생성 ---
    # def _create_solution_info(self):
    #     pass

    # --------------------------------
    # --- func-set: solution run -----
    # --- class-func: run solution ---
    def run_solution(self):
        pass

    # --- class-func: return solution edit ---
    def return_solution_edit(self):
        pass