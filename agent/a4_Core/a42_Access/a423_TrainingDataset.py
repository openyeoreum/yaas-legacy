import os
import json
import re
import sys
sys.path.append("/yaas")

## Dataset 경로 설정
def GetDataSetPath(projectName, email):
    DataSetPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s122_Storage/{email}/{projectName}/{projectName}_audiobook/{projectName}_dataset_audiobook_file"
    return DataSetPath

## Init TrainingDataset 경로 불러오기
def GetTrainingDatasetPath():
    TrainingDatasetPath = "/yaas/agent/a0_Database/a05_TrainingDataset/a051_TrainingDataset.json"
    return TrainingDatasetPath

## audiobookDataSetConfig 경로 설정
def GetDataSetConfigPath(projectName, email):
    DataSetConfigPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s122_Storage/{email}/{projectName}/{projectName}_audiobook/{projectName}_dataset_audiobook_file/{email}_{projectName}_AudiobookDataSet_Config.json"
    return DataSetConfigPath

## Dataset JSON 데이터 불러오기
def LoadJsonDataset(filepath):
    with open(filepath, 'r', encoding = 'utf-8') as file:
        DataDataset = json.load(file)
    return DataDataset

## DatasetName이 포함된 Dataset JSON 데이터 불러오기
def LoadExistingDataset(audiobookDatasetPath, DatasetName, InitDatasetPath):
    AllFiles = os.listdir(audiobookDatasetPath)

    # DatasetName이 포함된 파일 찾기
    for DatasetFile in AllFiles:
        if DatasetName in DatasetFile:
            DatasetPath = os.path.join(audiobookDatasetPath, DatasetFile)
            return LoadJsonDataset(DatasetPath)
        
    return LoadJsonDataset(InitDatasetPath)

## TrainingDataset Config 설정
def SetupTrainingDataset(projectName, email):
    # 디렉토리 경로 생성
    dataSetPath = GetDataSetPath(projectName, email)
    TrainingDatasetPath = GetTrainingDatasetPath()

    audiobookDataSetConfigFilePath = GetDataSetConfigPath(projectName, email)

    # JSON 데이터 불러오기
    scriptGenDataset = LoadExistingDataset(dataSetPath, "ScriptGenDataset", TrainingDatasetPath)
    bookPreprocessDataset = LoadExistingDataset(dataSetPath, "00_BookPreprocessDataSet", TrainingDatasetPath)
    indexDefinePreprocessDataset = LoadExistingDataset(dataSetPath, "01_IndexDefinePreprocessDataSet", TrainingDatasetPath)
    indexDefineDivisionPreprocessDataset = LoadExistingDataset(dataSetPath, "IndexDefineDivisionPreprocessDataset", TrainingDatasetPath)
    indexDefineDataset = LoadExistingDataset(dataSetPath, "01_IndexDefineDataSet", TrainingDatasetPath)
    duplicationPreprocessDataset = LoadExistingDataset(dataSetPath, "02-1_DuplicationPreprocessDataSet", TrainingDatasetPath)
    pronunciationPreprocessDataset = LoadExistingDataset(dataSetPath, "02-2_PronunciationPreprocessDataSet", TrainingDatasetPath)
    captionCompletionDataset = LoadExistingDataset(dataSetPath, "06_CaptionCompletionDataSet", TrainingDatasetPath)
    contextDefineDataset = LoadExistingDataset(dataSetPath, "07_ContextDefineDataSet", TrainingDatasetPath)
    contextCompletionDataset = LoadExistingDataset(dataSetPath, "08_ContextCompletionDataSet", TrainingDatasetPath)
    wMWMDefineDataset = LoadExistingDataset(dataSetPath, "09_WMWMDefineDataSet", TrainingDatasetPath)
    wMWMMatchingDataset = LoadExistingDataset(dataSetPath, "10_WMWMMatchingDataSet", TrainingDatasetPath)
    characterDefineDataset = LoadExistingDataset(dataSetPath, "11_CharacterDefineDataSet", TrainingDatasetPath)
    characterCompletionDataset = LoadExistingDataset(dataSetPath, "12_CharacterCompletionDataSet", TrainingDatasetPath)
    characterPostCompletionDataset = LoadExistingDataset(dataSetPath, "CharacterPostCompletionDataset", TrainingDatasetPath)
    characterPostCompletionLiteraryDataset = LoadExistingDataset(dataSetPath, "CharacterPostCompletionLiteraryDataset", TrainingDatasetPath)
    soundMatchingDataset = LoadExistingDataset(dataSetPath, "SoundMatchingDataset", TrainingDatasetPath)
    sfxMatchingDataset = LoadExistingDataset(dataSetPath, "15_SFXMatchingDataSet", TrainingDatasetPath)
    sfxMultiQueryDataset = LoadExistingDataset(dataSetPath, "SFXMultiQueryDataset", TrainingDatasetPath)
    translationIndexEnDataset = LoadExistingDataset(dataSetPath, "TranslationIndexEnDataset", TrainingDatasetPath)
    translationWordListEnDataset = LoadExistingDataset(dataSetPath, "TranslationWordListEnDataset", TrainingDatasetPath)
    translationBodyEnDataset = LoadExistingDataset(dataSetPath, "TranslationBodyEnDataset", TrainingDatasetPath)
    translationIndexJaDataset = LoadExistingDataset(dataSetPath, "TranslationIndexJaDataset", TrainingDatasetPath)
    translationWordListJaDataset = LoadExistingDataset(dataSetPath, "TranslationWordListJaDataset", TrainingDatasetPath)
    translationBodyJaDataset = LoadExistingDataset(dataSetPath, "TranslationBodyJaDataset", TrainingDatasetPath)
    translationIndexZhDataset = LoadExistingDataset(dataSetPath, "TranslationIndexZhDataset", TrainingDatasetPath)
    translationWordListZhDataset = LoadExistingDataset(dataSetPath, "TranslationWordListZhDataset", TrainingDatasetPath)
    translationBodyZhDataset = LoadExistingDataset(dataSetPath, "TranslationBodyZhDataset", TrainingDatasetPath)
    translationIndexEsDataset = LoadExistingDataset(dataSetPath, "TranslationIndexEsDataset", TrainingDatasetPath)
    translationWordListEsDataset = LoadExistingDataset(dataSetPath, "TranslationWordListEsDataset", TrainingDatasetPath)
    translationBodyEsDataset = LoadExistingDataset(dataSetPath, "TranslationBodyEsDataset", TrainingDatasetPath)
    correctionKoDataset = LoadExistingDataset(dataSetPath, "21_CorrectionKoDataSet", TrainingDatasetPath)

    ## audiobookDataSetConfig 생성
    if not os.path.exists(audiobookDataSetConfigFilePath):
        audiobookDataSetConfig = {
            "ProjectName": projectName,
            "ScriptGen": scriptGenDataset,
            "BookPreprocess": bookPreprocessDataset,
            "IndexDefinePreprocess": indexDefinePreprocessDataset,
            "IndexDefineDivisionPreprocess": indexDefineDivisionPreprocessDataset,
            "IndexDefine": indexDefineDataset,
            "DuplicationPreprocess": duplicationPreprocessDataset,
            "PronunciationPreprocess": pronunciationPreprocessDataset,
            "CaptionCompletion": captionCompletionDataset,
            "ContextDefine": contextDefineDataset,
            "ContextCompletion": contextCompletionDataset,
            "WMWMDefine": wMWMDefineDataset,
            "WMWMMatching": wMWMMatchingDataset,
            "CharacterDefine": characterDefineDataset,
            "CharacterCompletion": characterCompletionDataset,
            "CharacterPostCompletion": characterPostCompletionDataset,
            "CharacterPostCompletionLiterary": characterPostCompletionLiteraryDataset,
            "SoundMatching": soundMatchingDataset,
            "SFXMatching": sfxMatchingDataset,
            "SFXMultiQuery": sfxMultiQueryDataset,
            "TranslationIndexEn": translationIndexEnDataset,
            "TranslationWordListEn": translationWordListEnDataset,
            "TranslationBodyEn": translationBodyEnDataset,
            "TranslationIndexJa": translationIndexJaDataset,
            "TranslationWordListJa": translationWordListJaDataset,
            "TranslationBodyJa": translationBodyJaDataset,
            "TranslationIndexZh": translationIndexZhDataset,
            "TranslationWordListZh": translationWordListZhDataset,
            "TranslationBodyZh": translationBodyZhDataset,
            "TranslationIndexEs": translationIndexEsDataset,
            "TranslationWordListEs": translationWordListEsDataset,
            "TranslationBodyEs": translationBodyEsDataset,
            "CorrectionKo": correctionKoDataset,
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