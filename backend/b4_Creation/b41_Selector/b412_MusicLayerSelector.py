import os
import unicodedata
import json
import requests
import time
import random
import re
import copy
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from pydub import AudioSegment
from collections import defaultdict
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetSoundDataSet


##########################
##### VoiceLayer 생성 #####
##########################
## LoadVoiceLayer 로드
def LoadVoiceLayer(projectName, email, MainLang = 'Ko'):
    project = GetProject(projectName, email)
    VoiceLayer = project.MixingMasteringKo[1]['AudioBookLayers' + MainLang]
    
    return VoiceLayer



if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    mainLang = 'Ko'
    #########################################################################
    
    VoiceLayer = LoadVoiceLayer(projectName, email, MainLang = mainLang)
    
    print(VoiceLayer[0])