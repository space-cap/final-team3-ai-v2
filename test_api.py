#!/usr/bin/env python3
"""
카카오 알림톡 템플릿 AI 생성 시스템 테스트 스크립트
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"

class APITester:
    def __init__(self):
        self.session_id = None
        self.user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.template_id = None
        
    def print_section(self, title: str):
        """섹션 제목 출력"""
        print(f"\n{'='*50}")
        print(f"🧪 {title}")
        print('='*50)
    
    def print_success(self, message: str):
        """성공 메시지 출력"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """에러 메시지 출력"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """정보 메시지 출력"""
        print(f"ℹ️  {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """API 요청 수행"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=180)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=180)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise Exception("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        except requests.exceptions.Timeout:
            raise Exception("요청 시간이 초과되었습니다.")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP 오류: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"요청 실패: {str(e)}")
    
    def test_health_check(self):
        """1. 헬스체크 테스트"""
        self.print_section("시스템 헬스체크")
        
        try:
            response = self.make_request("GET", "/health")
            self.print_success("헬스체크 성공")
            
            status = response.get("status", {})
            print(f"   📊 데이터베이스 연결: {'✅' if status.get('database_connected') else '❌'}")
            print(f"   📊 벡터DB 로드: {'✅' if status.get('vectordb_loaded') else '❌'}")
            print(f"   📊 벡터DB 문서 수: {status.get('vectordb_document_count', 0)}")
            print(f"   📊 AI 모델 사용 가능: {'✅' if status.get('ai_model_available') else '❌'}")
            print(f"   📊 서버 가동시간: {status.get('uptime', 0):.1f}초")
            print(f"   📊 버전: {response.get('version', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.print_error(f"헬스체크 실패: {str(e)}")
            return False
    
    def test_create_session(self):
        """2. 세션 생성 테스트"""
        self.print_section("세션 생성")
        
        data = {
            "user_id": self.user_id,
            "session_name": "Python 테스트 세션",
            "session_description": "API 기능 테스트를 위한 세션",
            "client_info": {
                "platform": "Python Test Script",
                "version": "1.0.0"
            }
        }
        
        try:
            response = self.make_request("POST", "/sessions", data)
            self.session_id = response["session_id"]
            
            self.print_success("세션 생성 성공")
            print(f"   🆔 세션 ID: {self.session_id}")
            print(f"   👤 사용자 ID: {response['user_id']}")
            print(f"   📝 세션명: {response['session_name']}")
            print(f"   🟢 활성 상태: {response['is_active']}")
            
            return True
            
        except Exception as e:
            self.print_error(f"세션 생성 실패: {str(e)}")
            return False
    
    def test_generate_template(self):
        """3. 템플릿 생성 테스트"""
        self.print_section("템플릿 생성")
        
        if not self.session_id:
            self.print_error("세션이 생성되지 않았습니다.")
            return False
        
        data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query_text": "온라인 쇼핑몰 주문 확인 알림톡 템플릿을 만들어주세요",
            "business_type": "전자상거래",
            "template_type": "주문확인",
            "additional_context": {
                "target_audience": "일반 고객",
                "tone": "친근함"
            }
        }
        
        try:
            self.print_info("템플릿 생성 중... (1-2분 소요될 수 있습니다)")
            start_time = time.time()
            
            response = self.make_request("POST", "/templates/generate", data)
            
            elapsed_time = time.time() - start_time
            self.template_id = response["template_id"]
            
            self.print_success(f"템플릿 생성 성공 (실제 소요시간: {elapsed_time:.1f}초)")
            print(f"   🆔 템플릿 ID: {self.template_id}")
            print(f"   ⏱️  AI 처리시간: {response['processing_time']:.2f}초")
            
            analysis = response.get("template_analysis", {})
            print(f"   📊 품질 점수: {analysis.get('quality_score', 0):.2f}")
            print(f"   📊 준수 점수: {analysis.get('compliance_score', 0):.2f}")
            print(f"   📊 글자 수: {analysis.get('character_count', 0)}")
            print(f"   📊 변수 개수: {analysis.get('variable_count', 0)}")
            
            print(f"\n📄 생성된 템플릿:")
            print("-" * 50)
            print(response["template_content"])
            print("-" * 50)
            
            if analysis.get("suggestions"):
                print(f"\n💡 개선 제안:")
                for suggestion in analysis["suggestions"]:
                    print(f"   • {suggestion}")
            
            return True
            
        except Exception as e:
            self.print_error(f"템플릿 생성 실패: {str(e)}")
            return False
    
    def test_policy_query(self):
        """4. 정책 질의 테스트"""
        self.print_section("정책 질의")
        
        if not self.session_id:
            self.print_error("세션이 생성되지 않았습니다.")
            return False
        
        data = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query_text": "알림톡에서 할인 이벤트 관련 내용을 포함할 수 있나요?",
            "context": {
                "business_type": "전자상거래",
                "specific_concern": "광고성 내용"
            }
        }
        
        try:
            response = self.make_request("POST", "/query", data)
            
            self.print_success("정책 질의 성공")
            print(f"   🆔 질의 ID: {response['query_id']}")
            print(f"   📊 신뢰도: {response['confidence_score']:.2f}")
            print(f"   ⏱️  처리시간: {response['processing_time']:.2f}초")
            
            print(f"\n💬 AI 답변:")
            print("-" * 50)
            print(response["answer"])
            print("-" * 50)
            
            if response.get("source_documents"):
                print(f"\n📚 참조 문서 ({len(response['source_documents'])}개):")
                for i, doc in enumerate(response["source_documents"][:3], 1):
                    print(f"   {i}. {doc.get('source', 'Unknown')}")
            
            return True
            
        except Exception as e:
            self.print_error(f"정책 질의 실패: {str(e)}")
            return False
    
    def test_policy_search(self):
        """5. 정책 문서 검색 테스트"""
        self.print_section("정책 문서 검색")
        
        data = {
            "query": "변수 사용 규칙",
            "limit": 3
        }
        
        try:
            response = self.make_request("POST", "/policies/search", data)
            
            self.print_success("정책 검색 성공")
            print(f"   📊 검색 결과: {response['total_results']}건")
            
            documents = response.get("documents", [])
            if documents:
                print(f"\n📚 검색 결과:")
                for i, doc in enumerate(documents, 1):
                    print(f"   {i}. 📄 {doc.get('source', 'Unknown')}")
                    print(f"      🎯 관련도: {doc.get('relevance_score', 0):.2f}")
                    content = doc.get('content', '')
                    if len(content) > 100:
                        content = content[:100] + "..."
                    print(f"      📝 내용: {content}")
                    print()
            
            return True
            
        except Exception as e:
            self.print_error(f"정책 검색 실패: {str(e)}")
            return False
    
    def test_list_templates(self):
        """6. 템플릿 목록 조회 테스트"""
        self.print_section("템플릿 목록 조회")
        
        params = {
            "user_id": self.user_id,
            "limit": 5,
            "offset": 0
        }
        
        try:
            response = self.make_request("GET", "/templates", params=params)
            
            self.print_success("템플릿 목록 조회 성공")
            print(f"   📊 총 템플릿 수: {response['total_count']}")
            print(f"   📊 조회된 템플릿 수: {len(response['templates'])}")
            print(f"   📊 더 많은 데이터: {'예' if response['has_more'] else '아니요'}")
            
            templates = response.get("templates", [])
            if templates:
                print(f"\n📋 템플릿 목록:")
                for i, template in enumerate(templates, 1):
                    print(f"   {i}. 🆔 ID: {template.get('template_id')}")
                    print(f"      📝 이름: {template.get('template_name', '무제')}")
                    print(f"      🏷️  유형: {template.get('template_type', 'Unknown')}")
                    print(f"      📊 품질: {template.get('quality_score', 0):.2f}")
                    print(f"      ⭐ 즐겨찾기: {'예' if template.get('is_favorite') else '아니요'}")
                    print()
            
            return True
            
        except Exception as e:
            self.print_error(f"템플릿 목록 조회 실패: {str(e)}")
            return False
    
    def test_template_feedback(self):
        """7. 템플릿 피드백 테스트"""
        self.print_section("템플릿 피드백")
        
        if not self.template_id:
            self.print_error("생성된 템플릿이 없습니다.")
            return False
        
        data = {
            "template_id": self.template_id,
            "user_id": self.user_id,
            "rating": 5,
            "feedback": "매우 만족스러운 템플릿입니다. 실제 사용에 적합합니다.",
            "is_favorite": True
        }
        
        try:
            response = self.make_request("POST", "/templates/feedback", data)
            
            self.print_success("피드백 제출 성공")
            print(f"   🆔 템플릿 ID: {response['template_id']}")
            print(f"   ✅ 업데이트 성공: {response['updated']}")
            
            return True
            
        except Exception as e:
            self.print_error(f"피드백 제출 실패: {str(e)}")
            return False
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 카카오 알림톡 템플릿 AI 생성 시스템 테스트 시작")
        print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        test_results = []
        
        # 테스트 실행
        tests = [
            ("헬스체크", self.test_health_check),
            ("세션 생성", self.test_create_session),
            ("템플릿 생성", self.test_generate_template),
            ("정책 질의", self.test_policy_query),
            ("정책 검색", self.test_policy_search),
            ("템플릿 목록", self.test_list_templates),
            ("템플릿 피드백", self.test_template_feedback),
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
            except Exception as e:
                self.print_error(f"{test_name} 테스트 중 예외 발생: {str(e)}")
                test_results.append((test_name, False))
        
        # 결과 요약
        self.print_section("테스트 결과 요약")
        
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 통과" if result else "❌ 실패"
            print(f"   {test_name}: {status}")
        
        print(f"\n📊 전체 결과: {passed}/{total} 통과 ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        else:
            print("⚠️  일부 테스트가 실패했습니다. 서버 상태를 확인해주세요.")
        
        print(f"\n📚 API 문서: http://localhost:8000/docs")
        print(f"📊 헬스체크: http://localhost:8000/api/v1/health")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()