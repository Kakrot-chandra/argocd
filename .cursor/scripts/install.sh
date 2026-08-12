#!/usr/bin/env bash
set -euo pipefail

cd /workspace

echo "==> Validating Kubernetes manifests with kubeconform"
mapfile -t manifest_files < <(
  find gitops-argocd pod-metadata-master \
    \( -name '*.yml' -o -name '*.yaml' \) \
    ! -path '*/helm-chart/templates/*' \
    ! -path '*/helm-chart/Chart.yaml' \
    ! -name 'values.yaml' \
    -type f
)
kubeconform -summary -ignore-missing-schemas "${manifest_files[@]}"

echo "==> Linting Helm chart"
helm lint gitops-argocd/helm-chart/

echo "==> Dry-run client validation of sample deployments"
kubectl apply --dry-run=client --validate=false -f gitops-argocd/nginx-app/
kubectl apply --dry-run=client --validate=false -f gitops-argocd/health-check/
kubectl apply --dry-run=client --validate=false -f pod-metadata-master/pod-metadata/manifests/

echo "==> Install complete"
