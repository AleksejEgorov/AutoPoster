#!/bin/bash
cd /opt/autoposter
systemctl stop autoposter
sudo -u botrunner git pull --rebase
sudo -u botrunner /opt/autoposter/.venv/bin/pip install -r requirements.txt --no-cache-dir
chown botrunner:botrunner /opt/autoposter -R
systemctl start autoposter
systemctl status autoposter
