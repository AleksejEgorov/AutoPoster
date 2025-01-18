#!/bin/bash
cd /opt/autoposter
sudo -u botrunner git pull --rebase
sudo -u botrunner /opt/autoposter/.venv/bin/pip install -r requirements.txt
chown botrunner:botrunner /opt/autoposter -r
systemctl restart autoposter
systemctl status autoposter