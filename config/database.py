"""
MySQL 데이터베이스 설정 및 연결 관리
"""
import os
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import mysql.connector
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 설정
DATABASE_CONFIG = {
    'host': os.getenv('LOCAL_DB_HOST', 'localhost'),
    'user': os.getenv('LOCAL_DB_USER', 'steve'),
    'password': os.getenv('LOCAL_DB_PASSWORD', 'doolman'),
    'database': os.getenv('LOCAL_DB_NAME', 'alimtalk_ai_v2'),
    'charset': os.getenv('LOCAL_DB_CHARSET', 'utf8mb4'),
    'port': int(os.getenv('LOCAL_DB_PORT', 3306))
}

# SQLAlchemy 연결 URL 생성
DATABASE_URL = (
    f"mysql+mysqlconnector://"
    f"{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
    f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}"
    f"/{DATABASE_CONFIG['database']}"
    f"?charset={DATABASE_CONFIG['charset']}"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv('APP_DEBUG', 'False').lower() == 'true'
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스 생성
Base = declarative_base()

# 메타데이터
metadata = MetaData()

def get_db():
    """
    데이터베이스 세션을 반환하는 의존성 함수
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database_if_not_exists():
    """
    데이터베이스가 존재하지 않으면 생성
    """
    try:
        # 데이터베이스 연결 (데이터베이스 없이)
        connection = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            port=DATABASE_CONFIG['port']
        )
        
        cursor = connection.cursor()
        
        # 데이터베이스 생성 (존재하지 않을 경우)
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_CONFIG['database']} CHARACTER SET {DATABASE_CONFIG['charset']}")
        
        print(f"데이터베이스 '{DATABASE_CONFIG['database']}' 확인/생성 완료")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"데이터베이스 생성 중 오류 발생: {e}")
        raise

def create_tables():
    """
    모든 테이블 생성
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("모든 테이블이 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"테이블 생성 중 오류 발생: {e}")
        raise

def check_connection():
    """
    데이터베이스 연결 상태 확인
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return False