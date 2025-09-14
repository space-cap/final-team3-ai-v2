import pandas as pd
import numpy as np
from collections import Counter
import re

# Excel 파일 다시 읽기 (인코딩 문제 해결을 위해)
excel_file = 'data/JJ템플릿.xlsx'

# UTF-8로 인코딩하여 다시 읽기 시도
df = pd.read_excel(excel_file, sheet_name=0)  # 첫 번째 시트 읽기

print("=== 카카오 알림톡 승인받은 템플릿 상세 분석 ===\n")

# 컬럼명 정리 (한글 깨짐 방지)
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

print("1. 기본 통계")
print(f"- 총 템플릿 수: {len(df)}")
print(f"- 고유 텍스트 수: {df['텍스트'].nunique()}")

print("\n2. 분류별 분석")
print("\n2-1. 1차 분류:")
category1_counts = df['분류1차'].value_counts()
for cat, count in category1_counts.items():
    print(f"  {cat}: {count}개")

print("\n2-2. 2차 분류 (상위 10개):")
category2_counts = df['분류2차'].value_counts().head(10)
for cat, count in category2_counts.items():
    print(f"  {cat}: {count}개")

print("\n3. 버튼 분석")
button_counts = df['버튼'].value_counts().head(10)
print("상위 10개 버튼 유형:")
for btn, count in button_counts.items():
    print(f"  {btn}: {count}개")

print("\n4. 광고/순수 분류:")
ad_pure = df['광고순수'].value_counts()
print(ad_pure)

print("\n5. 템플릿 텍스트 길이 분석")
df['텍스트_길이'] = df['텍스트'].str.len()
print(f"평균 길이: {df['텍스트_길이'].mean():.1f}자")
print(f"최소 길이: {df['텍스트_길이'].min()}자")
print(f"최대 길이: {df['텍스트_길이'].max()}자")
print(f"중간값 길이: {df['텍스트_길이'].median():.1f}자")

print("\n6. 변수 사용 패턴 분석")
# #{변수명} 패턴 찾기
variable_pattern = r'#\{([^}]+)\}'
all_variables = []
for text in df['텍스트']:
    if pd.notna(text):
        variables = re.findall(variable_pattern, str(text))
        all_variables.extend(variables)

variable_counts = Counter(all_variables)
print("가장 많이 사용되는 변수 (상위 15개):")
for var, count in variable_counts.most_common(15):
    print(f"  #{{{var}}}: {count}번 사용")

print(f"\n총 변수 사용 횟수: {len(all_variables)}번")
print(f"고유 변수 개수: {len(variable_counts)}개")

print("\n7. 템플릿 예시 (분류별 대표 예시)")
for category in df['분류1차'].unique():
    if pd.notna(category):
        sample = df[df['분류1차'] == category]['텍스트'].iloc[0]
        print(f"\n[{category}] 예시:")
        if len(sample) > 100:
            print(f"  {sample[:100]}...")
        else:
            print(f"  {sample}")

print("\n8. 업무분류별 분석:")
work_category = df['업무분류'].value_counts()
for work, count in work_category.items():
    print(f"  {work}: {count}개")

print("\n9. 서비스분류별 분석:")
service_category = df['서비스분류'].value_counts()
for service, count in service_category.items():
    print(f"  {service}: {count}개")

# 상세 분석 결과를 별도 파일로 저장
analysis_results = {
    '분류1차_분포': category1_counts.to_dict(),
    '분류2차_분포': category2_counts.to_dict(),
    '버튼_분포': button_counts.to_dict(),
    '변수_사용_빈도': dict(variable_counts.most_common(20)),
    '텍스트_길이_통계': {
        '평균': df['텍스트_길이'].mean(),
        '최소': df['텍스트_길이'].min(),
        '최대': df['텍스트_길이'].max(),
        '중간값': df['텍스트_길이'].median()
    }
}

import json
with open('template_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_results, f, ensure_ascii=False, indent=2)

print(f"\n상세 분석 결과가 template_analysis_results.json에 저장되었습니다.")