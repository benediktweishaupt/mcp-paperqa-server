# PaperQA2 MCP Server - Production Deployment Guide

This guide covers production deployment, monitoring, and maintenance of the PaperQA2 MCP Server.

## 🚀 Production Setup

### System Requirements

**Minimum:**
- Python 3.9+
- 4GB RAM
- 2GB disk space (for documents and embeddings)
- Stable internet connection

**Recommended:**
- Python 3.11+
- 8GB RAM
- 10GB SSD storage
- High-bandwidth connection for embedding API calls

### Environment Setup

1. **Create dedicated environment:**
```bash
python3 -m venv paperqa-mcp-env
source paperqa-mcp-env/bin/activate  # Linux/Mac
# or paperqa-mcp-env\Scripts\activate  # Windows
```

2. **Install production dependencies:**
```bash
pip install paper-qa==5.28.0 mcp==1.13.0
```

3. **Verify installation:**
```bash
python3 -c "from paperqa import Settings; from mcp.server.fastmcp import FastMCP; print('✅ Dependencies ready')"
```

## 🔐 API Keys Configuration

### Required API Keys

**At minimum, you need ONE of:**
- `OPENAI_API_KEY` (GPT models + embeddings)
- `VOYAGE_API_KEY` + `OPENAI_API_KEY` (recommended for cost efficiency)
- `GEMINI_API_KEY` + `OPENAI_API_KEY` (for highest performance)

### Production Environment Variables

Create `/etc/paperqa-mcp/environment`:
```bash
# Core API Keys (choose your stack)
OPENAI_API_KEY=sk-your-openai-key-here
VOYAGE_API_KEY=pa-your-voyage-key-here
GEMINI_API_KEY=your-gemini-key-here

# Optional: Advanced Configuration
PAPERQA_LOG_LEVEL=INFO
PAPERQA_PAPERS_DIR=/var/lib/paperqa/papers
PAPERQA_MAX_CONCURRENT_REQUESTS=2
```

### API Key Security
```bash
# Set secure permissions
sudo chmod 600 /etc/paperqa-mcp/environment
sudo chown paperqa:paperqa /etc/paperqa-mcp/environment

# Load in server startup
source /etc/paperqa-mcp/environment
```

## 📁 File System Setup

### Directory Structure
```bash
sudo mkdir -p /opt/paperqa-mcp
sudo mkdir -p /var/lib/paperqa/papers
sudo mkdir -p /var/log/paperqa-mcp
sudo mkdir -p /etc/paperqa-mcp

# Set ownership
sudo useradd -r -s /bin/false paperqa
sudo chown -R paperqa:paperqa /opt/paperqa-mcp
sudo chown -R paperqa:paperqa /var/lib/paperqa
sudo chown -R paperqa:paperqa /var/log/paperqa-mcp
```

### Deploy Server
```bash
# Copy server file
sudo cp paperqa_mcp_server.py /opt/paperqa-mcp/
sudo chown paperqa:paperqa /opt/paperqa-mcp/paperqa_mcp_server.py
sudo chmod 755 /opt/paperqa-mcp/paperqa_mcp_server.py
```

## 🔧 Claude Desktop Configuration

### System-wide Configuration
For multi-user systems, create `/etc/claude/mcp.json`:
```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "/opt/paperqa-mcp/paperqa_mcp_server.py",
      "args": [],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "VOYAGE_API_KEY": "${VOYAGE_API_KEY}",
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "PAPERQA_PAPERS_DIR": "/var/lib/paperqa/papers",
        "PAPERQA_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### User Configuration
For single-user deployment (`~/.claude/mcp.json`):
```json
{
  "mcpServers": {
    "paperqa-academic": {
      "command": "python3",
      "args": ["/path/to/paperqa_mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "VOYAGE_API_KEY": "${VOYAGE_API_KEY}",
        "GEMINI_API_KEY": "${GEMINI_API_KEY}"
      }
    }
  }
}
```

## 📊 Monitoring & Logging

### Log Configuration

Update `paperqa_mcp_server.py` logging for production:
```python
import logging
from logging.handlers import RotatingFileHandler

# Production logging setup
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# File handler with rotation
file_handler = RotatingFileHandler(
    '/var/log/paperqa-mcp/server.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(log_formatter)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
```

### Health Monitoring

Create `/opt/paperqa-mcp/health_check.py`:
```python
#!/usr/bin/env python3
"""Health check script for PaperQA2 MCP Server"""
import asyncio
import sys
import time
import subprocess
from pathlib import Path

async def health_check():
    """Perform health check of the MCP server"""
    try:
        # Check server imports
        sys.path.append('/opt/paperqa-mcp')
        from paperqa_mcp_server import server, settings, get_library_status
        
        # Check server status
        status = await get_library_status()
        
        # Check disk space
        papers_dir = Path('/var/lib/paperqa/papers')
        disk_usage = sum(f.stat().st_size for f in papers_dir.glob('**/*') if f.is_file())
        
        print(f"✅ Server healthy")
        print(f"📁 Disk usage: {disk_usage / 1024 / 1024:.1f} MB")
        print(f"⚙️  Embedding model: {settings.embedding}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(health_check())
    sys.exit(0 if success else 1)
```

### Monitoring Scripts

Create monitoring cron job (`/etc/cron.d/paperqa-mcp`):
```bash
# Health check every 15 minutes
*/15 * * * * paperqa /usr/bin/python3 /opt/paperqa-mcp/health_check.py >> /var/log/paperqa-mcp/health.log 2>&1

# Log rotation check daily
0 2 * * * root /usr/sbin/logrotate /etc/logrotate.d/paperqa-mcp
```

## 🔄 Backup & Recovery

### Document Backup
```bash
#!/bin/bash
# /opt/paperqa-mcp/backup.sh

BACKUP_DIR="/backup/paperqa-mcp"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup papers directory
tar -czf "$BACKUP_DIR/$DATE/papers.tar.gz" -C /var/lib/paperqa papers/

# Backup configuration
cp -r /etc/paperqa-mcp "$BACKUP_DIR/$DATE/"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +

echo "✅ Backup completed: $BACKUP_DIR/$DATE"
```

### Recovery Procedure
```bash
#!/bin/bash
# /opt/paperqa-mcp/restore.sh

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls /backup/paperqa-mcp/
    exit 1
fi

BACKUP_PATH="/backup/paperqa-mcp/$BACKUP_DATE"

# Stop service if running
systemctl stop paperqa-mcp 2>/dev/null || true

# Restore papers
tar -xzf "$BACKUP_PATH/papers.tar.gz" -C /var/lib/paperqa/

# Restore configuration  
cp -r "$BACKUP_PATH/paperqa-mcp" /etc/

# Set permissions
chown -R paperqa:paperqa /var/lib/paperqa
chmod -R 640 /etc/paperqa-mcp

echo "✅ Recovery completed from $BACKUP_DATE"
```

## 🚦 Performance Tuning

### Embedding Model Selection

**For cost optimization:**
```python
# Use Voyage AI (6.5x cheaper than OpenAI)
settings = Settings(
    embedding="voyage-ai/voyage-3-lite",
    llm="gpt-4o-2024-11-20"
)
```

**For maximum accuracy:**
```python
# Use Gemini (highest MTEB scores)
settings = Settings(
    embedding="gemini/gemini-embedding-001", 
    llm="gpt-4o-2024-11-20"
)
```

### Concurrent Request Limits
```python
# Adjust based on your API rate limits
settings.answer.max_concurrent_requests = 3  # For higher-tier API plans
settings.answer.evidence_k = 8  # Balance between quality and cost
```

### Memory Optimization
```python
# For large document libraries
import gc
import asyncio

async def periodic_cleanup():
    """Periodic memory cleanup"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        gc.collect()
        logger.debug("Memory cleanup completed")

# Start cleanup task
asyncio.create_task(periodic_cleanup())
```

## 🛡️ Security Hardening

### API Key Rotation
```bash
#!/bin/bash
# /opt/paperqa-mcp/rotate_keys.sh

NEW_OPENAI_KEY=$1
NEW_VOYAGE_KEY=$2

if [ -z "$NEW_OPENAI_KEY" ] || [ -z "$NEW_VOYAGE_KEY" ]; then
    echo "Usage: $0 <new_openai_key> <new_voyage_key>"
    exit 1
fi

# Update environment file
sed -i "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$NEW_OPENAI_KEY/" /etc/paperqa-mcp/environment
sed -i "s/VOYAGE_API_KEY=.*/VOYAGE_API_KEY=$NEW_VOYAGE_KEY/" /etc/paperqa-mcp/environment

# Restart service
systemctl restart paperqa-mcp

echo "✅ API keys rotated successfully"
```

### Network Security
```bash
# Firewall rules (if running remote server)
sudo ufw allow ssh
sudo ufw allow from 10.0.0.0/8 to any port 8000  # Internal network only
sudo ufw --force enable
```

### File Permissions
```bash
# Secure all sensitive files
chmod 600 /etc/paperqa-mcp/environment
chmod 640 /etc/paperqa-mcp/mcp.json
chmod 755 /opt/paperqa-mcp/paperqa_mcp_server.py
chmod 750 /opt/paperqa-mcp/health_check.py
```

## 📈 Scaling Considerations

### Horizontal Scaling
For multiple users, deploy separate instances:
```bash
# User-specific deployments
/opt/paperqa-mcp/user1/
/opt/paperqa-mcp/user2/
/var/lib/paperqa/user1/papers/
/var/lib/paperqa/user2/papers/
```

### Resource Planning
- **10 users**: 8GB RAM, 50GB storage
- **50 users**: 32GB RAM, 250GB storage  
- **API costs**: ~$0.10-0.50 per research session

### Load Balancing
For high availability, use nginx to balance multiple server instances:
```nginx
upstream paperqa_mcp {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location / {
        proxy_pass http://paperqa_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔍 Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check Python environment
python3 -c "from paperqa import Settings; print('PaperQA2 OK')"
python3 -c "from mcp.server.fastmcp import FastMCP; print('FastMCP OK')"

# Check API keys
echo $OPENAI_API_KEY | cut -c1-8
```

**Slow responses:**
```bash
# Check API quotas and model performance
tail -f /var/log/paperqa-mcp/server.log | grep "cost\|time"
```

**Memory issues:**
```bash
# Monitor memory usage
ps aux | grep paperqa_mcp_server.py
free -h
```

### Debug Mode
Set environment variable for detailed logging:
```bash
export PAPERQA_LOG_LEVEL=DEBUG
```

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- **Weekly**: Check disk space and log rotation
- **Monthly**: Update dependencies and rotate API keys  
- **Quarterly**: Performance review and optimization

### Upgrade Procedure
```bash
# Backup current installation
./backup.sh

# Update dependencies
pip install --upgrade paper-qa mcp

# Test with health check
python3 /opt/paperqa-mcp/health_check.py

# Restart service
systemctl restart paperqa-mcp
```

---

**Production deployment is now complete! Your PaperQA2 MCP Server is ready for PhD-level academic research workflows.**