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

    PromptDataPath = "/yaas/agent/a0_Database/a04_PromptData"
    PromptFileMap = {
        # GeneralPrompt
        "JsonParsing": "/a041_DataCollectionPrompt/a0410_GeneralPrompt/a0412-01_JsonParsingPrompt.json",
        # DataCollectionPrompt
        "DemandCollectionDataDetail": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04111_DemandCollectionDataGenPrompt/a04111-01_DemandCollectionDataDetail.json",
        "DemandCollectionDataContext": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04111_DemandCollectionDataGenPrompt/a04111-02_DemandCollectionDataContext.json",
        "DemandCollectionDataExpertise": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04111_DemandCollectionDataGenPrompt/a04111-03-1_DemandCollectionDataExpertise.json",
        "DemandCollectionDataExpertiseChain": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04111_DemandCollectionDataGenPrompt/a04111-03-2_DemandCollectionDataExpertiseChain.json",
        "DemandCollectionDataUltimate": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04111_DemandCollectionDataGenPrompt/a04111-04-1_DemandCollectionDataUltimate.json",
        "DemandCollectionDataUltimateChain": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04111_DemandCollectionDataGenPrompt/a04111-04-2_DemandCollectionDataUltimateChain.json",
        "SupplyCollectionDataDetail": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04112_SupplyCollectionDataGenPrompt/a04112-01_SupplyCollectionDataDetail.json",
        "SupplyCollectionDataContext": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04112_SupplyCollectionDataGenPrompt/a04112-02_SupplyCollectionDataContext.json",
        "SupplyCollectionDataExpertise": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04112_SupplyCollectionDataGenPrompt/a04112-03-1_SupplyCollectionDataExpertise.json",
        "SupplyCollectionDataExpertiseChain": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04112_SupplyCollectionDataGenPrompt/a04112-03-2_SupplyCollectionDataExpertiseChain.json",
        "SupplyCollectionDataUltimate": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04112_SupplyCollectionDataGenPrompt/a04112-04-1_SupplyCollectionDataUltimate.json",
        "SupplyCollectionDataUltimateChain": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04112_SupplyCollectionDataGenPrompt/a04112-04-2_SupplyCollectionDataUltimateChain.json",
        "DemandSearchCollectionDataFilter": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04113_SearchCollectionDataFilterPrompt/a04113-01_DemandSearchCollectionDataFilter.json",
        "SupplySearchCollectionDataFilter": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04113_SearchCollectionDataFilterPrompt/a04113-02_SupplySearchCollectionDataFilter.json",
        "SimilaritySearchCollectionDataFilter": "/a041_DataCollectionPrompt/a0411_CollectionDataGenPrompt/a04113_SearchCollectionDataFilterPrompt/a04113-03_SimilaritySearchCollectionDataFilter.json",
        "PublisherContextDefine": "/a041_DataCollectionPrompt/a0412_TargetDataPrompt/a0412-01_PublisherContextDefine.json",
        "PublisherWMWMDefine": "/a041_DataCollectionPrompt/a0412_TargetDataPrompt/a0412-02_PublisherWMWMDefine.json",
        "PublisherServiceDemand": "/a041_DataCollectionPrompt/a0412_TargetDataPrompt/a0412-03_PublisherServiceDemand.json",
        "BestSellerContextDefine": "/a041_DataCollectionPrompt/a0413_TrendDataPrompt/a0413-01_BestSellerContextDefine.json",
        "BestSellerWMWMDefine": "/a041_DataCollectionPrompt/a0413_TrendDataPrompt/a0413-02_BestSellerWMWMDefine.json",
        "BestSellerCommentAnalysis": "/a041_DataCollectionPrompt/a0413_TrendDataPrompt/a0413-03_BestSellerCommentAnalysis.json",
        # BookScriptPrompt
        "DemandScriptPlan": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-01_DemandScriptPlan.json",
        "SupplyScriptPlan": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-02_SupplyScriptPlan.json",
        "SimilarityScriptPlan": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-03_SimilarityScriptPlan.json",
        "ScriptPlanFeedback": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-04_ScriptPlanFeedback.json",
        "TitleAndIndexGen": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-05_TitleAndIndexGen.json",
        "TitleAndIndexGenFeedback": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-06_TitleAndIndexGenFeedback.json",
        "SummaryOfIndexGen": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-07_SummaryOfIndexGen.json",
        "SummaryOfIndexGenFeedback": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-08_SummaryOfIndexGenFeedback.json",
        "ScriptIntroductionGen": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-09_ScriptIntroductionGen.json",
        "ScriptIntroductionGenFeedback": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-10_ScriptIntroductionGenFeedback.json",
        "ShortScriptGen": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-11_ShortScriptGen.json",
        "ShortScriptGenFeedback": "/a042_ScriptPrompt/a0421_BookScriptGenPrompt/a0421-12_ShortScriptGenFeedback.json",
        # ScriptSegmentationPrompt
        "ScriptLoad": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-PT01_ScriptLoad.json",
        "PDFMainLangCheck": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-P02_PDFMainLangCheck.json",
        "PDFLayoutCheck": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-P03_PDFLayoutCheck.json",
        "PDFResize": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-P04_PDFResize.json",
        "PDFSplit": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-P05_PDFSplit.json",
        "PDFFormCheck": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-P06_PDFFormCheck.json",
        "TXTSplit": "/a042_ScriptPrompt/a0422_ScriptSegmentationPrompt/a0422-T03_TXTSplit.json",
        # TranslationPrompt
        "TranslationIndexDefine": "/a043_TranslationPrompt/a043-01_TranslationIndexDefine.json",
        "TranslationBodySummary": "/a043_TranslationPrompt/a043-02_TranslationBodySummary.json",
        "WordListGen": "/a043_TranslationPrompt/a043-03_WordListGen.json",
        "UniqueWordListGen": "/a043_TranslationPrompt/a043-04_UniqueWordListGen.json",
        "WordListPostprocessing": "/a043_TranslationPrompt/a043-05_WordListPostprocessing.json",
        "IndexTranslation": "/a043_TranslationPrompt/a043-06_IndexTranslation.json",
        "BodyTranslationPreprocessing": "/a043_TranslationPrompt/a043-07_BodyTranslationPreprocessing.json",
        "BodyTranslation": "/a043_TranslationPrompt/a043-08_BodyTranslation.json",
        "BodyTranslationCheck": "/a043_TranslationPrompt/a043-08_BodyTranslationCheck.json",
        "BodyToneEditing": "/a043_TranslationPrompt/a043-08_BodyToneEditing.json",
        "BodyLanguageEditing": "/a043_TranslationPrompt/a043-08_BodyLanguageEditing.json",
        "BodyTranslationWordCheck": "/a043_TranslationPrompt/a043-08_BodyTranslationWordCheck.json",
        "TranslationEditing": "/a043_TranslationPrompt/a043-09_TranslationEditing.json",
        "TranslationRefinement": "/a043_TranslationPrompt/a043-09_TranslationRefinement.json",
        "TranslationKinfolkStyleRefinement": "/a043_TranslationPrompt/a043-09_TranslationKinfolkStyleRefinement.json",
        "TranslationProofreading": "/a043_TranslationPrompt/a043-10_TranslationProofreading.json",
        "TranslationDialogueAnalysis": "/a043_TranslationPrompt/a043-11_TranslationDialogueAnalysis.json",
        "TranslationDialogueEditing": "/a043_TranslationPrompt/a043-12_TranslationDialogueEditing.json",
        "AfterTranslationBodySummary": "/a043_TranslationPrompt/a043-14_AfterTranslationBodySummary.json",
        "AuthorResearch": "/a043_TranslationPrompt/a043-15_AuthorResearch.json",
        "TranslationCatchphrase": "/a043_TranslationPrompt/a043-16_TranslationCatchphrase.json",
        "TranslationFundingCatchphrase": "/a043_TranslationPrompt/a043-17_TranslationFundingCatchphrase.json",
        # AudioBookPrompt
        "BookPreprocess": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-00_BookPreprocess.json",
        "IndexDefinePreprocess": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-01_IndexDefinePreprocess.json",
        "IndexDefineDivisionPreprocess": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-02_IndexDefineDivisionPreprocess.json",
        "IndexDefine": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-03_IndexDefine.json",
        "DuplicationPreprocess": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-04_DuplicationPreprocess.json",
        "PronunciationPreprocess": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-05_PronunciationPreprocess.json",
        "CaptionCompletion": "/a045_AudioBookPrompt/a0451_ScriptPrompt/a0451-06_CaptionCompletion.json",
        "ContextDefine": "/a045_AudioBookPrompt/a0452_ContextPrompt/a0452-01_ContextDefine.json",
        "ContextCompletion": "/a045_AudioBookPrompt/a0452_ContextPrompt/a0452-02_ContextCompletion.json",
        "WMWMDefine": "/a045_AudioBookPrompt/a0452_ContextPrompt/a0452-03_WMWMDefine.json",
        "WMWMMatching": "/a045_AudioBookPrompt/a0452_ContextPrompt/a0452-04_WMWMMatching.json",
        "CharacterDefine": "/a045_AudioBookPrompt/a0453_CharacterPrompt/a0453-01_CharacterDefine.json",
        "CharacterCompletion": "/a045_AudioBookPrompt/a0453_CharacterPrompt/a0453-02_CharacterCompletion.json",
        "CharacterPostCompletion": "/a045_AudioBookPrompt/a0453_CharacterPrompt/a0453-03_CharacterPostCompletion.json",
        "CharacterPostCompletionLiterary": "/a045_AudioBookPrompt/a0453_CharacterPrompt/a0453-04_CharacterPostCompletionLiterary.json",
        "SoundMatching": "/a045_AudioBookPrompt/a0455_SoundPrompt/a0455-01_SoundMatching.json",
        "SFXMatching": "/a045_AudioBookPrompt/a0456_SFXPrompt/a0456-01_SFXMatching.json",
        "SFXMultiQuery": "/a045_AudioBookPrompt/a0456_SFXPrompt/a0456-02_SFXMultiQuery.json",
        "TranslationIndexEn": "/a045_AudioBookPrompt/a0457_TranslationPrompt/a0457-01_TranslationIndexEn.json",
        "CorrectionKo": "/a045_AudioBookPrompt/a0458_CorrectionPrompt/a0458-01_CorrectionKo.json",
        "ActorMatching": "/a045_AudioBookPrompt/a04510_MixingMasteringPrompt/a04510-01_ActorMatching.json",
        "SentsSpliting": "/a045_AudioBookPrompt/a04510_MixingMasteringPrompt/a04510-03_SentsSpliting.json",
        "VoiceInspection": "/a045_AudioBookPrompt/a04510_MixingMasteringPrompt/a04510-04_VoiceInspection.json",
        "VoiceSplit": "/a045_AudioBookPrompt/a04510_MixingMasteringPrompt/a04510-05_VoiceSplit.json",
        "VoiceSplitInspection": "/a045_AudioBookPrompt/a04510_MixingMasteringPrompt/a04510-06_VoiceSplitInspection.json",
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

    SoundDataPath = "/yaas/agent/a0_Database/a07_RelationalDatabase"
    SoundFileMap = {
        "VoiceDataSet": "/a072_Character/a072-01_VoiceDataSet.json",
        "LogoDataSet": "/a073_Logo/a073-01_LogoDataSet.json",
        "IntroDataSet": "/a074_Intro/a074-01_IntroDataSet.json",
        "TitleMusicDataSet": "/a075_Music/a075-01_TitleMusicDataSet.json",
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