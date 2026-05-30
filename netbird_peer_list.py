#!/usr/bin/env python3
import subprocess
import json
import sys

def get_netbird_fqdn_ip_list() -> list[dict[str, str]]:
    """netbird status --json から fqdn と IP のリストを抽出"""
    try:
        result = subprocess.run(
            ["netbird", "status", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️ netbird コマンドが失敗しました: {e.stderr.strip()}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("⚠️ netbird コマンドが見つかりません。PATH を確認してください。", file=sys.stderr)
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON パースエラー: {e}", file=sys.stderr)
        return []

    # 実際の構造: {"peers": {"total": aa, "connected": bb, "details": [...]}}
    peers_container = data.get("peers", {})

    if isinstance(peers_container, dict):
        # details キーを優先。なければ旧バージョン向けに配列か dict.values() を試す
        peers = peers_container.get("details", [])
        if not isinstance(peers, list):
            # フォールバック: details が無ければ配列そのものか値のリストを使用
            peers = peers_container if isinstance(peers_container, list) else list(peers_container.values())
    elif isinstance(peers_container, list):
        peers = peers_container
    else:
        peers = []

    fqdn_ip_list = []
    for peer in peers:
        # 安全策: 辞書でない要素（数値や文字列）はスキップ
        if not isinstance(peer, dict):
            continue

        fqdn = peer.get("fqdn")
        ip = peer.get("netbirdIp") or peer.get("netbird_ip") or peer.get("ip")

        if fqdn and ip:
            fqdn_ip_list.append({"fqdn": fqdn, "ip": ip})

    return fqdn_ip_list

if __name__ == "__main__":
    peers = get_netbird_fqdn_ip_list()
    
    # 標準出力へ結果表示
    for p in peers:
        print(f"{p['fqdn']} -> {p['ip']}")
        
    # 件数を標準エラー出力へ（パイプ処理時に邪魔にならないよう）
    print(f"\n✅ {len(peers)} peers extracted.", file=sys.stderr)
