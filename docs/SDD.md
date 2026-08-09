# TÀI LIỆU THIẾT KẾ HỆ THỐNG
## Auto Coding Bot — Nền tảng tự động hóa vòng đời phát triển phần mềm
**Phiên bản:** 1.0
**Loại tài liệu:** Software Design Document (SDD)
**Ngôn ngữ triển khai:** Python
**Giao diện:** Web (FastAPI + WebSocket)
---
## 1. TỔNG QUAN
### 1.1. Mục tiêu
Xây dựng một hệ thống nhận yêu cầu từ người dùng qua giao diện web, sau đó **tự động** thực hiện toàn bộ quy trình phát triển phần mềm mà không cần can thiệp thủ công ở từng bước:
1. Phân tích yêu cầu → lập kế hoạch kỹ thuật (design/plan)
2. Sinh mã nguồn (code generation)
3. Tự động kiểm thử (test tự sinh + chạy test)
4. Tự động phát hiện lỗi và tự sửa (self-healing loop)
5. Commit, tạo Pull Request, đẩy lên GitHub
6. Kích hoạt CI/CD để build và triển khai (deploy)
7. Báo cáo kết quả và trạng thái hoàn thành cho người dùng qua UI real-time
### 1.2. Phạm vi (Scope)
**Trong phạm vi (In-scope):**
- Hỗ trợ sinh code cho các dự án Python (mở rộng sau sang Node.js, v.v.)
- Vòng lặp tự sửa lỗi có giới hạn số lần thử
- Giao diện web hiển thị tiến trình theo thời gian thực
- Tích hợp GitHub (branch, commit, PR)
- Sandbox cách ly khi chạy code sinh ra
**Ngoài phạm vi (Out-of-scope) ở giai đoạn 1:**
- Tự động merge vào nhánh `main`/production mà không qua review
- Hỗ trợ đa ngôn ngữ lập trình đồng thời
- Tự động rollback production khi deploy lỗi (giai đoạn sau)
### 1.3. Đối tượng sử dụng
Lập trình viên/nhóm phát triển muốn giao một yêu cầu tính năng (feature request) ở dạng mô tả tự nhiên và nhận về một Pull Request đã được code, test, và sẵn sàng review.
---
## 2. KIẾN TRÚC TỔNG THỂ
```
┌─────────────┐      HTTP/WebSocket      ┌───────────────────┐
│   Web UI    │ ───────────────────────► │   FastAPI Backend  │
│ (Browser)   │ ◄─────────────────────── │   (API Gateway)    │
└─────────────┘      Realtime events     └─────────┬──────────┘
                                                    │
                                          ┌─────────▼──────────┐
                                          │   Task Queue        │
                                          │  (Celery + Redis)   │
                                          └─────────┬──────────┘
                                                    │
                                          ┌─────────▼──────────┐
                                          │   Orchestrator      │
                                          │   (State Machine)   │
                                          └──┬────┬────┬────┬──┘
                                             │    │    │    │
                        ┌────────────────────┘    │    │    └───────────────────┐
                        ▼                          ▼    ▼                        ▼
              ┌──────────────────┐     ┌──────────────────┐          ┌──────────────────┐
              │  Planning Agent   │     │  Code Gen Agent   │          │  Git/GitHub       │
              │  (Claude API)     │     │  (Claude API)     │          │  Integration      │
              └──────────────────┘     └────────┬──────────┘          └──────────────────┘
                                                 │
                                       ┌─────────▼──────────┐
                                       │  Sandbox Executor    │
                                       │  (Docker container)  │
                                       │  - chạy test         │
                                       │  - lint/type check   │
                                       └───────────────────────┘
```
### 2.1. Các thành phần chính
| Thành phần | Vai trò | Công nghệ đề xuất |
|---|---|---|
| Web UI | Nhận yêu cầu, hiển thị tiến trình real-time | HTML/JS hoặc React + WebSocket |
| API Gateway | Điều phối request từ UI, xác thực | FastAPI |
| Task Queue | Xử lý bất đồng bộ, tránh chặn HTTP request | Celery + Redis |
| Orchestrator | Điều phối vòng đời task theo state machine | Python (custom) |
| Planning Agent | Phân tích yêu cầu → sinh kế hoạch kỹ thuật | Claude API |
| Code Gen Agent | Sinh code theo từng bước kế hoạch | Claude API |
| Sandbox Executor | Chạy code sinh ra trong môi trường cách ly | Docker SDK for Python |
| Git Integration | Quản lý branch, commit, PR | GitPython / PyGithub |
| Event Store | Lưu log tiến trình để phát lại qua WebSocket | Redis Pub/Sub hoặc DB |
| Persistence | Lưu trạng thái task, lịch sử | PostgreSQL |
---
## 3. LUỒNG XỬ LÝ CHI TIẾT (TASK LIFECYCLE)
### 3.1. Sơ đồ trạng thái (State Machine)
```
CREATED → PLANNING → CODING → TESTING → (FAILED → CODING [retry])
                                    │
                                    ▼ (pass)
                              COMMITTING → PR_CREATED → CI_RUNNING → DONE
                                                              │
                                                              ▼ (fail)
                                                         NEEDS_ATTENTION
```
### 3.2. Mô tả từng bước
**Bước 1 — CREATED**
- Người dùng gửi yêu cầu qua Web UI (mô tả tự nhiên, ví dụ: "Thêm API đăng nhập bằng JWT")
- Backend tạo `task_id`, lưu vào DB, đẩy vào queue
**Bước 2 — PLANNING**
- Planning Agent (gọi Claude API) đọc yêu cầu + context codebase hiện tại (cấu trúc thư mục, các file liên quan)
- Output: danh sách các bước kỹ thuật cụ thể (task breakdown), file nào cần tạo/sửa, test case dự kiến
- Kết quả plan được hiển thị lên UI để người dùng có thể xác nhận/điều chỉnh (tùy chọn, có thể bỏ qua ở chế độ full-auto)
**Bước 3 — CODING**
- Với mỗi bước trong plan, Code Gen Agent sinh code (diff hoặc full file)
- Code được ghi vào working directory (nhánh git riêng, không đụng vào `main`)
**Bước 4 — TESTING**
- Sandbox Executor chạy trong container Docker cách ly:
  - Cài dependencies (`pip install -r requirements.txt`)
  - Chạy lint (`ruff`/`flake8`), type check (`mypy`)
  - Chạy test (`pytest`), thu thập kết quả dạng JSON
- Nếu **fail**: log lỗi được đưa ngược vào Code Gen Agent làm context để sửa → quay lại bước CODING (giới hạn `MAX_RETRIES`, ví dụ 5 lần)
- Nếu **pass**: chuyển sang bước tiếp theo
**Bước 5 — COMMITTING**
- Tự động commit theo từng logical change, message rõ ràng (có thể để Claude sinh commit message)
- Push lên nhánh feature riêng (`bot/feature-xxx`), **không bao giờ push thẳng vào `main`**
**Bước 6 — PR_CREATED**
- Tạo Pull Request tự động qua GitHub API, kèm mô tả: yêu cầu gốc, các thay đổi, kết quả test
- Gắn nhãn (label) `auto-generated` để dễ nhận diện khi review
**Bước 7 — CI_RUNNING**
- GitHub Actions được trigger tự động khi có PR → build lại, chạy test lần cuối trong môi trường CI chuẩn
- Đây là lớp kiểm tra độc lập thứ hai (không tin tưởng tuyệt đối vào sandbox nội bộ)
**Bước 8 — DONE / NEEDS_ATTENTION**
- Nếu CI pass: đánh dấu task hoàn thành, thông báo người dùng, PR sẵn sàng để review/merge thủ công
- Nếu CI fail sau khi đã hết số lần retry: chuyển trạng thái `NEEDS_ATTENTION`, thông báo chi tiết lỗi để người dùng can thiệp
---
## 4. THIẾT KẾ API (BACKEND)
### 4.1. REST Endpoints
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/tasks` | Tạo task mới từ yêu cầu người dùng |
| GET | `/api/tasks/{task_id}` | Lấy trạng thái/chi tiết task |
| GET | `/api/tasks` | Danh sách task (lịch sử) |
| POST | `/api/tasks/{task_id}/approve-plan` | Xác nhận kế hoạch trước khi coding (chế độ semi-auto) |
| POST | `/api/tasks/{task_id}/cancel` | Hủy task đang chạy |
| GET | `/api/tasks/{task_id}/logs` | Lấy log chi tiết (dạng phân trang) |
### 4.2. WebSocket
| Endpoint | Mô tả |
|---|---|
| `WS /ws/tasks/{task_id}` | Stream sự kiện real-time: `plan_ready`, `code_generated`, `test_result`, `retry`, `pr_created`, `done`, `error` |
### 4.3. Định dạng sự kiện (event) mẫu
```json
{
  "event": "test_result",
  "task_id": "abc123",
  "step": "generate_login_api",
  "attempt": 2,
  "passed": false,
  "errors": ["test_login_invalid_password FAILED: AssertionError..."],
  "timestamp": "2026-08-09T10:32:00Z"
}
```
---
## 5. THIẾT KẾ DỮ LIỆU (DATA MODEL)
### 5.1. Bảng `tasks`
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID | Khóa chính |
| user_prompt | TEXT | Yêu cầu gốc |
| status | ENUM | CREATED, PLANNING, CODING, TESTING, ... |
| repo_url | TEXT | Repo GitHub đích |
| branch_name | TEXT | Nhánh làm việc |
| pr_url | TEXT | Link PR sau khi tạo |
| created_at / updated_at | TIMESTAMP | |
### 5.2. Bảng `task_steps`
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID | |
| task_id | UUID | FK → tasks |
| description | TEXT | Mô tả bước |
| attempt_count | INT | Số lần thử lại |
| status | ENUM | PENDING, RUNNING, PASSED, FAILED |
### 5.3. Bảng `task_events` (log chi tiết, dùng để replay qua WebSocket)
| Cột | Kiểu |
|---|---|
| id | UUID |
| task_id | UUID |
| event_type | TEXT |
| payload | JSONB |
| created_at | TIMESTAMP |
---
## 6. AN TOÀN & CÁCH LY (SECURITY & SANDBOXING)
Đây là phần **bắt buộc** vì hệ thống chạy code do AI sinh ra:
1. **Không bao giờ chạy code sinh ra trên host chính** — luôn chạy trong container Docker riêng, không có quyền truy cập mạng ra ngoài trừ khi cần thiết (cài dependency), không mount volume nhạy cảm.
2. **Giới hạn tài nguyên container**: CPU, RAM, timeout thực thi (ví dụ tối đa 60–120 giây/lần chạy test).
3. **Không push trực tiếp vào `main`/production** — luôn qua nhánh riêng + Pull Request, để có bước review của con người.
4. **Giới hạn số lần retry** để tránh vòng lặp vô hạn tiêu tốn token API và tài nguyên.
5. **Secrets management**: API key (Claude, GitHub token) lưu qua biến môi trường/secret manager, không bao giờ để lộ trong log hay đưa vào prompt.
6. **Audit log**: Lưu lại toàn bộ code đã sinh, lệnh đã chạy, để có thể truy vết khi cần.
---
## 7. CHIẾN LƯỢC KIỂM THỬ (TESTING STRATEGY)
| Cấp độ | Mô tả |
|---|---|
| Unit test | Code Gen Agent được yêu cầu sinh kèm unit test cho mỗi function/module mới |
| Integration test | Chạy trong sandbox sau khi toàn bộ các bước của 1 task hoàn tất |
| Lint/Type check | `ruff` + `mypy` chạy trước khi cho phép chuyển sang bước test |
| CI test (lớp 2) | GitHub Actions chạy lại toàn bộ test suite trong môi trường sạch, độc lập với sandbox nội bộ |
---
## 8. CÔNG NGHỆ ĐỀ XUẤT (TECH STACK)
| Hạng mục | Lựa chọn |
|---|---|
| Ngôn ngữ backend | Python 3.12+ |
| Web framework | FastAPI |
| Async task queue | Celery + Redis |
| Database | PostgreSQL |
| AI model | Claude API (Anthropic) |
| Sandbox | Docker (Python SDK: `docker-py`) |
| Git | GitPython hoặc `git` CLI qua `subprocess` |
| GitHub API | PyGithub |
| CI/CD | GitHub Actions |
| Frontend | HTML/JS thuần hoặc React (tùy độ phức tạp UI) |
---
## 9. CẤU TRÚC THƯ MỤC DỰ ÁN (ĐỀ XUẤT)
```
auto-coding-bot/
├── backend/
│   ├── main.py                # FastAPI entrypoint
│   ├── api/
│   │   ├── tasks.py           # REST endpoints
│   │   └── websocket.py       # WS handler
│   ├── orchestrator/
│   │   ├── state_machine.py
│   │   └── task_runner.py
│   ├── agents/
│   │   ├── planning_agent.py
│   │   └── codegen_agent.py
│   ├── sandbox/
│   │   ├── docker_executor.py
│   │   └── test_runner.py
│   ├── integrations/
│   │   └── github_client.py
│   ├── models/                # SQLAlchemy models
│   └── workers/
│       └── celery_app.py
├── frontend/
│   └── (React hoặc HTML/JS thuần)
├── docker/
│   ├── sandbox.Dockerfile      # Image dùng để chạy code sinh ra
│   └── docker-compose.yml
├── tests/
├── .github/workflows/
│   └── ci.yml
├── requirements.txt
└── README.md
```
---
## 10. LỘ TRÌNH TRIỂN KHAI (ROADMAP ĐỀ XUẤT)
| Giai đoạn | Nội dung |
|---|---|
| **Phase 1 — MVP** | Orchestrator cơ bản (không retry loop), 1 agent code, chạy test đơn giản, chưa có UI (dùng CLI/API trực tiếp) |
| **Phase 2** | Thêm Web UI + WebSocket real-time, thêm sandbox Docker, thêm vòng lặp tự sửa lỗi |
| **Phase 3** | Tích hợp GitHub đầy đủ (branch, PR tự động), CI/CD |
| **Phase 4** | Đa dự án/đa ngôn ngữ, cơ chế phê duyệt kế hoạch (approve-plan), dashboard lịch sử task |
---
## 11. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)
- **Khả năng mở rộng**: Task queue cho phép chạy nhiều task song song (giới hạn theo worker)
- **Khả năng quan sát (observability)**: Log chi tiết mọi bước, có thể replay qua UI
- **Chịu lỗi**: Nếu worker crash giữa chừng, task phải resume được từ trạng thái đã lưu trong DB
- **Giới hạn chi phí**: Theo dõi số lượng token API đã dùng theo từng task, cảnh báo/dừng nếu vượt ngưỡng
---
## 12. GHI CHÚ CHO CLAUDE CODE KHI TRIỂN KHAI
Khi đưa tài liệu này cho Claude Code để bắt đầu code, nên yêu cầu theo thứ tự:
1. Dựng khung project theo cấu trúc thư mục ở mục 9
2. Triển khai Orchestrator + state machine (mục 3) trước, dùng mock cho Code Gen Agent để test luồng
3. Tích hợp Claude API thật cho Planning Agent và Code Gen Agent
4. Triển khai Sandbox Executor (Docker) — ưu tiên an toàn trước khi cho chạy code thật
5. Triển khai Git/GitHub integration
6. Xây Web UI cuối cùng, sau khi backend đã chạy ổn qua API/CLI
---
*Hết tài liệu.*
