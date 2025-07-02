import os
import sys
import json
sys.path.append("/yaas")

def GetTrainingDatasetPath():
    TrainingDatasetPath = "/yaas/agent/a5_Database/a55_TrainingDataset/a551_TrainingDataset.json"
    return TrainingDatasetPath

def GetDataSetConfigPath(projectName, email):
    PDataSetConfigPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_audiobook/{projectName}_dataset_audiobook_file/{email}_{projectName}_AudiobookDataSet_Config.json"
    return PDataSetConfigPath

def LoadJsonDataset(filepath):
    with open(filepath, 'r') as file:
        DataDataset = json.load(file)
    return DataDataset

def SetupTrainingDataset(projectName, email):
    # 디렉토리 경로 생성
    TrainingDatasetPath = GetTrainingDatasetPath()

    audiobookDataSetConfigFilePath = GetDataSetConfigPath(projectName, email)

    # JSON 데이터 불러오기
    trainingDataset = LoadJsonDataset(TrainingDatasetPath)

    ## audiobookDataSetConfig 생성
    if not os.path.exists(audiobookDataSetConfigFilePath):
        audiobookDataSetConfig = {
            "ProjectName": projectName,
            "ScriptGen": trainingDataset,
            "BookPreprocess": trainingDataset,
            "IndexDefinePreprocess": trainingDataset,
            "IndexDefineDivisionPreprocess": trainingDataset,
            "IndexDefine": trainingDataset,
            "DuplicationPreprocess": trainingDataset,
            "PronunciationPreprocess": trainingDataset,
            "CaptionCompletion": trainingDataset,
            # "TransitionPhargraph": trainingDataset,
            "ContextDefine": trainingDataset,
            "ContextCompletion": trainingDataset,
            "WMWMDefine": trainingDataset,
            "WMWMMatching": trainingDataset,
            "CharacterDefine": trainingDataset,
            "CharacterCompletion": trainingDataset,
            "CharacterPostCompletion": trainingDataset,
            "CharacterPostCompletionLiterary": trainingDataset,
            "SoundMatching": trainingDataset,
            "SFXMatching": trainingDataset,
            "SFXMultiQuery": trainingDataset,
            "TranslationIndexEn": trainingDataset,
            "TranslationWordListEn": trainingDataset,
            "TranslationBodyEn": trainingDataset,
            "TranslationIndexJa": trainingDataset,
            "TranslationWordListJa": trainingDataset,
            "TranslationBodyJa": trainingDataset,
            "TranslationIndexZh": trainingDataset,
            "TranslationWordListZh": trainingDataset,
            "TranslationBodyZh": trainingDataset,
            "TranslationIndexEs": trainingDataset,
            "TranslationWordListEs": trainingDataset,
            "TranslationBodyEs": trainingDataset,
            # "TranslationEn": trainingDataset,
            "CorrectionKo": trainingDataset,
            # "CorrectionEn": trainingDataset,
            ### 아래로 추가되는 데이터셋 작성 ###
        }
        ## 데이터셋 설정 생성
        with open(audiobookDataSetConfigFilePath, 'w', encoding = 'utf-8') as ConfigFile:
            json.dump(audiobookDataSetConfig, ConfigFile, ensure_ascii = False, indent = 4)

        print(f"[ Email: {email} | ProjectName: {projectName} | AudiobookDataSetConfig 완료 ]")
    else:
        print(f"[ Email: {email} | ProjectName: {projectName} | ExistedAudiobookDataSetConfig로 대처됨 ]")
         
if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    name = "yeoreum"
    projectName = "우리는행복을진단한다"
    #########################################################################
    
    SetupTrainingDataset(projectName, email)