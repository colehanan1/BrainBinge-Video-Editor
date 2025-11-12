# Deployment Guide - HeyGen Social Clipper

> Production deployment and cloud infrastructure setup guide

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Local Installation](#local-installation)
- [Cloud Deployment](#cloud-deployment)
- [Docker Deployment](#docker-deployment)
- [Webhook Server Setup](#webhook-server-setup)
- [Monitoring and Logging](#monitoring-and-logging)
- [Scaling Strategies](#scaling-strategies)
- [Security Considerations](#security-considerations)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Overview

This guide covers deploying HeyGen Social Clipper in production environments, including local servers, cloud platforms, and containerized deployments.

### Deployment Architectures

**Single Server (Simple)**
- Best for: Low volume, testing, small teams
- Processing: Sequential video processing
- Cost: Low
- Setup Time: < 1 hour

**Multi-Worker (Scalable)**
- Best for: Medium to high volume production
- Processing: Parallel video processing
- Cost: Medium
- Setup Time: 2-4 hours

**Cloud-Native (Enterprise)**
- Best for: High volume, enterprise production
- Processing: Auto-scaling, distributed processing
- Cost: Variable (pay-per-use)
- Setup Time: 1-2 days

## System Requirements

### Minimum Requirements

**Hardware:**
- CPU: 4 cores (Intel i5 or equivalent)
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 10 Mbps download/upload

**Software:**
- OS: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- Python: 3.9 or higher
- FFmpeg: 4.3 or higher
- Git: 2.25 or higher

### Recommended Requirements

**Hardware:**
- CPU: 8+ cores (Intel i7/Xeon or AMD Ryzen 7)
- RAM: 16 GB
- Storage: 200 GB NVMe SSD
- Network: 100 Mbps download/upload

**Software:**
- OS: Ubuntu 22.04 LTS
- Python: 3.10+
- FFmpeg: 5.0+
- Docker: 20.10+ (if using containers)

### Performance Estimates

**Processing Capacity (per server):**
- 60s video @ high quality: ~2-3 minutes
- Hourly capacity: 20-30 videos
- Daily capacity: 400-600 videos

**Resource Usage (per video):**
- Peak CPU: 80-100%
- RAM: 2-4 GB
- Temp Storage: 500 MB - 2 GB
- Network: 50-200 MB download (B-roll, assets)

## Local Installation

### Production Setup on Ubuntu/Debian

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    ffmpeg \
    git \
    build-essential \
    libssl-dev \
    supervisor

# Verify installations
python3.10 --version
ffmpeg -version
```

#### 2. Create Service User

```bash
# Create dedicated user for the service
sudo useradd -r -m -s /bin/bash heygen-clipper
sudo usermod -aG video heygen-clipper

# Switch to service user
sudo su - heygen-clipper
```

#### 3. Application Setup

```bash
# Clone repository
git clone https://github.com/yourusername/heygen-social-clipper.git
cd heygen-social-clipper

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install application
pip install -e .

# Verify installation
heygen-clipper --version
```

#### 4. Configuration

```bash
# Create configuration directory
mkdir -p /home/heygen-clipper/config
mkdir -p /home/heygen-clipper/data/output
mkdir -p /home/heygen-clipper/data/temp
mkdir -p /home/heygen-clipper/logs

# Copy example configurations
cp .env.example /home/heygen-clipper/.env
cp config/brand.example.yaml /home/heygen-clipper/config/brand.yaml

# Edit configuration
nano /home/heygen-clipper/.env
```

**Environment Variables:**
```bash
# API Keys
PEXELS_API_KEY=your_pexels_api_key_here

# Paths
OUTPUT_DIR=/home/heygen-clipper/data/output
TEMP_DIR=/home/heygen-clipper/data/temp
LOG_DIR=/home/heygen-clipper/logs

# Processing
MAX_WORKERS=4
PROCESSING_TIMEOUT=600

# Webhook
WEBHOOK_SECRET=generate_strong_secret_here
WEBHOOK_PORT=8000

# Logging
LOG_LEVEL=INFO
```

#### 5. Service Configuration (Systemd)

Create service file: `/etc/systemd/system/heygen-clipper-webhook.service`

```ini
[Unit]
Description=HeyGen Social Clipper Webhook Server
After=network.target

[Service]
Type=simple
User=heygen-clipper
Group=heygen-clipper
WorkingDirectory=/home/heygen-clipper/heygen-social-clipper
Environment="PATH=/home/heygen-clipper/heygen-social-clipper/venv/bin"
EnvironmentFile=/home/heygen-clipper/.env

ExecStart=/home/heygen-clipper/heygen-social-clipper/venv/bin/heygen-clipper webhook \
    --host 0.0.0.0 \
    --port 8000 \
    --config /home/heygen-clipper/config/brand.yaml \
    --output-dir /home/heygen-clipper/data/output

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=append:/home/heygen-clipper/logs/webhook.log
StandardError=append:/home/heygen-clipper/logs/webhook-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable heygen-clipper-webhook

# Start service
sudo systemctl start heygen-clipper-webhook

# Check status
sudo systemctl status heygen-clipper-webhook

# View logs
sudo journalctl -u heygen-clipper-webhook -f
```

## Cloud Deployment

### AWS EC2 Deployment

#### 1. Launch EC2 Instance

**Recommended Instance Type:**
- `c6i.2xlarge` (8 vCPU, 16 GB RAM) - Standard
- `c6i.4xlarge` (16 vCPU, 32 GB RAM) - High volume

**AMI:**
- Ubuntu Server 22.04 LTS

**Storage:**
- 100 GB GP3 SSD (3000 IOPS, 125 MB/s throughput)

**Security Group:**
```
Inbound Rules:
- SSH (22): Your IP only
- HTTP (80): 0.0.0.0/0 (if using load balancer)
- HTTPS (443): 0.0.0.0/0 (if using load balancer)
- Custom TCP (8000): Load balancer only (if using)

Outbound Rules:
- All traffic: 0.0.0.0/0
```

#### 2. Initial Setup

```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Run installation script
curl -fsSL https://raw.githubusercontent.com/yourusername/heygen-social-clipper/main/scripts/install-aws.sh | bash

# Configure environment
sudo nano /home/heygen-clipper/.env
```

#### 3. Optional: S3 Integration

Configure for output storage:

```bash
# Install AWS CLI
sudo apt install awscli -y

# Configure AWS credentials
aws configure

# Test S3 access
aws s3 ls s3://your-output-bucket
```

Modify webhook callback to upload to S3:
```python
# In webhook handler, after processing
import boto3

s3 = boto3.client('s3')
s3.upload_file(
    local_video_path,
    'your-output-bucket',
    f'processed/{video_filename}'
)
```

### Google Cloud Platform (GCP) Deployment

#### 1. Create Compute Engine Instance

```bash
# Create instance with gcloud CLI
gcloud compute instances create heygen-clipper \
    --machine-type=c2-standard-8 \
    --zone=us-central1-a \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=100GB \
    --boot-disk-type=pd-ssd \
    --tags=http-server,https-server
```

#### 2. Configure Firewall

```bash
# Create firewall rule for webhook
gcloud compute firewall-rules create allow-webhook \
    --allow=tcp:8000 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server
```

#### 3. Setup Application

```bash
# SSH to instance
gcloud compute ssh heygen-clipper --zone=us-central1-a

# Follow local installation steps
# (Same as Ubuntu/Debian setup above)
```

### Azure Deployment

#### 1. Create Virtual Machine

**Size:** Standard_D8s_v4 (8 vCPU, 32 GB RAM)
**Image:** Ubuntu Server 22.04 LTS
**Disk:** 100 GB Premium SSD

#### 2. Network Security Group

```
Inbound Rules:
- Port 22 (SSH): Your IP
- Port 8000 (Webhook): Internet
```

#### 3. Install Application

Same as Ubuntu/Debian local installation steps.

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -r -m -s /bin/bash heygen-clipper

# Set working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY setup.py .
COPY src/ ./src/
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /data/output /data/temp /config /logs
RUN chown -R heygen-clipper:heygen-clipper /app /data /config /logs

# Switch to application user
USER heygen-clipper

# Expose webhook port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')"

# Default command
CMD ["heygen-clipper", "webhook", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--config", "/config/brand.yaml", \
     "--output-dir", "/data/output"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  heygen-clipper:
    build: .
    container_name: heygen-clipper
    restart: unless-stopped

    ports:
      - "8000:8000"

    volumes:
      - ./config:/config:ro
      - ./data/output:/data/output
      - ./data/temp:/data/temp
      - ./logs:/logs

    environment:
      - PEXELS_API_KEY=${PEXELS_API_KEY}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - MAX_WORKERS=4
      - LOG_LEVEL=INFO

    env_file:
      - .env

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: unless-stopped

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro

    depends_on:
      - heygen-clipper
```

### Build and Run

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes Deployment

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: heygen-clipper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: heygen-clipper
  template:
    metadata:
      labels:
        app: heygen-clipper
    spec:
      containers:
      - name: heygen-clipper
        image: your-registry/heygen-clipper:latest
        ports:
        - containerPort: 8000
        env:
        - name: PEXELS_API_KEY
          valueFrom:
            secretKeyRef:
              name: heygen-secrets
              key: pexels-api-key
        volumeMounts:
        - name: output-storage
          mountPath: /data/output
        - name: config
          mountPath: /config
        resources:
          requests:
            cpu: "2"
            memory: "4Gi"
          limits:
            cpu: "4"
            memory: "8Gi"
      volumes:
      - name: output-storage
        persistentVolumeClaim:
          claimName: heygen-output-pvc
      - name: config
        configMap:
          name: heygen-config
---
apiVersion: v1
kind: Service
metadata:
  name: heygen-clipper-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: heygen-clipper
```

## Webhook Server Setup

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/heygen-clipper`:

```nginx
upstream heygen_clipper {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logging
    access_log /var/log/nginx/heygen-access.log;
    error_log /var/log/nginx/heygen-error.log;

    # Webhook endpoint
    location /webhook/ {
        proxy_pass http://heygen_clipper;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;

        # Body size for video uploads
        client_max_body_size 500M;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://heygen_clipper;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/heygen-clipper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

## Monitoring and Logging

### Application Logs

Configure structured logging in application:

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        return json.dumps(log_data)
```

### Log Rotation

Configure logrotate `/etc/logrotate.d/heygen-clipper`:

```
/home/heygen-clipper/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 heygen-clipper heygen-clipper
    sharedscripts
    postrotate
        systemctl reload heygen-clipper-webhook
    endscript
}
```

### Monitoring Tools

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

processing_time = Histogram('video_processing_seconds', 'Time spent processing videos')
videos_processed = Counter('videos_processed_total', 'Total videos processed')
active_jobs = Gauge('active_processing_jobs', 'Number of videos currently being processed')
```

**Health Check Endpoint:**
```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'version': '1.0.0',
        'uptime': time.time() - start_time,
        'active_jobs': get_active_job_count()
    }
```

## Scaling Strategies

### Horizontal Scaling

**Load Balancer Configuration:**
- Distribute webhook requests across multiple servers
- Use sticky sessions if needed for job tracking
- Implement job queue (Redis, RabbitMQ) for distributed processing

**Auto-Scaling (AWS Example):**
```bash
# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name heygen-clipper-asg \
    --launch-configuration-name heygen-clipper-lc \
    --min-size 2 \
    --max-size 10 \
    --desired-capacity 3 \
    --target-group-arns arn:aws:elasticloadbalancing:... \
    --health-check-type ELB \
    --health-check-grace-period 300
```

### Vertical Scaling

Upgrade instance resources based on usage:
- Monitor CPU, RAM, disk I/O
- Scale up during peak processing times
- Use spot instances for cost savings (non-critical workloads)

## Security Considerations

### Best Practices

1. **API Key Management**
   - Store in environment variables or secret managers
   - Rotate keys regularly
   - Use different keys for dev/staging/production

2. **Webhook Authentication**
   - Implement HMAC signature verification
   - Use HTTPS only
   - Rate limiting on webhook endpoints

3. **File Validation**
   - Validate file types and sizes
   - Scan for malware
   - Sanitize file names

4. **Network Security**
   - Firewall rules (allow only necessary ports)
   - VPC/subnet isolation
   - Security groups/NSGs

5. **User Permissions**
   - Run service with minimal privileges
   - Separate user for service
   - Read-only access where possible

## Backup and Recovery

### Data Backup

```bash
# Backup script
#!/bin/bash
BACKUP_DIR=/backups/heygen-$(date +%Y%m%d)
mkdir -p $BACKUP_DIR

# Backup configurations
cp -r /home/heygen-clipper/config $BACKUP_DIR/

# Backup logs
cp -r /home/heygen-clipper/logs $BACKUP_DIR/

# Sync to S3 (optional)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/heygen-backups/
```

### Disaster Recovery

1. **Configuration Backup:** Store in version control
2. **Data Backup:** Regular snapshots of output storage
3. **Infrastructure as Code:** Terraform/CloudFormation for reproducibility
4. **Runbooks:** Document recovery procedures

## Troubleshooting

### Common Issues

**Issue: FFmpeg not found**
```bash
# Solution: Install FFmpeg
sudo apt install ffmpeg
# Verify
which ffmpeg
ffmpeg -version
```

**Issue: Out of disk space**
```bash
# Check disk usage
df -h

# Clean temp files
rm -rf /home/heygen-clipper/data/temp/*

# Implement automatic cleanup
# Add to crontab: 0 * * * * find /home/heygen-clipper/data/temp -mtime +1 -delete
```

**Issue: High memory usage**
```bash
# Monitor memory
free -h
htop

# Adjust MAX_WORKERS in .env
# Reduce concurrent processing
```

**Issue: Webhook timeouts**
```bash
# Increase timeout in nginx config
proxy_read_timeout 1800s;

# Increase application timeout
PROCESSING_TIMEOUT=1800
```

### Debug Mode

Enable verbose logging:
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or pass flag
heygen-clipper process --verbose ...
```

---

**Last Updated:** 2025-11-12

For deployment support, contact: support@brainbinge.com
