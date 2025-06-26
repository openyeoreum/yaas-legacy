# 1. 베이스 이미지 선택
FROM python:3.11-slim

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul

# 3. [개선] 시스템 패키지 설치를 한 번에 실행
# 여러 RUN 명령어를 하나로 합쳐 이미지 레이어 수를 줄이고, apt-get update는 한 번만 실행합니다.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # 기본 유틸리티
    tzdata git curl wget \
    # Node.js 설치에 필요한 패키지
    nodejs \
    && \
    # Node.js LTS 설치 스크립트 실행 (curl을 먼저 설치해야 사용 가능)
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    # 시간대 설정
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    # 설치 후 불필요한 파일 정리
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 4. 작업 디렉터리 설정
WORKDIR /yaas

# 5. [개선] 의존성 설치를 위한 파일만 먼저 복사 (캐시 효율성 극대화)
# 소스코드보다 먼저 requirements.txt를 복사합니다.
# 이렇게 하면 requirements.txt 내용이 바뀔 때만 아래 pip install이 실행됩니다.
COPY requirements.txt .

# 6. [개선] 파이썬 패키지 설치
# 소스 코드를 복사하기 전에 의존성을 먼저 설치합니다.
RUN pip install --no-cache-dir -r requirements.txt

# 7. [개선] 나머지 모든 소스 코드 복사
# 의존성 설치가 끝난 후, 나머지 파일들을 복사합니다.
# 이제 소스 코드만 변경되면 여기부터 빌드가 다시 시작됩니다.
COPY . .

# 8. 컨테이너 실행
# 개발용으로 컨테이너를 계속 실행 상태로 유지
CMD [ "sleep", "infinity" ]