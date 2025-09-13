# PowerShell API 테스트 스크립트
# 카카오 알림톡 템플릿 AI 생성 시스템 테스트

Write-Host "=== 카카오 알림톡 템플릿 AI 시스템 테스트 ===" -ForegroundColor Green

$baseUrl = "http://localhost:8000/api/v1"

# 1. 헬스체크
Write-Host "`n1. 시스템 헬스체크..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
    Write-Host "✓ 헬스체크 성공" -ForegroundColor Green
    Write-Host "  - 데이터베이스 연결: $($healthResponse.status.database_connected)"
    Write-Host "  - 벡터DB 로드: $($healthResponse.status.vectordb_loaded)"
    Write-Host "  - AI 모델 사용 가능: $($healthResponse.status.ai_model_available)"
} catch {
    Write-Host "✗ 헬스체크 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. 세션 생성
Write-Host "`n2. 세션 생성 테스트..." -ForegroundColor Yellow
$sessionData = @{
    user_id = "test_user_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    session_name = "PowerShell 테스트 세션"
    session_description = "API 기능 테스트를 위한 세션"
} | ConvertTo-Json

try {
    $sessionResponse = Invoke-RestMethod -Uri "$baseUrl/sessions" -Method POST -Body $sessionData -ContentType "application/json"
    $sessionId = $sessionResponse.session_id
    $userId = $sessionResponse.user_id
    Write-Host "✓ 세션 생성 성공" -ForegroundColor Green
    Write-Host "  - 세션 ID: $sessionId"
    Write-Host "  - 사용자 ID: $userId"
} catch {
    Write-Host "✗ 세션 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. 템플릿 생성 테스트
Write-Host "`n3. 템플릿 생성 테스트..." -ForegroundColor Yellow
$templateData = @{
    session_id = $sessionId
    user_id = $userId
    query_text = "온라인 쇼핑몰 주문 확인 알림톡 템플릿을 만들어주세요"
    business_type = "전자상거래"
    template_type = "주문확인"
    additional_context = @{
        target_audience = "일반 고객"
        tone = "친근함"
    }
} | ConvertTo-Json -Depth 3

try {
    Write-Host "  템플릿 생성 중... (1-2분 소요될 수 있습니다)" -ForegroundColor Cyan
    $templateResponse = Invoke-RestMethod -Uri "$baseUrl/templates/generate" -Method POST -Body $templateData -ContentType "application/json" -TimeoutSec 180
    Write-Host "✓ 템플릿 생성 성공" -ForegroundColor Green
    Write-Host "  - 템플릿 ID: $($templateResponse.template_id)"
    Write-Host "  - 처리 시간: $($templateResponse.processing_time)초"
    Write-Host "  - 품질 점수: $($templateResponse.template_analysis.quality_score)"
    Write-Host "  - 준수 점수: $($templateResponse.template_analysis.compliance_score)"
    Write-Host "`n생성된 템플릿:" -ForegroundColor Cyan
    Write-Host "$($templateResponse.template_content)" -ForegroundColor White
} catch {
    Write-Host "✗ 템플릿 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 정책 질의 테스트
Write-Host "`n4. 정책 질의 테스트..." -ForegroundColor Yellow
$queryData = @{
    session_id = $sessionId
    user_id = $userId
    query_text = "알림톡에서 할인 이벤트 관련 내용을 포함할 수 있나요?"
    context = @{
        business_type = "전자상거래"
        specific_concern = "광고성 내용"
    }
} | ConvertTo-Json -Depth 3

try {
    $queryResponse = Invoke-RestMethod -Uri "$baseUrl/query" -Method POST -Body $queryData -ContentType "application/json" -TimeoutSec 120
    Write-Host "✓ 정책 질의 성공" -ForegroundColor Green
    Write-Host "  - 질의 ID: $($queryResponse.query_id)"
    Write-Host "  - 신뢰도: $($queryResponse.confidence_score)"
    Write-Host "`n답변:" -ForegroundColor Cyan
    Write-Host "$($queryResponse.answer)" -ForegroundColor White
} catch {
    Write-Host "✗ 정책 질의 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. 정책 문서 검색 테스트
Write-Host "`n5. 정책 문서 검색 테스트..." -ForegroundColor Yellow
$searchData = @{
    query = "변수 사용 규칙"
    limit = 3
} | ConvertTo-Json

try {
    $searchResponse = Invoke-RestMethod -Uri "$baseUrl/policies/search" -Method POST -Body $searchData -ContentType "application/json"
    Write-Host "✓ 정책 검색 성공" -ForegroundColor Green
    Write-Host "  - 검색 결과: $($searchResponse.total_results)건"
    if ($searchResponse.documents.Count -gt 0) {
        Write-Host "`n첫 번째 검색 결과:" -ForegroundColor Cyan
        Write-Host "  소스: $($searchResponse.documents[0].source)"
        Write-Host "  관련도: $($searchResponse.documents[0].relevance_score)"
    }
} catch {
    Write-Host "✗ 정책 검색 실패: $($_.Exception.Message)" -ForegroundColor Red
}

# 6. 템플릿 목록 조회 테스트
Write-Host "`n6. 템플릿 목록 조회 테스트..." -ForegroundColor Yellow
try {
    $templatesResponse = Invoke-RestMethod -Uri "$baseUrl/templates?user_id=$userId&limit=5" -Method GET
    Write-Host "✓ 템플릿 목록 조회 성공" -ForegroundColor Green
    Write-Host "  - 총 템플릿 수: $($templatesResponse.total_count)"
    Write-Host "  - 조회된 템플릿 수: $($templatesResponse.templates.Count)"
} catch {
    Write-Host "✗ 템플릿 목록 조회 실패: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 테스트 완료 ===" -ForegroundColor Green
Write-Host "API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다." -ForegroundColor Cyan