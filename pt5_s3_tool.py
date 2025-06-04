#!/usr/bin/env python3
"""
PT5 S3 Tool - A tool for copying files between local and S3 locations.

This script is specifically designed for the GCOOS ORION project to manage and 
transfer IFCB (Imaging FlowCytobot) data files to/from Amazon S3. IFCB is an 
automated submersible flow cytometer that provides continuous, high-resolution
measurements of phytoplankton and microzooplankton abundance and composition.

Features:
    - AWS credentials validation
    - Support for IFCB data file transfers
    - Recursive directory operations
    - Colorized console output
    - Concurrent file transfers (up to 32 workers)
    - Connection pool optimization (100 connections)
    - Automatic retry on failures (3 attempts)
    - Batched file submission (1000 files per batch)
    - Pre-computed S3 keys for improved performance
    - Overall progress tracking with tqdm
    - Detailed summary report with:
        * Total files processed
        * Total data transferred
        * Transfer duration
        * Average transfer rate
        * Files processed per second
    - Dry-run mode for testing
    - Environment variable configuration (automatically used when no args provided)
    - Detailed logging
    - File filtering options
    - Fast bulk deletion of S3 objects
    - Simplified S3 URI handling

Environment Variables:
    - IFCB_DATA_DIR: Default source directory for uploads
    - AWS_UPLOAD_URL: Default S3 destination (s3://bucket/prefix)
    Note: Environment variables are only used as defaults when no command-line
    arguments are provided. Command-line arguments always take precedence.

Usage Examples:
    # Download from S3 to local
    python pt5_s3_tool.py --source s3://bucket-name/prefix \
        --destination /local/path

    # Upload from local to S3
    python pt5_s3_tool.py --source /path/to/files \
        --destination s3://bucket-name/prefix

    # Copy with recursive option
    python pt5_s3_tool.py --source s3://bucket-name/prefix \
        --destination /local/path --recursive

    # Copy with file filter
    python pt5_s3_tool.py --source s3://bucket-name/prefix \
        --destination /local/path --filter '*.jpg'

    # Dry run to preview changes
    python pt5_s3_tool.py --source s3://bucket-name/prefix \
        --destination /local/path --dry-run

    # Delete files from S3 (using --source)
    python pt5_s3_tool.py --source s3://bucket-name/prefix \
        --delete [--recursive] [--filter '*.jpg']

    # Delete files from S3 (using --destination)
    python pt5_s3_tool.py --destination s3://bucket-name/prefix \
        --delete [--recursive] [--filter '*.jpg']

    # Dry run delete
    python pt5_s3_tool.py --source s3://bucket-name/prefix \
        --delete --dry-run

    # Using environment variables (no arguments needed)
    python pt5_s3_tool.py

System Requirements:
    - Python 3.6 or higher
    - Sufficient system resources for concurrent processing
    - Recommended: 4+ CPU cores and 8GB+ RAM for large file sets

Author: robertdcurrier@tamu.edu
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional, List, Tuple, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from colorama import Fore, Style, init
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress boto3's INFO messages about finding credentials
logging.getLogger('boto3.credentials').setLevel(logging.WARNING)
logging.getLogger('botocore.credentials').setLevel(logging.WARNING)

def validate_aws_credentials() -> bool:
    """Validate AWS credentials by making a simple API call."""
    try:
        session = boto3.Session()
        s3 = session.client('s3')
        s3.list_buckets()
        logger.info(f"{Fore.GREEN}AWS credentials validated{Style.RESET_ALL}")
        return True
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error: AWS credentials validation failed: "
            f"{str(e)}{Style.RESET_ALL}"
        )
        return False

def get_default_source() -> Optional[str]:
    """Get the default source directory from environment variables."""
    ifcb_dir = os.getenv('IFCB_DATA_DIR')
    if ifcb_dir and os.path.exists(ifcb_dir):
        return ifcb_dir
    return None

def get_default_bucket() -> Optional[str]:
    """Get the default bucket from AWS_UPLOAD_URL environment variable."""
    upload_url = os.getenv('AWS_UPLOAD_URL', '')
    if upload_url.startswith('s3://'):
        # Extract bucket from s3://bucket/path format
        parts = upload_url[5:].split('/')
        return parts[0]
    return None

def get_default_prefix() -> str:
    """Get the default prefix from AWS_UPLOAD_URL environment variable."""
    upload_url = os.getenv('AWS_UPLOAD_URL', '')
    if upload_url.startswith('s3://'):
        # Extract path after bucket
        parts = upload_url[5:].split('/')
        if len(parts) > 1:
            return '/'.join(parts[1:])
    return ''

def setup_argparse() -> argparse.ArgumentParser:
    """Set up and return the argument parser with all required options."""
    default_source = get_default_source()
    default_bucket = get_default_bucket()
    default_prefix = get_default_prefix()
    
    # Construct default destination if both bucket and prefix are available
    default_destination = None
    if default_bucket:
        default_destination = f"s3://{default_bucket}"
        if default_prefix:
            default_destination += f"/{default_prefix}"

    parser = argparse.ArgumentParser(
        description='Copy files between local and S3 locations'
    )
    
    # Source/destination arguments
    parser.add_argument(
        '--source',
        help='Source location (local path or s3://bucket/prefix)',
        default=default_source
    )
    parser.add_argument(
        '--destination',
        help='Destination location (local path or s3://bucket/prefix)',
        default=default_destination
    )
    
    # Common options
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process directories recursively'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be transferred without actually transferring'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Only validate AWS credentials and exit'
    )
    
    # Download specific options
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing files when downloading'
    )
    parser.add_argument(
        '--filter',
        help='Filter pattern for files to process (e.g., "*.png")'
    )
    
    # Delete option
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete files at the S3 destination (only works with S3 URLs)'
    )
    
    return parser

def validate_args(args: argparse.Namespace) -> bool:
    """Validate command line arguments based on operation mode."""
    # Parse source if it's in s3:// format
    if args.source and args.source.startswith('s3://'):
        # Extract bucket and prefix from s3://bucket/prefix format
        s3_path = args.source[5:]  # Remove 's3://'
        parts = s3_path.split('/', 1)  # Split at first '/'
        
        # Set bucket and prefix from source
        args.bucket = parts[0]
        args.prefix = parts[1] if len(parts) > 1 else ''
        
        logger.info(
            f"{Fore.CYAN}Using source: {args.source} "
            f"(bucket: {args.bucket}, prefix: {args.prefix}){Style.RESET_ALL}"
        )
    # Parse destination if it's in s3:// format
    elif args.destination and args.destination.startswith('s3://'):
        # Extract bucket and prefix from s3://bucket/prefix format
        s3_path = args.destination[5:]  # Remove 's3://'
        parts = s3_path.split('/', 1)  # Split at first '/'
        
        # Set bucket and prefix from destination
        args.bucket = parts[0]
        args.prefix = parts[1] if len(parts) > 1 else ''
        
        logger.info(
            f"{Fore.CYAN}Using destination: {args.destination} "
            f"(bucket: {args.bucket}, prefix: {args.prefix}){Style.RESET_ALL}"
        )
    else:
        logger.error(
            f"{Fore.RED}Error: Either source or destination must be an S3 URL "
            f"(s3://bucket/prefix){Style.RESET_ALL}"
        )
        return False
        
    # Common validation for all operations
    if not args.bucket:
        logger.error(
            f"{Fore.RED}Error: S3 bucket not specified. "
            f"Use s3://bucket/prefix format for S3 locations{Style.RESET_ALL}"
        )
        return False
        
    # Validate local paths
    if args.source and not args.source.startswith('s3://'):
        if not os.path.exists(args.source):
            logger.error(
                f"{Fore.RED}Error: Source path does not exist: "
                f"{args.source}{Style.RESET_ALL}"
            )
            return False
            
    if args.destination and not args.destination.startswith('s3://'):
        try:
            os.makedirs(args.destination, exist_ok=True)
            logger.info(
                f"{Fore.CYAN}Created destination directory: "
                f"{args.destination}{Style.RESET_ALL}"
            )
        except Exception as e:
            logger.error(
                f"{Fore.RED}Error creating destination directory: "
                f"{args.destination} - {str(e)}{Style.RESET_ALL}"
            )
            return False
    
    return True

def get_files_to_upload(
    source: str, 
    recursive: bool = False
) -> List[Tuple[str, str]]:
    """
    Get list of files to upload and their S3 keys.
    
    Args:
        source: Source file or directory path
        recursive: Whether to include subdirectories
        
    Returns:
        List of tuples containing (local_path, s3_key)
    """
    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")
        
    if source_path.is_file():
        return [(str(source_path), source_path.name)]
    else:
        files = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in source_path.glob(pattern):
            if file_path.is_file():
                # Get relative path for S3 key
                rel_path = file_path.relative_to(source_path)
                files.append((str(file_path), str(rel_path)))
            
        return files

def upload_file(s3_client: boto3.client, local_path: str, bucket: str, 
                s3_key: str, dry_run: bool = False) -> bool:
    """
    Upload a single file to S3.
    
    Args:
        s3_client: Boto3 S3 client
        local_path: Local file path
        bucket: S3 bucket name
        s3_key: S3 key (path in bucket)
        dry_run: Whether to simulate upload
        
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        if dry_run:
            logger.info(f"{Fore.CYAN}Would upload: {local_path} -> "
                       f"s3://{bucket}/{s3_key}{Style.RESET_ALL}")
            return True
            
        logger.debug(
            f"{Fore.CYAN}Starting upload of {local_path}{Style.RESET_ALL}"
        )
        with open(local_path, 'rb') as f:
            s3_client.upload_fileobj(f, bucket, s3_key)
        logger.debug(
            f"{Fore.GREEN}Completed upload of {local_path}{Style.RESET_ALL}"
        )
        return True
        
    except Exception as e:
        logger.error(f"{Fore.RED}Error uploading {local_path}: {str(e)}"
                    f"{Style.RESET_ALL}")
        return False

def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def print_summary_report(
    total_files: int, 
    total_size: int, 
    start_time: float,
    operation: str = "transfer"
) -> None:
    """
    Print a summary report of the file transfer process.
    
    Args:
        total_files: Total number of files processed
        total_size: Total size of files in bytes
        start_time: Start time of process
        operation: Operation type (upload, download, etc.)
    """
    end_time = time.time()
    duration = end_time - start_time
    avg_rate = total_size / duration if duration > 0 else 0
    files_per_second = total_files / duration if duration > 0 else 0
    
    logger.info(
        f"\n{Fore.GREEN}{operation.capitalize()} Summary "
        f"Report:{Style.RESET_ALL}"
    )
    logger.info(f"{Fore.CYAN}Total Files:{Style.RESET_ALL} {total_files}")
    logger.info(
        f"{Fore.CYAN}Total Size:{Style.RESET_ALL} {format_size(total_size)}"
    )
    logger.info(
        f"{Fore.CYAN}Duration:{Style.RESET_ALL} {duration:.2f} seconds"
    )
    logger.info(
        f"{Fore.CYAN}Average Rate:{Style.RESET_ALL} {format_size(avg_rate)}/s"
    )
    logger.info(
        f"{Fore.CYAN}Files/Second:{Style.RESET_ALL} {files_per_second:.2f}"
    )

def configure_s3_client() -> boto3.client:
    """Configure and return an S3 client with optimized settings."""
    session = boto3.Session()
    config = Config(
        max_pool_connections=100,  # Increase connection pool size
        retries={'max_attempts': 3},  # Add retry configuration
        connect_timeout=5,  # Connection timeout in seconds
        read_timeout=60,    # Read timeout in seconds
        tcp_keepalive=True  # Enable TCP keepalive
    )
    return session.client('s3', config=config)

def prepare_upload_tasks(
    files: List[Tuple[str, str]], 
    prefix: str
) -> List[Tuple[str, str]]:
    """Prepare upload tasks by combining prefix with S3 keys."""
    upload_tasks = []
    for local_path, s3_key in files:
        full_s3_key = os.path.join(prefix, s3_key).replace('\\', '/')
        upload_tasks.append((local_path, full_s3_key))
    return upload_tasks

def process_dry_run_upload(
    files: List[Tuple[str, str]], 
    args: argparse.Namespace
) -> bool:
    """Process dry run for upload operation."""
    total_size = sum(os.path.getsize(local_path) for local_path, _ in files)
    logger.info(
        f"{Fore.CYAN}Dry run - would upload {len(files)} files "
        f"({format_size(total_size)}) from {args.source} "
        f"to s3://{args.bucket}/{args.prefix}{Style.RESET_ALL}"
    )
    return True

def submit_upload_tasks(
    executor: ThreadPoolExecutor,
    upload_tasks: List[Tuple[str, str]],
    s3_client: boto3.client,
    args: argparse.Namespace,
    total_files: int
) -> Dict[Future, str]:
    """Submit upload tasks to the executor and return futures mapping."""
    future_to_file = {}
    
    # Show progress during file submission
    with tqdm(
        total=total_files, 
        desc="Submitting files", 
        unit="file"
    ) as submit_pbar:
        # Submit files in batches of 1000
        batch_size = 1000
        for i in range(0, len(upload_tasks), batch_size):
            batch = upload_tasks[i:i + batch_size]
            # Submit batch of files
            futures = [
                executor.submit(
                    upload_file, s3_client, local_path, args.bucket,
                    s3_key, args.dry_run
                ) for local_path, s3_key in batch
            ]
            # Map futures to file paths
            for future, (local_path, _) in zip(futures, batch):
                future_to_file[future] = local_path
            submit_pbar.update(len(batch))
    
    return future_to_file

def process_upload_results(
    future_to_file: Dict[Future, str],
    total_files: int
) -> Tuple[bool, int]:
    """Process upload results and return success status and total size."""
    success = True
    total_size = 0
    
    # Create progress bar for upload completion
    with tqdm(
        total=total_files, 
        desc="Uploading files", 
        unit="file"
    ) as pbar:
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                if not future.result():
                    success = False
                # Add file size to total
                file_size = os.path.getsize(file_path)
                total_size += file_size
                pbar.update(1)  # Update progress after each file
                logger.debug(
                    f"{Fore.GREEN}Successfully uploaded {file_path}"
                    f"{Style.RESET_ALL}"
                )
            except Exception as e:
                logger.error(
                    f"{Fore.RED}Error uploading {file_path}: {str(e)}"
                    f"{Style.RESET_ALL}"
                )
                success = False
                pbar.update(1)  # Update progress even on error
    
    return success, total_size

def upload_files(
    args: argparse.Namespace
) -> bool:
    """
    Upload files to S3 based on command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        bool: True if all uploads successful, False otherwise
    """
    try:
        # Configure S3 client
        s3_client = configure_s3_client()
        
        # Get files to upload
        files = get_files_to_upload(args.source, args.recursive)
        
        if not files:
            logger.warning(
                f"{Fore.YELLOW}No files found to upload{Style.RESET_ALL}"
            )
            return True
            
        # Handle dry run
        if args.dry_run:
            return process_dry_run_upload(files, args)
            
        # Log initial file count
        total_files = len(files)
        logger.info(
            f"{Fore.CYAN}Found {total_files} files to upload{Style.RESET_ALL}"
        )
            
        # Set up concurrent execution
        max_workers = min(32, total_files)  # Limit to 32 concurrent uploads
        logger.info(
            f"{Fore.CYAN}Using {max_workers} concurrent workers"
            f"{Style.RESET_ALL}"
        )
        
        # Initialize statistics and prepare tasks
        start_time = time.time()
        upload_tasks = prepare_upload_tasks(files, args.prefix)
        
        logger.info(
            f"{Fore.CYAN}Starting ThreadPoolExecutor with {max_workers} "
            f"workers{Style.RESET_ALL}"
        )
        
        # Execute uploads concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_file = submit_upload_tasks(
                executor, upload_tasks, s3_client, args, total_files
            )
            
            logger.info(
                f"{Fore.CYAN}All uploads submitted, waiting for completion"
                f"{Style.RESET_ALL}"
            )
            
            # Process results
            success, total_size = process_upload_results(
                future_to_file, total_files
            )
                        
        # Print summary report
        print_summary_report(total_files, total_size, start_time, "upload")
        return success
        
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error during upload process: {str(e)}"
            f"{Style.RESET_ALL}"
        )
        return False

def list_s3_objects(
    s3_client: boto3.client,
    bucket: str,
    prefix: str,
    recursive: bool = False,
    filter_pattern: str = None
) -> List[dict]:
    """
    List objects in an S3 bucket with the given prefix.
    
    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        prefix: S3 key prefix
        recursive: Whether to list objects recursively
        filter_pattern: Optional pattern to filter objects
        
    Returns:
        List of S3 object dictionaries
    """
    try:
        # If not recursive and prefix doesn't end with '/', add it
        if not recursive and prefix and not prefix.endswith('/'):
            prefix = prefix + '/'
            
        # List objects in the bucket with the given prefix
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
            Delimiter='' if recursive else '/'
        )
        
        objects = []
        for page in page_iterator:
            # Add objects
            if 'Contents' in page:
                for obj in page['Contents']:
                    # Skip "directory" objects (keys ending with '/')
                    if obj['Key'].endswith('/'):
                        continue
                        
                    # Apply filter if specified
                    if filter_pattern:
                        import fnmatch
                        filename = os.path.basename(obj['Key'])
                        if not fnmatch.fnmatch(filename, filter_pattern):
                            continue
                            
                    objects.append(obj)
                    
            # Add common prefixes (directories) if not recursive
            if not recursive and 'CommonPrefixes' in page:
                for prefix_obj in page['CommonPrefixes']:
                    logger.debug(
                        f"{Fore.CYAN}Found directory: "
                        f"{prefix_obj['Prefix']}{Style.RESET_ALL}"
                    )
        
        return objects
        
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error listing objects in bucket {bucket}: "
            f"{str(e)}{Style.RESET_ALL}"
        )
        return []

def parse_s3_source(source: str) -> Tuple[str, str]:
    """Parse an S3 URI into bucket and prefix components."""
    if not source.startswith('s3://'):
        return None, None
        
    # Extract bucket and prefix from s3://bucket/prefix format
    s3_path = source[5:]  # Remove 's3://'
    parts = s3_path.split('/', 1)  # Split at first '/'
    
    # Set bucket and prefix from source
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''
    
    # Remove trailing slash from prefix if present
    if prefix.endswith('/'):
        prefix = prefix[:-1]
    
    return bucket, prefix

def prepare_download_tasks(
    objects: List[dict], 
    prefix: str,
    destination: str
) -> List[Tuple[str, str, int]]:
    """Prepare download tasks by mapping S3 keys to local paths."""
    download_tasks = []
    for obj in objects:
        s3_key = obj['Key']
        # Remove prefix from key to create relative path
        rel_path = s3_key
        if prefix and s3_key.startswith(prefix):
            rel_path = s3_key[len(prefix):]
            if rel_path.startswith('/'):
                rel_path = rel_path[1:]
                
        local_path = os.path.join(destination, rel_path)
        download_tasks.append((s3_key, local_path, obj['Size']))
    return download_tasks

def process_dry_run_download(
    objects: List[dict], 
    prefix: str,
    args: argparse.Namespace
) -> bool:
    """Process dry run for download operation."""
    total_size = sum(obj['Size'] for obj in objects)
    logger.info(
        f"{Fore.CYAN}Dry run - would download {len(objects)} files "
        f"({format_size(total_size)}) from s3://{args.bucket}/{args.prefix} "
        f"to {args.destination}{Style.RESET_ALL}"
    )
    return True

def download_file(
    s3_client: boto3.client,
    bucket: str,
    s3_key: str,
    local_path: str,
    dry_run: bool = False,
    overwrite: bool = False
) -> bool:
    """
    Download a single file from S3.
    
    Args:
        s3_client: Boto3 S3 client
        bucket: S3 bucket name
        s3_key: S3 key (path in bucket)
        local_path: Local file path
        dry_run: Whether to simulate download
        overwrite: Whether to overwrite existing files
        
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        if os.path.exists(local_path) and not overwrite:
            logger.debug(
                f"{Fore.YELLOW}Skipping existing file: {local_path}"
                f"{Style.RESET_ALL}"
            )
            return True
            
        if dry_run:
            logger.info(
                f"{Fore.CYAN}Would download: s3://{bucket}/{s3_key} -> "
                f"{local_path}{Style.RESET_ALL}"
            )
            return True
            
        # Create directory if it doesn't exist
        os.makedirs(
            os.path.dirname(os.path.abspath(local_path)), 
            exist_ok=True
        )
            
        logger.debug(
            f"{Fore.CYAN}Starting download of {s3_key}{Style.RESET_ALL}"
        )
        s3_client.download_file(bucket, s3_key, local_path)
        logger.debug(
            f"{Fore.GREEN}Completed download of {s3_key}{Style.RESET_ALL}"
        )
        return True
        
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error downloading {s3_key}: {str(e)}"
            f"{Style.RESET_ALL}"
        )
        return False

def submit_download_tasks(
    executor: ThreadPoolExecutor,
    download_tasks: List[Tuple[str, str, int]],
    s3_client: boto3.client,
    args: argparse.Namespace,
    total_files: int
) -> Dict[Future, Tuple[str, str, int]]:
    """Submit download tasks to the executor and return futures mapping."""
    future_to_file = {}
    
    # Show progress during file submission
    with tqdm(
        total=total_files, 
        desc="Submitting files", 
        unit="file"
    ) as submit_pbar:
        # Submit files in batches of 1000
        batch_size = 1000
        for i in range(0, len(download_tasks), batch_size):
            batch = download_tasks[i:i + batch_size]
            # Submit batch of files
            futures = [
                executor.submit(
                    download_file, 
                    s3_client, 
                    args.bucket,
                    s3_key, 
                    local_path, 
                    args.dry_run,
                    args.overwrite
                ) for s3_key, local_path, size in batch
            ]
            # Map futures to file info
            for future, (s3_key, local_path, size) in zip(
                futures, batch
            ):
                future_to_file[future] = (s3_key, local_path, size)
            submit_pbar.update(len(batch))
    
    return future_to_file

def process_download_results(
    future_to_file: Dict[Future, Tuple[str, str, int]],
    total_files: int
) -> Tuple[bool, int]:
    """Process download results and return success status and total size."""
    success = True
    total_size = 0
    
    # Create progress bar for download completion
    with tqdm(
        total=total_files, 
        desc="Downloading files", 
        unit="file"
    ) as pbar:
        for future in as_completed(future_to_file):
            s3_key, local_path, size = future_to_file[future]
            try:
                if not future.result():
                    success = False
                # Add file size to total
                total_size += size
                pbar.update(1)  # Update progress after each file
                logger.debug(
                    f"{Fore.GREEN}Successfully downloaded {s3_key}"
                    f"{Style.RESET_ALL}"
                )
            except Exception as e:
                logger.error(
                    f"{Fore.RED}Error downloading {s3_key}: {str(e)}"
                    f"{Style.RESET_ALL}"
                )
                success = False
                pbar.update(1)  # Update progress even on error
    
    return success, total_size

def download_files(
    args: argparse.Namespace
) -> bool:
    """
    Download files from S3 based on command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        bool: True if all downloads successful, False otherwise
    """
    try:
        # Parse source if it's in s3:// format
        if args.source and args.source.startswith('s3://'):
            args.bucket, args.prefix = parse_s3_source(args.source)
            
            logger.info(
                f"{Fore.CYAN}Using source: {args.source} "
                f"(bucket: {args.bucket}, prefix: {args.prefix})"
                f"{Style.RESET_ALL}"
            )
        
        # Configure S3 client
        s3_client = configure_s3_client()
        
        # List objects to download
        logger.info(
            f"{Fore.CYAN}Listing objects in bucket {args.bucket} "
            f"with prefix {args.prefix}{Style.RESET_ALL}"
        )
        objects = list_s3_objects(
            s3_client, 
            args.bucket, 
            args.prefix,  # Use the parsed prefix, not the full S3 URL
            args.recursive,
            args.filter
        )
        
        if not objects:
            logger.warning(
                f"{Fore.YELLOW}No files found to download{Style.RESET_ALL}"
            )
            return True
            
        # Log initial file count
        total_files = len(objects)
        logger.info(
            f"{Fore.CYAN}Found {total_files} files to download"
            f"{Style.RESET_ALL}"
        )
        
        # Handle dry run
        if args.dry_run:
            return process_dry_run_download(objects, args.prefix, args)
            
        # Set up concurrent execution
        max_workers = min(32, total_files)  # Limit to 32 concurrent downloads
        logger.info(
            f"{Fore.CYAN}Using {max_workers} concurrent workers"
            f"{Style.RESET_ALL}"
        )
        
        # Initialize statistics and prepare tasks
        start_time = time.time()
        download_tasks = prepare_download_tasks(
            objects, args.prefix, args.destination
        )
        
        logger.info(
            f"{Fore.CYAN}Starting ThreadPoolExecutor with {max_workers} "
            f"workers{Style.RESET_ALL}"
        )
        
        # Execute downloads concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_file = submit_download_tasks(
                executor, download_tasks, s3_client, args, total_files
            )
            
            logger.info(
                f"{Fore.CYAN}All downloads submitted, waiting for completion"
                f"{Style.RESET_ALL}"
            )
            
            # Process results
            success, total_size = process_download_results(
                future_to_file, total_files
            )
                        
        # Print summary report
        print_summary_report(total_files, total_size, start_time, "download")
        return success
        
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error during download process: {str(e)}"
            f"{Style.RESET_ALL}"
        )
        return False

def list_bucket_contents(
    args: argparse.Namespace
) -> bool:
    """
    List contents of an S3 bucket based on command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        bool: True if listing successful, False otherwise
    """
    try:
        # Parse source if it's in s3:// format
        if args.source and args.source.startswith('s3://'):
            # Extract bucket and prefix from s3://bucket/prefix format
            s3_path = args.source[5:]  # Remove 's3://'
            parts = s3_path.split('/', 1)  # Split at first '/'
            
            # Set bucket and prefix from source
            args.bucket = parts[0]
            args.prefix = parts[1] if len(parts) > 1 else ''
            
            logger.info(
                f"{Fore.CYAN}Using source: {args.source} "
                f"(bucket: {args.bucket}, prefix: {args.prefix})"
                f"{Style.RESET_ALL}"
            )
        
        # Configure S3 client
        session = boto3.Session()
        s3_client = session.client('s3')
        
        # Use source as prefix if provided, otherwise use prefix
        prefix = args.source if args.source else args.prefix
        
        logger.info(
            f"{Fore.CYAN}Listing objects in bucket {args.bucket} "
            f"with prefix {prefix}{Style.RESET_ALL}"
        )
        
        objects = list_s3_objects(
            s3_client, 
            args.bucket, 
            prefix, 
            args.recursive,
            args.filter
        )
        
        if not objects:
            logger.warning(
                f"{Fore.YELLOW}No objects found in bucket {args.bucket} "
                f"with prefix {prefix}{Style.RESET_ALL}"
            )
            return True
            
        # Print objects
        logger.info(
            f"{Fore.GREEN}Found {len(objects)} objects:{Style.RESET_ALL}"
        )
        
        total_size = 0
        for obj in objects:
            s3_key = obj['Key']
            size = obj['Size']
            total_size += size
            last_modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
            logger.info(
                f"{Fore.CYAN}  {s3_key} - {format_size(size)} - "
                f"{last_modified}{Style.RESET_ALL}"
            )
            
        logger.info(
            f"{Fore.GREEN}Total: {len(objects)} objects, "
            f"{format_size(total_size)}{Style.RESET_ALL}"
        )
        
        return True
        
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error listing bucket contents: {str(e)}"
            f"{Style.RESET_ALL}"
        )
        return False

def process_dry_run_delete(
    objects: List[dict],
    bucket: str,
    prefix: str
) -> bool:
    """Process dry run for delete operation."""
    total_size = sum(obj['Size'] for obj in objects)
    logger.info(
        f"{Fore.CYAN}Dry run - would delete {len(objects)} files "
        f"({format_size(total_size)}) from s3://{bucket}/{prefix}"
        f"{Style.RESET_ALL}"
    )
    return True

def batch_delete_objects(
    s3_client: boto3.client,
    bucket: str,
    objects: List[dict],
    total_files: int
) -> Tuple[bool, int]:
    """Delete objects in batches and return success status and total size."""
    success = True
    total_size = 0
    batch_size = 1000  # Maximum allowed by S3 API
    
    with tqdm(
        total=total_files, 
        desc="Deleting files", 
        unit="file"
    ) as pbar:
        # Process in batches
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            
            try:
                # Add sizes to total
                for obj in batch:
                    total_size += obj.get('Size', 0)
                
                # Prepare delete request
                delete_objects = {
                    'Objects': [{'Key': obj['Key']} for obj in batch],
                    'Quiet': True  # Don't return detailed results
                }
                
                # Delete batch
                response = s3_client.delete_objects(
                    Bucket=bucket,
                    Delete=delete_objects
                )
                
                # Check for errors
                if 'Errors' in response and response['Errors']:
                    for error in response['Errors']:
                        logger.error(
                            f"{Fore.RED}Error deleting {error['Key']}: "
                            f"{error['Code']} - {error['Message']}"
                            f"{Style.RESET_ALL}"
                        )
                        success = False
                
                # Update progress
                pbar.update(len(batch))
                
            except Exception as e:
                logger.error(
                    f"{Fore.RED}Error in batch delete: {str(e)}"
                    f"{Style.RESET_ALL}"
                )
                success = False
                pbar.update(len(batch))
    
    return success, total_size

def delete_files(
    args: argparse.Namespace
) -> bool:
    """
    Delete files from S3 based on command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        bool: True if all deletions successful, False otherwise
    """
    try:
        # Ensure destination is an S3 URL
        if not args.destination or not args.destination.startswith('s3://'):
            logger.error(
                f"{Fore.RED}Error: --destination must be an S3 URL "
                f"(s3://bucket/prefix) for delete operation{Style.RESET_ALL}"
            )
            return False
            
        # Parse destination
        bucket, prefix = parse_s3_source(args.destination)
        
        logger.info(
            f"{Fore.CYAN}Using destination: {args.destination} "
            f"(bucket: {bucket}, prefix: {prefix}){Style.RESET_ALL}"
        )
        
        # Configure S3 client
        session = boto3.Session()
        s3_client = session.client('s3')
        
        # List objects to delete
        objects = list_s3_objects(
            s3_client, 
            bucket, 
            prefix, 
            recursive=args.recursive,
            filter_pattern=args.filter
        )
        
        if not objects:
            logger.warning(
                f"{Fore.YELLOW}No files found to delete{Style.RESET_ALL}"
            )
            return True
            
        # Log initial file count
        total_files = len(objects)
        logger.info(
            f"{Fore.CYAN}Found {total_files} files to delete{Style.RESET_ALL}"
        )
        
        # Handle dry run
        if args.dry_run:
            return process_dry_run_delete(objects, bucket, prefix)
            
        # Initialize statistics
        start_time = time.time()
        
        # Delete objects in batches
        success, total_size = batch_delete_objects(
            s3_client, bucket, objects, total_files
        )
        
        # Print summary
        print_summary_report(
            total_files, 
            total_size,  # Now passing the actual total size
            start_time,
            operation="deletion"
        )
        
        return success
        
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}"
        )
        return False

def print_usage_examples() -> None:
    """Print usage examples for the tool."""
    print("\nExamples:")
    print("  Copy from S3 to local:")
    print("    ./pt5_s3_tool.py --source s3://bucket-name/prefix \\")
    print("      --destination /local/path")
    print("  Copy from local to S3:")
    print("    ./pt5_s3_tool.py --source /path/to/files \\")
    print("      --destination s3://bucket-name/prefix")
    print("  Copy with recursive option:")
    print("    ./pt5_s3_tool.py --source s3://bucket-name/prefix \\")
    print("      --destination /local/path --recursive")
    print("  Copy with file filter:")
    print("    ./pt5_s3_tool.py --source s3://bucket-name/prefix \\")
    print("      --destination /local/path --filter '*.jpg'")
    print("  Dry run to preview changes:")
    print("    ./pt5_s3_tool.py --source s3://bucket-name/prefix \\")
    print("      --destination /local/path --dry-run")
    print("  Delete files from S3 (using --source):")
    print("    ./pt5_s3_tool.py --source s3://bucket-name/prefix \\")
    print("      --delete [--recursive] [--filter '*.jpg']")
    print("  Delete files from S3 (using --destination):")
    print("    ./pt5_s3_tool.py --destination s3://bucket-name/prefix \\")
    print("      --delete [--recursive] [--filter '*.jpg']")
    print("  Dry run delete:")
    print("    ./pt5_s3_tool.py --source s3://bucket-name/prefix \\")
    print("      --delete --dry-run")

def execute_operation(args: argparse.Namespace) -> bool:
    """Execute the requested operation based on source and destination."""
    try:
        # Configure S3 client
        s3_client = configure_s3_client()
        
        # Handle delete operation
        if args.delete:
            # Use source if destination is not provided
            if not args.destination and args.source and args.source.startswith('s3://'):
                args.destination = args.source
                
            if not args.destination or not args.destination.startswith('s3://'):
                logger.error(
                    f"{Fore.RED}Error: Either --source or --destination must be an "
                    f"S3 URL (s3://bucket/prefix) for delete operation{Style.RESET_ALL}"
                )
                return False
            logger.info(
                f"{Fore.GREEN}Starting delete operation...{Style.RESET_ALL}"
            )
            return delete_files(args)
        
        # Determine operation type based on source/destination
        is_download = args.source and args.source.startswith('s3://')
        is_upload = args.destination and args.destination.startswith('s3://')
        
        if is_download:
            logger.info(
                f"{Fore.GREEN}Starting download from S3...{Style.RESET_ALL}"
            )
            return download_files(args)
        elif is_upload:
            logger.info(
                f"{Fore.GREEN}Starting upload to S3...{Style.RESET_ALL}"
            )
            return upload_files(args)
        else:
            logger.error(
                f"{Fore.RED}Error: Invalid operation. Either source or "
                f"destination must be an S3 URL{Style.RESET_ALL}"
            )
            return False
            
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error during operation: {str(e)}{Style.RESET_ALL}"
        )
        return False

def main() -> int:
    """Main entry point for the application."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Check if we have any command-line arguments beyond the script name
    has_args = len(sys.argv) > 1
    
    # Check if we have environment variables set that we can use as defaults
    has_env_defaults = (
        get_default_source() is not None or 
        get_default_bucket() is not None
    )
    
    # Print usage examples if no arguments provided and no env defaults
    if not has_args and not has_env_defaults:
        parser.print_help()
        print_usage_examples()
        return 0
    
    # If no arguments but we have env defaults, proceed with defaults
    if not has_args and has_env_defaults:
        logger.info(
            f"{Fore.CYAN}Using environment variables as defaults{Style.RESET_ALL}"
        )

    # If --validate is set, only check credentials and exit
    if args.validate:
        logger.info(
            f"{Fore.CYAN}Validating AWS credentials...{Style.RESET_ALL}"
        )
        return 0 if validate_aws_credentials() else 1

    if not validate_args(args):
        return 1

    if not validate_aws_credentials():
        return 1

    try:
        success = execute_operation(args)
        return 0 if success else 1
    except Exception as e:
        logger.error(
            f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}"
        )
        return 1

if __name__ == '__main__':
    sys.exit(main())
