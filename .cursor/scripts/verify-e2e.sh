#!/usr/bin/env bash
set -euo pipefail

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

echo "==> Deploying nginx demo app"
kubectl create namespace demo --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f /workspace/gitops-argocd/nginx-app/ -n demo
kubectl rollout status deployment/nginx -n demo --timeout=120s

NODE_PORT=$(kubectl get svc nginx-service -n demo -o jsonpath='{.spec.ports[0].nodePort}')
echo "==> Checking nginx on NodePort ${NODE_PORT}"
HTTP_CODE=$(curl -s -o /tmp/nginx-response.html -w "%{http_code}" "http://localhost:${NODE_PORT}/")
if [[ "${HTTP_CODE}" != "200" ]]; then
  echo "Expected HTTP 200, got ${HTTP_CODE}" >&2
  exit 1
fi

if ! grep -q "Welcome to nginx" /tmp/nginx-response.html; then
  echo "nginx welcome page not found in response" >&2
  exit 1
fi

echo "==> End-to-end verification passed (nginx serving on port ${NODE_PORT})"
