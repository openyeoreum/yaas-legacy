import os
import sys
import json
sys.path.append("/yaas")

from agent.a1_Connector.a14_Models import Prompt
from agent.a1_Connector.a13_Database import get_db

def GetPromptDataPath():
    RootPath = "/yaas"
    DataPath = "agent/a5_Database/a54_PromptData"
    return os.path.join(RootPath, DataPath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddPromptToDB():
    with get_db() as db:
        
        # JSON 데이터 불러오기
        PromptDataPath = GetPromptDataPath()
        
        # GeneralPrompt
        jsonParsing = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5410_GeneralPrompt/a5412-01_JsonParsingPrompt.json")
        # DataCollectionPrompt
        demandCollectionDataDetail = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-01_DemandCollectionDataDetail.json")
        demandCollectionDataContext = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-02_DemandCollectionDataContext.json")
        demandCollectionDataExpertise = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-03-1_DemandCollectionDataExpertise.json")
        demandCollectionDataExpertiseChain = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-03-2_DemandCollectionDataExpertiseChain.json")
        demandCollectionDataUltimate = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-04-1_DemandCollectionDataUltimate.json")
        demandCollectionDataUltimateChain = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54111_DemandCollectionDataGenPrompt/a54111-04-2_DemandCollectionDataUltimateChain.json")
        supplyCollectionDataDetail = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-01_SupplyCollectionDataDetail.json")
        supplyCollectionDataContext = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-02_SupplyCollectionDataContext.json")
        supplyCollectionDataExpertise = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-03-1_SupplyCollectionDataExpertise.json")
        supplyCollectionDataExpertiseChain = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-03-2_SupplyCollectionDataExpertiseChain.json")
        supplyCollectionDataUltimate = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-04-1_SupplyCollectionDataUltimate.json")
        supplyCollectionDataUltimateChain = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54112_SupplyCollectionDataGenPrompt/a54112-04-2_SupplyCollectionDataUltimateChain.json")
        demandSearchCollectionDataFilter = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-01_DemandSearchCollectionDataFilter.json")
        supplySearchCollectionDataFilter = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-02_SupplySearchCollectionDataFilter.json")
        similaritySearchCollectionDataFilter = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5411_CollectionDataGenPrompt/a54113_SearchCollectionDataFilterPrompt/a54113-03_SimilaritySearchCollectionDataFilter.json")
        publisherContextDefine = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-01_PublisherContextDefine.json")
        publisherWMWMDefine = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-02_PublisherWMWMDefine.json")
        publisherServiceDemand = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5412_TargetDataPrompt/a5412-03_PublisherServiceDemand.json")
        bestSellerContextDefine = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-01_BestSellerContextDefine.json")
        bestSellerWMWMDefine = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-02_BestSellerWMWMDefine.json")
        bestSellerCommentAnalysis = LoadJsonFrame(PromptDataPath + "/a541_DataCollectionPrompt/a5413_TrendDataPrompt/a5413-03_BestSellerCommentAnalysis.json")
        # InstantScriptPrompt
        changesAfterMeditation_Script = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5421_InstantScriptPrompt/a5421-01_ChangesAfterMeditation_Script.json")
        sejongCityOfficeOfEducation_Poem = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5421_InstantScriptPrompt/a5421-02_SejongCityOfficeOfEducation_Poem.json")
        # BookScriptPrompt
        demandScriptPlan = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5422-01_DemandScriptPlan.json")
        supplyScriptPlan = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-02_SupplyScriptPlan.json")
        similarityScriptPlan = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-03_SimilarityScriptPlan.json")
        scriptPlanFeedback = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-04_ScriptPlanFeedback.json")
        titleAndIndexGen = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-05_TitleAndIndexGen.json")
        titleAndIndexGenFeedback = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-06_TitleAndIndexGenFeedback.json")
        summaryOfIndexGen = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-07_SummaryOfIndexGen.json")
        summaryOfIndexGenFeedback = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-08_SummaryOfIndexGenFeedback.json")
        scriptIntroductionGen = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-09_ScriptIntroductionGen.json")
        scriptIntroductionGenFeedback = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-10_ScriptIntroductionGenFeedback.json")
        shortScriptGen = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-11_ShortScriptGen.json")
        shortScriptGenFeedback = LoadJsonFrame(PromptDataPath + "/a542_ScriptPrompt/a5422_BookScriptPrompt/a5423-12_ShortScriptGenFeedback.json")
        # TranslationPrompt
        translationIndexDefine = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-01_TranslationIndexDefine.json")
        translationBodySummary = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-02_TranslationBodySummary.json")
        wordListGen = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-03_WordListGen.json")
        uniqueWordListGen = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-04_UniqueWordListGen.json")
        wordListPostprocessing = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-05_WordListPostprocessing.json")
        indexTranslation = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-06_IndexTranslation.json")
        bodyTranslationPreprocessing = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-07_BodyTranslationPreprocessing.json")
        bodyTranslation = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-08_BodyTranslation.json")
        bodyTranslationCheck = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-08_BodyTranslationCheck.json")
        bodyToneEditing = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-08_BodyToneEditing.json")
        bodyLanguageEditing = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-08_BodyLanguageEditing.json")
        bodyTranslationWordCheck = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-08_BodyTranslationWordCheck.json")
        translationEditing = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-09_TranslationEditing.json")
        translationRefinement = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-09_TranslationRefinement.json")
        translationKinfolkStyleRefinement = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-09_TranslationKinfolkStyleRefinement.json")
        translationProofreading = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-10_TranslationProofreading.json")
        translationDialogueAnalysis = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-11_TranslationDialogueAnalysis.json")
        translationDialogueEditing = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-12_TranslationDialogueEditing.json")
        afterTranslationBodySummary = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-14_AfterTranslationBodySummary.json")
        authorResearch = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-15_AuthorResearch.json")
        translationCatchphrase = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-16_TranslationCatchphrase.json")
        translationFundingCatchphrase = LoadJsonFrame(PromptDataPath + "/a543_TranslationPrompt/a543-17_TranslationFundingCatchphrase.json")
        # TextBookPrompt
        # AudioBookPrompt
        bookPreprocess = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-00_BookPreprocess.json")
        indexDefinePreprocess = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-01_IndexDefinePreprocess.json")
        indexDefineDivisionPreprocess = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-02_IndexDefineDivisionPreprocess.json")
        indexDefine = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-03_IndexDefine.json")
        duplicationPreprocess = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-04_DuplicationPreprocess.json")
        pronunciationPreprocess = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-05_PronunciationPreprocess.json")
        captionCompletion = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-06_CaptionCompletion.json")
        # transitionPhargraph = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5451_ScriptPrompt/a5451-06_TransitionPhargraph.json")
        contextDefine = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-01_ContextDefine.json")
        contextCompletion = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-02_ContextCompletion.json")
        wMWMDefine = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-03_WMWMDefine.json")
        wMWMMatching = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5452_ContextPrompt/a5452-04_WMWMMatching.json")
        characterDefine = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-01_CharacterDefine.json")
        characterCompletion = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-02_CharacterCompletion.json")
        characterPostCompletion = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-03_CharacterPostCompletion.json")
        characterPostCompletionLiterary = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5453_CharacterPrompt/a5453-04_CharacterPostCompletionLiterary.json")
        soundMatching = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5455_SoundPrompt/a5455-01_SoundMatching.json")
        sFXMatching = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5456_SFXPrompt/a5456-01_SFXMatching.json")
        sFXMultiQuery = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5456_SFXPrompt/a5456-02_SFXMultiQuery.json")
        translationIndexEn = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-01_TranslationIndexEn.json")
        # translationWordListEn = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-02_TranslationWordListEn.json")
        # translationBodyEn = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-03_TranslationBodyEn.json")
        # translationIndexJa = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-04_TranslationIndexJa.json")
        # translationWordListJa = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-05_TranslationWordListJa.json")
        # translationBodyJa = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-06_TranslationBodyJa.json")
        # translationIndexZh = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-07_TranslationIndexZh.json")
        # translationWordListZh = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-08_TranslationWordListZh.json")
        # translationBodyZh = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-09_TranslationBodyZh.json")
        # translationIndexEs = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-10_TranslationIndexEs.json")
        # translationWordListEs = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-11_TranslationWordListEs.json")
        # translationBodyEs = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5457_TranslationPrompt/a5457-12_TranslationBodyEs.json")
        correctionKo = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5458_CorrectionPrompt/a5458-01_CorrectionKo.json")
        # correctionEn = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a5458_CorrectionPrompt/a5458-02_CorrectionEn.json")
        actorMatching = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-01_ActorMatching.json")
        sentsSpliting = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-03_SentsSpliting.json")
        voiceInspection = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-04_VoiceInspection.json")
        voiceSplit = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-05_VoiceSplit.json")
        voiceSplitInspection = LoadJsonFrame(PromptDataPath + "/a545_AudioBookPrompt/a54510_MixingMasteringPrompt/a54510-06_VoiceSplitInspection.json")
        # VideoBookPrompt

        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingPrompt = db.query(Prompt).first()

        # DB Commit
        if ExistingPrompt:
            ExistingPrompt.JsonParsing = jsonParsing
            ExistingPrompt.DemandCollectionDataDetail = demandCollectionDataDetail
            ExistingPrompt.DemandCollectionDataContext = demandCollectionDataContext
            ExistingPrompt.DemandCollectionDataExpertise = demandCollectionDataExpertise
            ExistingPrompt.DemandCollectionDataExpertiseChain = demandCollectionDataExpertiseChain
            ExistingPrompt.DemandCollectionDataUltimate = demandCollectionDataUltimate
            ExistingPrompt.DemandCollectionDataUltimateChain = demandCollectionDataUltimateChain
            ExistingPrompt.SupplyCollectionDataDetail = supplyCollectionDataDetail
            ExistingPrompt.SupplyCollectionDataContext = supplyCollectionDataContext
            ExistingPrompt.SupplyCollectionDataExpertise = supplyCollectionDataExpertise
            ExistingPrompt.SupplyCollectionDataExpertiseChain = supplyCollectionDataExpertiseChain
            ExistingPrompt.SupplyCollectionDataUltimate = supplyCollectionDataUltimate
            ExistingPrompt.SupplyCollectionDataUltimateChain = supplyCollectionDataUltimateChain
            ExistingPrompt.DemandSearchCollectionDataFilter = demandSearchCollectionDataFilter
            ExistingPrompt.SupplySearchCollectionDataFilter = supplySearchCollectionDataFilter
            ExistingPrompt.SimilaritySearchCollectionDataFilter = similaritySearchCollectionDataFilter
            ExistingPrompt.PublisherContextDefine = publisherContextDefine
            ExistingPrompt.PublisherWMWMDefine = publisherWMWMDefine
            ExistingPrompt.PublisherServiceDemand = publisherServiceDemand
            ExistingPrompt.BestSellerContextDefine = bestSellerContextDefine
            ExistingPrompt.BestSellerWMWMDefine = bestSellerWMWMDefine
            ExistingPrompt.BestSellerCommentAnalysis = bestSellerCommentAnalysis
            ExistingPrompt.ChangesAfterMeditation_Script = changesAfterMeditation_Script
            ExistingPrompt.SejongCityOfficeOfEducation_Poem = sejongCityOfficeOfEducation_Poem
            ExistingPrompt.DemandScriptPlan = demandScriptPlan
            ExistingPrompt.SupplyScriptPlan = supplyScriptPlan
            ExistingPrompt.SimilarityScriptPlan = similarityScriptPlan
            ExistingPrompt.ScriptPlanFeedback = scriptPlanFeedback
            ExistingPrompt.TitleAndIndexGen = titleAndIndexGen
            ExistingPrompt.TitleAndIndexGenFeedback = titleAndIndexGenFeedback
            ExistingPrompt.SummaryOfIndexGen = summaryOfIndexGen
            ExistingPrompt.SummaryOfIndexGenFeedback = summaryOfIndexGenFeedback
            ExistingPrompt.ScriptIntroductionGen = scriptIntroductionGen
            ExistingPrompt.ScriptIntroductionGenFeedback = scriptIntroductionGenFeedback
            ExistingPrompt.ShortScriptGen = shortScriptGen
            ExistingPrompt.ShortScriptGenFeedback = shortScriptGenFeedback
            ExistingPrompt.TranslationIndexDefine = translationIndexDefine
            ExistingPrompt.TranslationBodySummary = translationBodySummary
            ExistingPrompt.WordListGen = wordListGen
            ExistingPrompt.UniqueWordListGen = uniqueWordListGen
            ExistingPrompt.WordListPostprocessing = wordListPostprocessing
            ExistingPrompt.IndexTranslation = indexTranslation
            ExistingPrompt.BodyTranslationPreprocessing = bodyTranslationPreprocessing
            ExistingPrompt.BodyTranslation = bodyTranslation
            ExistingPrompt.BodyTranslationCheck = bodyTranslationCheck
            ExistingPrompt.BodyToneEditing = bodyToneEditing
            ExistingPrompt.BodyLanguageEditing = bodyLanguageEditing
            ExistingPrompt.BodyTranslationWordCheck = bodyTranslationWordCheck
            ExistingPrompt.TranslationEditing = translationEditing
            ExistingPrompt.TranslationRefinement = translationRefinement
            ExistingPrompt.TranslationKinfolkStyleRefinement = translationKinfolkStyleRefinement
            ExistingPrompt.TranslationProofreading = translationProofreading
            ExistingPrompt.TranslationDialogueAnalysis = translationDialogueAnalysis
            ExistingPrompt.TranslationDialogueEditing = translationDialogueEditing
            # ExistingPrompt.TranslationDialoguePostprocessing = translationDialoguePostprocessing
            ExistingPrompt.AfterTranslationBodySummary = afterTranslationBodySummary
            ExistingPrompt.AuthorResearch = authorResearch
            ExistingPrompt.TranslationCatchphrase = translationCatchphrase
            ExistingPrompt.TranslationFundingCatchphrase = translationFundingCatchphrase
            ExistingPrompt.BookPreprocess = bookPreprocess
            ExistingPrompt.IndexDefinePreprocess = indexDefinePreprocess
            ExistingPrompt.IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess
            ExistingPrompt.IndexDefine = indexDefine
            ExistingPrompt.DuplicationPreprocess = duplicationPreprocess
            ExistingPrompt.PronunciationPreprocess = pronunciationPreprocess
            ExistingPrompt.CaptionCompletion = captionCompletion
            # ExistingPrompt.TransitionPhargraph = transitionPhargraph
            ExistingPrompt.ContextDefine = contextDefine
            ExistingPrompt.ContextCompletion = contextCompletion
            ExistingPrompt.WMWMDefine = wMWMDefine
            ExistingPrompt.WMWMMatching = wMWMMatching
            ExistingPrompt.CharacterDefine = characterDefine
            ExistingPrompt.CharacterCompletion = characterCompletion
            ExistingPrompt.CharacterPostCompletion = characterPostCompletion
            ExistingPrompt.CharacterPostCompletionLiterary = characterPostCompletionLiterary
            ExistingPrompt.SoundMatching = soundMatching
            ExistingPrompt.SFXMatching = sFXMatching
            ExistingPrompt.SFXMultiQuery = sFXMultiQuery
            ExistingPrompt.TranslationIndexEn = translationIndexEn
            # ExistingPrompt.TranslationWordListEn = translationWordListEn
            # ExistingPrompt.TranslationBodyEn = translationBodyEn
            # ExistingPrompt.TranslationIndexJa = translationIndexJa
            # ExistingPrompt.TranslationWordListJa = translationWordListJa
            # ExistingPrompt.TranslationBodyJa = translationBodyJa
            # ExistingPrompt.TranslationIndexZh = translationIndexZh
            # ExistingPrompt.TranslationWordListZh = translationWordListZh
            # ExistingPrompt.TranslationBodyZh = translationBodyZh
            # ExistingPrompt.TranslationIndexEs = translationIndexEs
            # ExistingPrompt.TranslationWordListEs = translationWordListEs
            # ExistingPrompt.TranslationBodyEs = translationBodyEs
            # ExistingPrompt.TranslationEn = translationEn
            ExistingPrompt.CorrectionKo = correctionKo
            # ExistingPrompt.CorrectionEn = correctionEn
            ExistingPrompt.ActorMatching = actorMatching
            ExistingPrompt.SentsSpliting = sentsSpliting
            ExistingPrompt.VoiceInspection = voiceInspection
            ExistingPrompt.VoiceSplit = voiceSplit
            ExistingPrompt.VoiceSplitInspection = voiceSplitInspection
            ### 아래로 추가되는 프롬프트 작성 ###

            print(f"[ General | AddPromptToDB 변경사항 업데이트 ]")
        else:
            prompt = Prompt(
                JsonParsing = jsonParsing,
                DemandCollectionDataDetail = demandCollectionDataDetail,
                DemandCollectionDataContext = demandCollectionDataContext,
                DemandCollectionDataExpertise = demandCollectionDataExpertise,
                DemandCollectionDataExpertiseChain = demandCollectionDataExpertiseChain,
                DemandCollectionDataUltimate = demandCollectionDataUltimate,
                DemandCollectionDataUltimateChain = demandCollectionDataUltimateChain,
                SupplyCollectionDataDetail = supplyCollectionDataDetail,
                SupplyCollectionDataContext = supplyCollectionDataContext,
                SupplyCollectionDataExpertise = supplyCollectionDataExpertise,
                SupplyCollectionDataExpertiseChain = supplyCollectionDataExpertiseChain,
                SupplyCollectionDataUltimate = supplyCollectionDataUltimate,
                SupplyCollectionDataUltimateChain = supplyCollectionDataUltimateChain,
                DemandSearchCollectionDataFilter = demandSearchCollectionDataFilter,
                SupplySearchCollectionDataFilter = supplySearchCollectionDataFilter,
                SimilaritySearchCollectionDataFilter = similaritySearchCollectionDataFilter,
                PublisherContextDefine = publisherContextDefine,
                PublisherWMWMDefine = publisherWMWMDefine,
                PublisherServiceDemand = publisherServiceDemand,
                BestSellerContextDefine = bestSellerContextDefine,
                BestSellerWMWMDefine = bestSellerWMWMDefine,
                BestSellerCommentAnalysis = bestSellerCommentAnalysis,
                ChangesAfterMeditation_Script = changesAfterMeditation_Script,
                SejongCityOfficeOfEducation_Poem = sejongCityOfficeOfEducation_Poem,
                DemandScriptPlan = demandScriptPlan,
                SupplyScriptPlan = supplyScriptPlan,
                SimilarityScriptPlan = similarityScriptPlan,
                ScriptPlanFeedback = scriptPlanFeedback,
                TitleAndIndexGen = titleAndIndexGen,
                TitleAndIndexGenFeedback = titleAndIndexGenFeedback,
                SummaryOfIndexGen = summaryOfIndexGen,
                SummaryOfIndexGenFeedback = summaryOfIndexGenFeedback,
                ScriptIntroductionGen = scriptIntroductionGen,
                ScriptIntroductionGenFeedback = scriptIntroductionGenFeedback,
                ShortScriptGen = shortScriptGen,
                ShortScriptGenFeedback = shortScriptGenFeedback,
                TranslationIndexDefine = translationIndexDefine,
                TranslationBodySummary = translationBodySummary,
                WordListGen = wordListGen,
                UniqueWordListGen = uniqueWordListGen,
                WordListPostprocessing = wordListPostprocessing,
                IndexTranslation = indexTranslation,
                BodyTranslationPreprocessing = bodyTranslationPreprocessing,
                BodyTranslation = bodyTranslation,
                BodyTranslationCheck = bodyTranslationCheck,
                BodyToneEditing = bodyToneEditing,
                BodyLanguageEditing = bodyLanguageEditing,
                BodyTranslationWordCheck = bodyTranslationWordCheck,
                TranslationEditing = translationEditing,
                TranslationRefinement = translationRefinement,
                TranslationKinfolkStyleRefinement = translationKinfolkStyleRefinement,
                TranslationProofreading = translationProofreading,
                TranslationDialogueAnalysis = translationDialogueAnalysis,
                TranslationDialogueEditing = translationDialogueEditing,
                # TranslationDialoguePostprocessing = translationDialoguePostprocessing,
                AfterTranslationBodySummary = afterTranslationBodySummary,
                AuthorResearch = authorResearch,
                TranslationCatchphrase = translationCatchphrase,
                TranslationFundingCatchphrase = translationFundingCatchphrase,
                BookPreprocess = bookPreprocess,
                IndexDefinePreprocess = indexDefinePreprocess,
                IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess,
                IndexDefine = indexDefine,
                DuplicationPreprocess = duplicationPreprocess,
                PronunciationPreprocess = pronunciationPreprocess,
                CaptionCompletion = captionCompletion,
                # TransitionPhargraph = transitionPhargraph,
                ContextDefine = contextDefine,
                ContextCompletion = contextCompletion,
                WMWMDefine = wMWMDefine,
                WMWMMatching = wMWMMatching,
                CharacterDefine = characterDefine,
                CharacterCompletion = characterCompletion,
                CharacterPostCompletion = characterPostCompletion,
                CharacterPostCompletionLiterary = characterPostCompletionLiterary,
                SoundMatching = soundMatching,
                SFXMatching = sFXMatching,
                SFXMultiQuery = sFXMultiQuery,
                TranslationIndexEn = translationIndexEn,
                # TranslationWordListEn = translationWordListEn,
                # TranslationBodyEn = translationBodyEn,
                # TranslationIndexJa = translationIndexJa,
                # TranslationWordListJa = translationWordListJa,
                # TranslationBodyJa = translationBodyJa,
                # TranslationIndexZh = translationIndexZh,
                # TranslationWordListZh = translationWordListZh,
                # TranslationBodyZh = translationBodyZh,
                # TranslationIndexEs = translationIndexEs,
                # TranslationWordListEs = translationWordListEs,
                # TranslationBodyEs = translationBodyEs,
                CorrectionKo = correctionKo,
                # CorrectionEn = correctionEn,
                ActorMatching = actorMatching,
                SentsSpliting = sentsSpliting,
                VoiceInspection = voiceInspection,
                VoiceSplit = voiceSplit,
                VoiceSplitInspection = voiceSplitInspection
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(prompt)
            print(f"[ General | AddPromptToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddPromptToDB()