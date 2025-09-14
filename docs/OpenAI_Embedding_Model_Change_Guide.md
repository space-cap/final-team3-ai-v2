# OpenAI 임베딩 모델 변경 가이드

## 개요

OpenAI 임베딩 모델을 변경할 때는 단순히 코드만 수정하는 것이 아니라, 기존에 임베딩된 벡터 데이터와의 호환성 문제로 인해 전체 벡터 데이터베이스를 재구축해야 합니다.

## 임베딩 모델 변경이 필요한 경우

1. **성능 개선**: 더 나은 성능의 새로운 모델 출시 시
2. **비용 최적화**: 더 저렴한 모델로 변경하여 운영 비용 절감
3. **기능 개선**: 새로운 기능이나 언어 지원이 추가된 모델 사용
4. **모델 지원 중단**: 기존 모델이 deprecated 되어 새 모델로 마이그레이션 필요

## 임베딩 모델 변경 시 주의사항

### ⚠️ 중요: 벡터 데이터 비호환성

- **서로 다른 임베딩 모델로 생성된 벡터는 비교할 수 없습니다**
- 임베딩 모델을 변경하면 기존 벡터 데이터베이스의 모든 데이터를 새로운 모델로 다시 임베딩해야 합니다
- 기존 벡터와 새 벡터를 혼합하여 사용하면 검색 결과가 부정확해집니다

### 데이터 일관성 보장

- 모든 벡터 데이터가 동일한 임베딩 모델로 생성되어야 합니다
- 부분적 업데이트는 권장하지 않습니다 (전체 재임베딩 필요)

## 임베딩 모델 변경 절차

### 1단계: 코드 수정

#### vector_store.py 수정
```python
# OpenAI 임베딩 모델 설정
self.embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv('OPENAI_API_KEY'),
    model="text-embedding-3-small"  # 새로운 모델로 변경
)
```

#### vector_store_simple.py 수정
```python
# OpenAI embeddings
self.embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model="text-embedding-3-small",  # 새로운 모델로 변경
)
```

### 2단계: 기존 벡터 데이터 삭제

임베딩 모델이 변경되면 기존 벡터 데이터는 더 이상 유효하지 않으므로 삭제해야 합니다.

#### ChromaDB 사용 시
```python
# _clear_collection() 메소드가 자동으로 호출됨
# 또는 수동으로 벡터 데이터베이스 디렉토리 삭제
rm -rf ./data/vectordb
```

#### FAISS 사용 시
```python
# FAISS 인덱스 파일 삭제
rm -rf ./data/vectordb_simple
```

### 3단계: 새로운 모델로 재임베딩

```python
from app.services.vector_store import vector_store_service

# 정책 문서들을 새로운 임베딩 모델로 재임베딩
success = vector_store_service.load_and_embed_policies()
if success:
    print('정책 임베딩 완료!')
    info = vector_store_service.get_collection_info()
    print(f'컬렉션 정보: {info}')
```

### 4단계: 검증

재임베딩 완료 후 다음 사항들을 확인합니다:

1. **벡터 개수 확인**: 기존과 동일한 수의 문서 청크가 임베딩되었는지 확인
2. **검색 기능 테스트**: 샘플 쿼리로 검색이 정상 작동하는지 확인
3. **성능 비교**: 새로운 모델의 검색 품질과 응답 속도 확인

```python
# 검색 테스트 예제
results = vector_store_service.get_relevant_policies(
    "카카오톡 알림톡 변수 사용법", k=3
)
print(f"검색 결과 수: {results['total_results']}")
for policy in results['policies']:
    print(f"- {policy['source']}: {policy['relevance_score']}")
```

## 자동화 스크립트

### 전체 재임베딩 스크립트

```python
# scripts/re_embed_with_new_model.py
"""
새로운 임베딩 모델로 전체 재임베딩 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.vector_store import vector_store_service

def main():
    print("=== 임베딩 모델 변경 후 재임베딩 프로세스 시작 ===")

    # 1. 현재 벡터 스토어 정보 확인
    print("\n1. 현재 벡터 스토어 상태 확인...")
    info = vector_store_service.get_collection_info()
    print(f"컬렉션: {info.get('name', 'N/A')}")
    print(f"문서 수: {info.get('count', 0)}")

    # 2. 재임베딩 실행
    print("\n2. 정책 문서 재임베딩 시작...")
    success = vector_store_service.load_and_embed_policies()

    if success:
        # 3. 재임베딩 결과 확인
        print("\n3. 재임베딩 결과 확인...")
        new_info = vector_store_service.get_collection_info()
        print(f"새 컬렉션: {new_info.get('name', 'N/A')}")
        print(f"새 문서 수: {new_info.get('count', 0)}")

        # 4. 검색 테스트
        print("\n4. 검색 기능 테스트...")
        test_query = "카카오톡 알림톡 변수 사용 방법"
        results = vector_store_service.get_relevant_policies(test_query, k=2)

        print(f"테스트 쿼리: '{test_query}'")
        print(f"검색 결과: {results['total_results']}건")

        for i, policy in enumerate(results['policies'], 1):
            print(f"  {i}. {policy['source']} (점수: {policy['relevance_score']:.4f})")

        print("\n=== 재임베딩 프로세스 완료 ===")
    else:
        print("\n❌ 재임베딩 실패!")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
```

### 사용법
```bash
# 가상환경 활성화
.venv\Scripts\activate

# 재임베딩 스크립트 실행
python scripts/re_embed_with_new_model.py
```

## 임베딩 모델별 특징

### text-embedding-ada-002 (Legacy)
- **출시**: 2022년
- **차원**: 1536
- **특징**: 안정적이지만 구형 모델
- **비용**: 상대적으로 비쌈

### text-embedding-3-small (권장)
- **출시**: 2024년
- **차원**: 1536 (기본)
- **특징**: 더 나은 성능, 저렴한 비용
- **비용**: ada-002 대비 약 5배 저렴
- **성능**: 대부분의 벤치마크에서 ada-002보다 우수

### text-embedding-3-large
- **출시**: 2024년
- **차원**: 3072 (기본)
- **특징**: 최고 성능, 큰 차원
- **비용**: 3-small보다 비싸지만 ada-002보다는 저렴
- **용도**: 최고 품질이 필요한 경우

## 모니터링 및 알림

### 임베딩 모델 변경 체크리스트

- [ ] 코드에서 임베딩 모델 변경
- [ ] 기존 벡터 데이터베이스 백업 (필요 시)
- [ ] 기존 벡터 데이터 삭제
- [ ] 새로운 모델로 전체 재임베딩
- [ ] 임베딩 결과 검증 (문서 수, 검색 품질)
- [ ] 성능 테스트 (검색 속도, 정확도)
- [ ] 문서 업데이트 (개발 문서, 설정 파일)
- [ ] 변경사항 커밋 및 배포

### 주의사항

1. **프로덕션 환경에서는 다운타임 고려**: 재임베딩 중에는 검색 기능이 제한될 수 있음
2. **백업 보관**: 문제 발생 시 롤백을 위한 기존 벡터 데이터 백업
3. **점진적 배포**: 개발 → 스테이징 → 프로덕션 순으로 단계적 적용
4. **성능 모니터링**: 변경 후 검색 품질과 응답 시간 모니터링

## 관련 파일

- `app/services/vector_store.py`: ChromaDB 기반 벡터 스토어
- `app/services/vector_store_simple.py`: FAISS 기반 벡터 스토어
- `docs/Development_Process.md`: 전체 개발 프로세스 문서
- `data/policies/`: 임베딩할 정책 문서들

## 문의 및 지원

임베딩 모델 변경 과정에서 문제가 발생하면 다음 로그들을 확인하세요:

- 벡터 스토어 초기화 오류
- 임베딩 프로세스 오류
- OpenAI API 관련 오류
- 검색 기능 오류

각 단계별 상세한 로그가 출력되므로 오류 메시지를 참고하여 문제를 해결할 수 있습니다.