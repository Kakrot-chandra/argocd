FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        fuse-overlayfs \
        docker.io \
        iptables \
        yamllint \
    && rm -rf /var/lib/apt/lists/*

# kubectl
RUN curl -fsSL "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
        -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl

# Helm
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# kubeconform
RUN curl -fsSL https://github.com/yannh/kubeconform/releases/download/v0.6.7/kubeconform-linux-amd64.tar.gz \
        | tar -xz -C /usr/local/bin kubeconform

# kind (optional local cluster via Docker)
RUN curl -fsSL -o /usr/local/bin/kind \
        https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64 \
    && chmod +x /usr/local/bin/kind

# ArgoCD CLI
RUN curl -fsSL -o /usr/local/bin/argocd \
        https://github.com/argoproj/argo-cd/releases/download/v2.14.2/argocd-linux-amd64 \
    && chmod +x /usr/local/bin/argocd

# k3s (single-node Kubernetes for local GitOps development)
RUN curl -fsSL https://get.k3s.io | INSTALL_K3S_SKIP_SELINUX_RPM=true sh -s - --write-kubeconfig-mode 644

RUN echo 'user_allow_other\nmount_max = 100000' > /etc/fuse.conf

USER ubuntu
