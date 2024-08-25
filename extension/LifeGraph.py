import sys
sys.path.append("/yaas")

from e1_Solution.e11_LifeGraphUpdate import LifeGraphUpdate
from e1_Solution.e12_LifeGraphAnalysisUpdate import LifeGraphAnalysisProcess
from e1_Solution.e13_LifeGraphReactionUpdate import LifeGraphReactionProcess

### LifeGraph : 라이프그래프 업데이트 및 피드백 ###
def LifeGraph(email, projectName, term, reactionYYMM):

    LifeGraphUpdate(term)

    ## LifeGraphAnalysis 추가 개발 사항
    # 1. 라이프 그래프 분석 (한/영) 두 가지로 결과 나오도록 구성
    # 2. 라이프 그래프 분석 결과 리포트가 형성되도록 구성
    LifeGraphAnalysisProcess(projectName, email)

    ## Reaction 데이터 업데이트 방법
    # 1. 스티비에 "상세 통계 한번에 내보내기"
    # 2. 폴더 압축을 풀고, "전송.csv" 파일을 추가하여 "YYMMDD_reaction" 폴더 완성
    # 3. 폴더 추가 및 프로세스 진행
    # 4. "MMDD_reaction_구글폼매칭실패.json"은 라이프그래프 구글시트에 없는 대상임으로, 수동으로(사람이 직접) 업데이트
    LifeGraphReactionProcess(reactionYYMM)
    
    print("[ 라이프그래프 구글시트 업데이트 완료 ]")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "General"
    projectName = "Meditation"
    term = "Day"
    reactionYYMM = "2408"
    #########################################################################
    
    LifeGraph(email, projectName, term, reactionYYMM)