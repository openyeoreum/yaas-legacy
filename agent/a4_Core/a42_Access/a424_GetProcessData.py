import os
import sys
import json
sys.path.append("/yaas")

from agent.a4_Core.a42_Access.a422_Project import GetProjectConfigPath
from agent.a4_Core.a42_Access.a423_TrainingDataset import GetDataSetConfigPath

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

    PromptDataPath = "/yaas/agent/a2_Database/a24_PromptData"
    PromptFileMap = {
        # GeneralPrompt
        "JsonParsing": "/a241_DataCollectionPrompt/a2410_GeneralPrompt/a2412-01_JsonParsingPrompt.json",
        # DataCollectionPrompt
        "DemandCollectionDataDetail": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24111_DemandCollectionDataGenPrompt/a24111-01_DemandCollectionDataDetail.json",
        "DemandCollectionDataContext": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24111_DemandCollectionDataGenPrompt/a24111-02_DemandCollectionDataContext.json",
        "DemandCollectionDataExpertise": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24111_DemandCollectionDataGenPrompt/a24111-03-1_DemandCollectionDataExpertise.json",
        "DemandCollectionDataExpertiseChain": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24111_DemandCollectionDataGenPrompt/a24111-03-2_DemandCollectionDataExpertiseChain.json",
        "DemandCollectionDataUltimate": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24111_DemandCollectionDataGenPrompt/a24111-04-1_DemandCollectionDataUltimate.json",
        "DemandCollectionDataUltimateChain": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24111_DemandCollectionDataGenPrompt/a24111-04-2_DemandCollectionDataUltimateChain.json",
        "SupplyCollectionDataDetail": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24112_SupplyCollectionDataGenPrompt/a24112-01_SupplyCollectionDataDetail.json",
        "SupplyCollectionDataContext": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24112_SupplyCollectionDataGenPrompt/a24112-02_SupplyCollectionDataContext.json",
        "SupplyCollectionDataExpertise": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24112_SupplyCollectionDataGenPrompt/a24112-03-1_SupplyCollectionDataExpertise.json",
        "SupplyCollectionDataExpertiseChain": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24112_SupplyCollectionDataGenPrompt/a24112-03-2_SupplyCollectionDataExpertiseChain.json",
        "SupplyCollectionDataUltimate": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24112_SupplyCollectionDataGenPrompt/a24112-04-1_SupplyCollectionDataUltimate.json",
        "SupplyCollectionDataUltimateChain": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24112_SupplyCollectionDataGenPrompt/a24112-04-2_SupplyCollectionDataUltimateChain.json",
        "DemandSearchCollectionDataFilter": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24113_SearchCollectionDataFilterPrompt/a24113-01_DemandSearchCollectionDataFilter.json",
        "SupplySearchCollectionDataFilter": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24113_SearchCollectionDataFilterPrompt/a24113-02_SupplySearchCollectionDataFilter.json",
        "SimilaritySearchCollectionDataFilter": "/a241_DataCollectionPrompt/a2411_CollectionDataGenPrompt/a24113_SearchCollectionDataFilterPrompt/a24113-03_SimilaritySearchCollectionDataFilter.json",
        "PublisherContextDefine": "/a241_DataCollectionPrompt/a2412_TargetDataPrompt/a2412-01_PublisherContextDefine.json",
        "PublisherWMWMDefine": "/a241_DataCollectionPrompt/a2412_TargetDataPrompt/a2412-02_PublisherWMWMDefine.json",
        "PublisherServiceDemand": "/a241_DataCollectionPrompt/a2412_TargetDataPrompt/a2412-03_PublisherServiceDemand.json",
        "BestSellerContextDefine": "/a241_DataCollectionPrompt/a2413_TrendDataPrompt/a2413-01_BestSellerContextDefine.json",
        "BestSellerWMWMDefine": "/a241_DataCollectionPrompt/a2413_TrendDataPrompt/a2413-02_BestSellerWMWMDefine.json",
        "BestSellerCommentAnalysis": "/a241_DataCollectionPrompt/a2413_TrendDataPrompt/a2413-03_BestSellerCommentAnalysis.json",
        # BookScriptPrompt
        "DemandScriptPlan": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-01_DemandScriptPlan.json",
        "SupplyScriptPlan": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-02_SupplyScriptPlan.json",
        "SimilarityScriptPlan": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-03_SimilarityScriptPlan.json",
        "ScriptPlanFeedback": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-04_ScriptPlanFeedback.json",
        "TitleAndIndexGen": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-05_TitleAndIndexGen.json",
        "TitleAndIndexGenFeedback": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-06_TitleAndIndexGenFeedback.json",
        "SummaryOfIndexGen": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-07_SummaryOfIndexGen.json",
        "SummaryOfIndexGenFeedback": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-08_SummaryOfIndexGenFeedback.json",
        "ScriptIntroductionGen": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-09_ScriptIntroductionGen.json",
        "ScriptIntroductionGenFeedback": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-10_ScriptIntroductionGenFeedback.json",
        "ShortScriptGen": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-11_ShortScriptGen.json",
        "ShortScriptGenFeedback": "/a242_ScriptPrompt/a2421_BookScriptGenPrompt/a2421-12_ShortScriptGenFeedback.json",
        # ScriptSegmentationPrompt
        "ScriptLoad": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-PT01_ScriptLoad.json",
        "PDFMainLangCheck": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-P02_PDFMainLangCheck.json",
        "PDFLayoutCheck": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-P03_PDFLayoutCheck.json",
        "PDFResize": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-P04_PDFResize.json",
        "PDFSplit": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-P05_PDFSplit.json",
        "PDFFormCheck": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-P06_PDFFormCheck.json",
        "TXTSplit": "/a242_ScriptPrompt/a2422_ScriptSegmentationPrompt/a2422-T03_TXTSplit.json",
        # TranslationPrompt
        "TranslationIndexDefine": "/a243_TranslationPrompt/a243-01_TranslationIndexDefine.json",
        "TranslationBodySummary": "/a243_TranslationPrompt/a243-02_TranslationBodySummary.json",
        "WordListGen": "/a243_TranslationPrompt/a243-03_WordListGen.json",
        "UniqueWordListGen": "/a243_TranslationPrompt/a243-04_UniqueWordListGen.json",
        "WordListPostprocessing": "/a243_TranslationPrompt/a243-05_WordListPostprocessing.json",
        "IndexTranslation": "/a243_TranslationPrompt/a243-06_IndexTranslation.json",
        "BodyTranslationPreprocessing": "/a243_TranslationPrompt/a243-07_BodyTranslationPreprocessing.json",
        "BodyTranslation": "/a243_TranslationPrompt/a243-08_BodyTranslation.json",
        "BodyTranslationCheck": "/a243_TranslationPrompt/a243-08_BodyTranslationCheck.json",
        "BodyToneEditing": "/a243_TranslationPrompt/a243-08_BodyToneEditing.json",
        "BodyLanguageEditing": "/a243_TranslationPrompt/a243-08_BodyLanguageEditing.json",
        "BodyTranslationWordCheck": "/a243_TranslationPrompt/a243-08_BodyTranslationWordCheck.json",
        "TranslationEditing": "/a243_TranslationPrompt/a243-09_TranslationEditing.json",
        "TranslationRefinement": "/a243_TranslationPrompt/a243-09_TranslationRefinement.json",
        "TranslationKinfolkStyleRefinement": "/a243_TranslationPrompt/a243-09_TranslationKinfolkStyleRefinement.json",
        "TranslationProofreading": "/a243_TranslationPrompt/a243-10_TranslationProofreading.json",
        "TranslationDialogueAnalysis": "/a243_TranslationPrompt/a243-11_TranslationDialogueAnalysis.json",
        "TranslationDialogueEditing": "/a243_TranslationPrompt/a243-12_TranslationDialogueEditing.json",
        "AfterTranslationBodySummary": "/a243_TranslationPrompt/a243-14_AfterTranslationBodySummary.json",
        "AuthorResearch": "/a243_TranslationPrompt/a243-15_AuthorResearch.json",
        "TranslationCatchphrase": "/a243_TranslationPrompt/a243-16_TranslationCatchphrase.json",
        "TranslationFundingCatchphrase": "/a243_TranslationPrompt/a243-17_TranslationFundingCatchphrase.json",
        # AudioBookPrompt
        "BookPreprocess": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-00_BookPreprocess.json",
        "IndexDefinePreprocess": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-01_IndexDefinePreprocess.json",
        "IndexDefineDivisionPreprocess": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-02_IndexDefineDivisionPreprocess.json",
        "IndexDefine": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-03_IndexDefine.json",
        "DuplicationPreprocess": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-04_DuplicationPreprocess.json",
        "PronunciationPreprocess": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-05_PronunciationPreprocess.json",
        "CaptionCompletion": "/a245_AudioBookPrompt/a2451_ScriptPrompt/a2451-06_CaptionCompletion.json",
        "ContextDefine": "/a245_AudioBookPrompt/a2452_ContextPrompt/a2452-01_ContextDefine.json",
        "ContextCompletion": "/a245_AudioBookPrompt/a2452_ContextPrompt/a2452-02_ContextCompletion.json",
        "WMWMDefine": "/a245_AudioBookPrompt/a2452_ContextPrompt/a2452-03_WMWMDefine.json",
        "WMWMMatching": "/a245_AudioBookPrompt/a2452_ContextPrompt/a2452-04_WMWMMatching.json",
        "CharacterDefine": "/a245_AudioBookPrompt/a2453_CharacterPrompt/a2453-01_CharacterDefine.json",
        "CharacterCompletion": "/a245_AudioBookPrompt/a2453_CharacterPrompt/a2453-02_CharacterCompletion.json",
        "CharacterPostCompletion": "/a245_AudioBookPrompt/a2453_CharacterPrompt/a2453-03_CharacterPostCompletion.json",
        "CharacterPostCompletionLiterary": "/a245_AudioBookPrompt/a2453_CharacterPrompt/a2453-04_CharacterPostCompletionLiterary.json",
        "SoundMatching": "/a245_AudioBookPrompt/a2455_SoundPrompt/a2455-01_SoundMatching.json",
        "SFXMatching": "/a245_AudioBookPrompt/a2456_SFXPrompt/a2456-01_SFXMatching.json",
        "SFXMultiQuery": "/a245_AudioBookPrompt/a2456_SFXPrompt/a2456-02_SFXMultiQuery.json",
        "TranslationIndexEn": "/a245_AudioBookPrompt/a2457_TranslationPrompt/a2457-01_TranslationIndexEn.json",
        "CorrectionKo": "/a245_AudioBookPrompt/a2458_CorrectionPrompt/a2458-01_CorrectionKo.json",
        "ActorMatching": "/a245_AudioBookPrompt/a24510_MixingMasteringPrompt/a24510-01_ActorMatching.json",
        "SentsSpliting": "/a245_AudioBookPrompt/a24510_MixingMasteringPrompt/a24510-03_SentsSpliting.json",
        "VoiceInspection": "/a245_AudioBookPrompt/a24510_MixingMasteringPrompt/a24510-04_VoiceInspection.json",
        "VoiceSplit": "/a245_AudioBookPrompt/a24510_MixingMasteringPrompt/a24510-05_VoiceSplit.json",
        "VoiceSplitInspection": "/a245_AudioBookPrompt/a24510_MixingMasteringPrompt/a24510-06_VoiceSplitInspection.json",
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

    SoundDataPath = "/yaas/agent/a2_Database/a27_RelationalDatabase"
    SoundFileMap = {
        "VoiceDataSet": "/a272_Character/a272-01_VoiceDataSet.json",
        "LogoDataSet": "/a273_Logo/a273-01_LogoDataSet.json",
        "IntroDataSet": "/a274_Intro/a274-01_IntroDataSet.json",
        "TitleMusicDataSet": "/a275_Music/a275-01_TitleMusicDataSet.json",
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