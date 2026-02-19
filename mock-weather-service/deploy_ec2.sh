#!/bin/bash
# EC2 Deployment Script for Mock Weather Service

set -e

echo "🚀 Setting up Mock Weather Service on EC2..."

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install Python
echo "🐍 Installing Python..."
sudo yum install python3 python3-pip -y

# Install dependencies
echo "📚 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create systemd service
echo "⚙️  Creating systemd service..."
sudo tee /etc/systemd/system/weather-mock.service > /dev/null <<EOF
[Unit]
Description=Mock Weather Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/gunicorn -w 2 -b 0.0.0.0:8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
echo "▶️  Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable weather-mock
sudo systemctl start weather-mock

# Check status
echo "✅ Service status:"
sudo systemctl status weather-mock --no-pager

echo ""
echo "🎉 Deployment complete!"
echo "📍 Service running on: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
echo "🔍 Test with: curl http://localhost:8080/health"
