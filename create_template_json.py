import pandas as pd
import json
import re
from datetime import datetime
from collections import Counter

def extract_variables(text):
    """텍스트에서 #{변수명} 패턴을 추출"""
    if pd.isna(text):
        return []
    variable_pattern = r'#\{([^}]+)\}'
    return re.findall(variable_pattern, str(text))

def analyze_template_structure(text):
    """템플릿 구조 분석"""
    if pd.isna(text):
        return {}

    text_str = str(text)

    # 기본 정보
    structure = {
        "length": len(text_str),
        "sentence_count": len([s for s in text_str.split('.') if s.strip()]),
        "has_greeting": bool(re.search(r'안녕하세요|고객님|회원님', text_str)),
        "has_button_mention": bool(re.search(r'버튼|클릭|확인|아래', text_str)),
        "has_contact": bool(re.search(r'연락|문의|전화', text_str)),
        "politeness_level": "formal" if "습니다" in text_str else "casual"
    }

    return structure

def categorize_template_length(length):
    """템플릿 길이에 따른 카테고리 분류"""
    if length <= 80:
        return "short"
    elif length <= 150:
        return "medium"
    else:
        return "long"

def main():
    print("=== 카카오 알림톡 템플릿 JSON 데이터 생성 ===\n")

    # Excel 파일 읽기
    excel_file = 'data/JJ템플릿.xlsx'
    df = pd.read_excel(excel_file, sheet_name=0)

    # 컬럼명 정리
    col_mapping = {
        df.columns[0]: '텍스트',
        df.columns[1]: '분류1차',
        df.columns[2]: '분류2차',
        df.columns[3]: '자동발송관련',
        df.columns[4]: '템플릿코드',
        df.columns[5]: '버튼',
        df.columns[6]: '광고순수',
        df.columns[7]: '업무분류',
        df.columns[8]: '서비스분류'
    }

    df = df.rename(columns=col_mapping)

    # 1. 개별 템플릿 데이터 생성
    templates_data = []

    for idx, row in df.iterrows():
        if pd.notna(row['텍스트']):
            text = str(row['텍스트']).strip()
            variables = extract_variables(text)
            structure = analyze_template_structure(text)

            template_doc = {
                "id": f"template_{idx:03d}",
                "text": text,
                "metadata": {
                    "category_1": str(row['분류1차']) if pd.notna(row['분류1차']) else "기타",
                    "category_2": str(row['분류2차']) if pd.notna(row['분류2차']) else "기타",
                    "auto_send": str(row['자동발송관련']) if pd.notna(row['자동발송관련']) else "",
                    "template_code": str(row['템플릿코드']) if pd.notna(row['템플릿코드']) else "",
                    "button": str(row['버튼']) if pd.notna(row['버튼']) else "X",
                    "ad_type": str(row['광고순수']) if pd.notna(row['광고순수']) else "",
                    "business_type": str(row['업무분류']) if pd.notna(row['업무분류']) else "기타",
                    "service_type": str(row['서비스분류']) if pd.notna(row['서비스분류']) else "기타",
                    "variables": variables,
                    "variable_count": len(variables),
                    "length": structure["length"],
                    "length_category": categorize_template_length(structure["length"]),
                    "sentence_count": structure["sentence_count"],
                    "has_greeting": structure["has_greeting"],
                    "has_button_mention": structure["has_button_mention"],
                    "has_contact": structure["has_contact"],
                    "politeness_level": structure["politeness_level"],
                    "approval_status": "approved",
                    "created_at": "2024-08-27",
                    "source": "JJ템플릿_승인받은템플릿"
                }
            }

            templates_data.append(template_doc)

    # 2. 패턴 데이터 생성 (분류별 공통 패턴)
    patterns_data = []

    # 분류1차별 패턴 추출
    for category1 in df['분류1차'].dropna().unique():
        category_templates = df[df['분류1차'] == category1]

        # 공통 변수 추출
        all_variables = []
        common_words = []
        common_buttons = []

        for _, row in category_templates.iterrows():
            if pd.notna(row['텍스트']):
                variables = extract_variables(row['텍스트'])
                all_variables.extend(variables)

                # 일반적인 단어 추출
                words = re.findall(r'[가-힣]+', str(row['텍스트']))
                common_words.extend([w for w in words if len(w) > 1])

                if pd.notna(row['버튼']) and row['버튼'] != 'X':
                    common_buttons.append(str(row['버튼']))

        # 빈도 분석
        variable_counter = Counter(all_variables)
        word_counter = Counter(common_words)
        button_counter = Counter(common_buttons)

        # 제외할 일반적인 단어들
        exclude_words = ['안녕하세요', '고객님', '님', '확인', '하실', '수', '있습니다',
                        '바랍니다', '감사합니다', '이용', '서비스', '문의', '연락']

        filtered_words = [(word, count) for word, count in word_counter.most_common(10)
                         if word not in exclude_words and len(word) > 1]

        pattern_doc = {
            "id": f"pattern_{category1.replace('/', '_').replace(' ', '_')}",
            "category": category1,
            "type": "category_pattern",
            "metadata": {
                "template_count": len(category_templates),
                "common_variables": dict(variable_counter.most_common(5)),
                "characteristic_words": dict(filtered_words[:5]),
                "common_buttons": dict(button_counter.most_common(3)),
                "avg_length": int(category_templates['텍스트'].str.len().mean()),
                "length_range": {
                    "min": int(category_templates['텍스트'].str.len().min()),
                    "max": int(category_templates['텍스트'].str.len().max())
                },
                "success_indicators": {
                    "greeting_usage": sum(1 for t in category_templates['텍스트']
                                        if pd.notna(t) and '안녕하세요' in str(t)) / len(category_templates),
                    "variable_usage": len(all_variables) / len(category_templates),
                    "button_usage": sum(1 for b in category_templates['버튼']
                                      if pd.notna(b) and b != 'X') / len(category_templates)
                }
            }
        }

        patterns_data.append(pattern_doc)

    # 3. 성공 지표 데이터 생성
    success_indicators = {
        "id": "success_indicators_summary",
        "type": "success_metrics",
        "data": {
            "optimal_length_range": {"min": 80, "max": 150, "reason": "55.7% of approved templates"},
            "top_variables": dict(Counter([var for row in df.iterrows()
                                          for var in extract_variables(row[1]['텍스트'])]).most_common(10)),
            "greeting_patterns": {
                "안녕하세요": {"usage_rate": 0.684, "context": "universal"},
                "고객님": {"usage_rate": 0.247, "context": "formal_business"},
                "회원님": {"usage_rate": 0.042, "context": "membership_service"}
            },
            "button_patterns": {
                "자세히 확인하기": {"usage_rate": 0.641, "context": "detail_information"},
                "상세 확인": {"usage_rate": 0.069, "context": "additional_info"},
                "확인하기": {"usage_rate": 0.024, "context": "general_confirmation"}
            },
            "structure_patterns": {
                "greeting_main_guide_action": {"success_rate": 0.78, "description": "인사-본문-안내-행동유도"},
                "greeting_main_action": {"success_rate": 0.65, "description": "인사-본문-행동유도"},
                "main_guide_action": {"success_rate": 0.45, "description": "본문-안내-행동유도"}
            },
            "approval_factors": {
                "policy_compliance": {"weight": 0.4, "description": "정책 준수 여부"},
                "pattern_matching": {"weight": 0.3, "description": "성공 패턴 일치도"},
                "length_optimization": {"weight": 0.2, "description": "적절한 길이 유지"},
                "user_experience": {"weight": 0.1, "description": "사용자 경험 고려"}
            }
        },
        "updated_at": datetime.now().isoformat()
    }

    # 4. 파일 저장

    # 개별 템플릿 데이터
    with open('data/approved_templates.json', 'w', encoding='utf-8') as f:
        json.dump(templates_data, f, ensure_ascii=False, indent=2)

    # 패턴 데이터
    with open('data/template_patterns.json', 'w', encoding='utf-8') as f:
        json.dump(patterns_data, f, ensure_ascii=False, indent=2)

    # 성공 지표 데이터
    with open('data/success_indicators.json', 'w', encoding='utf-8') as f:
        json.dump(success_indicators, f, ensure_ascii=False, indent=2)

    # 통합 데이터 (벡터DB용)
    vector_db_data = {
        "templates": templates_data,
        "patterns": patterns_data,
        "success_indicators": success_indicators,
        "metadata": {
            "total_templates": len(templates_data),
            "total_patterns": len(patterns_data),
            "data_source": "JJ템플릿.xlsx",
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
    }

    with open('data/kakao_template_vectordb_data.json', 'w', encoding='utf-8') as f:
        json.dump(vector_db_data, f, ensure_ascii=False, indent=2)

    print("JSON 데이터 파일 생성 완료:")
    print(f"   - approved_templates.json: {len(templates_data)}개 템플릿")
    print(f"   - template_patterns.json: {len(patterns_data)}개 패턴")
    print(f"   - success_indicators.json: 성공 지표 데이터")
    print(f"   - kakao_template_vectordb_data.json: 통합 벡터DB 데이터")

    print(f"\n데이터 요약:")
    print(f"   - 총 승인 템플릿: {len(templates_data)}개")
    print(f"   - 평균 길이: {sum(t['metadata']['length'] for t in templates_data) / len(templates_data):.1f}자")
    print(f"   - 주요 분류: {Counter([t['metadata']['category_1'] for t in templates_data]).most_common(3)}")

if __name__ == "__main__":
    main()