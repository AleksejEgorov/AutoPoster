# AutoPoster

AutoPoster is a tool for automating the reposting of content across multiple social media platforms such as Telegram, VK, and Instagram.

## Project Structure

- **autoposter_common.py**: Contains common utility functions used across the project.
- **autoposter_tg.py**: Handles fetching and reposting content from/to Telegram.
- **autoposter_vk.py**: Handles fetching and reposting content from/to VK.
- **autoposter_inst.py**: Handles reposting content to Instagram.
- **main.py**: Main entry point for running the repost cycle.
- **config.yaml**: Configuration file for setting up the project.

## Requirements

Host, where this bot is installed, must be accessible from Instagram via HTTPS (443/TCP)

## Usage

### Prepare environment

```bash
cd /opt
apt install git python3 python3-pip python3-venv
git clone https://github.com/AleksejEgorov/AutoPoster.git autoposter
cd autoposter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

### Create service

First, create system user:

```bash
sudo useradd -r -s /bin/false botrunner
```

Next, create systemd unit file `/etc/systemd/system/autoposter.service` with:

```ini
[Unit]
Description=Autoposter to Telegram and Instagram
After=network.target

[Service]
User=botrunner
Group=botrunner
Type=simple
WorkingDirectory=/opt/autoposter
ExecStart=/opt/autoposter/.venv/bin/python3 /opt/autoposter/main.py
Restart=no

[Install]
WantedBy=multi-user.target
```

### Configuration

Copy `config_sample.yaml` to `config.yaml` and populate with your values. Config contains sensitive information, so secure it with `chmod 600`.

### Run

```bash
sudo systemctl daemon-reload
sudo systemctl enable autoposter
sudo systemctl start autoposter
sudo systemctl status autoposter
# and take a look to the log:
journalctl -xeu autoposter
```

When configuration changed, don't forget to restart sercice with `sudo systemctl restart autoposter`.

### Update

```bash
/opt/autoposter/updater.sh
```
