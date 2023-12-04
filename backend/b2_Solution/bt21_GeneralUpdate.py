import sys
sys.path.append("/yaas")

from backend.b2_Solution.b21_General.b212_PromptCommit import AddPromptToDB
from backend.b2_Solution.b21_General.b213_TrainingDatasetCommit import AddTrainingDatasetToDB
from backend.b2_Solution.b22_User.b221_UserCommit import AddUserToDB
from backend.b2_Solution.b22_User.b223_ProjectsStorageCommit import AddProjectsStorageToDB
from backend.b2_Solution.b23_Project.b231_Core.b2312_CoreCommit import AddProjectToDB
from backend.b2_Solution.b23_Project.b231_Core.b2312_CoreFileCommit import MoveTextFile, AddTextToDB

### b211_PromptCommit ###
AddPromptToDB()

### b221_UserCommit ###
AddUserToDB('yeoreum00128@gmail.com', 'yeoreum', '0128')
AddUserToDB('junsun0128@gmail.com', 'junyoung', '0128')
AddUserToDB('ahyeon0128@gmail.com', 'ahyeon', '0128')

### b223_ProjectsStorageCommit ###
AddProjectsStorageToDB('yeoreum', 'yeoreum00128@gmail.com')
AddProjectsStorageToDB('junyoung', 'junsun0128@gmail.com')
AddProjectsStorageToDB('ahyeon', 'ahyeon0128@gmail.com')

### b232_ProjectCommit ###
AddProjectToDB('데미안', 'yeoreum00128@gmail.com')
AddProjectToDB('빨간머리앤', 'yeoreum00128@gmail.com')
AddProjectToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
AddProjectToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
AddProjectToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
AddProjectToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
AddProjectToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')
AddProjectToDB('살아서천국극락낙원에가는방법', 'yeoreum00128@gmail.com')

### b233_ProjectFileCommit ###
# AddTextToDB
AddTextToDB('데미안', 'yeoreum00128@gmail.com')
AddTextToDB('빨간머리앤', 'yeoreum00128@gmail.com')
AddTextToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
AddTextToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
AddTextToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
AddTextToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
AddTextToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')
AddTextToDB('살아서천국극락낙원에가는방법', 'yeoreum00128@gmail.com')

### b212_TrainingDatasetCommit ###
AddTrainingDatasetToDB('데미안', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('빨간머리앤', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('웹3.0메타버스', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('나는선비로소이다', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('나는노비로소이다', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('카이스트명상수업', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('우리는행복을진단한다', 'yeoreum00128@gmail.com')
AddTrainingDatasetToDB('살아서천국극락낙원에가는방법', 'yeoreum00128@gmail.com')