import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import VoiceDataSet
from backend.b1_Api.b13_Database import get_db

def GetRelationalDataPath():
    RootPath = "/yaas"
    DataPath = "backend/b5_Database/b57_RelationalDatabase"
    return os.path.join(RootPath, DataPath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddVoiceDataSetToDB():
    with get_db() as db:
        
        # JSON 데이터 불러오기
        RelationalDataPath = GetRelationalDataPath()
        typeCastVoiceDataSet = LoadJsonFrame(RelationalDataPath + "/b572_Character/b572-01_TypeCastVoiceDataSet.json")
        ExistingVoiceDataSet = db.query(VoiceDataSet).first()

        # DB Commit
        if ExistingVoiceDataSet:
                ExistingVoiceDataSet.TypeCastVoiceDataSet = typeCastVoiceDataSet                
                print(f"[ General | AddExistingVoiceDataSetToDB 변경사항 업데이트 ]")
        else:
            voiceDataSet = VoiceDataSet(
                TypeCastVoiceDataSet = typeCastVoiceDataSet
                )
            db.add(voiceDataSet)
            print(f"[ General | AddVoiceDataSetToDB 완료 ]")
        db.commit()
         
if __name__ == "__main__":   
    
    AddVoiceDataSetToDB()