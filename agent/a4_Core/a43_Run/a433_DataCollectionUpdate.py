import sys
sys.path.append("/yaas")

from agent.a5_Solution.a51_Collection.a511_VectorDatabase.a5115_VDBSearch import YaaSsearch
from agent.a5_Solution.a51_Collection.a512_TargetData.a5122_PublisherData.a51221_PublisherScraper import PublisherDataUpdate
from agent.a5_Solution.a51_Collection.a512_TargetData.a5122_PublisherData.a51222_PublisherUpdate import PublisherDataProcessUpdate
from agent.a5_Solution.a51_Collection.a513_TrendData.a5132_BestSellerData.a51321_BestSellerScraper import BookDataUpdate
from agent.a5_Solution.a51_Collection.a513_TrendData.a5132_BestSellerData.a51322_BestSellerUpdate import BookDataProcessUpdate

########################################
########################################
##### SolutionDataCollectionUpdate #####
########################################
########################################

### 솔루션에 데이터컬렉션 진행 및 업데이트 ###
def SolutionDataCollectionUpsert(ProjectName, email, DataCollection, MessagesReview):

    #####################################
    ### 01_TargetDataCollectionUpsert ###
    #####################################
    
    ### 01-01_Meditation ###
    
    ### 01-02_Publisher ###
    if 'Publisher' in DataCollection:
        PublisherDataUpdate()
        PublisherDataProcessUpdate(ProjectName, email, MessagesReview = MessagesReview)

    ### 01-03_Education ###

    ### 01-04_Company ###

    ####################################
    ### 02_TrendDataCollectionUpsert ###
    ####################################
    
    ### 02-01_Influencer ###
    
    ### 02-02_BestSeller ###
    if 'Book' in DataCollection:
        BookDataUpdate()
        BookDataProcessUpdate(ProjectName, email, MessagesReview = MessagesReview)
    
    ###############################
    ### 03_ScriptDataCollection ###
    ###############################

########################################
########################################
##### SolutionDataCollectionSearch #####
########################################
########################################

### 솔루션에 데이터컬렉션 진행 및 업데이트 ###
def SolutionDataCollectionSearch(ProjectName, email, Search, Intention, Extension, Collection, Range, MessagesReview):

    ###############################
    ### 01_DataCollectionSearch ###
    ###############################
    
    YaaSsearch(ProjectName, email, Search, Intention, Extension, Collection, Range, MessagesReview = MessagesReview)