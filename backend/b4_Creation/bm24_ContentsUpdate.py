import sys
sys.path.append("/yaas")

from backend.b4_Creation.b43_Creator.b421_BestSellerWebScraper import BestsellerWebScraper

##########################
##########################
##### ContentsUpdate #####
##########################
##########################

### Creation에 마케팅 전략 보고서 제작 및 업데이트 ###
# 스크랩은 도서, 인물, 콘텐츠
# 벡터DB는 도서, 인물, 콘텐츠를 하나의 모델로(페르소나를 형성하는 모델) 통합
# 도서별 마케팅 전략 보고서, 주간/월간 트렌드 보고서(글 콘텐츠 3개), 도서별 콜드메일 마케팅