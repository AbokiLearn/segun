#!/bin/bash

# updates and installs
sudo apt update && sudo apt upgrade -y
sudo apt install software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    npm \
    certbot \
    python3-certbot-nginx
sudo npm install -g pm2
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# set python version
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --set python3 /usr/bin/python3.11

# create project dir
sudo mkdir -p /app/telegram-server
sudo chown -R $USER:$USER /app/telegram-server
cd /app/telegram-server

# create venv
/home/ubuntu/.cargo/bin/uv venv

# configure nginx
sudo tee /etc/nginx/sites-available/telegram-api << EOF
server {
    listen 80;
    server_name telegram-api.wazobiacode.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/telegram-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# get cert
# sudo certbot --nginx -d telegram-api.wazobiacode.com
# echo "0 0 1 * * /usr/bin/certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null

echo "Initial setup complete. The CI/CD pipeline will handle deployments."
