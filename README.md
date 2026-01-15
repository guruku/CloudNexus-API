# CloudNexus API

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)

A robust Python Backend API for mobile applications, built with FastAPI and optimized for AWS Lambda deployment.

## Features

- 🚀 **FastAPI + Mangum** - High-performance async API with Lambda compatibility
- 🗄️ **RDS Integration** - PostgreSQL/MySQL via SQLAlchemy with connection pooling
- 📦 **S3 Storage** - File upload and backup functionality
- 🔄 **Cold Start Optimized** - Retry logic with exponential backoff
- 📊 **CloudWatch Logging** - Structured logs for monitoring
- 🔒 **CORS Enabled** - Ready for mobile/web clients

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with RDS connectivity test |
| GET | `/items` | Fetch all tasks (pagination & filtering) |
| POST | `/items` | Create a new task |
| GET | `/items/{id}` | Get specific task by ID |
| POST | `/upload` | Upload file to S3 bucket |
| POST | `/backup` | Backup tasks table to S3 |

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL database (local or RDS)
- AWS credentials (for S3 operations)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/cloudnexus-api.git
cd cloudnexus-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or export variables:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=cloudnexus
export DB_USER=postgres
export DB_PASS=your_password
export S3_BUCKET=your-bucket-name
export AWS_REGION=us-east-1
```

### Run Locally

```bash
# Start development server
python main.py

# Or with uvicorn
uvicorn main:app --reload --port 8000
```

Access the API documentation at `http://localhost:8000/docs`

## Project Structure

```
cloudnexus-api/
├── main.py           # FastAPI app & routes
├── database.py       # SQLAlchemy models & session
├── utils.py          # S3 & logging utilities
├── requirements.txt  # Dependencies
├── DEPLOYMENT.md     # AWS deployment guide
└── .gitignore
```

## AWS Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on:

- VPC & Security Groups configuration
- IAM roles and policies
- Lambda function setup
- API Gateway integration

### Quick Deploy with SAM

```bash
sam build
sam deploy --guided
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Lambda Adapter | Mangum |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL (RDS) |
| Storage | Amazon S3 |
| AWS SDK | boto3 |

## License

MIT License - see [LICENSE](LICENSE) for details.
