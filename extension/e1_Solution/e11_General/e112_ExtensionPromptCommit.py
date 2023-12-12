import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import ExtensionPrompt
from backend.b1_Api.b13_Database import get_db

def GetExtensionPromptDataPath():
    RootPath = "/yaas"
    DataPath = "extension/e4_Database/e43_PromptData"
    return os.path.join(RootPath, DataPath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddExtensionPromptToDB():
    with get_db() as db:
        
        # JSON 데이터 불러오기
        ExtensionPromptDataPath = GetExtensionPromptDataPath()
        
        lifeGraphTranslationKo = LoadJsonFrame(ExtensionPromptDataPath + "/e431_LifeGraphPrompt/e4311_Preprocess/e4311-01_LifeGraphTranslationKo.json")
        lifeGraphTranslationEn = LoadJsonFrame(ExtensionPromptDataPath + "/e431_LifeGraphPrompt/e4311_Preprocess/e4311-02_LifeGraphTranslationEn.json")
        lifeGraphContextDefine = LoadJsonFrame(ExtensionPromptDataPath + "/e431_LifeGraphPrompt/e4312_Context/e4312-01_LifeGraphContextDefine.json")
        lifeGraphWMWMDefine = LoadJsonFrame(ExtensionPromptDataPath + "/e431_LifeGraphPrompt/e4312_Context/e4312-02_LifeGraphWMWMDefine.json")
        # lifeGraphWMWMMatching = LoadJsonFrame(ExtensionPromptDataPath + "/e431_LifeGraphPrompt/e4312_Context/e4312-03_LifeGraphWMWMMatching.json")
        # videoPreprocess = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4341_Preprocess/e4341-01_VideoPreprocess.json")
        # videoTranslationKo = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4341_Preprocess/e4341-02_VideoTranslationKo.json")
        # videoTranslationEn = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4341_Preprocess/e4341-03_VideoTranslationEn.json")
        # videoContextDefine = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4342_Context/e4342-01_VideoContextDefine.json")
        # videoContextCompletion = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4342_Context/e4342-02_VideoContextCompletion.json")
        # videoWMWMDefine = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4342_Context/e4342-03_VideoWMWMDefine.json")
        # videoWMWMMatching = LoadJsonFrame(ExtensionPromptDataPath + "/e434_VideoPrompt/e4342_Context/e4342-04_VideoWMWMMatching.json")
        ### 아래로 추가되는 프롬프트 작성 ###

        ExistingExtensionPrompt = db.query(ExtensionPrompt).first()

        # DB Commit
        if ExistingExtensionPrompt:
                ExistingExtensionPrompt.LifeGraphTranslationKo = lifeGraphTranslationKo
                ExistingExtensionPrompt.LifeGraphTranslationEn = lifeGraphTranslationEn
                ExistingExtensionPrompt.LifeGraphContextDefine = lifeGraphContextDefine
                ExistingExtensionPrompt.LifeGraphWMWMDefine = lifeGraphWMWMDefine
                # ExistingExtensionPrompt.LifeGraphWMWMMatching = lifeGraphWMWMMatching
                # ExistingExtensionPrompt.VideoPreprocess = videoPreprocess
                # ExistingExtensionPrompt.VideoTranslationKo = videoTranslationKo
                # ExistingExtensionPrompt.VideoTranslationEn = videoTranslationEn
                # ExistingExtensionPrompt.VideoContextDefine = videoContextDefine
                # ExistingExtensionPrompt.VideoContextCompletion = videoContextCompletion
                # ExistingExtensionPrompt.VideoWMWMDefine = videoWMWMDefine
                # ExistingExtensionPrompt.VideoWMWMMatching = videoWMWMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                
                print(f"[ General | AddExtensionPromptToDB 변경사항 업데이트 ]")
        else:
            extensionPrompt = ExtensionPrompt(
                LifeGraphTranslationKo = lifeGraphTranslationKo,
                LifeGraphTranslationEn = lifeGraphTranslationEn,
                LifeGraphContextDefine = lifeGraphContextDefine,
                LifeGraphWMWMDefine = lifeGraphWMWMDefine
                # LifeGraphWMWMMatching = lifeGraphWMWMMatching,
                # VideoPreprocess = videoPreprocess,
                # VideoTranslationKo = videoTranslationKo,
                # VideoTranslationEn = videoTranslationEn,
                # VideoContextDefine = videoContextDefine,
                # VideoContextCompletion = videoContextCompletion,
                # VideoWMWMDefine = videoWMWMDefine,
                # VideoWMWMMatching = lifeGraphWMWMMatching
                ### 아래로 추가되는 프롬프트 작성 ###
                )
            db.add(extensionPrompt)
            print(f"[ General | AddPromptToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddExtensionPromptToDB()