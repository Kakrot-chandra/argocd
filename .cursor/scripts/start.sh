#!/usr/bin/env bash
set -euo pipefail

start_docker() {
  if docker info >/dev/null 2>&1; then
    echo "Docker daemon already running"
    return 0
  fi

  echo "Starting Docker daemon (vfs storage driver)"
  sudo mkdir -p /var/run
  sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
  sudo dockerd --storage-driver=vfs >/tmp/dockerd.log 2>&1 &

  for _ in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
      sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
      echo "Docker daemon ready"
      return 0
    fi
    sleep 1
  done

  echo "Docker daemon failed to start" >&2
  tail -20 /tmp/dockerd.log >&2 || true
  return 1
}

start_k3s() {
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

  if kubectl get nodes >/dev/null 2>&1; then
    echo "k3s cluster already running"
    return 0
  fi

  echo "Starting k3s cluster"
  sudo k3s server \
    --write-kubeconfig-mode 644 \
    --disable traefik \
    --snapshotter=fuse-overlayfs \
    --flannel-backend=host-gw \
    >/tmp/k3s.log 2>&1 &

  for _ in $(seq 1 90); do
    if kubectl get nodes 2>/dev/null | grep -q Ready; then
      echo "k3s cluster ready"
      return 0
    fi
    sleep 2
  done

  echo "k3s cluster failed to start" >&2
  tail -30 /tmp/k3s.log >&2 || true
  return 1
}

start_docker
start_k3s

echo "Development cluster is ready. Use: export KUBECONFIG=/etc/rancher/k3s/k3s.yaml"
