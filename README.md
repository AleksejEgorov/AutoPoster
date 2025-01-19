# AutoPoster

AutoPoster is a tool for automating the reposting of content across multiple social media platforms such as Telegram, VK, and Instagram.

## :warning: CAUTION :warning:

This branch contains code for grabbing telegram posts as source with telethon library. Sometimes it can cause force logoff from your account on all your devices. Thesee changes are commenten now, but you can use it without any warranty.

You have been informed.

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

### Configuration

Copy `config_sample.yaml` to `config.yaml` and populate with your values. Config contains sensitive information, so secure it with `chmod 600`.
