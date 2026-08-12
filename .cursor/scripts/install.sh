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

echo "==> Rendering and validating Helm templates"
helm template random-shapes gitops-argocd/helm-chart/ | kubeconform -summary -ignore-missing-schemas

echo "==> Install complete"
