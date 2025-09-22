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
    solution_tree_paths_file_path = "/yaas/agent/a2_DataFrame/a23_Solution/a231_SolutionPaths.json"

    # -----------------------------
    # --- class-init --------------
    # --- class-func: Base 초기화 ---
    def __init__(self, email: str, project_name: str, solution: str, process_number: str, process_name: str, sub_solution: str = None, next_solution: str = None) -> None:
        """사용자-프로젝트의 Core와 Solution에 통합 Base 기능을 수행하는 클래스입니다.

        Attributes:
            email (str): 이메일
            project_name (str): yymmdd_프로젝트명
            solution (str): 솔루션명 (ex. Collection, ScriptSegmentation 등)
            process_number (str): 솔루션 안에 프로세스 번호
            process_name (str): 솔루션 안에 프로세스명
            sub_solution (str): Script 솔루션 등에서 sub_solution이 필요한 경우 sub_solution명 (ex. ScriptGen, ScriptSegmentation, ScriptStruction)
            next_solution (str): 다음 솔루션이 필요한 경우 다음 솔루션명 (ex. Collection, ScriptSegmentation 등)
        """
        # attributes 설정
        self.email = email
        self.project_name = project_name
        self.solution = solution
        self.process_number = process_number
        self.process_name = process_name

        # script 솔루션 등에서 sub_solution과 next_solution이 필요한 경우
        if sub_solution is not None:
            self.solution = sub_solution
        self.next_solution = next_solution

        # core_paths_dict 불러오기
        self.core_paths_dict = self._load_core_paths_file()

        # solution_paths_dict 불러오기
        self.solution_paths_dict = self._load_solution_paths_file()

        # core_paths 가져오기
        # form
        self.user_access_form_json_file_path, self.user_config_form_json_file_path, self.user_logs_form_json_file_path, self.project_config_form_json_file_path, self.project_logs_form_json_file_path = self._read_core_form_path_data()
        # dir_and_file
        self.user_dir_path, self.user_access_json_file_path, self.user_config_json_file_path, self.user_log_json_file_path, self.core_dir_path, self.core_config_json_file_path, self.core_log_json_file_path, self.solution_dir_path = self._read_core_dir_and_file_path_data()
        
        # solution_

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
        if self.solution == "Script":
            if self.sub_solution == "ScriptGen":
                solution_paths = solution_paths_dict["ScriptGenPaths"]
            if self.sub_solution == "ScriptSegmentation":
                solution_paths = solution_paths_dict["ScriptSegmentationPaths"]
            if self.sub_solution == "ScriptStruction":
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
    
    # -----------------------------------------
    # --- func-set: read core paths -----------
    # --- class-func: core_form_path 가져오기 ---
    def _read_core_form_path_data(self) -> str:
        """Core의 Form 경로를 반환합니다.
        Returns:
            core_form_path (str): CorePaths.json에서 Form값 반환
        """
        # core_dir_path 가져오기
        core_dir_path = self.core_paths_dict["Form"]["CoreDirPath"]

        # form_path 가져오기
        user_access_form_json_file_path = self.core_paths_dict["Form"]["UserAccessFormJsonFilePath"].format(CoreDirPath=core_dir_path)
        user_config_form_json_file_path = self.core_paths_dict["Form"]["UserConfigFormJsonFilePath"].format(CoreDirPath=core_dir_path)
        user_logs_form_json_file_path = self.core_paths_dict["Form"]["UserLogsFormJsonFilePath"].format(CoreDirPath=core_dir_path)
        project_config_form_json_file_path = self.core_paths_dict["Form"]["ProjectConfigFormJsonFilePath"].format(CoreDirPath=core_dir_path)
        project_logs_form_json_file_path = self.core_paths_dict["Form"]["ProjectLogsFormJsonFilePath"].format(CoreDirPath=core_dir_path)

        return user_access_form_json_file_path, user_config_form_json_file_path, user_logs_form_json_file_path, project_config_form_json_file_path, project_logs_form_json_file_path

    # --- class-func: core_dir_and_file_path 가져오기 ---
    def _read_core_dir_and_file_path_data(self) -> str:
        """Core의 User, Core, Solution 디렉토리와 폴더 경로를 반환합니다.

        Returns:
            user_path (str): CorePaths.json에서 DirAndFile -> User값 반환
            core_path (str): CorePaths.json에서 DirAndFile -> Core값 반환
            solution_path (str): CorePaths.json에서 DirAndFile -> Solution값 반환
        """
        # user_storage_dir_path 가져오기
        user_storage_dir_path = self.core_paths_dict["DirAndFile"]["UserStorageDirPath"]

        # user_path 가져오기
        user_dir_path = self.core_paths_dict["DirAndFile"]["User"]["UserDirPath"].format(StorageDirPath=user_storage_dir_path, Email=self.email)
        user_access_json_file_path = self.core_paths_dict["DirAndFile"]["User"]["UserAccessJsonFilePath"].format(UserDirPath=user_dir_path, Email=self.email)
        user_config_json_file_path = self.core_paths_dict["DirAndFile"]["User"]["UserConfigJsonFilePath"].format(UserDirPath=user_dir_path, Email=self.email)
        user_log_json_file_path = self.core_paths_dict["DirAndFile"]["User"]["UserLogJsonFilePath"].format(UserDirPath=user_dir_path, Email=self.email)

        # core_path 가져오기
        core_dir_path = self.core_paths_dict["DirAndFile"]["Core"]["CoreDirPath"].format(UserDirPath=user_dir_path, ProjectName=self.project_name)
        core_config_json_file_path = self.core_paths_dict["DirAndFile"]["Core"]["CoreConfigJsonFilePath"].format(CoreDirPath=core_dir_path, ProjectName=self.project_name)
        core_log_json_file_path = self.core_paths_dict["DirAndFile"]["Core"]["CoreLogJsonFilePath"].format(CoreDirPath=core_dir_path, ProjectName=self.project_name)

        # solution_path 가져오기
        solution_dir_path = self.core_paths_dict["DirAndFile"]["Solution"]["SolutionDirPath"].format(CoreDirPath=core_dir_path, ProjectName=self.project_name, Solution=self.solution)
        if self.next_solution is not None:
            solution_dir_path = self.core_paths_dict["DirAndFile"]["Solution"]["Solution(NextSolution)DirPath"].format(CoreDirPath=core_dir_path, ProjectName=self.project_name, Solution=self.solution, NextSolution=self.next_solution)
        
        return user_dir_path, user_access_json_file_path, user_config_json_file_path, user_log_json_file_path, core_dir_path, core_config_json_file_path, core_log_json_file_path, solution_dir_path

    # --------------------------------------------------------
    # --- func-set: read process paths -----------------------
    # --- class-func: process_form_paths 가져오기 --------------
    def _read_process_form_path_data(self) -> str:
        """Process의 Form 경로를 반환합니다.
        Returns:
            process_form_json_file_path (str): ProcessPaths.json에서 Form값 반환
        """
        # script_segmentation_dir_path 가져오기
        script_segmentation_dir_path = self.solution_paths_dict["Form"]["ScriptSegmentationFormPath"]
        
        # form_path 가져오기
        start_form_json_file_path = self.solution_paths_dict["Form"]["StartFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        script_load_form_json_file_path = self.solution_paths_dict["Form"]["ScriptLoadFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        pdf_main_lang_check_form_json_file_path = self.solution_paths_dict["Form"]["PDFMainLangCheckFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        pdf_layout_check_form_json_file_path = self.solution_paths_dict["Form"]["PDFLayoutCheckFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        pdf_resize_form_json_file_path = self.solution_paths_dict["Form"]["PDFResizeFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        pdf_split_form_json_file_path = self.solution_paths_dict["Form"]["PDFSplitFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        pdf_form_check_form_json_file_path = self.solution_paths_dict["Form"]["PDFFormCheckFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        txt_main_lang_check_form_json_file_path = self.solution_paths_dict["Form"]["TXTMainLangCheckFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)
        txt_split_form_json_file_path = self.solution_paths_dict["Form"]["TXTSplitFormJsonFilePath"].format(ScriptSegmentationDirPath=script_segmentation_dir_path)

        return start_form_json_file_path, script_load_form_json_file_path, pdf_main_lang_check_form_json_file_path, pdf_layout_check_form_json_file_path, pdf_resize_form_json_file_path, pdf_split_form_json_file_path, pdf_form_check_form_json_file_path, txt_main_lang_check_form_json_file_path, txt_split_form_json_file_path

    # ---------------------------------------------------------------
    # --- func-set: read data_frame_and_data_set paths --------------
    # --- class-func: process_data_frame_and_data_set_path 가져오기 ---
    def _read_process_data_frame_and_data_set_path_data(self) -> str:
        """Process의 DataFrame, DataSet 디렉토리와 폴더 경로를 반환합니다.

        Returns:
            data_frame (str): ProcessPaths.json에서 DirAndFile -> DataFrame값 반환
            data_set (str): ProcessPaths.json에서 DirAndFile -> DataSet값 반환
        """
        # upload_dir_path 가져오기
        upload_dir_path = self.solution_paths_dict["DirAndFile"]["UploadDirPath"].format(SolutionDirPath=self.solution_dir_path, ProjectName=self.project_name)

        # data_frame_path 가져오기
        data_frame_dir_path = self.solution_paths_dict["DirAndFile"]["DataFrame"]["DataFrameDirPath"].format(SolutionDirPath=self.solution_dir_path, ProjectName=self.project_name)
        input_list_json_file_path = self.solution_paths_dict["DirAndFile"]["DataFrame"]["InputListJsonFilePath"].format(DataFrameDirPath=data_frame_dir_path, Email=self.email, ProjectName=self.project_name, ProcessNumber=self.process_number, ProcessName=self.process_name)
        middle_frame_json_file_path = self.solution_paths_dict["DirAndFile"]["DataFrame"]["MiddleFrameJsonFilePath"].format(DataFrameDirPath=data_frame_dir_path, Email=self.email, ProjectName=self.project_name, ProcessNumber=self.process_number, ProcessName=self.process_name)

        # data_set_path 가져오기
        data_set_dir_path = self.solution_paths_dict["DirAndFile"]["DataSet"]["DataSetDirPath"].format(SolutionDirPath=self.solution_dir_path, ProjectName=self.project_name)
        data_set_json_file_path = self.solution_paths_dict["DirAndFile"]["DataSet"]["DataSetJsonFilePath"].format(DataSetDirPath=data_set_dir_path, Email=self.email, ProjectName=self.project_name, ProcessNumber=self.process_number, ProcessName=self.process_name)

        return upload_dir_path, data_frame_dir_path, input_list_json_file_path, middle_frame_json_file_path, data_set_dir_path, data_set_json_file_path

    # ------------------------------------------------------------------
    # --- func-set: read mix_and_master paths --------------------------
    # --- class-func: script_segmentation_mix_and_master_path 가져오기 ---
    def _read_script_segmentation_mix_and_master_path_data(self) -> str:
        """ScriptSegmentation의 DataFrame, DataSet, Mixed, Master 디렉토리와 폴더 경로를 반환합니다.

        Returns:
            data_frame (str): ScriptSegmentationPaths.json에서 DirAndFile -> DataFrame값 반환
            data_set (str): ScriptSegmentationPaths.json에서 DirAndFile -> DataSet값 반환
            mixed (str): ScriptSegmentationPaths.json에서 DirAndFile -> Mixed값 반환
            master (str): ScriptSegmentationPaths.json에서 DirAndFile -> Master값 반환
        """
        # upload_dir_path 가져오기
        upload_dir_path = self.solution_paths_dict["DirAndFile"]["UploadDirPath"].format(SolutionDirPath=self.solution_dir_path, ProjectName=self.project_name)

        # data_frame_path 가져오기
        data_frame_dir_path = self.solution_paths_dict["DirAndFile"]["DataFrame"]["DataFrameDirPath"].format(SolutionDirPath=self.solution_dir_path, ProjectName=self.project_name)
        input_list_json_file_path = self.solution_paths_dict["DirAndFile"]["DataFrame"]["InputListJsonFilePath"].format(DataFrameDirPath=data_frame_dir_path, Email=self.email, ProcessNumber=self.process_number, ProjectName=self.project_name)
        middle_frame_json_file_path = self.solution_paths_dict["DirAndFile"]["DataFrame"]["MiddleFrameJsonFilePath"].format(DataFrameDirPath=data_frame_dir_path, Email=self.email, ProcessNumber=self.process_number, ProjectName=self.project_name)

        # data_set_path 가져오기
        data_set_dir_path = self.solution_paths_dict["DirAndFile"]["DataSet"]["DataSetDirPath"].format(SolutionDirPath=self.solution_dir_path, ProjectName=self.project_name)