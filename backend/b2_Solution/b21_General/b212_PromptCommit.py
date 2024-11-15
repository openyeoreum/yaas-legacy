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
        
        sejongCityOfficeOfEducation_Elementary = LoadJsonFrame(PromptDataPath + "/b540_ScriptGenPrompt/b540-01_SejongCityOfficeOfEducation_Elementary.json")
        bookPreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-00_BookPreprocess.json")
        indexDefinePreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-01_IndexDefinePreprocess.json")
        indexDefineDivisionPreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-02_IndexDefineDivisionPreprocess.json")
        indexDefine = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-03_IndexDefine.json")
        duplicationPreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-04_DuplicationPreprocess.json")
        pronunciationPreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-05_PronunciationPreprocess.json")
        captionCompletion = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-06_CaptionCompletion.json")
        # transitionPhargraph = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-06_TransitionPhargraph.json")
        contextDefine = LoadJsonFrame(PromptDataPath + "/b542_ContextPrompt/b542-01_ContextDefine.json")
        contextCompletion = LoadJsonFrame(PromptDataPath + "/b542_ContextPrompt/b542-02_ContextCompletion.json")
        wMWMDefine = LoadJsonFrame(PromptDataPath + "/b542_ContextPrompt/b542-03_WMWMDefine.json")
        wMWMMatching = LoadJsonFrame(PromptDataPath + "/b542_ContextPrompt/b542-04_WMWMMatching.json")
        characterDefine = LoadJsonFrame(PromptDataPath + "/b543_CharacterPrompt/b543-01_CharacterDefine.json")
        characterCompletion = LoadJsonFrame(PromptDataPath + "/b543_CharacterPrompt/b543-02_CharacterCompletion.json")
        characterPostCompletion = LoadJsonFrame(PromptDataPath + "/b543_CharacterPrompt/b543-03_CharacterPostCompletion.json")
        characterPostCompletionLiterary = LoadJsonFrame(PromptDataPath + "/b543_CharacterPrompt/b543-04_CharacterPostCompletionLiterary.json")
        soundMatching = LoadJsonFrame(PromptDataPath + "/b545_SoundPrompt/b545-01_SoundMatching.json")
        sFXMatching = LoadJsonFrame(PromptDataPath + "/b546_SFXPrompt/b546-01_SFXMatching.json")
        sFXMultiQuery = LoadJsonFrame(PromptDataPath + "/b546_SFXPrompt/b546-02_SFXMultiQuery.json")
        translationIndexEn = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-01_TranslationIndexEn.json")
        # translationWordListEn = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-02_TranslationWordListEn.json")
        # translationBodyEn = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-03_TranslationBodyEn.json")
        # translationIndexJa = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-04_TranslationIndexJa.json")
        # translationWordListJa = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-05_TranslationWordListJa.json")
        # translationBodyJa = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-06_TranslationBodyJa.json")
        # translationIndexZh = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-07_TranslationIndexZh.json")
        # translationWordListZh = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-08_TranslationWordListZh.json")
        # translationBodyZh = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-09_TranslationBodyZh.json")
        # translationIndexEs = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-10_TranslationIndexEs.json")
        # translationWordListEs = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-11_TranslationWordListEs.json")
        # translationBodyEs = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-12_TranslationBodyEs.json")
        correctionKo = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-01_CorrectionKo.json")
        # correctionEn = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-02_CorrectionEn.json")
        sentsSpliting = LoadJsonFrame(PromptDataPath + "/b5410_MixingMasteringPrompt/b5410-02_SentsSpliting.json")
        voiceInspection = LoadJsonFrame(PromptDataPath + "/b5410_MixingMasteringPrompt/b5410-04_VoiceInspection.json")
        voiceSplit = LoadJsonFrame(PromptDataPath + "/b5410_MixingMasteringPrompt/b5410-05_VoiceSplit.json")
        voiceSplitInspection = LoadJsonFrame(PromptDataPath + "/b5410_MixingMasteringPrompt/b5410-06_VoiceSplitInspection.json")
        bestSellerContextDefine = LoadJsonFrame(PromptDataPath + "/b5411_CreatorPrompt/b5411-01_BestSellerContextDefine.json")
        bestSellerCommentAnalysis = LoadJsonFrame(PromptDataPath + "/b5411_CreatorPrompt/b5411-02_BestSellerCommentAnalysis.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingPrompt = db.query(Prompt).first()

        # DB Commit
        if ExistingPrompt:
            ExistingPrompt.SejongCityOfficeOfEducation_Elementary = sejongCityOfficeOfEducation_Elementary
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
            ExistingPrompt.BestSellerContextDefine = bestSellerContextDefine
            ExistingPrompt.BestSellerCommentAnalysis = bestSellerCommentAnalysis
            ### 아래로 추가되는 프롬프트 작성 ###
            
            print(f"[ General | AddPromptToDB 변경사항 업데이트 ]")
        else:
            prompt = Prompt(
                SejongCityOfficeOfEducation_Elementary = sejongCityOfficeOfEducation_Elementary,
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
                VoiceSplitInspection = voiceSplitInspection,
                BestSellerContextDefine = bestSellerContextDefine,
                BestSellerCommentAnalysis = bestSellerCommentAnalysis
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(prompt)
            print(f"[ General | AddPromptToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddPromptToDB()