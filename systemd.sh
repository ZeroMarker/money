sudo cp bnb-bot.service /etc/systemd/system/bnb-bot.service

sudo nano /etc/systemd/system/bnb-bot.service

sudo systemctl daemon-reload

sudo systemctl enable bnb-bot.service
sudo systemctl start bnb-bot.service

sudo systemctl status bnb-bot.service
journalctl -u bnb-bot.service -e   # 查看最近日誌
journalctl -u bnb-bot.service -f   # 即時追蹤

cd /app
git pull
sudo systemctl restart bnb-bot.service