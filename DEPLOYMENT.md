# CloudNexus API - AWS Deployment Checklist

This document provides deployment instructions for the CloudNexus API on AWS Lambda with RDS and S3 integration.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.9+ runtime
- Access to create Lambda functions, RDS instances, and S3 buckets

---

## 1. VPC Security Groups

### Lambda Security Group

Create a security group for the Lambda function:

| Type     | Protocol | Port Range | Source/Destination    | Description            |
|----------|----------|------------|------------------------|------------------------|
| Outbound | TCP      | 5432       | RDS Security Group    | PostgreSQL access      |
| Outbound | TCP      | 443        | 0.0.0.0/0             | HTTPS (S3, AWS APIs)   |

### RDS Security Group

Configure the RDS security group to allow Lambda access:

| Type    | Protocol | Port Range | Source                  | Description            |
|---------|----------|------------|-------------------------|------------------------|
| Inbound | TCP      | 5432       | Lambda Security Group   | PostgreSQL from Lambda |

> **Important**: Place Lambda in the same VPC and subnets as RDS for connectivity.

---

## 2. IAM Role & Policies

### Lambda Execution Role

Create an IAM role with the following policies:

#### Basic Execution (Required)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

#### VPC Access (Required for RDS)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
                "ec2:AssignPrivateIpAddresses",
                "ec2:UnassignPrivateIpAddresses"
            ],
            "Resource": "*"
        }
    ]
}
```

#### S3 Access
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR_BUCKET_NAME",
                "arn:aws:s3:::YOUR_BUCKET_NAME/*"
            ]
        }
    ]
}
```

---

## 3. Environment Variables

Configure these environment variables in Lambda:

| Variable      | Description                    | Example                          |
|---------------|--------------------------------|----------------------------------|
| `DB_HOST`     | RDS endpoint                   | `mydb.xxxxx.us-east-1.rds.amazonaws.com` |
| `DB_PORT`     | Database port                  | `5432`                          |
| `DB_NAME`     | Database name                  | `cloudnexus`                    |
| `DB_USER`     | Database username              | `api_user`                      |
| `DB_PASS`     | Database password              | `(use Secrets Manager)`         |
| `S3_BUCKET`   | S3 bucket name                 | `cloudnexus-storage`            |
| `AWS_REGION`  | AWS region                     | `us-east-1`                     |
| `LOG_LEVEL`   | Logging level                  | `INFO`                          |
| `CORS_ORIGINS`| Allowed origins (comma-sep)    | `*` or `https://app.example.com`|

> **Security Tip**: Use AWS Secrets Manager for `DB_PASS` in production.

---

## 4. Lambda Configuration

### Recommended Settings

| Setting              | Value        | Reason                              |
|----------------------|--------------|-------------------------------------|
| Runtime              | Python 3.11  | Latest stable Python runtime        |
| Memory               | 512 MB       | Balance of cost and performance     |
| Timeout              | 30 seconds   | Allow time for cold starts + queries|
| Handler              | `main.handler` | Mangum handler location           |
| Architecture         | arm64        | Better price-performance            |

### Deployment Package

```bash
# Install dependencies to package directory
pip install -r requirements.txt -t package/

# Copy application files
cp main.py database.py utils.py package/

# Create deployment ZIP
cd package && zip -r ../deployment.zip .
```

---

## 5. RDS Configuration

### Database Setup

```sql
-- Create database
CREATE DATABASE cloudnexus;

-- Create application user
CREATE USER api_user WITH ENCRYPTED PASSWORD 'your_secure_password';

-- Grant privileges
GRANT CONNECT ON DATABASE cloudnexus TO api_user;
GRANT USAGE ON SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO api_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO api_user;
```

### Connection Recommendations

- Enable **RDS Proxy** for connection pooling in high-traffic scenarios
- Use **Multi-AZ** deployment for production availability
- Enable **encryption at rest** for compliance

---

## 6. S3 Bucket Configuration

### Bucket Policy (Optional - for public read access)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/uploads/*"
        }
    ]
}
```

### CORS Configuration

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

---

## 7. API Gateway Setup

### Configuration

1. Create HTTP API (recommended) or REST API
2. Configure Lambda integration with `main.handler`
3. Enable CORS through API Gateway settings
4. Set up custom domain (optional)

### Routes

| Method | Route              | Integration        |
|--------|--------------------|--------------------|
| ANY    | `/{proxy+}`        | Lambda             |
| GET    | `/health`          | Lambda             |

---

## 8. Monitoring & Alerts

### CloudWatch Alarms (Recommended)

- Lambda errors > 1% of invocations
- Lambda duration > 10 seconds (p95)
- RDS CPU > 80%
- RDS free storage < 20%

### Log Insights Query

```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

---

## Quick Deployment Commands

```bash
# 1. Package the application
./package.sh  # or manual steps above

# 2. Create/Update Lambda function
aws lambda update-function-code \
    --function-name cloudnexus-api \
    --zip-file fileb://deployment.zip

# 3. Set environment variables
aws lambda update-function-configuration \
    --function-name cloudnexus-api \
    --environment "Variables={DB_HOST=xxx,DB_PORT=5432,...}"

# 4. Test the deployment
curl https://your-api-gateway-url/health
```

---

## Troubleshooting

| Issue                    | Cause                          | Solution                        |
|--------------------------|--------------------------------|---------------------------------|
| Connection timeout       | VPC misconfiguration           | Check security groups, subnets  |
| Import errors            | Missing dependencies           | Verify requirements.txt package |
| Permission denied (S3)   | IAM policy missing             | Add S3 permissions to role      |
| Cold start > 10s         | VPC ENI creation               | Use provisioned concurrency     |
