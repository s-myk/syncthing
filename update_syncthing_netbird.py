#!/usr/bin/env python3
import subprocess
import json
import sys
import requests

# --- 設定 ---
HOST_URL = 'http://127.0.0.1:8384'

# --- Netbird 関数 (提供されたコードをそのまま使用) ---
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

    peers_container = data.get("peers", {})

    if isinstance(peers_container, dict):
        peers = peers_container.get("details", [])
        if not isinstance(peers, list):
            peers = peers_container if isinstance(peers_container, list) else list(peers_container.values())
    elif isinstance(peers_container, list):
        peers = peers_container
    else:
        peers = []

    fqdn_ip_list = []
    for peer in peers:
        if not isinstance(peer, dict):
            continue

        fqdn = peer.get("fqdn")
        ip = peer.get("netbirdIp") or peer.get("netbird_ip") or peer.get("ip")

        if fqdn and ip:
            fqdn_ip_list.append({"fqdn": fqdn, "ip": ip})

    return fqdn_ip_list

# --- Syncthing API 関数 ---

def get_api_key():
    """syncthing cli から APIキーを取得"""
    try:
        result = subprocess.run(
            ["syncthing", "cli", "config", "gui", "apikey", "get"],
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"エラー: Syncthing APIキーの取得に失敗: {e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("エラー: syncthing コマンドが見つかりません。", file=sys.stderr)
        return None

def main():
    print("🔄 Netbirdピア情報を取得中...", file=sys.stderr)
    netbird_peers = get_netbird_fqdn_ip_list()
    
    if not netbird_peers:
        print("❌ Netbirdのピア情報が取得できませんでした。処理を終了します。", file=sys.stderr)
        return

    # FQDNとIPのマッピングを作成（検索用に小文字化）
    peer_map = []
    for p in netbird_peers:
        fqdn_lower = p['fqdn'].lower()
        hostname_part = fqdn_lower.split('.')[0]
        peer_map.append({
            "fqdn_full": fqdn_lower,
            "hostname": hostname_part,
            "ip": p['ip'],
            "original_fqdn": p['fqdn']
        })

    print(f"✅ {len(netbird_peers)} peers found in Netbird.", file=sys.stderr)

    # Syncthing APIキー取得
    api_key = get_api_key()
    if not api_key:
        return

    headers = {'X-API-Key': api_key}

    # Syncthing設定取得
    print("🔄 Syncthing設定を取得中...", file=sys.stderr)
    response = requests.get(f'{HOST_URL}/rest/config', headers=headers)
    if response.status_code != 200:
        print(f"❌ Syncthing設定の取得に失敗: {response.status_code}", file=sys.stderr)
        return

    config = response.json()
    updated_count = 0

    # 各デバイスを確認
    for device in config['devices']:
        device_name = device.get('name', '').lower().strip()
        if not device_name:
            continue

        # Netbirdのリストから一致するものを探す
        matched_peer = None
        for peer in peer_map:
            if peer['fqdn_full'] == device_name:
                matched_peer = peer
                break
            if peer['hostname'] == device_name:
                matched_peer = peer
                break
        
        if matched_peer:
            ip = matched_peer['ip']
            new_addresses = [
                f"quic4://{ip}",
                f"tcp4://{ip}",
                "dynamic"
            ]

            if device.get('addresses') != new_addresses:
                print(f"🔧 Updating '{device['name']}' (ID: {device['deviceID'][:7]}...) -> {ip}", file=sys.stderr)
                device['addresses'] = new_addresses
                updated_count += 1
            else:
                print(f"✅ Skipped '{device['name']}' (Already up to date)", file=sys.stderr)

    if updated_count > 0:
        print(f"🔄 {updated_count} devices modified. Sending config...", file=sys.stderr)
        
        # --- 修正箇所: メソッドをPUTに変更し、json引数を使用 ---
        put_response = requests.put(
            f'{HOST_URL}/rest/config', 
            headers=headers, 
            json=config
        )
        
        if put_response.status_code == 200:
            print("✅ Syncthing設定の更新に成功しました。", file=sys.stderr)
        else:
            print(f"❌ 更新に失敗: {put_response.status_code}", file=sys.stderr)
            print(put_response.text, file=sys.stderr)
    else:
        print("ℹ️ 更新対象のデバイスはありませんでした。", file=sys.stderr)

if __name__ == "__main__":
    main()
