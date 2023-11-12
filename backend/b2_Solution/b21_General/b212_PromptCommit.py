import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import Prompt
from backend.b1_Api.b13_Database import get_db

def GetPromptDataPath(relativePath='../../b5_Database/b54_PromptData/'):
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CurrentDir, relativePath)

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
        captionPhargraph = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-04_CaptionPhargraph.json")
        # transitionPhargraph = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-05_TransitionPhargraph.json")
        bodySummary = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-06_BodySummary.json")
        contextDefine = LoadJsonFrame(PromptDataPath + "/b542_ContextPrompt/b542-01_ContextDefine.json")
        # contextCompletion = LoadJsonFrame(PromptDataPath + "/b542_ContextPrompt/b542-02_ContextCompletion.json")
        characterDefine = LoadJsonFrame(PromptDataPath + "/b543_CharacterPrompt/b543-01_CharacterDefine.json")
        characterCompletion = LoadJsonFrame(PromptDataPath + "/b543_CharacterPrompt/b543-02_CharacterCompletion.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingPrompt = db.query(Prompt).first()

        # DB Commit
        if ExistingPrompt:
                ExistingPrompt.IndexDefinePreprocess = indexDefinePreprocess
                ExistingPrompt.IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess
                ExistingPrompt.IndexDefine = indexDefine
                ExistingPrompt.CaptionPhargraph = captionPhargraph
                # ExistingPrompt.TransitionPhargraph = transitionPhargraph
                ExistingPrompt.BodySummary = bodySummary
                ExistingPrompt.ContextDefine = contextDefine
                # ExistingPrompt.ContextCompletion = contextCompletion
                ExistingPrompt.CharacterDefine = characterDefine
                ExistingPrompt.CharacterCompletion = characterCompletion
                ### 아래로 추가되는 프롬프트 작성 ###
                
                print(f"[ General | AddPromptToDB 변경사항 업데이트 ]")
        else:
            prompt = Prompt(
                IndexDefinePreprocess = indexDefinePreprocess,
                IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess,
                IndexDefine = indexDefine,
                CaptionPhargraph = captionPhargraph,
                # TransitionPhargraph = transitionPhargraph,
                BodySummary = bodySummary,
                ContextDefine = contextDefine,
                # ContextCompletion = contextCompletion,
                CharacterDefine = characterDefine,
                CharacterCompletion = characterCompletion
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(prompt)
            print(f"[ General | AddPromptToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddPromptToDB()