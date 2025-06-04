# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

PT5 S3 Tool is a Python tool for efficiently transferring Imaging FlowCytobot (IFCB) data files to and from Amazon S3. IFCB is an automated submersible flow cytometer that provides continuous, high-resolution measurements of phytoplankton and microzooplankton abundance and composition. The tool is designed for high-performance concurrent transfers with optimized connection pooling, batched operations, and progress tracking.

## Key Commands

### Installation
```bash
pip install -r requirements.txt
```

### Running the Tool
```bash
# Use environment variables (defaults from .env file)
python pt5_s3_tool.py

# Upload from local to S3
python pt5_s3_tool.py --source /path/to/files --destination s3://bucket/prefix --recursive

# Download from S3 to local  
python pt5_s3_tool.py --source s3://bucket/prefix --destination /local/path --recursive

# Delete files from S3
python pt5_s3_tool.py --destination s3://bucket/prefix --delete --recursive

# Dry run mode
python pt5_s3_tool.py --source /path/to/files --destination s3://bucket/prefix --dry-run
```

### Code Style Enforcement
The codebase follows PEP 8 guidelines with:
- Maximum line length: 79 characters
- Maximum function length: 35 lines
- Docstrings required for all functions

Currently, no automated linting or testing tools are configured. When adding code, ensure it follows these guidelines manually.

## Architecture

### Core Components

1. **Main Entry Point** (`main()` in pt5_s3_tool.py:1275)
   - Parses command line arguments
   - Validates AWS credentials
   - Routes to appropriate operation (upload/download/list/delete)

2. **Operation Modes**
   - **Upload**: Transfers local files to S3 (`upload_files()` at line 517)
   - **Download**: Transfers S3 objects to local filesystem (`download_files()` at line 853)
   - **List**: Lists S3 bucket contents (`list_bucket_contents()` at line 955)
   - **Delete**: Bulk deletes S3 objects (`delete_files()` at line 1115)

3. **Concurrency Model**
   - Uses ThreadPoolExecutor with up to 32 workers
   - Batched submission of 1000 files at a time
   - Pre-computed paths for performance
   - Connection pool of 100 connections

4. **Configuration**
   - Environment variables loaded from `.env` file via python-dotenv
   - AWS credentials: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - Default paths: `IFCB_DATA_DIR` (local), `AWS_UPLOAD_URL` (S3)
   - Command-line arguments always override environment defaults

5. **Error Handling**
   - Automatic retry on failures (3 attempts)
   - Comprehensive logging with colorized output
   - Graceful handling of missing files and network issues

## Key Design Patterns

1. **S3 URI Parsing**: The tool accepts S3 locations in `s3://bucket/prefix` format and automatically parses them into bucket and prefix components

2. **Progress Tracking**: Uses tqdm for real-time progress bars during:
   - File submission to thread pool
   - Actual transfer operations
   - Summary statistics after completion

3. **Batch Operations**: 
   - Downloads and uploads are batched for efficiency
   - S3 delete operations use the bulk delete API (1000 objects per request)

4. **Resource Management**:
   - Proper cleanup of ThreadPoolExecutor contexts
   - File handles closed after operations
   - Connection pooling to prevent resource exhaustion

## Environment Setup

Create a `.env` file in the project root with:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_UPLOAD_URL=s3://your-bucket/path
IFCB_DATA_DIR=/path/to/ifcb/data
```

These environment variables serve as defaults when no command-line arguments are provided.