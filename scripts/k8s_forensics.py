#!/usr/bin/env python3
"""
K8s / Docker Swarm 集群取证工具
===============================
从服务器磁盘镜像中提取 K8s/Docker Swarm 配置，重建集群拓扑，提取 Secrets。

用法:
  python k8s_forensics.py -d /mnt/server1/            # 单节点
  python k8s_forensics.py -d /mnt/server1/ /mnt/server2/ /mnt/server3/  # 集群
"""
import os
import re
import json
import yaml
import base64
import sqlite3
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime


class ClusterForensics:
    def __init__(self, node_dirs: list[str]):
        self.node_dirs = [Path(d) for d in node_dirs]
        self.findings = defaultdict(list)
        self.topology = {"nodes": [], "services": [], "secrets": [], "network": []}

    # ================================================================
    # K8s 取证
    # ================================================================
    def analyze_k8s(self, node_path: Path, node_name: str):
        """分析 K8s 节点"""
        k8s_paths = [
            "/etc/kubernetes/",
            "/var/lib/kubelet/",
            "/var/lib/etcd/",
            "/opt/cni/",
            "/etc/cni/",
        ]

        found = False
        for kp in k8s_paths:
            full = node_path / kp.lstrip("/")
            if full.exists():
                found = True
                break

        if not found:
            return

        print(f"\n  [K8s] {node_name}")

        # 1. kubelet 配置 → 节点角色
        kubelet_conf = node_path / "var/lib/kubelet/config.yaml"
        if kubelet_conf.exists():
            with open(kubelet_conf) as f:
                conf = yaml.safe_load(f)
            print(f"    节点名: {conf.get('nodeName', '?')}")
            print(f"    集群 DNS: {conf.get('clusterDNS', '?')}")

        # 2. kubeconfig → API server 地址
        kubeconfig = node_path / "etc/kubernetes/kubelet.conf"
        if kubeconfig.exists():
            with open(kubeconfig) as f:
                kc = yaml.safe_load(f)
            for cluster in kc.get("clusters", []):
                server = cluster.get("cluster", {}).get("server", "")
                if server:
                    print(f"    API Server: {server}")
                    self.topology["network"].append({"node": node_name, "api_server": server})
            for user in kc.get("users", []):
                cert = user.get("user", {}).get("client-certificate-data", "")
                if cert:
                    print(f"    客户端证书: 已嵌入")

        # 3. manifests → 静态 Pod (控制平面组件)
        manifests_dir = node_path / "etc/kubernetes/manifests"
        if manifests_dir.exists():
            for mf in manifests_dir.glob("*.yaml"):
                with open(mf) as f:
                    pod = yaml.safe_load(f)
                name = pod.get("metadata", {}).get("name", mf.stem)
                ns = pod.get("metadata", {}).get("namespace", "default")
                print(f"    静态Pod: {name} ({ns})")
                self.topology["services"].append({"node": node_name, "pod": name, "type": "static"})

        # 4. etcd 数据库 → 所有 K8s 对象
        etcd_dir = node_path / "var/lib/etcd/member"
        if etcd_dir.exists():
            self._analyze_etcd(etcd_dir, node_name)

        # 5. ConfigMap 和 Secret 残留
        pods_dir = node_path / "var/lib/kubelet/pods"
        if pods_dir.exists():
            self._extract_k8s_secrets_from_volumes(pods_dir, node_name)

        self.topology["nodes"].append({"name": node_name, "type": "k8s"})

    def _analyze_etcd(self, etcd_dir: Path, node_name: str):
        """分析 etcd 数据库 — K8s 的'源数据'"""
        # etcd 默认不加密，直接解析 bolt 数据库
        db_path = etcd_dir / "snap" / "db"
        if not db_path.exists():
            return

        print(f"    etcd: {db_path.stat().st_size/(1024*1024):.0f} MB")

        # 搜索 JSON 格式的 K8s 对象 (etcd 存储为 protobuf, 但也含 JSON 片段)
        try:
            with open(db_path, "rb") as f:
                data = f.read(10 * 1024 * 1024)  # 读前 10MB
            text = data.decode("utf-8", errors="replace")

            # 搜索 Secret
            for match in re.finditer(r'"(?:data|stringData)"\s*:\s*\{([^}]+)\}', text):
                print(f"    Secret 片段: {match.group(1)[:200]}")

            # 搜索 ConfigMap
            for match in re.finditer(r'"ConfigMap"[^}]*"data"\s*:\s*\{([^}]+)\}', text):
                print(f"    ConfigMap: {match.group(1)[:200]}")

            # 搜索 Service ClusterIP
            for match in re.finditer(r'"clusterIP"\s*:\s*"(\d+\.\d+\.\d+\.\d+)"', text):
                print(f"    Service IP: {match.group(1)}")
                self.topology["network"].append({"node": node_name, "service_ip": match.group(1)})

        except Exception as e:
            print(f"    etcd 解析错误: {e}")

    def _extract_k8s_secrets_from_volumes(self, pods_dir: Path, node_name: str):
        """从 Pod 卷中提取 Secret 挂载"""
        for secret_vol in pods_dir.rglob("**/volumes/kubernetes.io~secret/*"):
            if secret_vol.is_dir():
                for f in secret_vol.iterdir():
                    if f.is_file():
                        try:
                            content = f.read_text()[:500]
                            print(f"    Secret: {secret_vol.name}/{f.name} = {content[:100]}")
                            self.topology["secrets"].append({
                                "node": node_name,
                                "secret_name": secret_vol.name,
                                "key": f.name,
                                "value": content[:200],
                            })
                        except Exception:
                            pass

    # ================================================================
    # Docker Swarm 取证
    # ================================================================
    def analyze_swarm(self, node_path: Path, node_name: str):
        """分析 Docker Swarm 节点"""
        swarm_dir = node_path / "var/lib/docker/swarm"
        if not swarm_dir.exists():
            return

        print(f"\n  [Swarm] {node_name}")

        # 1. 节点角色 (manager/worker)
        for f in swarm_dir.rglob("**/state.json"):
            try:
                with open(f) as fh:
                    state = json.load(fh)
                role = state.get("role", "?")
                print(f"    角色: {role}")
                self.topology["nodes"].append({"name": node_name, "type": f"swarm-{role}"})
            except Exception:
                pass

        # 2. 服务配置
        for f in swarm_dir.rglob("**/tasks/**/*.json"):
            try:
                with open(f) as fh:
                    task = json.load(fh)
                service = task.get("Service", {}).get("Spec", {}).get("Name", "?")
                print(f"    服务: {service}")
                self.topology["services"].append({"node": node_name, "service": service})
            except Exception:
                pass

    # ================================================================
    # 通用: 提取所有环境变量 (可能含密码)
    # ================================================================
    def extract_env_vars(self, node_path: Path, node_name: str):
        """从 Docker/K8s/Podman 配置中提取环境变量"""
        patterns = [
            "**/docker-compose.yml",
            "**/docker-compose.yaml",
            "**/.env",
            "**/config.env",
            "**/Dockerfile",
        ]

        for pattern in patterns:
            for f in node_path.rglob(pattern):
                try:
                    content = f.read_text(errors="replace")
                    # 提取 PASSWORD/SECRET/KEY/TOKEN 等敏感环境变量
                    for line in content.split("\n"):
                        line = line.strip()
                        if any(kw in line.upper() for kw in ["PASSWORD", "PASSWD", "SECRET", "KEY", "TOKEN", "API_KEY"]):
                            print(f"    [{f.name}] {line[:150]}")
                            self.topology["secrets"].append({
                                "node": node_name,
                                "file": str(f.relative_to(node_path)),
                                "line": line[:200],
                            })
                except Exception:
                    pass

    # ================================================================
    # 集群拓扑重建
    # ================================================================
    def rebuild_topology(self):
        """从收集的信息重建集群拓扑"""
        print(f"\n{'='*60}")
        print(f"集群拓扑重建")
        print(f"{'='*60}")

        print(f"\n节点 ({len(self.topology['nodes'])}):")
        for n in self.topology["nodes"]:
            print(f"  {n['name']} ({n['type']})")

        print(f"\n服务 ({len(self.topology['services'])}):")
        for s in self.topology["services"][:20]:
            print(f"  {s.get('node', '?')} → {s.get('service') or s.get('pod', '?')}")

        print(f"\n网络连接 ({len(self.topology['network'])}):")
        for n in self.topology["network"][:10]:
            for k, v in n.items():
                if k != "node":
                    print(f"  {n.get('node', '?')} → {v}")

        if self.topology["secrets"]:
            print(f"\n🔑 发现的 Secrets/密码 ({len(self.topology['secrets'])}):")
            for s in self.topology["secrets"][:10]:
                print(f"  [{s.get('node', '?')}] {s.get('file', '')}: {s.get('line', s.get('value', ''))[:120]}")

    # ================================================================
    # 主流程
    # ================================================================
    def run(self):
        for node_dir in self.node_dirs:
            if not node_dir.exists():
                print(f"跳过: {node_dir} (不存在)")
                continue

            node_name = node_dir.name
            print(f"\n分析节点: {node_name}")

            # K8s
            self.analyze_k8s(node_dir, node_name)

            # Docker Swarm
            self.analyze_swarm(node_dir, node_name)

            # 环境变量
            self.extract_env_vars(node_dir, node_name)

        # 跨节点关联 → 集群拓扑
        self.rebuild_topology()

        return self.topology


def main():
    parser = argparse.ArgumentParser(description="K8s/Docker Swarm 集群取证")
    parser.add_argument("-d", "--dirs", nargs="+", required=True,
                       help="服务器节点目录 (已挂载的镜像)")
    parser.add_argument("-o", "--output", help="输出 JSON")
    args = parser.parse_args()

    cf = ClusterForensics(args.dirs)
    topology = cf.run()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(topology, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n结果已保存: {args.output}")


if __name__ == "__main__":
    main()
