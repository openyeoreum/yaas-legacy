import sys
sys.path.append("/yaas")

from extension.e1_Solution.e11_General.e112_ExtensionPromptCommit import AddExtensionPromptToDB
from extension.e1_Solution.e12_ExtensionProject.e121_LifeGraph.e1211_LifeGraphCommit import AddLifeGraphToDB
from extension.e1_Solution.e12_ExtensionProject.e124_Video.e1241_VideoCommit import AddVideoToDB

### e112_ExtensionPromptCommit ###
AddExtensionPromptToDB()

### e1211_LifeGraphCommit ###
AddLifeGraphToDB("CourseraMeditation", "Duck-JooLee", "Coursera", "Global", 23120601)

# ### e1241_VideoCommit ###
# AddVideoToDB("MaumMeditation", "Hoe-JunJeong", "Youtube", "MeditationLifeOrg", "Ko", 23120601)