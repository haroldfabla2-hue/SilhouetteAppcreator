# CI/CD Pipeline Configuration Guide

## Overview

This repository contains a comprehensive CI/CD pipeline for MCP Core Superior, consisting of 10 automated workflows that handle everything from testing to deployment and monitoring.

## Workflows Overview

### 1. Automated Testing (`01-automated-testing.yml`)
- **Triggers**: Push to main/develop, Pull Requests, Daily at 2 AM
- **Components**:
  - Unit tests across Python 3.9, 3.10, 3.11
  - Integration tests with PostgreSQL and Redis
  - Performance and benchmark testing
  - Concurrency testing for multi-agent scenarios
- **Services**: PostgreSQL 15, Redis 7
- **Artifacts**: Test reports, coverage reports, performance baselines

### 2. Code Quality & Security (`02-code-quality.yml`)
- **Triggers**: Push to main/develop, Pull Requests
- **Tools**:
  - Flake8, Black, isort for code formatting
  - MyPy for type checking
  - Bandit, Semgrep, Safety for security scanning
  - CPD for code duplication detection
  - Complexity analysis with Radon
- **Outputs**: Quality reports, SARIF files for GitHub Security tab

### 3. Docker Build and Push (`03-docker-build.yml`)
- **Triggers**: Push to main/develop, Version tags
- **Features**:
  - Multi-platform builds (amd64, arm64)
  - Security scanning with Trivy and Grype
  - Push to GitHub Container Registry
  - Optional push to Docker Hub
  - Legacy format image support
- **Security**: SBOM generation, provenance tracking

### 4. Automated Deployment (`04-automated-deployment.yml`)
- **Triggers**: Push to main/develop, Version tags, Manual dispatch
- **Environments**: Staging, Production
- **Features**:
  - Database migrations with Alembic
  - Zero-downtime deployments
  - AWS ECS, Google Cloud Run, Azure Container Instances support
  - Health checks and smoke tests
  - Slack/Teams notifications
- **Security**: Deployment permissions validation

### 5. Performance Regression Testing (`05-performance-regression.yml`)
- **Triggers**: Push to main, Pull Requests, Weekly
- **Components**:
  - Benchmark testing with pytest-benchmark
  - Load testing with Locust
  - Memory profiling with memory_profiler
  - Baseline comparison and regression detection
- **Outputs**: Performance reports, HTML reports, trend analysis

### 6. Security Vulnerability Scanning (`06-security-scanning.yml`)
- **Triggers**: Push to main/develop, Pull Requests, Daily
- **Tools**:
  - Safety, pip-audit for dependency vulnerabilities
  - Bandit, Semgrep for static analysis
  - Trivy, Grype for container scanning
  - Docker Bench for Security
  - License compatibility checking
- **Outputs**: Security dashboards, SARIF reports, GitHub Security tab integration

### 7. Documentation Generation (`07-documentation.yml`)
- **Triggers**: Push to main/develop, Pull Requests, Manual
- **Features**:
  - API documentation with pdoc3 and Sphinx
  - Agent-specific documentation
  - Deployment and development guides
  - MkDocs site generation
  - GitHub Pages, Netlify, Vercel deployment
- **Validation**: Docstring coverage, Markdown link checking

### 8. Backup and Disaster Recovery (`08-backup-disaster-recovery.yml`)
- **Triggers**: Daily at 2 AM, Manual dispatch
- **Components**:
  - Database backups with pg_dump
  - Configuration backups
  - Code snapshots
  - S3 storage with automated cleanup
  - Disaster recovery simulation
- **Retention**: 30 days for regular backups, 90 days for archives

### 9. Monitoring and Alerting (`09-monitoring-alerts.yml`)
- **Triggers**: Push to main/develop, Every 6 hours, Manual
- **Features**:
  - Prometheus configuration
  - Grafana dashboards
  - AlertManager setup
  - APM instrumentation (OpenTelemetry, Jaeger, DataDog)
  - Custom metrics implementation
- **Alerts**: Service downtime, response time, error rates, resource usage

### 10. Automated Rollback (`10-rollback-automation.yml`)
- **Triggers**: Health check failures, Manual dispatch
- **Features**:
  - Comprehensive health checks
  - Emergency backup creation
  - Automated rollback execution
  - Zero-downtime rollback procedures
  - Post-rollback verification
- **Triggers**: Critical health issues, slow response times, database failures

## Required Secrets and Configuration

### GitHub Secrets

Configure these secrets in your GitHub repository settings:

#### Deployment Secrets
```bash
# Production Environment
PRODUCTION_HOST=your-production-host.com
PRODUCTION_USER=deploy
PRODUCTION_DEPLOYMENT_KEY=-----BEGIN RSA PRIVATE KEY-----...
PRODUCTION_DB_URL=postgresql://user:pass@host:5432/db
PRODUCTION_REDIS_URL=redis://host:6379
PRODUCTION_JWT_SECRET=your-super-secret-jwt-key
PRODUCTION_CONTEXTFORGE_URL=http://contextforge:8001

# Staging Environment  
STAGING_HOST=your-staging-host.com
STAGING_USER=deploy
STAGING_DEPLOYMENT_KEY=-----BEGIN RSA PRIVATE KEY-----...
STAGING_DB_URL=postgresql://user:pass@host:5432/staging_db
STAGING_REDIS_URL=redis://host:6379
STAGING_JWT_SECRET=your-staging-jwt-secret
STAGING_CONTEXTFORGE_URL=http://contextforge-staging:8001
```

#### Cloud Platform Secrets
```bash
# AWS
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-west-2

# Google Cloud
GCP_SERVICE_ACCOUNT_KEY=base64-encoded-service-account-key
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1

# Azure
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_RESOURCE_GROUP=your-resource-group

# Docker Hub
DOCKERHUB_USERNAME=your-dockerhub-username
DOCKERHUB_TOKEN=your-dockerhub-token

# Monitoring
GRAFANA_URL=https://your-grafana-instance.com
GRAFANA_API_KEY=your-grafana-api-key
APM_ENDPOINT=https://your-apm-endpoint.com
APM_API_KEY=your-apm-api-key
DATADOG_API_KEY=your-datadog-api-key
DATADOG_APP_KEY=your-datadog-app-key

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...

# Documentation Hosting
NETLIFY_AUTH_TOKEN=your-netlify-token
NETLIFY_SITE_ID=your-netlify-site-id
VERCEL_TOKEN=your-vercel-token

# Backup Storage
STAGING_BACKUP_S3=your-staging-backup-bucket
PRODUCTION_BACKUP_S3=your-production-backup-bucket
```

### Environment Variables

Some workflows use these environment variables:

```bash
# Docker Registry
REGISTRY=ghcr.io
IMAGE_NAME=${{ github.repository }}

# Python Version
PYTHON_VERSION=3.11

# Kubernetes (Optional)
KUBECONFIG_DATA=base64-encoded-kubeconfig
```

## Workflow Execution Order

The workflows are designed to execute in the following order:

1. **Code Quality** → **Testing** → **Security** (parallel for PRs)
2. **Docker Build** (after quality gates pass)
3. **Documentation Generation** (after build succeeds)
4. **Deployment** (to staging → production with approvals)
5. **Performance Testing** (after deployment)
6. **Monitoring Setup** (continuous)
7. **Backup** (scheduled daily)
8. **Rollback** (triggered by health checks)

## Quality Gates

### Required to Merge
- ✅ All tests passing
- ✅ Code quality checks (flake8, mypy, bandit)
- ✅ Security scans (no critical vulnerabilities)
- ✅ Documentation generation
- ✅ Docker build and security scan

### Required for Production Deployment
- ✅ Staging deployment successful
- ✅ Performance regression tests pass
- ✅ Security scan results acceptable
- ✅ Manual approval from designated reviewers

### Automatic Rollback Triggers
- Service health check failures
- Database connectivity issues
- Response time > 2 seconds
- Error rate > 10%
- Memory usage > 1GB
- CPU usage > 80%

## Getting Started

### For Developers

1. **Fork/Clone** the repository
2. **Create a feature branch** from `develop`
3. **Make your changes** with tests
4. **Push to trigger CI/CD** pipeline
5. **Wait for all checks** to pass
6. **Create Pull Request** to `develop` or `main`

### For DevOps Engineers

1. **Configure GitHub Secrets** as listed above
2. **Set up infrastructure** (PostgreSQL, Redis, hosting)
3. **Configure monitoring** (Grafana, Prometheus, APM)
4. **Test deployment pipeline** in staging
5. **Approve production deployments** as needed

### For Release Management

1. **Tag releases** with semantic versioning: `v1.0.0`
2. **Monitor deployments** via Slack/Teams notifications
3. **Review performance metrics** after each deployment
4. **Handle rollbacks** if issues are detected
5. **Update documentation** for major releases

## Troubleshooting

### Common Issues

#### Tests Failing
- Check test reports in GitHub Actions artifacts
- Verify database and Redis connectivity
- Review code quality issues
- Check for dependency conflicts

#### Deployment Failures
- Verify environment variables are set correctly
- Check SSH keys and permissions
- Ensure target hosts are accessible
- Review deployment logs

#### Security Scan Issues
- Update vulnerable dependencies
- Review false positives
- Configure ignore rules if needed
- Address critical vulnerabilities immediately

#### Performance Regressions
- Review benchmark comparison reports
- Investigate memory leaks
- Check database query performance
- Optimize concurrent task limits

### Getting Help

- Check workflow logs in GitHub Actions
- Review deployment and rollback reports
- Monitor Slack/Teams notifications
- Consult monitoring dashboards
- Check backup and disaster recovery logs

## Best Practices

### Code Quality
- Write tests for new features
- Follow PEP 8 style guidelines
- Add docstrings to all public functions
- Use type hints where possible
- Keep cyclomatic complexity low

### Security
- Never commit secrets to the repository
- Use environment variables for configuration
- Regularly update dependencies
- Monitor for new vulnerabilities
- Follow principle of least privilege

### Deployment
- Deploy to staging first
- Use blue-green or rolling deployments
- Always have a rollback plan
- Monitor deployments closely
- Keep infrastructure as code

### Monitoring
- Set up comprehensive alerts
- Monitor key performance indicators
- Track error rates and response times
- Review logs regularly
- Test alert notifications

## Maintenance

### Regular Tasks
- **Weekly**: Review performance reports
- **Monthly**: Update dependencies
- **Quarterly**: Review and update security policies
- **Annually**: Disaster recovery testing

### Keeping Up to Date
- Monitor security advisories
- Update CI/CD configuration as needed
- Review and optimize performance
- Update documentation regularly
- Test rollback procedures

This CI/CD pipeline provides a robust, secure, and automated deployment process for MCP Core Superior, ensuring high quality, security, and reliability in production environments.
