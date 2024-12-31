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
        
        # DataCollectionPrompt
        publisherContextDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_TargetDataPrompt/b5411-01_PublisherContextDefine.json")
        publisherWMWMDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_TargetDataPrompt/b5411-02_PublisherWMWMDefine.json")
        publisherServiceDemand = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5411_TargetDataPrompt/b5411-03_PublisherServiceDemand.json")
        bestSellerContextDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5412_TrendDataPrompt/b5412-01_BestSellerContextDefine.json")
        bestSellerWMWMDefine = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5412_TrendDataPrompt/b5412-02_BestSellerWMWMDefine.json")
        bestSellerCommentAnalysis = LoadJsonFrame(PromptDataPath + "/b541_DataCollectionPrompt/b5412_TrendDataPrompt/b5412-03_BestSellerCommentAnalysis.json")
        # ScriptPrompt
        changesAfterMeditation_Script = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5421_InstantScriptPrompt/b5421-01_ChangesAfterMeditation_Script.json")
        sejongCityOfficeOfEducation_Poem = LoadJsonFrame(PromptDataPath + "/b542_ScriptPrompt/b5421_InstantScriptPrompt/b5421-02_SejongCityOfficeOfEducation_Poem.json")
        # TextBookPrompt
        # AudioBookPrompt
        bookPreprocess = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-00_BookPreprocess.json")
        indexDefinePreprocess = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-01_IndexDefinePreprocess.json")
        indexDefineDivisionPreprocess = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-02_IndexDefineDivisionPreprocess.json")
        indexDefine = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-03_IndexDefine.json")
        duplicationPreprocess = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-04_DuplicationPreprocess.json")
        pronunciationPreprocess = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-05_PronunciationPreprocess.json")
        captionCompletion = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-06_CaptionCompletion.json")
        # transitionPhargraph = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5441_ScriptPrompt/b5441-06_TransitionPhargraph.json")
        contextDefine = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5442_ContextPrompt/b5442-01_ContextDefine.json")
        contextCompletion = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5442_ContextPrompt/b5442-02_ContextCompletion.json")
        wMWMDefine = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5442_ContextPrompt/b5442-03_WMWMDefine.json")
        wMWMMatching = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5442_ContextPrompt/b5442-04_WMWMMatching.json")
        characterDefine = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5443_CharacterPrompt/b5443-01_CharacterDefine.json")
        characterCompletion = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5443_CharacterPrompt/b5443-02_CharacterCompletion.json")
        characterPostCompletion = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5443_CharacterPrompt/b5443-03_CharacterPostCompletion.json")
        characterPostCompletionLiterary = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5443_CharacterPrompt/b5443-04_CharacterPostCompletionLiterary.json")
        soundMatching = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5445_SoundPrompt/b5445-01_SoundMatching.json")
        sFXMatching = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5446_SFXPrompt/b5446-01_SFXMatching.json")
        sFXMultiQuery = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5446_SFXPrompt/b5446-02_SFXMultiQuery.json")
        translationIndexEn = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-01_TranslationIndexEn.json")
        # translationWordListEn = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-02_TranslationWordListEn.json")
        # translationBodyEn = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-03_TranslationBodyEn.json")
        # translationIndexJa = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-04_TranslationIndexJa.json")
        # translationWordListJa = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-05_TranslationWordListJa.json")
        # translationBodyJa = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-06_TranslationBodyJa.json")
        # translationIndexZh = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-07_TranslationIndexZh.json")
        # translationWordListZh = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-08_TranslationWordListZh.json")
        # translationBodyZh = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-09_TranslationBodyZh.json")
        # translationIndexEs = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-10_TranslationIndexEs.json")
        # translationWordListEs = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-11_TranslationWordListEs.json")
        # translationBodyEs = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5447_TranslationPrompt/b5447-12_TranslationBodyEs.json")
        correctionKo = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5448_CorrectionPrompt/b5448-01_CorrectionKo.json")
        # correctionEn = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b5448_CorrectionPrompt/b5448-02_CorrectionEn.json")
        sentsSpliting = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b54410_MixingMasteringPrompt/b54410-02_SentsSpliting.json")
        voiceInspection = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b54410_MixingMasteringPrompt/b54410-04_VoiceInspection.json")
        voiceSplit = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b54410_MixingMasteringPrompt/b54410-05_VoiceSplit.json")
        voiceSplitInspection = LoadJsonFrame(PromptDataPath + "/b544_AudioBookPrompt/b54410_MixingMasteringPrompt/b54410-06_VoiceSplitInspection.json")
        # VideoBookPrompt

        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingPrompt = db.query(Prompt).first()

        # DB Commit
        if ExistingPrompt:
            ExistingPrompt.PublisherContextDefine = publisherContextDefine
            ExistingPrompt.PublisherWMWMDefine = publisherWMWMDefine
            ExistingPrompt.PublisherServiceDemand = publisherServiceDemand
            ExistingPrompt.BestSellerContextDefine = bestSellerContextDefine
            ExistingPrompt.BestSellerWMWMDefine = bestSellerWMWMDefine
            ExistingPrompt.BestSellerCommentAnalysis = bestSellerCommentAnalysis
            ExistingPrompt.ChangesAfterMeditation_Script = changesAfterMeditation_Script
            ExistingPrompt.SejongCityOfficeOfEducation_Poem = sejongCityOfficeOfEducation_Poem
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
            ExistingPrompt.SentsSpliting = sentsSpliting
            ExistingPrompt.VoiceInspection = voiceInspection
            ExistingPrompt.VoiceSplit = voiceSplit
            ExistingPrompt.VoiceSplitInspection = voiceSplitInspection
            ### 아래로 추가되는 프롬프트 작성 ###
            
            print(f"[ General | AddPromptToDB 변경사항 업데이트 ]")
        else:
            prompt = Prompt(
                PublisherContextDefine = publisherContextDefine,
                PublisherWMWMDefine = publisherWMWMDefine,
                PublisherServiceDemand = publisherServiceDemand,
                BestSellerContextDefine = bestSellerContextDefine,
                BestSellerWMWMDefine = bestSellerWMWMDefine,
                BestSellerCommentAnalysis = bestSellerCommentAnalysis,
                ChangesAfterMeditation_Script = changesAfterMeditation_Script,
                SejongCityOfficeOfEducation_Poem = sejongCityOfficeOfEducation_Poem,
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