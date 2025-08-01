import os
import shutil
import PyPDF2
import json
import sys
from PyPDF2 import PdfWriter
sys.path.append("/yaas")

#########################
##### Script 불러오기 #####
#########################
## Load1-1: Script 로드
def LoadScript(projectName, email, Solution, ScriptDataFramePath, ProjectDataFrameScriptCheckPath, AutoSegmentation = "No"):
    ## 1. 결과 파일이 이미 존재하는지 확인, 존재하면 해당 내용을 리턴
    ScriptCheckJsonPath = os.path.join(ProjectDataFrameScriptCheckPath)
    if not os.path.exists(ScriptCheckJsonPath):

        ## 2. 스크립트 파일 디렉토리 경로 설정
        ScriptDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_script/{projectName}_upload_script_file"

        ## 3. 디렉토리 내에서 스크립트 파일 찾기
        AllFiles = os.listdir(ScriptDirPath)
        TxtFiles = [f for f in AllFiles if f.lower().endswith(".txt")]
        PdfFiles = [f for f in AllFiles if f.lower().endswith(".pdf")]

        ## 4. 파일 추출, 여러 파일이 있을 경우 .txt 파일을 우선 선택
        TargetFileName = None
        FileExtension = None

        if TxtFiles:
            TargetFileName = TxtFiles[0]
            FileExtension = ".txt"
        elif PdfFiles:
            TargetFileName = PdfFiles[0]
            FileExtension = ".pdf"
        else:
            ## 처리할 스크립트 파일이 없는 경우 함수 종료
            sys.exit(f"\n\n[ 원고 파일(txt, pdf)를 아래 경로에 복사해주세요. ]\n({ScriptDirPath})\n\n")
        
        ## 5. 원본 파일을 복사하여 새로운 이름으로 저장
        OriginalFilePath = os.path.join(ScriptDirPath, TargetFileName)

        NewFileName = f"{projectName}_Script({Solution}){FileExtension}"
        NewFilePath = os.path.join(ScriptDirPath, NewFileName)
        shutil.copy2(OriginalFilePath, NewFilePath)

        ## 6. 파일 확장자에 따라 내용을 추출
        FileContent = ""
        FileExtensionTag = FileExtension
        
        if FileExtension == ".txt":
            with open(OriginalFilePath, 'r', encoding='utf-8') as File:
                FileContent = File.read()
            FileExtensionTag = "txt"
        
        elif FileExtension == ".pdf":
            PdfReader = PyPDF2.PdfReader(OriginalFilePath)
            
            # PDF 페이지별로 분할 저장할 폴더 생성
            PdfDirPath = os.path.join(ScriptDirPath, f"{projectName}_Script({Solution})_pdf")
            os.makedirs(PdfDirPath, exist_ok = True)
            
            # PDF 페이지별로 분할하여 저장
            for PageNum, Page in enumerate(PdfReader.pages):
                PageContent = Page.extract_text() or ""
                FileContent += PageContent
                
                # 각 페이지를 별도 PDF로 저장
                PdfWriter_instance = PdfWriter()
                PdfWriter_instance.add_page(Page)
                PageFilePath = os.path.join(PdfDirPath, f"{projectName}_Script({Solution})_{PageNum}.pdf")
                with open(PageFilePath, 'wb') as PageFile:
                    PdfWriter_instance.write(PageFile)
            
            # PDF 내용 유무에 따라 확장자 분류
            if FileContent.strip():
                FileExtensionTag = "pdf(text)"
            else:
                FileExtensionTag = "pdf(Image)"

        ## 7. 추출된 정보로 ScriptCheckDataFrame 생성
        ScriptCheckDataFramePath = os.path.join(ScriptDataFramePath, f"a5312-00_ScriptCheckFrame.json")
        # ScriptCheckDataFrame 불러오기
        with open(ScriptCheckDataFramePath, 'r', encoding = 'utf-8') as ScriptCheckDataFrameJson:
            ScriptCheck = json.load(ScriptCheckDataFrameJson)

        # ScriptCheckDataFrame 업데이트
        ScriptCheck[0]['ProjectName'] = projectName
        ScriptCheck[0]['FileExtension'] = FileExtensionTag
        ScriptCheck[0]['Solution'] = Solution
        ScriptCheck[0]['AutoSegmentation'] = AutoSegmentation

        # ScriptCheckDataFrame 저장
        with open(ProjectDataFrameScriptCheckPath, 'w', encoding = 'utf-8') as ScriptCheckDataFrameJson:
            json.dump(ScriptCheck, ScriptCheckDataFrameJson, ensure_ascii = False, indent = 4)

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '250516_업데이트'
    Solution = 'Translation'
    ScriptDataFramePath = '/yaas/agent/a5_Database/a53_ProjectData/a531_ScriptProject/a5313_ScriptUpload'
    ProjectScriptDataFramePath = f'/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_script/{projectName}_dataframe_script_file'
    ProjectDataFrameScriptCheckPath = os.path.join(ProjectScriptDataFramePath, f"{email}_{projectName}_01_ScriptCheckDataFrame({Solution}).json")
    #########################################################################
    LoadScript(projectName, email, Solution, ScriptDataFramePath, ProjectDataFrameScriptCheckPath, AutoSegmentation = "Yes")