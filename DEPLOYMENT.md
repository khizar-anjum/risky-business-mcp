# Deployment Guide for Risky Business MCP Server

This guide covers various deployment methods for your GitHub Repository Search MCP Server.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for version control)
- Docker (optional, for containerized deployment)

## Method 1: Local Development Installation

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd risky-business-mcp
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Or install just the runtime dependencies
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp config.env.example .env
# Edit .env with your GitHub token and other settings
```

### 5. Run the Server
```bash
python main.py
```

## Method 2: Using Makefile (Recommended for Development)

### 1. Setup Development Environment
```bash
make setup
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Run Commands
```bash
make help          # Show all available commands
make run           # Run the MCP server
make test          # Run tests
make lint          # Run linting checks
make format        # Format code
make build         # Build the package
```

## Method 3: Docker Deployment

### 1. Build Docker Image
```bash
docker build -t risky-business-mcp .
```

### 2. Run Container
```bash
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_token_here \
  risky-business-mcp
```

### 3. Using Docker Compose
```bash
# Copy and configure environment
cp config.env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# View logs
docker-compose logs -f mcp-server

# Stop services
docker-compose down
```

## Method 4: Production Deployment

### 1. Build Package
```bash
make build
```

### 2. Install on Production Server
```bash
pip install dist/risky_business_mcp-0.1.0-py3-none-any.whl
```

### 3. Create Systemd Service
Create `/etc/systemd/system/risky-business-mcp.service`:

```ini
[Unit]
Description=Risky Business MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/risky-business-mcp
Environment=PATH=/opt/risky-business-mcp/venv/bin
ExecStart=/opt/risky-business-mcp/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Service
```bash
sudo systemctl enable risky-business-mcp
sudo systemctl start risky-business-mcp
sudo systemctl status risky-business-mcp
```

## Method 5: Cloud Deployment

### AWS EC2
1. Launch EC2 instance with Ubuntu/Debian
2. Install Python and dependencies
3. Clone repository and follow local installation steps
4. Use systemd service for auto-restart

### Google Cloud Run
1. Build and push Docker image to Google Container Registry
2. Deploy to Cloud Run with environment variables
3. Set up GitHub token as secret

### Heroku
1. Create `Procfile`:
   ```
   web: python main.py
   ```
2. Deploy using Heroku CLI or GitHub integration

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | None | Yes (for higher rate limits) |
| `HOST` | Server host | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |
| `DEBUG` | Debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |

## Health Checks

The server includes health check endpoints:
- `/health` - Basic health status
- `/ready` - Readiness check
- `/live` - Liveness check

## Monitoring and Logging

### Log Files
- Application logs: `logs/mcp-server.log`
- Access logs: `logs/access.log`
- Error logs: `logs/error.log`

### Metrics
- Request count
- Response time
- Error rate
- GitHub API rate limit usage

## Security Considerations

1. **GitHub Token**: Store securely, never commit to version control
2. **Network Access**: Restrict to necessary IP ranges
3. **Rate Limiting**: Implement request throttling
4. **Input Validation**: All user inputs are validated
5. **HTTPS**: Use TLS in production

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Port Already in Use**: Change port in configuration
3. **GitHub API Rate Limits**: Add GitHub token to increase limits
4. **Permission Denied**: Check file permissions and user access

### Debug Mode
```bash
export DEBUG=true
python main.py
```

### Log Analysis
```bash
tail -f logs/mcp-server.log
grep "ERROR" logs/mcp-server.log
```

## Performance Optimization

1. **Connection Pooling**: aiohttp handles this automatically
2. **Caching**: Implement Redis for frequently searched queries
3. **Async Processing**: Server is fully async for better performance
4. **Resource Limits**: Monitor memory and CPU usage

## Backup and Recovery

1. **Configuration**: Backup `.env` and configuration files
2. **Logs**: Archive logs regularly
3. **Database**: If using persistent storage, backup data
4. **Code**: Use Git for version control

## Updates and Maintenance

1. **Regular Updates**: Keep dependencies updated
2. **Security Patches**: Monitor for security vulnerabilities
3. **Backup Before Updates**: Always backup before major changes
4. **Rollback Plan**: Have rollback procedures ready

## Support

For issues and questions:
1. Check the logs for error messages
2. Review this deployment guide
3. Check GitHub issues for known problems
4. Create new issue with detailed error information
