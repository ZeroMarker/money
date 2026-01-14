sops --encrypt secrets.yaml > secrets.yaml.enc

sops --encrypt -i secrets.yaml

export SOPS_AGE_KEY_FILE=/etc/age/server.key

sops exec-env secrets.yaml 'python /app/your_app.py'

## 保存私钥
age-keygen -o agekeys.txt
# 先確認內容（只看私钥行）
grep '^AGE-SECRET-KEY-' agekeys.txt

# 然後直接把那一行寫入目標檔案（替換掉所有舊內容）
grep '^AGE-SECRET-KEY-' agekeys.txt | sudo tee /etc/age/server.key > /dev/null

# 設定正確權限
sudo chmod 600 /etc/age/server.key
sudo chown root:root /etc/age/server.key   # 或改成你的服務用戶


## 解密
export SOPS_AGE_KEY_FILE=/etc/age/server.key

# 推薦：不落地明文，直接注入環境變數運行程式
sops exec-env secrets.yaml 'python /app/your_app.py'
