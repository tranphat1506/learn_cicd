# Lộ trình học CI/CD 5 tuần (100 giờ)

> **Hồ sơ của bạn:** đã biết Docker / Compose / container · muốn automate **software + model** (model chỉ test – đánh giá – đóng gói – deploy, **không train**) · học **cả GitHub Actions, GitLab CI và Jenkins** · 20h/tuần trong 4–5 tuần.

---

## 0. Kết quả bạn phải đạt được sau 5 tuần

Không phải "đã xem hết docs", mà là **làm được**:

1. Viết pipeline CI/CD từ đầu cho 1 service, bằng **cả 3 nền tảng** (GitHub Actions, GitLab CI, Jenkins), hiểu vì sao mỗi khái niệm tồn tại.
2. Build image production-grade: multi-stage, cache, non-root, tag theo commit SHA, scan lỗ hổng, ký số (cosign), SBOM.
3. Deploy tự động có **healthcheck + smoke test + rollback**; secrets không nằm trong repo (OIDC / masked variables / Jenkins credentials).
4. Xây **model release pipeline**: validate artifact → evaluation gate trên golden dataset → so baseline → đóng gói → deploy shadow/canary → promote hoặc auto-rollback.
5. Đọc được log pipeline khi fail trong < 10 phút, biết debug runner, cache, permission, network.
6. Nói được trong phỏng vấn: sự khác nhau giữa CI và CD, artifact vs cache, blue-green vs canary, tại sao pin action theo SHA, DORA metrics là gì.

**Một câu chốt để định hướng:** CI/CD không phải "viết file YAML". Nó là **hệ thống ra quyết định tự động**: thay đổi này có được phép đi tiếp hay không, dựa trên bằng chứng (test, scan, metric, smoke test). YAML chỉ là chỗ bạn khai báo bằng chứng nào cần thu thập.

---

## 1. Bản đồ kiến thức (học theo lớp, không học vẹt lệnh)

| Lớp | Nội dung | Mức cần đạt |
|---|---|---|
| 1. Nền | Git workflow, branch protection, semver, artifact vs cache, idempotency | Hiểu + làm |
| 2. CI | lint, unit/integration/contract test, coverage gate, matrix, flaky test | Thành thạo |
| 3. Build | Docker multi-stage, layer cache, registry, tag strategy, buildx | Thành thạo |
| 4. Bảo mật chuỗi cung ứng | SAST, dependency scan, image scan (Trivy), SBOM, cosign, OIDC, pin by SHA | Hiểu + làm |
| 5. CD | environment, approval, blue-green/rolling/canary, healthcheck, rollback, migration | Thành thạo |
| 6. Đa nền tảng | mapping concept GitHub ↔ GitLab ↔ Jenkins; runner/agent; reusable pipeline | Thành thạo |
| 7. Model CI/CD | data/model versioning (DVC), registry (MLflow), eval gate, drift, shadow deploy | Hiểu + làm |
| 8. Vận hành | K8s tối thiểu, Helm, GitOps (ArgoCD), Prometheus/Grafana, DORA | Hiểu, làm demo nhỏ |

> Lớp 8 là "đủ dùng", đừng sa vào học K8s chuyên sâu — nó là một lộ trình riêng.

---

## 2. Nguyên tắc học (quan trọng hơn nội dung)

- **70% thời gian là gõ và làm fail pipeline**, 30% đọc docs. Xem video chỉ để lấy bản đồ.
- **Mỗi ngày phải có 1 artifact commit được**: workflow xanh, Dockerfile, report, README.
- **Cố tình làm pipeline fail** rồi sửa: sai cache key, thiếu secret, test flaky, image không chạy vì non-root. Đây là kỹ năng thật.
- **Không copy YAML mẫu rồi để đó.** Mỗi dòng phải trả lời được: "dòng này để làm gì, bỏ đi thì hỏng ở đâu".
- **Ghi log học tập** (`notes/`): mỗi lỗi gặp phải → triệu chứng → nguyên nhân → cách sửa. Đây là tài liệu ôn phỏng vấn tốt nhất.
- Dùng **repo public** để không tốn quota phút CI. Jenkins chạy local bằng Docker.

### Tự kiểm tra đầu vào (nếu thiếu thì bù 2–3h)
- Shell: pipe, exit code, `set -euo pipefail`, biến môi trường.
- Linux: process, port, permission, file system, `curl`, `ss`, `journalctl`.
- Networking: DNS, HTTP status, TLS, reverse proxy, firewall.
- Python/Node: quản lý dependency, lockfile, virtualenv/node_modules.
- YAML: indent, anchor, multi-document.

---

## 2.5. Chạy lab trên laptop 9GB RAM (Ryzen 5 3500U) — đọc trước khi bắt đầu

**Nguyên tắc vàng: máy bạn là nơi viết code, không phải nơi chạy CI.**
Runner miễn phí của GitHub (repo public: 4 vCPU / 16GB; private: 2 vCPU / 7GB) mạnh hơn laptop của bạn. Hãy để CI chạy trên cloud, máy local chỉ chạy 1 service khi cần debug.

### Ngân sách RAM thực tế (tổng 9GB, hệ điều hành đã ăn ~2.5–3GB)

| Thành phần | RAM |
|---|---|
| OS + desktop + browser (5–8 tab) | 3.5–4 GB |
| VS Code + terminal | 1–1.5 GB |
| Docker daemon | 0.3 GB |
| 1 container service (Postgres/MLflow) | 0.3–0.7 GB |
| Jenkins (chỉ khi học tuần 3) | 1 GB |
| k3d 1 node (tuần 5, tuỳ chọn) | 0.6–1 GB |

→ **Quy tắc: tối đa 2 "thứ nặng" cùng lúc.** Ví dụ: Jenkins + Postgres = OK; Jenkins + MLflow + Grafana + k3d = chắc chắn OOM.

### Việc phải làm ngay (15 phút)

1. **Bật swap 6–8GB** để không bị OOM-kill giữa pipeline:
   ```bash
   sudo fallocate -l 6G /swapfile && sudo chmod 600 /swapfile
   sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   sudo sysctl vm.swappiness=20
   ```
   (Ubuntu có thể dùng `zram-tools` thay thế; swap trên SSD chậm nhưng cứu được phiên học.)
2. **Giới hạn Docker**: luôn đặt `--memory` khi chạy container nặng, đừng build nhiều image song song.
3. **Tắt mọi thứ không dùng**: `docker compose down`, `docker system prune` cuối mỗi ngày, đóng tab Chrome.
4. **Không cài** PyTorch/TensorFlow, Elasticsearch, full GitLab self-host, Kind nhiều node, ArgoCD local nếu không cần.

### Điều chỉnh công cụ so với kế hoạch gốc

| Hạng mục | Bản gốc | Bản 9GB |
|---|---|---|
| Build/test/scan | local + CI | **chỉ CI hosted**; local chỉ chạy unit test nhanh |
| Jenkins | controller + agent | **1 container, 0 agent, 1 executor**, `-Xmx512m`, bật/tắt theo ngày |
| GitLab | self-host | **gitlab.com shared runner** (400 phút/tháng free) |
| `act` | chạy local | tuỳ chọn, chỉ workflow nhỏ; bỏ nếu thấy chậm |
| K8s | kind + ArgoCD | **k3d 1 node** hoặc **killercoda.com** (cluster trên browser, không tốn RAM) |
| MLflow | server + Postgres | **sqlite backend**, `--memory=700m` |
| Monitoring | Prometheus + Grafana local | **Grafana Cloud free** + Prometheus chỉ bật khi demo |
| Model | PyTorch/LLM | **scikit-learn + ONNX**, artifact < 50MB, dataset vài nghìn dòng |
| Load test | k6 local | chạy k6 **trong CI**, local dùng locust nhẹ hoặc bỏ |

### Lệnh mẫu tiết kiệm RAM

```bash
# Jenkins tối giản (chỉ bật khi học tuần 3, tắt sau khi xong)
docker run -d --name jenkins --memory=1g --memory-swap=2g \
  -e JAVA_OPTS="-Xmx512m -XX:MaxMetaspaceSize=256m -XX:+UseSerialGC" \
  -p 8080:8080 -v jenkins_home:/var/jenkins_home jenkins/jenkins:lts-jdk17

# MLflow với sqlite, không cần Postgres
docker run -d --name mlflow --memory=700m -p 5000:5000 \
  -v "$PWD/mlflow:/mlflow" \
  ghcr.io/mlflow/mlflow:latest \
  mlflow server --backend-store-uri sqlite:////mlflow/mlflow.db \
  --default-artifact-root /mlflow/artifacts --host 0.0.0.0

# k3d 1 node duy nhất (không agent), chỉ khi thực sự cần K8s
k3d cluster create lab --agents 0 --k3s-arg "--disable=traefik@server:0"
```

Với `docker compose`, dùng **profiles** để không bật hết service cùng lúc:
```yaml
services:
  api:      { profiles: ["app"] }
  postgres: { profiles: ["app", "test"] }
  mlflow:   { profiles: ["ml"] }
  grafana:  { profiles: ["monitor"] }
```
→ `docker compose --profile app up`, `--profile ml up`… mỗi lần chỉ 1–2 container.

### Cách deploy khi không có server riêng

Chọn 1 trong 3, đừng làm cả 3:
1. **Self-hosted runner trên chính laptop, chỉ cho job deploy** (job nhẹ: pull image + `compose up`), build vẫn ở GitHub. Chỉ dùng cho repo private.
2. **VPS free tier** (Oracle Cloud A1, Fly.io, Render) — sát thực tế nhất, nhưng mất thời gian đăng ký.
3. **Deploy "giả lập" bằng Compose local + script rollback**, chấp nhận không qua mạng. Đủ để học cơ chế.

> Nếu chỉ có 9GB, **ưu tiên tuyệt đối việc hiểu cơ chế** hơn là dựng đủ hạ tầng. Nhà tuyển dụng hỏi "vì sao canary 5% rồi 25%", không hỏi "bạn có chạy Grafana local không".

---

## 3. Lộ trình chi tiết theo ngày (5 tuần × 5 ngày × 4h)

### Tuần 1 — Nền tảng + CI đầu tiên (GitHub Actions)

| Ngày | Nội dung | Bài làm (deliverable) |
|---|---|---|
| 1 | Git nâng cao: trunk-based vs gitflow, conventional commits, semver, tag, PR, protected branch, CODEOWNERS | Repo `capstone/` khởi tạo, branch protection bật, commit convention + PR template |
| 2 | Giải phẫu pipeline: stage/job/step, runner, artifact, cache, matrix, env, secret, fail-fast, idempotency | Workflow `ci.yml`: checkout → setup → lint → unit test, chạy xanh trên PR |
| 3 | Testing trong CI: unit vs integration vs contract, pytest fixture, coverage gate, testcontainers/Compose trong CI, flaky test | Test suite + coverage ≥ 80% làm **fail** pipeline khi tụt; 1 integration test dùng Postgres qua service container |
| 4 | Docker production: multi-stage, layer caching, `.dockerignore`, non-root, healthcheck, tag theo SHA, buildx cache | `Dockerfile` production + push lên GHCR với tag `sha-<short>` và `latest` chỉ trên main |
| 5 | Ôn + mini project: lint → test → build → scan → push | Pipeline CI hoàn chỉnh, có sơ đồ trong `README` |

**Mốc kiểm tra tuần 1:** ai clone repo, mở PR, thấy pipeline tự chạy và chặn merge khi test fail.

---

### Tuần 2 — GitHub Actions nâng cao + CD + supply chain

| Ngày | Nội dung | Bài làm |
|---|---|---|
| 1 | Reusable workflow, composite action, `workflow_call`, matrix chiến lược, cache đúng key, self-hosted runner, `act` để chạy local | Tách CI thành reusable workflow; chạy thử bằng `act` |
| 2 | Secrets & quyền: `GITHUB_TOKEN` least privilege, environment protection + required reviewer, OIDC lên cloud (không lưu access key), pin action theo commit SHA | Deploy role qua OIDC; workflow không còn secret cloud dài hạn |
| 3 | Supply chain: SBOM (syft), Trivy (image + fs), cosign sign/verify, SLSA concept, Dependabot, dependency review | Pipeline: scan → fail nếu có CVE critical → ký image → verify trước deploy |
| 4 | CD thật: deploy VPS qua SSH/rsync, blue-green vs rolling, healthcheck, smoke test, auto-rollback, migration DB (expand/contract) | Deploy staging tự động; smoke test fail → tự rollback bản trước |
| 5 | Mini project: CI/CD end-to-end cho software | build → scan → sign → deploy staging → smoke → approve → prod |

**Mốc kiểm tra tuần 2:** bấm merge → 10 phút sau staging chạy bản mới; nếu smoke test fail, hệ thống tự về bản cũ và báo lỗi.

---

### Tuần 3 — GitLab CI + Jenkins (hiểu bản chất đa nền tảng)

| Ngày | Nội dung | Bài làm |
|---|---|---|
| 1 | GitLab CI: `.gitlab-ci.yml`, stage, `needs` (DAG), `rules`, cache vs artifacts, `include`, environment | Port CI tuần 1 sang GitLab, chạy xanh trên MR |
| 2 | GitLab nâng cao: runner/executor, tag runner, service + dind, masked/protected variable, child pipeline, coverage report, merge request pipeline | Build image trong GitLab, đẩy lên registry, coverage hiện trên MR |
| 3 | Jenkins: controller/agent, Jenkinsfile (declarative vs scripted), plugin, credentials, Docker agent | Jenkins local (Docker, `--memory=1g`, `-Xmx512m`) chạy lint + test + build cho cùng repo |
| 4 | Jenkins nâng cao: parallel stage, shared library, multibranch, webhook, backup config | Viết shared library `buildAndTest()` dùng lại cho 2 repo (chạy tối đa 1 build song song) |
| 5 | **Bài tổng hợp: 1 pipeline – 3 nền tảng** + bảng mapping khái niệm | 3 file cấu hình + bảng so sánh trong `notes/` |

**Bảng mapping bạn phải tự viết được:**

| Khái niệm | GitHub Actions | GitLab CI | Jenkins |
|---|---|---|---|
| Đơn vị chạy | job + step | job | stage + step |
| Nơi chạy | runner | runner (executor) | agent/node |
| Tái sử dụng | reusable workflow / composite action | `include` + `extends` | shared library |
| Điều kiện | `if`, `on` | `rules`, `only/except` | `when` |
| Lưu file giữa job | artifact | artifact | `stash`/`archiveArtifacts` |
| Cache | `actions/cache` | `cache` | plugin/cache dir |
| Secret | Secrets + OIDC | masked/protected variables | Credentials + `withCredentials` |
| Môi trường | Environment + protection | Environment + protected | Folder/credential scope |

**Mốc kiểm tra tuần 3:** giải thích được "cùng một pipeline, vì sao GitLab dùng DAG `needs`, Jenkins dùng agent, GitHub dùng matrix" — tức là hiểu mô hình chứ không thuộc cú pháp.

---

### Tuần 4 — Model CI/CD: test, đánh giá, đóng gói, phát hành (không train)

> Vì không train, "CI/CD cho model" thực chất là **model validation & release pipeline**. Test của model = evaluation trên bộ dữ liệu vàng + so baseline + kiểm tra hợp đồng dữ liệu.

| Ngày | Nội dung | Bài làm |
|---|---|---|
| 1 | Khác biệt software vs model: reproducibility, version cả **code + data + model**, model registry. DVC (version artifact/data), MLflow (tracking + registry) | Đưa model `.pkl`/`.onnx` vào DVC; đăng ký 2 version trong MLflow registry |
| 2 | Evaluation gate: golden dataset, metric threshold, so baseline, phát hiện regression, ý nghĩa thống kê (đừng gate bằng 0.001), report tự động (Evidently) | Script `evaluate.py` exit code ≠ 0 khi metric tụt; report HTML lưu làm artifact |
| 3 | Đóng gói & serving: FastAPI/BentoML/MLServer, contract schema (pydantic), inference test, latency benchmark, load test (k6/locust) | Service `/predict` + test schema + benchmark p95 latency, fail nếu vượt ngưỡng |
| 4 | Phát hành model: shadow → canary → promote, feature flag, rollback version, drift monitoring, data quality check (pandera/Great Expectations) | Deploy model mới ở chế độ shadow, so sánh output với bản prod trước khi promote |
| 5 | Ghép pipeline model hoàn chỉnh | validate artifact → eval gate → package → sign → deploy staging → shadow → approve → canary → promote |

**Cấu trúc pipeline model (dùng lại được cho mọi loại model):**

```
[artifact + schema] → [data quality check] → [eval trên golden set]
      → [so baseline: fail nếu tụt] → [build image] → [scan + sign]
      → [deploy staging] → [smoke + latency] → [shadow so sánh]
      → [manual approve] → [canary 5% → 25% → 100%] → [monitor drift]
```

**Mốc kiểm tra tuần 4:** tạo một model "kém hơn" (ví dụ hạ chất lượng file model) → pipeline **phải đỏ** và không cho deploy. Đây là bằng chứng pipeline có giá trị thật.

---

### Tuần 5 — Capstone + vận hành + phỏng vấn

| Ngày | Nội dung | Bài làm |
|---|---|---|
| 1 | K8s tối thiểu cho CD: Deployment/Service/ConfigMap/Secret/Probe, Helm cơ bản | Dùng **killercoda.com** (cluster trên browser) hoặc **k3d 1 node**; chạy app + model service bằng Helm chart |
| 2 | GitOps với ArgoCD (hoặc CD thuần nếu hết thời gian): dev/staging/prod, promote bằng PR, drift detection | ArgoCD sync repo `deploy/` — ưu tiên làm trên killercoda để không tốn RAM |
| 3 | Observability & vận hành: log/metric/trace, alert, SLO, runbook rollback; DORA metrics (lead time, deploy frequency, MTTR, change failure rate) | Grafana Cloud free + Prometheus chỉ bật khi demo; viết `RUNBOOK.md` |
| 4 | Hoàn thiện capstone + README + demo script | Video/gif demo 3–5 phút, README có sơ đồ kiến trúc |
| 5 | Ôn phỏng vấn + tự đánh giá | Trả lời 30 câu hỏi trong `notes/interview.md`, chấm checklist |

---

## 4. Capstone (sản phẩm cuối khóa)

**Tên:** `model-release-platform` — nền tảng phát hành model có quality gate.

**Thành phần:**
1. `app/` — FastAPI serve model + `/health`, `/predict`, `/metrics`.
2. `model/` — artifact + `evaluate.py` + golden dataset (DVC).
3. `.github/workflows/ci.yml`, `cd.yml` — pipeline chính.
4. `.gitlab-ci.yml` — bản port tương đương.
5. `Jenkinsfile` + `vars/buildAndTest.groovy` — bản Jenkins.
6. `deploy/` — Compose (local/staging) + Helm chart (kind).
7. `monitoring/` — Prometheus + Grafana + Evidently drift report.
8. `docs/` — architecture, ADR (vì sao chọn canary, vì sao OIDC), runbook.

**Tiêu chí "đạt":**
- [ ] PR fail khi: lint lỗi, test fail, coverage tụt, CVE critical, eval metric tụt, latency vượt ngưỡng.
- [ ] Image được ký và verify trước deploy.
- [ ] Không có secret dài hạn trong repo (OIDC hoặc credential store).
- [ ] Deploy staging tự động; prod cần approve; rollback < 2 phút.
- [ ] Cùng logic pipeline chạy được trên 3 nền tảng.
- [ ] Có dashboard + alert + runbook.
- [ ] README đủ để người khác clone và chạy lại trong 15 phút.

---

## 5. Tài nguyên chọn lọc (đừng học lan man)

**Bắt buộc**
- GitHub Actions docs — https://docs.github.com/en/actions
- GitHub Actions security hardening — https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- GitLab CI/CD docs — https://docs.gitlab.com/ci/
- Jenkins Handbook — https://www.jenkins.io/doc/book/
- Docker multi-stage builds — https://docs.docker.com/build/building/multi-stage/
- Trivy — https://trivy.dev/latest/docs/
- Sigstore cosign — https://docs.sigstore.dev/
- DVC — https://dvc.org/doc
- MLflow Model Registry — https://mlflow.org/docs/latest/model-registry.html
- Evidently — https://docs.evidentlyai.com/
- k6 — https://grafana.com/docs/k6/latest/

**Nên có**
- `act` (chạy GitHub Actions local) — https://github.com/nektos/act
- kind — https://kind.sigs.k8s.io/
- Argo CD — https://argo-cd.readthedocs.io/
- Prometheus + Grafana getting started
- Google SRE Book (chương SLO, postmortem) — đọc chọn lọc
- "Accelerate" / DORA metrics — đọc phần metrics

**Bỏ qua ở giai đoạn này:** service mesh, Terraform nâng cao, multi-cloud, chứng chỉ CKA full, tự viết CI engine.

---

## 6. Lỗi người mới hay mắc (đọc trước để tiết kiệm 20h)

1. **Học cú pháp 3 nền tảng trước khi hiểu pipeline.** → Học 1 nền tảng đến khi thành thạo, rồi port; bảng mapping sẽ tự hình thành.
2. **Cache sai key** → cache "độc" làm test pass giả. Key phải gồm lockfile hash + OS + phiên bản runtime.
3. **Artifact vs cache lẫn lộn.** Artifact = sản phẩm cần giữ (image, report); cache = tăng tốc, được phép mất.
4. **Để secret trong repo "tạm".** → Dùng OIDC; bật secret scanning.
5. **Deploy không có smoke test** → "pipeline xanh, app chết" là lỗi phổ biến nhất.
6. **Rollback không được test** → rollback chưa thử = không có rollback.
7. **Gate model bằng metric tuyệt đối** thay vì so baseline + khoảng tin cậy → pipeline đỏ/ xanh ngẫu nhiên.
8. **Bỏ qua tính idempotent**: chạy lại pipeline phải cho cùng kết quả, không tạo resource trùng.
9. **Không giới hạn quyền `GITHUB_TOKEN`** → mặc định quá rộng.
10. **Học K8s quá sớm** → CD bằng Compose/SSH đã đủ để hiểu; K8s chỉ là "nơi chạy".
11. **Dựng đủ hạ tầng trên máy yếu** (Jenkins + GitLab runner + MLflow + Grafana + kind cùng lúc) → máy swap liên tục, pipeline timeout, dễ bỏ cuộc. Hãy để CI cloud làm việc nặng.

---

## 7. Cách tự đánh giá mỗi cuối tuần (30 phút)

Trả lời bằng lời, không nhìn tài liệu:
1. CI khác CD ở đâu? Delivery khác Deployment ở đâu?
2. Vì sao artifact phải bất biến (immutable)? Tag `latest` nguy hiểm thế nào?
3. Nếu pipeline chạy 12 phút, bạn tối ưu theo thứ tự nào?
4. Blue-green vs canary: khi nào chọn cái nào?
5. Làm sao biết model mới "tệ hơn" model cũ một cách có ý nghĩa?
6. Nếu runner hết disk giữa pipeline, debug thế nào?
7. Bạn chứng minh với sếp rằng CI/CD đáng đầu tư bằng số liệu nào?

---

## 8. Sau khóa này nên học gì

- Terraform/IaC cho hạ tầng (nếu deploy cloud thật).
- Kubernetes sâu + CKA (nếu mục tiêu là platform engineer).
- LLM/AI app CI: prompt eval, RAG evaluation, guardrail test — mở rộng tự nhiên của tuần 4.
- FinOps: tối ưu chi phí CI runner và hạ tầng.
- Chứng chỉ (tuỳ mục tiêu): GitHub Actions certificate, GitLab Certified CI/CD Associate, CKA.
