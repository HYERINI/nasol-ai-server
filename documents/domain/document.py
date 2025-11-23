from datetime import datetime, timedelta

## documents 형식은 여러 종류가 있다.
'''
- 주요 문서 분석 대상 타입
    - 영수증(사진/스캔) - 이미지 기반 문서 포함
    - 거래 명세서
    - 계약서
    - 공문/보고서 (PDF)
    - 표/테이블 포함 문서
    - 원천징수영수증
    - 급여명세서
    - 홈택스 연말정산 간소화 자료
- 문서 종류에 따라 다음 항목을 추출 → JSON 형태로 제공(추후 논의)
    - 제목/일자/발신자/수신자
    - 총 금액, 품목 (영수증)
    - 조항별 구조 (계약서)
    - 표/테이블 데이터
    - 문서 메타데이터
    - 지출별 카테고리 (EX; 식비, 카페, 의류비)
        - 소득별 지출 비중 가이드
        - 신용/체크/현금영수증 사용액 구분
        - 국민연금·건강보험·고용보험 납부액
        - 연금저축/IRP 납입액
        - 의료비, 교육비, 기부금 등
'''
## 위 형태별에 따라 domain을 만드는 것은 redis에만 저장되는 app 특성 상 낭비가 될 가능성이 높다.
## session_id redis에 저장되어있는 session_id
## file_key는 대상 항목 (Ex; 원천징수증_근무처명, 원천징수영수증_급여, 영수증_거래처, 영수증_금액 등등)
## file_value는 대상 항목의 수치 (Ex; 코드랩주식회사, 100000000, GS_강남점, 25000 등등)로 관리한다.
## 추후 시간이 남으면 key 값은 코드화

class Document:
    def __init__(self, session_id:str, file_key:str, file_value:str):
        self.session_id = session_id
        self.file_key = file_key
        self.file_value = file_value
