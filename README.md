# model-api — scaffold cho capstone CI/CD

Service nhỏ (scikit-learn + FastAPI) để học **CI/CD cho software và model**. Model ở đây
**không được train trong pipeline**: `model/seed_artifact.py` đóng vai "artifact đến từ nơi khác"
(vendor, notebook, registry). Tuần 4 sẽ thay nó bằng DVC/MLflow và giữ nguyên mọi thứ phía sau.

## Quick start

```bash
make setup       # tạo .venv + cài dependencies
make seed        # sinh model artifact + golden dataset (chỉ lần đầu / khi reset)
make test        # pytest + coverage gate 80%
make lint        # ruff
make eval        # model quality gate (exit != 0 nếu metric tụt)
make run         # http://127.0.0.1:8000/docs
```

Lần đầu tiên, baseline chưa tồn tại thì `make eval` sẽ tạo `model/baseline.json`.
Từ đó trở đi, baseline là **hợp đồng chất lượng** và phải được review trong PR khi thay đổi.

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/predict \
  -H 'content-type: application/json' \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'
```

## Cấu trúc

```
app/                 FastAPI service: /health /predict /metrics
model/
  seed_artifact.py   stand-in cho artifact bên ngoài (không thuộc CI)
  evaluate.py        quality gate, exit code là hợp đồng với CI
  gate.json          ngưỡng: accuracy, độ tụt cho phép, macro F1, p95 latency
  baseline.json      snapshot đã commit, được review khi thay đổi
  artifacts/         model.pkl (gitignored, sinh bằng `make seed`)
  data/golden.csv    golden dataset nhỏ, ổn định
tests/               schema, model contract, API
Dockerfile           multi-stage, non-root, healthcheck
compose.yaml         profiles: `app` và `ml` (không bật cùng lúc)
.github/workflows/   ci.yml: quality -> evaluate -> build
```

## Pipeline hiện có

```
lint -> unit test + coverage 80% -> model evaluation gate -> docker build (+ push GHCR trên main)
```

- `evaluate` là **job riêng** vì gate chất lượng model phải nhìn thấy rõ trong PR, không bị chôn trong log test.
- Test và build chạy trên runner GitHub, không chạy trên laptop.

## Cách làm gate "đỏ" để kiểm chứng (bài tập tuần 4)

```bash
# 1. làm model tệ đi: huấn luyện lại chỉ với 1 lớp, hoặc sửa seed để dùng dummy classifier
# 2. chạy: make seed && make eval  -> phải exit code 1
# 3. sửa lại, chạy: make seed && make eval -> exit code 0
```

Nếu pipeline vẫn xanh khi model tệ hơn, gate của bạn đang trang trí.

## Máy yếu (9GB RAM)

- `make up` chỉ bật 1 container API; MLflow nằm sau profile `ml`.
- Build/scan nặng: để CI làm. Local chỉ chạy unit test và 1 service.
- K8s: dùng killercoda hoặc `k3d ... --agents 0`, đừng dùng kind nhiều node.

## Việc tiếp theo (theo tuần)

- **Tuần 2:** scan image (Trivy), SBOM (syft), ký (cosign), OIDC, deploy staging + smoke test + rollback.
- **Tuần 3:** port pipeline sang GitLab CI và Jenkins, viết bảng mapping khái niệm.
- **Tuần 4:** thay `seed_artifact` bằng pull từ MLflow registry/DVC; thêm shadow + canary + drift.
- **Tuần 5:** Helm + GitOps + dashboard + runbook, rồi demo.
