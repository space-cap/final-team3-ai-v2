import pandas as pd
import re
from collections import Counter, defaultdict

# Excel 파일 읽기
df = pd.read_excel('data/JJ템플릿.xlsx', sheet_name=0)

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

print("=== 카카오 알림톡 템플릿 생성을 위한 핵심 패턴 분석 ===\n")

# 1. 템플릿 시작 패턴 분석
print("1. 템플릿 시작 패턴 분석")
start_patterns = []
for text in df['텍스트']:
    if pd.notna(text):
        # 첫 20자 추출
        start = str(text)[:20].strip()
        start_patterns.append(start)

start_counter = Counter(start_patterns)
print("가장 많이 사용되는 시작 패턴 (상위 10개):")
for pattern, count in start_counter.most_common(10):
    print(f"  '{pattern}': {count}번")

# 2. 인사말 패턴 분석
print("\n2. 인사말 패턴 분석")
greetings = ['안녕하세요', '고객님', '회원님', '님,', '님께서']
greeting_usage = {}
for greeting in greetings:
    count = sum(1 for text in df['텍스트'] if pd.notna(text) and greeting in str(text))
    greeting_usage[greeting] = count

print("인사말 사용 빈도:")
for greeting, count in sorted(greeting_usage.items(), key=lambda x: x[1], reverse=True):
    print(f"  '{greeting}': {count}개 템플릿에서 사용")

# 3. 업종별 템플릿 특성 분석
print("\n3. 업종별 템플릿 특성 분석")
business_patterns = {}
for category in df['분류1차'].unique():
    if pd.notna(category):
        category_templates = df[df['분류1차'] == category]['텍스트']

        # 해당 카테고리에서 자주 사용되는 단어들
        words = []
        for text in category_templates:
            if pd.notna(text):
                # 특수문자 제거하고 단어 추출
                clean_text = re.sub(r'[^\w\s가-힣]', ' ', str(text))
                words.extend(clean_text.split())

        word_counter = Counter(words)
        # 일반적인 단어들 제외 (안녕하세요, 고객님 등)
        common_words = ['안녕하세요', '고객님', '님', '확인', '하실', '수', '있습니다', '바랍니다', '감사합니다']
        filtered_words = [(word, count) for word, count in word_counter.most_common(10) if word not in common_words and len(word) > 1]

        business_patterns[category] = filtered_words[:5]

for category, words in business_patterns.items():
    print(f"[{category}] 특징적 단어:")
    for word, count in words:
        print(f"  {word}: {count}번")

# 4. 길이별 템플릿 패턴
print("\n4. 길이별 템플릿 특성")
df['텍스트_길이'] = df['텍스트'].str.len()

short_templates = df[df['텍스트_길이'] <= 80]
medium_templates = df[(df['텍스트_길이'] > 80) & (df['텍스트_길이'] <= 150)]
long_templates = df[df['텍스트_길이'] > 150]

print(f"짧은 템플릿 (80자 이하): {len(short_templates)}개")
print(f"  주요 분류: {short_templates['분류2차'].value_counts().head(3).to_dict()}")

print(f"중간 템플릿 (81-150자): {len(medium_templates)}개")
print(f"  주요 분류: {medium_templates['분류2차'].value_counts().head(3).to_dict()}")

print(f"긴 템플릿 (151자 이상): {len(long_templates)}개")
print(f"  주요 분류: {long_templates['분류2차'].value_counts().head(3).to_dict()}")

# 5. 변수 사용 패턴 심화 분석
print("\n5. 변수 사용 패턴 심화 분석")
variable_pattern = r'#\{([^}]+)\}'
category_variables = defaultdict(list)

for idx, row in df.iterrows():
    if pd.notna(row['텍스트']):
        variables = re.findall(variable_pattern, str(row['텍스트']))
        category_variables[row['분류1차']].extend(variables)

print("분류별 주요 변수 사용:")
for category, variables in category_variables.items():
    if category and variables:
        var_counter = Counter(variables)
        top_vars = var_counter.most_common(3)
        print(f"[{category}]: {', '.join([f'#{{{var}}}({count})' for var, count in top_vars])}")

# 6. 버튼 텍스트와 템플릿 내용 상관관계
print("\n6. 버튼 텍스트 분석")
button_categories = {}
for button in df['버튼'].unique():
    if pd.notna(button) and button != 'X':
        related_categories = df[df['버튼'] == button]['분류2차'].value_counts().head(3)
        if len(related_categories) > 0:
            button_categories[button] = related_categories.to_dict()

print("주요 버튼별 연관 분류:")
for button, categories in list(button_categories.items())[:8]:
    print(f"[{button}]: {list(categories.keys())[:2]}")

# 7. 성공적인 템플릿 패턴 (상위 분류 기준)
print("\n7. 성공적인 템플릿 구조 패턴")
top_category = df['분류2차'].value_counts().index[0]  # 가장 많은 분류
top_templates = df[df['분류2차'] == top_category]['텍스트']

print(f"최다 분류 '{top_category}' 템플릿 구조 분석:")
structure_patterns = []
for text in top_templates.head(10):
    if pd.notna(text):
        # 문장 구조 패턴 분석
        sentences = str(text).split('.')
        if len(sentences) >= 2:
            structure = f"{len(sentences)}문장"
            has_greeting = "인사" if "안녕" in str(text) or "고객님" in str(text) else "무인사"
            has_button_mention = "버튼언급" if "버튼" in str(text) or "클릭" in str(text) else "무버튼언급"
            structure_patterns.append(f"{structure}-{has_greeting}-{has_button_mention}")

structure_counter = Counter(structure_patterns)
print("구조 패턴 분석:")
for pattern, count in structure_counter.most_common(5):
    print(f"  {pattern}: {count}개")

print("\n=== 분석 완료 ===")
print("이 분석 결과를 바탕으로 AI 템플릿 생성 시스템을 구축할 수 있습니다.")