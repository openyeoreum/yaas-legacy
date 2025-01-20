import sys
sys.path.append("/yaas")

from backend.b2_Solution.b22_DataCollection.b221_VectorDatabase.b2215_VDBSearch import YaaSsearch
from backend.b2_Solution.b22_DataCollection.b222_TargetData.b2222_PublisherData.b22221_PublisherScraper import PublisherDataUpdate
from backend.b2_Solution.b22_DataCollection.b222_TargetData.b2222_PublisherData.b22222_PublisherUpdate import PublisherProcessUpdate
from backend.b2_Solution.b22_DataCollection.b223_TrendData.b2232_BestSellerData.b22321_BestSellerScraper import BookDataUpdate
from backend.b2_Solution.b22_DataCollection.b223_TrendData.b2232_BestSellerData.b22322_BestSellerUpdate import BookProcessUpdate

########################################
########################################
##### SolutionDataCollectionUpdate #####
########################################
########################################

### 솔루션에 데이터컬렉션 진행 및 업데이트 ###
def SolutionDataCollectionUpsert(ProjectName, email, DataCollection):

    #####################################
    ### 01_TargetDataCollectionUpsert ###
    #####################################
    
    ### 01-01_Meditation ###
    
    ### 01-02_Publisher ###
    if 'Publisher' in DataCollection:
        PublisherDataUpdate()
        PublisherProcessUpdate(ProjectName, email)

    ### 01-03_Education ###

    ### 01-04_Company ###

    ####################################
    ### 02_TrendDataCollectionUpsert ###
    ####################################
    
    ### 02-01_Influencer ###
    
    ### 02-02_BestSeller ###
    if 'BestSeller' in DataCollection:
        BookDataUpdate()
        BookProcessUpdate(ProjectName, email)
    
    ###############################
    ### 03_ScriptDataCollection ###
    ###############################

########################################
########################################
##### SolutionDataCollectionSearch #####
########################################
########################################

### 솔루션에 데이터컬렉션 진행 및 업데이트 ###
def SolutionDataCollectionSearch(ProjectName, email, DataCollection):
    Result = YaaSsearch(ProjectName, email, Search, Intention, Extension, Collection, Range, MessagesReview)