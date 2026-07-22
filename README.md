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

## 실행 방법 (Docker만 사용)

로컬에 Python, Node.js, npm 또는 PostgreSQL을 설치할 필요가 없습니다. Docker Desktop만 설치하고 실행한 뒤, 프로젝트 최상위 폴더에서 아래 명령을 실행하세요.

### 사전 요구사항

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 실행 상태
- Windows PowerShell

### 최초 실행

```powershell
# 배포용 환경변수 파일 생성
Copy-Item .env.example .env

# .env 파일을 열어 POSTGRES_PASSWORD, SECRET_KEY,
# JWT_SECRET_KEY, ADMIN_PASSWORD 값을 반드시 변경

# DB, 백엔드, 프론트엔드 이미지 빌드 및 실행
docker compose up --build -d
```

실행이 완료되면 브라우저에서 `http://localhost:8080`으로 접속합니다.

### 구성

| 서비스 | 역할 | 외부 접속 |
|------|------|----------|
| frontend | Vue SPA를 제공하는 Nginx, API/WebSocket 프록시 | `http://localhost:8080` |
| backend | Flask API 및 Socket.IO 서버 | 내부 네트워크에서만 접근 |
| db | PostgreSQL 데이터베이스 | 내부 네트워크에서만 접근 |

### 관리 명령

```powershell
# 컨테이너 실행 상태 확인
docker compose ps

# 모든 서비스 로그 확인
docker compose logs -f

# 특정 서비스 로그 확인
docker compose logs -f backend

# 서비스 중지 및 컨테이너 제거 (데이터는 유지)
docker compose down

# 다음 실행 시 재시작
docker compose up -d
```

### 데이터 유지 및 초기화

PostgreSQL 데이터는 `postgres_data` 볼륨에, 업로드 이미지는 `uploads_data` 볼륨에 보존됩니다. 따라서 `docker compose down` 후 다시 실행해도 데이터는 유지됩니다.

과제 데이터를 포함해 완전히 초기화해야 할 때만 아래 명령을 사용하세요.

```powershell
docker compose down -v
```

### 기본 관리자 계정

관리자 계정은 `.env`의 `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL` 값으로 처음 DB가 생성될 때 만들어집니다. `.env.example`의 예시 비밀번호는 반드시 변경해야 합니다.

## 기술 스택

- **Backend**: Python 3, Flask, SQLAlchemy, Flask-JWT-Extended, Flask-SocketIO
- **Frontend**: Vue 3, Vue Router, Pinia, Axios, Socket.IO Client, Vite
- **Database**: PostgreSQL 16
- **Deployment**: Docker Compose, Nginx
