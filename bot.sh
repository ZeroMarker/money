sudo cp bnb-bot.service /etc/systemd/system/bnb-bot.service

sudo systemctl daemon-reload

sudo systemctl enable bnb-bot.service

sudo systemctl start bnb-bot.service
