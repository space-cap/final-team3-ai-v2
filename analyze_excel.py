import pandas as pd
import numpy as np

# Excel 파일 읽기
excel_file = 'data/JJ템플릿.xlsx'

# 모든 시트 이름 확인
xl = pd.ExcelFile(excel_file)
print("Available sheets:", xl.sheet_names)

# '승인받은템플릿' 시트 읽기
if '승인받은템플릿' in xl.sheet_names:
    df = pd.read_excel(excel_file, sheet_name='승인받은템플릿')
    print("\n=== 승인받은템플릿 시트 분석 ===")
    print(f"총 행 수: {len(df)}")
    print(f"총 열 수: {len(df.columns)}")
    print("\n컬럼 목록:")
    for i, col in enumerate(df.columns):
        print(f"{i+1}. {col}")

    print("\n데이터 타입:")
    print(df.dtypes)

    print("\n첫 5행 데이터:")
    print(df.head())

    # 각 컬럼의 고유값 개수 확인
    print("\n각 컬럼별 고유값 개수:")
    for col in df.columns:
        unique_count = df[col].nunique()
        print(f"{col}: {unique_count}개")

    # 결측값 확인
    print("\n결측값 확인:")
    print(df.isnull().sum())

    # 데이터를 CSV로 저장 (분석 편의를 위해)
    df.to_csv('approved_templates_analysis.csv', index=False, encoding='utf-8-sig')
    print("\n분석된 데이터를 approved_templates_analysis.csv로 저장했습니다.")

else:
    print("'승인받은템플릿' 시트를 찾을 수 없습니다.")
    print("사용 가능한 시트:", xl.sheet_names)