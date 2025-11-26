import os
import json
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class FinancialAnalyzerService:
    """
    Redis에서 복호화된 재무 데이터를 AI로 분석하고 카테고리별로 분류하는 서비스
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def categorize_financial_data(self, decrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """
        복호화된 재무 데이터를 AI로 분석하여 카테고리별로 분류
        
        Args:
            decrypted_data: 복호화된 데이터 {"소득:급여": "3000000", "지출:식비": "500000", ...}
            
        Returns:
            카테고리별로 분류된 데이터
        """
        # 소득/지출 분리
        income_items = {}
        expense_items = {}
        
        for key, value in decrypted_data.items():
            if key == "USER_TOKEN":
                continue
                
            # "타입:항목" 형태에서 분리
            if ":" in key:
                doc_type, field = key.split(":", 1)
                
                if "소득" in doc_type or "income" in doc_type.lower():
                    income_items[field] = value
                elif "지출" in doc_type or "expense" in doc_type.lower():
                    expense_items[field] = value
        
        # AI로 각각 분석
        categorized_income = self._categorize_income(income_items) if income_items else {}
        categorized_expense = self._categorize_expense(expense_items) if expense_items else {}
        
        # 종합 분석 및 추천
        recommendations = self._generate_recommendations(categorized_income, categorized_expense)
        
        return {
            "income": categorized_income,
            "expense": categorized_expense,
            "recommendations": recommendations,
            "summary": self._generate_summary(categorized_income, categorized_expense)
        }
    
    def _categorize_income(self, income_items: Dict[str, str]) -> Dict[str, Any]:
        """소득을 카테고리별로 분류"""
        if not income_items:
            return {}
            
        prompt = f"""
다음 소득 항목들을 분석하여 아래 카테고리로 분류해줘:

소득 항목:
{json.dumps(income_items, ensure_ascii=False, indent=2)}

분류 카테고리:
1. 고정소득 (fixed_income): 매월 일정하게 들어오는 소득 (급여, 월급, 연봉 등)
2. 변동소득 (variable_income): 불규칙적으로 들어오는 소득 (상여, 보너스, 성과급 등)
3. 기타소득 (other_income): 부수입, 이자소득, 배당소득 등

반드시 다음 JSON 형식으로만 답변해:
{{
  "fixed_income": {{"항목명": "금액"}},
  "variable_income": {{"항목명": "금액"}},
  "other_income": {{"항목명": "금액"}},
  "total_by_category": {{
    "fixed": 총액,
    "variable": 총액,
    "other": 총액
  }},
  "total_income": 전체총액
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0
            )
            
            result_text = response.choices[0].message.content.strip()
            # JSON 추출 (마크다운 코드블록 제거)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(result_text)
        except Exception as e:
            print(f"[ERROR] Income categorization failed: {str(e)}")
            return {"error": str(e), "raw_items": income_items}

    def _categorize_expense(self, expense_items: Dict[str, str]) -> Dict[str, Any]:
        """지출을 카테고리별로 분류"""
        if not expense_items:
            return {}
            
        prompt = f"""
다음 지출 항목들을 분석하여 아래 카테고리로 분류해줘:

지출 항목:
{json.dumps(expense_items, ensure_ascii=False, indent=2)}

분류 카테고리:
1. 필수지출 (essential):
   - 주거비 (housing): 월세, 관리비, 주택대출 등
   - 식비 (food): 식료품, 외식비 등
   - 교통비 (transportation): 대중교통, 차량유지비, 주유비 등
   - 통신비 (communication): 휴대폰, 인터넷 등
   - 보험료 (insurance): 건강보험, 자동차보험 등

2. 선택지출 (discretionary):
   - 문화생활 (culture): 영화, 공연, 취미 등
   - 쇼핑 (shopping): 의류, 잡화 등
   - 여행 (travel): 국내외 여행 경비
   - 미용 (beauty): 미용실, 화장품 등
   - 교육 (education): 학원, 도서, 강의 등

3. 금융지출 (financial):
   - 저축 (savings): 적금, 예금 등
   - 투자 (investment): 주식, 펀드, 부동산 등
   - 대출상환 (loan_repayment): 각종 대출 원리금 상환

4. 기타지출 (other): 위에 해당하지 않는 항목

반드시 다음 JSON 형식으로만 답변해:
{{
  "essential": {{
    "housing": {{"항목명": "금액"}},
    "food": {{"항목명": "금액"}},
    "transportation": {{"항목명": "금액"}},
    "communication": {{"항목명": "금액"}},
    "insurance": {{"항목명": "금액"}}
  }},
  "discretionary": {{
    "culture": {{"항목명": "금액"}},
    "shopping": {{"항목명": "금액"}},
    "travel": {{"항목명": "금액"}},
    "beauty": {{"항목명": "금액"}},
    "education": {{"항목명": "금액"}}
  }},
  "financial": {{
    "savings": {{"항목명": "금액"}},
    "investment": {{"항목명": "금액"}},
    "loan_repayment": {{"항목명": "금액"}}
  }},
  "other": {{"항목명": "금액"}},
  "total_by_main_category": {{
    "essential": 총액,
    "discretionary": 총액,
    "financial": 총액,
    "other": 총액
  }},
  "total_expense": 전체총액
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0
            )
            
            result_text = response.choices[0].message.content.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(result_text)
        except Exception as e:
            print(f"[ERROR] Expense categorization failed: {str(e)}")
            return {"error": str(e), "raw_items": expense_items}

    def _generate_recommendations(self, income_data: Dict, expense_data: Dict) -> Dict[str, Any]:
        """소득/지출 데이터를 기반으로 자산 분배 추천"""
        if not income_data or not expense_data:
            return {"message": "소득 또는 지출 데이터가 부족합니다"}
        
        # 안전한 타입 변환
        try:
            total_income = int(income_data.get("total_income", 0)) if income_data.get("total_income") else 0
        except (ValueError, TypeError):
            total_income = 0
            
        try:
            total_expense = int(expense_data.get("total_expense", 0)) if expense_data.get("total_expense") else 0
        except (ValueError, TypeError):
            total_expense = 0
        
        prompt = f"""
당신은 전문 재무설계사입니다. 다음 데이터를 분석하여 자산 분배를 추천해주세요.

소득 분석:
{json.dumps(income_data, ensure_ascii=False, indent=2)}

지출 분석:
{json.dumps(expense_data, ensure_ascii=False, indent=2)}

다음 항목들을 포함하여 분석해주세요:

1. 재무 건전성 평가
   - 소득 대비 지출 비율
   - 필수지출 비율
   - 선택지출 비율
   - 저축/투자 비율

2. 자산 분배 추천 (월 가처분소득 기준)
   - 비상자금: X원 (Y%)
   - 단기저축: X원 (Y%)
   - 장기투자: X원 (Y%)
   - 보험: X원 (Y%)
   - 기타: X원 (Y%)

3. 개선 제안 (우선순위 순)
   - 줄일 수 있는 지출 항목
   - 늘려야 할 항목
   - 구체적인 실행 방법

4. 목표별 저축 계획
   - 단기 목표 (1년 이내)
   - 중기 목표 (1-5년)
   - 장기 목표 (5년 이상)

반드시 다음 JSON 형식으로만 답변해:
{{
  "health_score": {{
    "overall": 0-100점,
    "income_to_expense_ratio": 비율,
    "essential_expense_ratio": 비율,
    "savings_ratio": 비율,
    "comment": "평가 코멘트"
  }},
  "asset_allocation": {{
    "emergency_fund": {{"amount": 금액, "percentage": 비율, "reason": "이유"}},
    "short_term_savings": {{"amount": 금액, "percentage": 비율, "reason": "이유"}},
    "long_term_investment": {{"amount": 금액, "percentage": 비율, "reason": "이유"}},
    "insurance": {{"amount": 금액, "percentage": 비율, "reason": "이유"}},
    "other": {{"amount": 금액, "percentage": 비율, "reason": "이유"}}
  }},
  "improvement_suggestions": [
    {{"priority": 1, "category": "카테고리", "action": "구체적 행동", "expected_saving": 예상절감액}},
    {{"priority": 2, "category": "카테고리", "action": "구체적 행동", "expected_saving": 예상절감액}}
  ],
  "savings_goals": {{
    "short_term": {{"target": "목표", "amount": 금액, "months": 개월}},
    "medium_term": {{"target": "목표", "amount": 금액, "months": 개월}},
    "long_term": {{"target": "목표", "amount": 금액, "months": 개월}}
  }}
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(result_text)
        except Exception as e:
            print(f"[ERROR] Recommendation generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _generate_summary(self, income_data: Dict, expense_data: Dict) -> Dict[str, Any]:
        """전체 재무 상황 요약"""
        # 안전한 타입 변환
        try:
            total_income = int(income_data.get("total_income", 0)) if income_data.get("total_income") else 0
        except (ValueError, TypeError):
            total_income = 0
            
        try:
            total_expense = int(expense_data.get("total_expense", 0)) if expense_data.get("total_expense") else 0
        except (ValueError, TypeError):
            total_expense = 0
        
        surplus = total_income - total_expense
        surplus_ratio = (surplus / total_income * 100) if total_income > 0 else 0
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "surplus": surplus,
            "surplus_ratio": round(surplus_ratio, 2),
            "status": "흑자" if surplus > 0 else "적자" if surplus < 0 else "수지균형"
        }
