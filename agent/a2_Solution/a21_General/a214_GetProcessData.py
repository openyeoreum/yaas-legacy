import os
import sys
import json
sys.path.append("/yaas")

from agent.a2_Solution.a21_General.a212_Project import GetProjectConfigPath
from agent.a2_Solution.a21_General.a213_TrainingDataset import GetDataSetConfigPath

## JSON 파일을 불러오는 함수
def LoadJsonFrame(FilePath):
    with open(FilePath, 'r', encoding = 'utf-8') as JsonFrame: # 변수명 변경: FilePath
        DataFrame = json.load(JsonFrame) # 변수명 변경: DataFrame
    return DataFrame

## JSON 파일을 저장하는 함수
def SaveJsonData(FilePath, Data):
    with open(FilePath, 'w', encoding = 'utf-8') as JsonData:
        json.dump(Data, JsonData, ensure_ascii = False, indent = 4)

##########################
##########################
##### GetPromptFrame #####
##########################
##########################

## PromptFrame을 가져오는 함수
def GetPromptFrame(Process, MainLang):

    PromptDataPath = "/yaas/agent/a5_Database/a54_PromptData"
    PromptFileMap = {
        # GeneralPrompt
        "JsonParsing": "/a541_DataCollectionPrompt/a5410_GeneralPrompt/a5412-01_JsonParsingPrompt",
        # DataCollectionPrompt
        "DemandCollectionDataDetail": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-01_DemandCollectionDataDetail",
        "DemandCollectionDataContext": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-02_DemandCollectionDataContext",
        "DemandCollectionDataExpertise": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-03-1_DemandCollectionDataExpertise",
        "DemandCollectionDataExpertiseChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-03-2_DemandCollectionDataExpertiseChain",
        "DemandCollectionDataUltimate": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-04-1_DemandCollectionDataUltimate",
        "DemandCollectionDataUltimateChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-04-2_DemandCollectionDataUltimateChain",
        "SupplyCollectionDataDetail": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-01_SupplyCollectionDataDetail",
        "SupplyCollectionDataContext": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-02_SupplyCollectionDataContext",
        "SupplyCollectionDataExpertise": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-03-1_SupplyCollectionDataExpertise",
        "SupplyCollectionDataExpertiseChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-03-2_SupplyCollectionDataExpertiseChain",
        "SupplyCollectionDataUltimate": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-04-1_SupplyCollectionDataUltimate",
        "SupplyCollectionDataUltimateChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-04-2_SupplyCollectionDataUltimateChain",
        "DemandSearchCollectionDataFilter": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-01_DemandSearchCollectionDataFilter",
        "SupplySearchCollectionDataFilter": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-02_SupplySearchCollectionDataFilter",
        "SimilaritySearchCollectionDataFilter": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-03_SimilaritySearchCollectionDataFilter",
        "PublisherContextDefine": "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-01_PublisherContextDefine",
        "PublisherWMWMDefine": "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-02_PublisherWMWMDefine",
        "PublisherServiceDemand": "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-03_PublisherServiceDemand",
        "BestSellerContextDefine": "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-01_BestSellerContextDefine",
        "BestSellerWMWMDefine": "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-02_BestSellerWMWMDefine",
        "BestSellerCommentAnalysis": "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-03_BestSellerCommentAnalysis",
        # InstantScriptPrompt
        "ChangesAfterMeditation_Script": "/a542_ScriptPrompt/a5421_InstantScriptPrompt/a5421-01_ChangesAfterMeditation_Script",
        "SejongCityOfficeOfEducation_Poem": "/a542_ScriptPrompt/a5421_InstantScriptPrompt/a5421-02_SejongCityOfficeOfEducation_Poem",
        # BookScriptPrompt
        "DemandScriptPlan": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5422-01_DemandScriptPlan",
        "SupplyScriptPlan": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-02_SupplyScriptPlan",
        "SimilarityScriptPlan": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-03_SimilarityScriptPlan",
        "ScriptPlanFeedback": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-04_ScriptPlanFeedback",
        "TitleAndIndexGen": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-05_TitleAndIndexGen",
        "TitleAndIndexGenFeedback": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-06_TitleAndIndexGenFeedback",
        "SummaryOfIndexGen": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-07_SummaryOfIndexGen",
        "SummaryOfIndexGenFeedback": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-08_SummaryOfIndexGenFeedback",
        "ScriptIntroductionGen": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-09_ScriptIntroductionGen",
        "ScriptIntroductionGenFeedback": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-10_ScriptIntroductionGenFeedback",
        "ShortScriptGen": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-11_ShortScriptGen",
        "ShortScriptGenFeedback": "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-12_ShortScriptGenFeedback",
        # ScriptUploadPrompt
        "PDFMainLangCheck": "/a542_ScriptPrompt/a5423_ScriptUploadPrompt/a5423-P02_PDFMainLangCheck",
        # TranslationPrompt
        "TranslationIndexDefine": "/a543_TranslationPrompt/a543-01_TranslationIndexDefine",
        "TranslationBodySummary": "/a543_TranslationPrompt/a543-02_TranslationBodySummary",
        "WordListGen": "/a543_TranslationPrompt/a543-03_WordListGen",
        "UniqueWordListGen": "/a543_TranslationPrompt/a543-04_UniqueWordListGen",
        "WordListPostprocessing": "/a543_TranslationPrompt/a543-05_WordListPostprocessing",
        "IndexTranslation": "/a543_TranslationPrompt/a543-06_IndexTranslation",
        "BodyTranslationPreprocessing": "/a543_TranslationPrompt/a543-07_BodyTranslationPreprocessing",
        "BodyTranslation": "/a543_TranslationPrompt/a543-08_BodyTranslation",
        "BodyTranslationCheck": "/a543_TranslationPrompt/a543-08_BodyTranslationCheck",
        "BodyToneEditing": "/a543_TranslationPrompt/a543-08_BodyToneEditing",
        "BodyLanguageEditing": "/a543_TranslationPrompt/a543-08_BodyLanguageEditing",
        "BodyTranslationWordCheck": "/a543_TranslationPrompt/a543-08_BodyTranslationWordCheck",
        "TranslationEditing": "/a543_TranslationPrompt/a543-09_TranslationEditing",
        "TranslationRefinement": "/a543_TranslationPrompt/a543-09_TranslationRefinement",
        "TranslationKinfolkStyleRefinement": "/a543_TranslationPrompt/a543-09_TranslationKinfolkStyleRefinement",
        "TranslationProofreading": "/a543_TranslationPrompt/a543-10_TranslationProofreading",
        "TranslationDialogueAnalysis": "/a543_TranslationPrompt/a543-11_TranslationDialogueAnalysis",
        "TranslationDialogueEditing": "/a543_TranslationPrompt/a543-12_TranslationDialogueEditing",
        "AfterTranslationBodySummary": "/a543_TranslationPrompt/a543-14_AfterTranslationBodySummary",
        "AuthorResearch": "/a543_TranslationPrompt/a543-15_AuthorResearch",
        "TranslationCatchphrase": "/a543_TranslationPrompt/a543-16_TranslationCatchphrase",
        "TranslationFundingCatchphrase": "/a543_TranslationPrompt/a543-17_TranslationFundingCatchphrase",
        # AudioBookPrompt
        "BookPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-00_BookPreprocess",
        "IndexDefinePreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-01_IndexDefinePreprocess",
        "IndexDefineDivisionPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-02_IndexDefineDivisionPreprocess",
        "IndexDefine": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-03_IndexDefine",
        "DuplicationPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-04_DuplicationPreprocess",
        "PronunciationPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-05_PronunciationPreprocess",
        "CaptionCompletion": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-06_CaptionCompletion",
        "ContextDefine": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-01_ContextDefine",
        "ContextCompletion": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-02_ContextCompletion",
        "WMWMDefine": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-03_WMWMDefine",
        "WMWMMatching": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-04_WMWMMatching",
        "CharacterDefine": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-01_CharacterDefine",
        "CharacterCompletion": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-02_CharacterCompletion",
        "CharacterPostCompletion": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-03_CharacterPostCompletion",
        "CharacterPostCompletionLiterary": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-04_CharacterPostCompletionLiterary",
        "SoundMatching": "/a545_AudioBookPrompt/a5455_SoundPrompt/a5455-01_SoundMatching",
        "SFXMatching": "/a545_AudioBookPrompt/a5456_SFXPrompt/a5456-01_SFXMatching",
        "SFXMultiQuery": "/a545_AudioBookPrompt/a5456_SFXPrompt/a5456-02_SFXMultiQuery",
        "TranslationIndexEn": "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-01_TranslationIndexEn",
        "CorrectionKo": "/a545_AudioBookPrompt/a5458_CorrectionPrompt/a5458-01_CorrectionKo",
        "ActorMatching": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-01_ActorMatching",
        "SentsSpliting": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-03_SentsSpliting",
        "VoiceInspection": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-04_VoiceInspection",
        "VoiceSplit": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-05_VoiceSplit",
        "VoiceSplitInspection": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-06_VoiceSplitInspection",
    }

    # MainLang 태그 설정
    if MainLang.lower() == "ko":
        MainLangTag = "(ko).json"
    else:
        MainLangTag = "(en).json"

    # Process 인수가 맵에 있는지 확인
    if Process in PromptFileMap:
        RelativePath = PromptFileMap[Process] + MainLangTag # 변수명 변경: RelativePath
        FullFilePath = PromptDataPath + RelativePath # 변수명 변경: FullFilePath
        PromptFrame = LoadJsonFrame(FullFilePath) # 변수명 변경: PromptFrame
        return PromptFrame
    else:
        return None

###########################
###########################
##### GetSoundDataSet #####
###########################
###########################

## SoundDataSet을 가져오는 함수
def GetSoundDataSet(soundDataSet):

    SoundDataPath = "/yaas/agent/a5_Database/a57_RelationalDatabase"
    SoundFileMap = {
        "VoiceDataSet": "/a572_Character/a572-01_VoiceDataSet.json",
        "LogoDataSet": "/a573_Logo/a573-01_LogoDataSet.json",
        "IntroDataSet": "/a574_Intro/a574-01_IntroDataSet.json",
        "TitleMusicDataSet": "/a575_Music/a575-01_TitleMusicDataSet.json",
    }

    # soundDataSet 인수가 맵에 있는지 확인
    if soundDataSet in SoundFileMap:
        RelativePath = SoundFileMap[soundDataSet]
        FullFilePath = SoundDataPath + RelativePath
        SoundFrame = LoadJsonFrame(FullFilePath)
        return SoundFrame
    else:
        return None

#####################
#####################
##### GetScript #####
#####################
#####################

## Project를 가져오는 함수
def GetScript(projectName, email, Option):
# 경로 설정
    ScriptDirPath = f"/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage/{email}/{projectName}/{projectName}_script/{projectName}_upload_script_file"
    ScriptTextPath = os.path.join(ScriptDirPath, f"{projectName}_{Option}.txt")
    with open(ScriptTextPath, 'r', encoding = 'utf-8') as file:
        ScriptText = file.read()
    return ScriptText

##############################
##############################
##### GetTrainingDataset #####
##############################
##############################

## TrainingDataset을 가져오는 함수
def GetTrainingDataset(projectName, email):
    trainingDataset = LoadJsonFrame(GetDataSetConfigPath(projectName, email))
    return trainingDataset

## TrainingDataset을 저장하는 함수
def SaveTrainingDataset(projectName, email, trainingDataset):
    trainingDatasetPath = GetDataSetConfigPath(projectName, email)
    SaveJsonData(trainingDatasetPath, trainingDataset)

######################
######################
##### GetProject #####
######################
######################

## Project를 가져오는 함수
def GetProject(projectName, email):
    project = LoadJsonFrame(GetProjectConfigPath(projectName, email))
    return project

## Project를 저장하는 함수
def SaveProject(projectName, email, project):
    projectPath = GetProjectConfigPath(projectName, email)
    SaveJsonData(projectPath, project)

if __name__ == "__main__":
    
    GetPromptFrame("IndexDefinePreprocess")