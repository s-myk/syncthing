#!/bin/bash

#!/usr/bin/env awk -f
#!/usr/bin/awk -f

set -eux

script_dir_path=$(dirname $(readlink -f $0))

# tailscale status | awk '{if ($2 != "(\"hello\")") printf("tcp4://%s, tcp4://%s, dynamic\n", $2, $1)};' | sort > $script_dir_path/syncthing_adresses.txt
# tailscale status | awk '$2 != "(\"hello\")" {printf("tcp4://%s, tcp4://%s, dynamic\n", $2, $1)};' | sort > $script_dir_path/syncthing_adresses.txt
# tailscale status | awk '$2 != "(\x22hello\x22)" {printf("tcp4://%s, tcp4://%s, dynamic\n", $2, $1)};' | sort > $script_dir_path/syncthing_adresses.txt
tailscale status | awk '/100./ {printf("tcp4://%s, tcp4://%s, dynamic\n", $2, $1)};' | sort > $script_dir_path/syncthing_adresses.txt

# crontab -e
# */10 *    *   *   * ~/Sync/syncthing_adresses.sh
