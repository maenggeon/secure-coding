# Tiny Second-hand Shopping Platform

화이트햇 스쿨 시큐어 코딩 과제 - 중고거래 플랫폼

Flask(Python) 백엔드 + Vue.js 프론트엔드로 구현된 보안 중심 중고거래 플랫폼입니다.

## 주요 기능

- **사용자 관리**: 회원가입, 로그인/로그아웃, 프로필 조회/수정, 비밀번호 변경
- **상품 관리**: 상품 등록/조회/검색/수정/삭제, 이미지 업로드
- **채팅**: 전체 채팅, 1:1 채팅 (WebSocket 실시간)
- **신고/차단**: 사용자/상품 신고, 자동 차단 정책
- **송금**: 사용자 간 송금, 송금 내역 조회
- **관리자**: 회원/상품/신고 관리, 감사 로그 조회

## 보안 기능

| 항목 | 구현 내용 |
|------|-----------|
| 비밀번호 암호화 | PBKDF2-SHA256 + Salt (260,000 iterations) |
| 비밀번호 정책 | 8~24자, 영문 대/소문자/숫자/특수문자 중 3종류 이상 |
| 로그인 시도 제한 | 5회 실패 시 10분 계정 잠금 |
| 인증 | JWT Bearer Token |
| CSRF 방지 | 상태 변경 API에 X-CSRF-Token 헤더 검증 |
| SQL Injection 방지 | SQLAlchemy ORM 파라미터 바인딩 |
| IDOR 방지 | 리소스 소유권 서버 측 검증 |
| 파일 업로드 검증 | 확장자/MIME 타입/크기(5MB) 제한 |
| 송금 무결성 | DB 트랜잭션 + 멱등성 키(idempotency_key) |
| 신고 오남용 방지 | 동일 대상 중복 신고 차단 |
| 감사 로그 | 로그인, 송금, 신고, IDOR 시도 등 기록 |

## 프로젝트 구조

```
secure-coding/
├── backend/          # Flask API 서버
│   ├── app/
│   │   ├── models/   # DB 모델
│   │   ├── routes/   # API 라우트
│   │   ├── services/ # 비즈니스 로직
│   │   └── utils/    # 보안 유틸리티
│   ├── requirements.txt
│   └── run.py
├── frontend/         # Vue.js SPA
│   ├── src/
│   │   ├── views/    # 페이지 컴포넌트
│   │   ├── stores/   # Pinia 상태 관리
│   │   └── api/      # Axios API 클라이언트
│   └── package.json
└── README.md
```

## 환경 설정

### 사전 요구사항

- Python 3.10+
- Node.js 18+
- npm

### 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화 (Windows)
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
copy .env.example .env
# .env 파일에서 SECRET_KEY, JWT_SECRET_KEY 등을 변경하세요
```

### 프론트엔드 설정

```bash
cd frontend
npm install
```

## 실행 방법

### 1. 백엔드 서버 실행

```bash
cd backend
venv\Scripts\activate   # Windows
python run.py
```

서버가 `http://localhost:5000` 에서 실행됩니다.

### 2. 프론트엔드 개발 서버 실행

```bash
cd frontend
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

## 기본 관리자 계정

`.env` 파일 설정값 기준 (변경 가능):

| 항목 | 기본값 |
|------|--------|
| 아이디 | admin |
| 비밀번호 | Admin@12345 |

## API Base URL

```
http://localhost:5000/api
```

## 프로덕션 빌드

```bash
# 프론트엔드 빌드
cd frontend
npm run build

# 빌드 결과물(dist/)을 Flask static 폴더에 배치하거나
# Nginx 등 리버스 프록시로 서빙
```

프로덕션 환경에서는 반드시 HTTPS(TLS)를 적용하세요.

## Docker 배포

Docker Compose로 PostgreSQL DB, Flask API, Vue/Nginx 프론트엔드를 함께 실행할 수 있습니다.
프론트엔드는 기본적으로 `http://localhost:8080`에서 제공되며, API와 WebSocket은 Nginx를 통해 내부 백엔드로 전달됩니다.

```bash
# 프로젝트 최상위에서 실행
copy .env.example .env
# .env의 비밀번호와 SECRET_KEY, JWT_SECRET_KEY를 반드시 변경
docker compose up --build -d
```

상태 확인과 종료는 아래 명령을 사용합니다.

```bash
docker compose ps
docker compose logs -f
docker compose down
```

`postgres_data`(DB)와 `uploads_data`(업로드 이미지)는 Docker 볼륨으로 보존됩니다. 데이터를 포함해 완전히 초기화하려면 `docker compose down -v`를 사용합니다.

## 기술 스택

- **Backend**: Python 3, Flask, SQLAlchemy, Flask-JWT-Extended, Flask-SocketIO
- **Frontend**: Vue 3, Vue Router, Pinia, Axios, Socket.IO Client, Vite
- **Database**: SQLite (개발용, PostgreSQL 등으로 교체 가능)
