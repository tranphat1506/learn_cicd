#!/usr/bin/env bash
# Low-spec lab setup: swap + a report you can act on.
# Usage: sudo bash scripts/setup-env.sh
#        SWAP_SIZE=8G sudo -E bash scripts/setup-env.sh
set -euo pipefail

SWAPFILE="${SWAPFILE:-/swapfile}"
SWAP_SIZE="${SWAP_SIZE:-6G}"
SWAPPINESS="${SWAPPINESS:-20}"

if [[ ${EUID} -ne 0 ]]; then
  echo "run with sudo: sudo bash $0" >&2
  exit 1
fi

echo "==> memory before"
free -h || true

if swapon --show=NAME --noheadings | grep -qx "${SWAPFILE}"; then
  echo "==> ${SWAPFILE} already active, skipping swap creation"
elif [[ -f ${SWAPFILE} ]]; then
  echo "==> ${SWAPFILE} exists but is not active, enabling it"
  chmod 600 "${SWAPFILE}"
  mkswap "${SWAPFILE}" >/dev/null
  swapon "${SWAPFILE}"
else
  echo "==> creating ${SWAP_SIZE} swap at ${SWAPFILE}"
  fallocate -l "${SWAP_SIZE}" "${SWAPFILE}" || {
    echo "fallocate failed (filesystem may not support it), trying dd" >&2
    dd if=/dev/zero of="${SWAPFILE}" bs=1M count=$(( ${SWAP_SIZE%G} * 1024 )) status=progress
  }
  chmod 600 "${SWAPFILE}"
  mkswap "${SWAPFILE}" >/dev/null
  swapon "${SWAPFILE}"
fi

if ! grep -q "^${SWAPFILE}[[:space:]]" /etc/fstab; then
  echo "${SWAPFILE} none swap sw 0 0" >> /etc/fstab
  echo "==> added ${SWAPFILE} to /etc/fstab"
fi

echo "==> vm.swappiness=${SWAPPINESS}"
sysctl -w "vm.swappiness=${SWAPPINESS}" >/dev/null
printf 'vm.swappiness=%s\n' "${SWAPPINESS}" > /etc/sysctl.d/99-cicd-lab.conf

echo "==> memory after"
free -h

if command -v docker >/dev/null 2>&1; then
  echo "==> docker limits (containers should always set --memory)"
  docker info --format 'driver={{.Driver}} cpus={{.NCPU}} mem={{.MemTotal}}' 2>/dev/null || \
    echo "docker installed but daemon not reachable for this user"
else
  echo "==> docker not found in PATH"
fi

cat <<'EOF'

Reminders for a 9GB machine:
  * max 2 heavy things at once (Jenkins + Postgres is fine; +MLflow is not)
  * heavy build/test/scan belong to CI runners, not this laptop
  * docker system prune -f at the end of each day
  * k3d cluster create lab --agents 0   (never kind multi-node)
EOF
