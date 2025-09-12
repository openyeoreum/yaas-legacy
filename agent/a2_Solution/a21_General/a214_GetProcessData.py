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
        "JsonParsing": "/a541_DataCollectionPrompt/a5410_GeneralPrompt/a5412-01_JsonParsingPrompt.json",
        # DataCollectionPrompt
        "DemandCollectionDataDetail": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-01_DemandCollectionDataDetail.json",
        "DemandCollectionDataContext": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-02_DemandCollectionDataContext.json",
        "DemandCollectionDataExpertise": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-03-1_DemandCollectionDataExpertise.json",
        "DemandCollectionDataExpertiseChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-03-2_DemandCollectionDataExpertiseChain.json",
        "DemandCollectionDataUltimate": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-04-1_DemandCollectionDataUltimate.json",
        "DemandCollectionDataUltimateChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-04-2_DemandCollectionDataUltimateChain.json",
        "SupplyCollectionDataDetail": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-01_SupplyCollectionDataDetail.json",
        "SupplyCollectionDataContext": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-02_SupplyCollectionDataContext.json",
        "SupplyCollectionDataExpertise": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-03-1_SupplyCollectionDataExpertise.json",
        "SupplyCollectionDataExpertiseChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-03-2_SupplyCollectionDataExpertiseChain.json",
        "SupplyCollectionDataUltimate": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-04-1_SupplyCollectionDataUltimate.json",
        "SupplyCollectionDataUltimateChain": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-04-2_SupplyCollectionDataUltimateChain.json",
        "DemandSearchCollectionDataFilter": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-01_DemandSearchCollectionDataFilter.json",
        "SupplySearchCollectionDataFilter": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-02_SupplySearchCollectionDataFilter.json",
        "SimilaritySearchCollectionDataFilter": "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-03_SimilaritySearchCollectionDataFilter.json",
        "PublisherContextDefine": "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-01_PublisherContextDefine.json",
        "PublisherWMWMDefine": "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-02_PublisherWMWMDefine.json",
        "PublisherServiceDemand": "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-03_PublisherServiceDemand.json",
        "BestSellerContextDefine": "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-01_BestSellerContextDefine.json",
        "BestSellerWMWMDefine": "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-02_BestSellerWMWMDefine.json",
        "BestSellerCommentAnalysis": "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-03_BestSellerCommentAnalysis.json",
        # BookScriptPrompt
        "DemandScriptPlan": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-01_DemandScriptPlan.json",
        "SupplyScriptPlan": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-02_SupplyScriptPlan.json",
        "SimilarityScriptPlan": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-03_SimilarityScriptPlan.json",
        "ScriptPlanFeedback": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-04_ScriptPlanFeedback.json",
        "TitleAndIndexGen": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-05_TitleAndIndexGen.json",
        "TitleAndIndexGenFeedback": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-06_TitleAndIndexGenFeedback.json",
        "SummaryOfIndexGen": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-07_SummaryOfIndexGen.json",
        "SummaryOfIndexGenFeedback": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-08_SummaryOfIndexGenFeedback.json",
        "ScriptIntroductionGen": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-09_ScriptIntroductionGen.json",
        "ScriptIntroductionGenFeedback": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-10_ScriptIntroductionGenFeedback.json",
        "ShortScriptGen": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-11_ShortScriptGen.json",
        "ShortScriptGenFeedback": "/a542_ScriptPrompt/a5421_BookScriptGenPrompt/a5421-12_ShortScriptGenFeedback.json",
        # ScriptSegmentationPrompt
        "ScriptLoad": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-PT01_ScriptLoad.json",
        "PDFMainLangCheck": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-P02_PDFMainLangCheck.json",
        "PDFLayoutCheck": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-P03_PDFLayoutCheck.json",
        "PDFResize": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-P04_PDFResize.json",
        "PDFSplit": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-P05_PDFSplit.json",
        "PDFFormCheck": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-P06_PDFFormCheck.json",
        "TXTSplit": "/a542_ScriptPrompt/a5422_ScriptSegmentationPrompt/a5422-T03_TXTSplit.json",
        # TranslationPrompt
        "TranslationIndexDefine": "/a543_TranslationPrompt/a543-01_TranslationIndexDefine.json",
        "TranslationBodySummary": "/a543_TranslationPrompt/a543-02_TranslationBodySummary.json",
        "WordListGen": "/a543_TranslationPrompt/a543-03_WordListGen.json",
        "UniqueWordListGen": "/a543_TranslationPrompt/a543-04_UniqueWordListGen.json",
        "WordListPostprocessing": "/a543_TranslationPrompt/a543-05_WordListPostprocessing.json",
        "IndexTranslation": "/a543_TranslationPrompt/a543-06_IndexTranslation.json",
        "BodyTranslationPreprocessing": "/a543_TranslationPrompt/a543-07_BodyTranslationPreprocessing.json",
        "BodyTranslation": "/a543_TranslationPrompt/a543-08_BodyTranslation.json",
        "BodyTranslationCheck": "/a543_TranslationPrompt/a543-08_BodyTranslationCheck.json",
        "BodyToneEditing": "/a543_TranslationPrompt/a543-08_BodyToneEditing.json",
        "BodyLanguageEditing": "/a543_TranslationPrompt/a543-08_BodyLanguageEditing.json",
        "BodyTranslationWordCheck": "/a543_TranslationPrompt/a543-08_BodyTranslationWordCheck.json",
        "TranslationEditing": "/a543_TranslationPrompt/a543-09_TranslationEditing.json",
        "TranslationRefinement": "/a543_TranslationPrompt/a543-09_TranslationRefinement.json",
        "TranslationKinfolkStyleRefinement": "/a543_TranslationPrompt/a543-09_TranslationKinfolkStyleRefinement.json",
        "TranslationProofreading": "/a543_TranslationPrompt/a543-10_TranslationProofreading.json",
        "TranslationDialogueAnalysis": "/a543_TranslationPrompt/a543-11_TranslationDialogueAnalysis.json",
        "TranslationDialogueEditing": "/a543_TranslationPrompt/a543-12_TranslationDialogueEditing.json",
        "AfterTranslationBodySummary": "/a543_TranslationPrompt/a543-14_AfterTranslationBodySummary.json",
        "AuthorResearch": "/a543_TranslationPrompt/a543-15_AuthorResearch.json",
        "TranslationCatchphrase": "/a543_TranslationPrompt/a543-16_TranslationCatchphrase.json",
        "TranslationFundingCatchphrase": "/a543_TranslationPrompt/a543-17_TranslationFundingCatchphrase.json",
        # AudioBookPrompt
        "BookPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-00_BookPreprocess.json",
        "IndexDefinePreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-01_IndexDefinePreprocess.json",
        "IndexDefineDivisionPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-02_IndexDefineDivisionPreprocess.json",
        "IndexDefine": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-03_IndexDefine.json",
        "DuplicationPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-04_DuplicationPreprocess.json",
        "PronunciationPreprocess": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-05_PronunciationPreprocess.json",
        "CaptionCompletion": "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-06_CaptionCompletion.json",
        "ContextDefine": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-01_ContextDefine.json",
        "ContextCompletion": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-02_ContextCompletion.json",
        "WMWMDefine": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-03_WMWMDefine.json",
        "WMWMMatching": "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-04_WMWMMatching.json",
        "CharacterDefine": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-01_CharacterDefine.json",
        "CharacterCompletion": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-02_CharacterCompletion.json",
        "CharacterPostCompletion": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-03_CharacterPostCompletion.json",
        "CharacterPostCompletionLiterary": "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-04_CharacterPostCompletionLiterary.json",
        "SoundMatching": "/a545_AudioBookPrompt/a5455_SoundPrompt/a5455-01_SoundMatching.json",
        "SFXMatching": "/a545_AudioBookPrompt/a5456_SFXPrompt/a5456-01_SFXMatching.json",
        "SFXMultiQuery": "/a545_AudioBookPrompt/a5456_SFXPrompt/a5456-02_SFXMultiQuery.json",
        "TranslationIndexEn": "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-01_TranslationIndexEn.json",
        "CorrectionKo": "/a545_AudioBookPrompt/a5458_CorrectionPrompt/a5458-01_CorrectionKo.json",
        "ActorMatching": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-01_ActorMatching.json",
        "SentsSpliting": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-03_SentsSpliting.json",
        "VoiceInspection": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-04_VoiceInspection.json",
        "VoiceSplit": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-05_VoiceSplit.json",
        "VoiceSplitInspection": "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-06_VoiceSplitInspection.json",
    }

    # MainLang 태그 설정
    if MainLang.lower() == "ko":
        MainLangTag = "ko"
    else:
        MainLangTag = "global"

    # Process 인수가 맵에 있는지 확인
    if Process in PromptFileMap:
        RelativePath = PromptFileMap[Process]
        FullFilePath = PromptDataPath + RelativePath
        PromptFrame = LoadJsonFrame(FullFilePath)[MainLangTag]
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