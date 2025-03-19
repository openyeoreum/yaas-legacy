import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import Prompt
from backend.b1_Api.b13_Database import get_db

def GetPromptDataPath():
    RootPath = "/yaas"
    DataPath = "backend/b5_Database/b54_PromptData"
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
        jsonParsing = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5410_GeneralPrompt/b5412-01_JsonParsingPrompt.json")
        # DataCollectionPrompt
        demandCollectionDataDetail = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54111_DemandCollectionDataGenPrompt/b54111-01_DemandCollectionDataDetail.json")
        demandCollectionDataContext = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54111_DemandCollectionDataGenPrompt/b54111-02_DemandCollectionDataContext.json")
        demandCollectionDataExpertise = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54111_DemandCollectionDataGenPrompt/b54111-03-1_DemandCollectionDataExpertise.json")
        demandCollectionDataExpertiseChain = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54111_DemandCollectionDataGenPrompt/b54111-03-2_DemandCollectionDataExpertiseChain.json")
        demandCollectionDataUltimate = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54111_DemandCollectionDataGenPrompt/b54111-04-1_DemandCollectionDataUltimate.json")
        demandCollectionDataUltimateChain = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54111_DemandCollectionDataGenPrompt/b54111-04-2_DemandCollectionDataUltimateChain.json")
        supplyCollectionDataDetail = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54112_SupplyCollectionDataGenPrompt/b54112-01_SupplyCollectionDataDetail.json")
        supplyCollectionDataContext = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54112_SupplyCollectionDataGenPrompt/b54112-02_SupplyCollectionDataContext.json")
        supplyCollectionDataExpertise = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54112_SupplyCollectionDataGenPrompt/b54112-03-1_SupplyCollectionDataExpertise.json")
        supplyCollectionDataExpertiseChain = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54112_SupplyCollectionDataGenPrompt/b54112-03-2_SupplyCollectionDataExpertiseChain.json")
        supplyCollectionDataUltimate = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54112_SupplyCollectionDataGenPrompt/b54112-04-1_SupplyCollectionDataUltimate.json")
        supplyCollectionDataUltimateChain = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54112_SupplyCollectionDataGenPrompt/b54112-04-2_SupplyCollectionDataUltimateChain.json")
        demandSearchCollectionDataFilter = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54113_SearchCollectionDataFilterPrompt/b54113-01_DemandSearchCollectionDataFilter.json")
        supplySearchCollectionDataFilter = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54113_SearchCollectionDataFilterPrompt/b54113-02_SupplySearchCollectionDataFilter.json")
        similaritySearchCollectionDataFilter = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_CollectionDataGenPrompt/b54113_SearchCollectionDataFilterPrompt/b54113-03_SimilaritySearchCollectionDataFilter.json")
        publisherContextDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5412_TargetDataPrompt/b5412-01_PublisherContextDefine.json")
        publisherWMWMDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5412_TargetDataPrompt/b5412-02_PublisherWMWMDefine.json")
        publisherServiceDemand = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5412_TargetDataPrompt/b5412-03_PublisherServiceDemand.json")
        bestSellerContextDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5413_TrendDataPrompt/b5413-01_BestSellerContextDefine.json")
        bestSellerWMWMDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5413_TrendDataPrompt/b5413-02_BestSellerWMWMDefine.json")
        bestSellerCommentAnalysis = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5413_TrendDataPrompt/b5413-03_BestSellerCommentAnalysis.json")
        # InstantScriptPrompt
        changesAfterMeditation_Script = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5421_InstantScriptPrompt/b5421-01_ChangesAfterMeditation_Script.json")
        sejongCityOfficeOfEducation_Poem = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5421_InstantScriptPrompt/b5421-02_SejongCityOfficeOfEducation_Poem.json")
        # BookScriptPrompt
        demandScriptPlan = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5422-01_DemandScriptPlan.json")
        supplyScriptPlan = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-02_SupplyScriptPlan.json")
        similarityScriptPlan = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-03_SimilarityScriptPlan.json")
        scriptPlanFeedback = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-04_ScriptPlanFeedback.json")
        titleAndIndexGen = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-05_TitleAndIndexGen.json")
        titleAndIndexGenFeedback = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-06_TitleAndIndexGenFeedback.json")
        summaryOfIndexGen = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-07_SummaryOfIndexGen.json")
        summaryOfIndexGenFeedback = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-08_SummaryOfIndexGenFeedback.json")
        scriptIntroductionGen = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-09_ScriptIntroductionGen.json")
        scriptIntroductionGenFeedback = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-10_ScriptIntroductionGenFeedback.json")
        shortScriptGen = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-11_ShortScriptGen.json")
        shortScriptGenFeedback = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5422_BookScriptPrompt/b5423-12_ShortScriptGenFeedback.json")
        # TranslationPrompt
        translationIndexDefine = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-01_TranslationIndexDefine.json")
        translationBodySummary = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-02_TranslationBodySummary.json")
        wordListGen = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-03_WordListGen.json")
        uniqueWordListGen = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-04_UniqueWordListGen.json")
        wordListPostprocessing = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-05_WordListPostprocessing.json")
        indexTranslation = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-06_IndexTranslation.json")
        bodyTranslationPreprocessing = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-07_BodyTranslationPreprocessing.json")
        bodyTranslation = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-08_BodyTranslation.json")
        bodyTranslationCheck = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-08_BodyTranslationCheck.json")
        bodyTranslationWordCheck = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-08_BodyTranslationWordCheck.json")
        translationEditing = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-09_TranslationEditing.json")
        translationRefinement = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-09_TranslationRefinement.json")
        translationKinfolkStyleRefinement = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-09_TranslationKinfolkStyleRefinement.json")
        translationProofreading = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-10_TranslationProofreading.json")
        translationDialogueAnalysis = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-11_TranslationDialogueAnalysis.json")
        translationDialogueEditing = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-12_TranslationDialogueEditing.json")
        afterTranslationBodySummary = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-14_AfterTranslationBodySummary.json")
        authorResearch = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-15_AuthorResearch.json")
        translationCatchphrase = LoadJsonFrame(PromptDataPath + "/b543_TranslationPrompt/b543-16_TranslationCatchphrase.json")
        # TextBookPrompt
        # AudioBookPrompt
        bookPreprocess = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-00_BookPreprocess.json")
        indexDefinePreprocess = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-01_IndexDefinePreprocess.json")
        indexDefineDivisionPreprocess = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-02_IndexDefineDivisionPreprocess.json")
        indexDefine = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-03_IndexDefine.json")
        duplicationPreprocess = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-04_DuplicationPreprocess.json")
        pronunciationPreprocess = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-05_PronunciationPreprocess.json")
        captionCompletion = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-06_CaptionCompletion.json")
        # transitionPhargraph = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5451_ScriptPrompt/b5451-06_TransitionPhargraph.json")
        contextDefine = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5452_ContextPrompt/b5452-01_ContextDefine.json")
        contextCompletion = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5452_ContextPrompt/b5452-02_ContextCompletion.json")
        wMWMDefine = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5452_ContextPrompt/b5452-03_WMWMDefine.json")
        wMWMMatching = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5452_ContextPrompt/b5452-04_WMWMMatching.json")
        characterDefine = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5453_CharacterPrompt/b5453-01_CharacterDefine.json")
        characterCompletion = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5453_CharacterPrompt/b5453-02_CharacterCompletion.json")
        characterPostCompletion = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5453_CharacterPrompt/b5453-03_CharacterPostCompletion.json")
        characterPostCompletionLiterary = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5453_CharacterPrompt/b5453-04_CharacterPostCompletionLiterary.json")
        soundMatching = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5455_SoundPrompt/b5455-01_SoundMatching.json")
        sFXMatching = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5456_SFXPrompt/b5456-01_SFXMatching.json")
        sFXMultiQuery = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5456_SFXPrompt/b5456-02_SFXMultiQuery.json")
        translationIndexEn = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-01_TranslationIndexEn.json")
        # translationWordListEn = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-02_TranslationWordListEn.json")
        # translationBodyEn = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-03_TranslationBodyEn.json")
        # translationIndexJa = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-04_TranslationIndexJa.json")
        # translationWordListJa = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-05_TranslationWordListJa.json")
        # translationBodyJa = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-06_TranslationBodyJa.json")
        # translationIndexZh = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-07_TranslationIndexZh.json")
        # translationWordListZh = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-08_TranslationWordListZh.json")
        # translationBodyZh = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-09_TranslationBodyZh.json")
        # translationIndexEs = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-10_TranslationIndexEs.json")
        # translationWordListEs = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-11_TranslationWordListEs.json")
        # translationBodyEs = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5457_TranslationPrompt/b5457-12_TranslationBodyEs.json")
        correctionKo = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5458_CorrectionPrompt/b5458-01_CorrectionKo.json")
        # correctionEn = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b5458_CorrectionPrompt/b5458-02_CorrectionEn.json")
        actorMatching = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b54510_MixingMasteringPrompt/b54510-01_ActorMatching.json")
        sentsSpliting = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b54510_MixingMasteringPrompt/b54510-03_SentsSpliting.json")
        voiceInspection = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b54510_MixingMasteringPrompt/b54510-04_VoiceInspection.json")
        voiceSplit = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b54510_MixingMasteringPrompt/b54510-05_VoiceSplit.json")
        voiceSplitInspection = LoadJsonFrame(PromptDataPath + "/b545_AudioBookPrompt/b54510_MixingMasteringPrompt/b54510-06_VoiceSplitInspection.json")
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