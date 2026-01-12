# 安装 PM2
npm install pm2 -g
# 启动 Python 策略
pm2 start main.py --name "my_strategy" --interpreter python3
# 查看状态
pm2 status
# 设置开机自启
pm2 save
pm2 startup