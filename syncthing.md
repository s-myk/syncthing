# Syncthing

- Installing Syncthing on Ubuntu  
  https://apt.syncthing.net/

  ```shell
  # Add the release PGP keys:
  sudo mkdir -p /etc/apt/keyrings
  sudo curl -L -o /etc/apt/keyrings/syncthing-archive-keyring.gpg https://syncthing.net/release-key.gpg

  # Add the "stable-v2" channel to your APT sources:
  echo "deb [signed-by=/etc/apt/keyrings/syncthing-archive-keyring.gpg] https://apt.syncthing.net/ syncthing stable-v2" | sudo tee /etc/apt/sources.list.d/syncthing.list

  sudo apt-get update
  sudo apt-get install syncthing
  sudo systemctl enable -now syncthing@$USER
  ```

- Remove Syncthing conflict and swap files

  ```console
  find . -name *sync-conflict-*
  find . -name *sync-conflict-* | xargs rm
  ```

  ```console
  find . -name ".syncthing.*.tmp*"
  find . -name ".syncthing.*.tmp*" | xargs rm
  ```

- Installing Syncthing on Synology

  Syncthing packages  
  https://synocommunity.com/package/syncthing
  - DS220+ : x86_64
  - DS218play : aarch64

- Syncthing Configuration  
  https://docs.syncthing.net/users/config.html

  ```shell
  nano ~/.local/state/syncthing/config.xml  # new
  nano ~/.config/syncthing/config.xml       # old
  ```

- File Versioning  
  https://docs.syncthing.net/users/versioning.html

---

- Trouble Shooting
  - Host check error
    - Why do I get “Host check error” in the GUI/API?  
      https://docs.syncthing.net/users/faq.html#why-do-i-get-host-check-error-in-the-gui-api

    ```xml:config.xml
    <gui enabled="true" tls="false">
        <insecureSkipHostcheck>true</insecureSkipHostcheck> # ADD THIS
    </gui>
    ```

  - inotify limits
    - How do I increase the inotify limit to get my filesystem watcher to work?  
      https://docs.syncthing.net/users/faq.html#how-do-i-increase-the-inotify-limit-to-get-my-filesystem-watcher-to-work

    ```console
    echo "fs.inotify.max_user_watches=204800" | sudo tee -a /etc/sysctl.conf

    sudo sh -c 'echo 204800 > /proc/sys/fs/inotify/max_user_watches'
    ```

---

- How to set up a system service  
  https://docs.syncthing.net/users/autostart.html#how-to-set-up-a-system-service
  - syncthing@.service  
    https://github.com/syncthing/syncthing/blob/main/etc/linux-systemd/system/syncthing%40.service
- How to set up a user service  
  https://docs.syncthing.net/users/autostart.html#how-to-set-up-a-user-service
  - syncthing.service  
    https://github.com/syncthing/syncthing/blob/main/etc/linux-systemd/user/syncthing.service
