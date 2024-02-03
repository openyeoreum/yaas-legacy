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
        
        indexDefinePreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-01_IndexDefinePreprocess.json")
        indexDefineDivisionPreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-02_IndexDefineDivisionPreprocess.json")
        indexDefine = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-03_IndexDefine.json")
        # preprocessBody = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-04_PreprocessBody.json")
        captionCompletion = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-05_CaptionCompletion.json")
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
        translationKo = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-01_TranslationKo.json")
        # translationEn = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-02_TranslationEn.json")
        correctionKo = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-01_CorrectionKo.json")
        # correctionEn = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-02_CorrectionEn.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingPrompt = db.query(Prompt).first()

        # DB Commit
        if ExistingPrompt:
                ExistingPrompt.IndexDefinePreprocess = indexDefinePreprocess
                ExistingPrompt.IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess
                ExistingPrompt.IndexDefine = indexDefine
                # ExistingPrompt.PreprocessBody = preprocessBody
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
                ExistingPrompt.TranslationKo = translationKo
                # ExistingPrompt.TranslationEn = translationEn
                ExistingPrompt.CorrectionKo = correctionKo
                # ExistingPrompt.CorrectionEn = correctionEn
                ### 아래로 추가되는 프롬프트 작성 ###
                
                print(f"[ General | AddPromptToDB 변경사항 업데이트 ]")
        else:
            prompt = Prompt(
                IndexDefinePreprocess = indexDefinePreprocess,
                IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess,
                IndexDefine = indexDefine,
                # PreprocessBody = preprocessBody,
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
                TranslationKo = translationKo,
                # TranslationEn = translationEn,
                CorrectionKo = correctionKo
                # CorrectionEn = correctionEn
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(prompt)
            print(f"[ General | AddPromptToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddPromptToDB()