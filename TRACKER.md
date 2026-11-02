# Tiến độ 5 tuần

Đánh dấu `[x]` khi có **artifact commit được**, không phải khi "đã đọc xong".

## Chuẩn bị môi trường (làm trước tuần 1)
- [ ] Bật swap 6–8GB, kiểm tra `free -h`
- [ ] `docker system prune` thói quen cuối ngày
- [ ] Chọn deploy target (self-hosted runner / VPS free / Compose local)
- [ ] Xác nhận CI chạy trên runner cloud, không build nặng ở máy local

## Tuần 1 — Nền tảng + CI (GitHub Actions)
- [ ] D1: Repo + branch protection + convention
- [ ] D2: `ci.yml` lint + unit test chạy xanh trên PR
- [ ] D3: Coverage gate + integration test với service container
- [ ] D4: Dockerfile production + push GHCR tag `sha-*`
- [ ] D5: Pipeline CI đầy đủ + sơ đồ trong README

## Tuần 2 — CD + supply chain
- [ ] D1: Reusable workflow + `act` chạy local
- [ ] D2: OIDC + environment approval + pin action theo SHA
- [ ] D3: Trivy + SBOM + cosign sign/verify
- [ ] D4: Deploy staging + smoke test + auto-rollback
- [ ] D5: CI/CD end-to-end có approve trước prod

## Tuần 3 — GitLab + Jenkins
- [ ] D1: `.gitlab-ci.yml` port từ GitHub
- [ ] D2: Build image + coverage report trên MR
- [ ] D3: Jenkinsfile chạy lint/test/build
- [ ] D4: Shared library dùng cho 2 repo
- [ ] D5: Bảng mapping 3 nền tảng + 3 file cấu hình

## Tuần 4 — Model release pipeline
- [ ] D1: DVC + MLflow registry, 2 version model
- [ ] D2: `evaluate.py` fail khi metric tụt + report hiển thị trên MR/PR
- [ ] D3: `/predict` + schema test + benchmark latency
- [ ] D4: Shadow deploy + so sánh output + drift monitoring
- [ ] D5: Pipeline model end-to-end có gate + promote

## Tuần 5 — Capstone
- [ ] D1: Chạy app + model service trên killercoda (hoặc k3d 1 node) bằng Helm
- [ ] D2: ArgoCD sync dev/staging (trên killercoda nếu máy yếu)
- [ ] D3: Grafana Cloud + alert + runbook
- [ ] D4: Demo 3–5 phút + README kiến trúc
- [ ] D5: Trả lời 30 câu phỏng vấn + tự chấm checklist

## Bằng chứng cuối khóa
- [ ] Tạo model kém hơn → pipeline đỏ, không deploy
- [ ] Xóa/thu hồi secret → pipeline báo lỗi rõ ràng
- [ ] Rollback prod < 2 phút (đã đo)
- [ ] Người khác clone và chạy lại trong 15 phút
