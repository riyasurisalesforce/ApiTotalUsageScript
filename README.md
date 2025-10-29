# Salesforce API Total Usage CSV Extractor

A Python script that extracts API Total Usage data from Salesforce Event Log Files using the Salesforce CLI for authentication and data retrieval.

## Overview

This tool automates the extraction of API usage metrics from Salesforce Event Log Files, providing detailed CSV reports of API calls made against your Salesforce org. It's designed for administrators and developers who need to monitor API consumption and analyze usage patterns.

## Features

- **Automated Authentication**: Uses JWT flow via Salesforce CLI
- **Event Log File Processing**: Queries and downloads ApiTotalUsage event logs
- **Streaming CSV Export**: Efficiently streams large CSV files to disk
- **Comprehensive Logging**: Detailed execution logs for troubleshooting
- **Organized Output**: Separate directories for logs and CSV files
- **Date-based Naming**: Files named with EventLog dates for consistency
- **Error Handling**: Robust error handling with detailed logging
- **Production Ready**: Suitable for scheduled/automated execution

## Prerequisites

### Required Software
- **Python 3.6+**
- **Salesforce CLI** (sf command)

### Salesforce Setup
- **Connected App** with JWT authentication enabled
- **Private key file** for JWT signing
- **User permissions** to access Event Log Files
- **Org alias** configured in Salesforce CLI (required for script operation)

### Python Dependencies
The script uses only standard Python libraries:
- `sys`, `json`, `logging`, `subprocess`, `argparse`, `os`
- `datetime`, `pathlib`, `typing`
- `requests` (install with: `pip install requests`)

## Installation

1. **Clone or download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/.../extract_total_usage_calls.py
   ```

2. **Install dependencies:**
   ```bash
   pip install requests
   ```

3. **Install Salesforce CLI:**
   ```bash
   # macOS
   brew install salesforce-cli

   # npm
   npm install -g @salesforce/cli

   # Or download from: https://developer.salesforce.com/tools/sfdxcli
   ```

## Configuration

### Connected App Setup

1. **Create Connected App in Salesforce:**
    - Setup → App Manager → New Connected App
    - Enable OAuth Settings
    - Enable "Use digital signatures"
    - Upload your certificate
    - Add OAuth scopes: `api`, `refresh_token`

2. **Generate Private Key:**
   ```bash
   # Generate private key
   openssl genrsa -out server.key 2048

   # Generate certificate
   openssl req -new -x509 -key server.key -out server.crt -days 365
   ```

3. **Configure User Permissions:**
    - Assign "API Only User" or appropriate profile
    - Grant "View Event Log Files" permission

### 4. Set Up Org Alias (Required)

**Important**: The script requires an org alias to be configured in Salesforce CLI. This alias is used for all SF CLI commands.

**To set up the alias, authenticate once manually:**
```bash
sf org login jwt \
  --client-id "YOUR_CLIENT_ID" \
  --username "your-username@company.com" \
  --jwt-key-file "/path/to/server.key" \
  --instance-url "https://yourcompany.my.salesforce.com" \
  --alias "my-org"
```

**Verify the alias is set:**
```bash
sf org list
```

You should see your org listed with the alias you specified. The script will use this alias for all subsequent operations.

## Usage

### Basic Usage
```bash
python3 extract_total_usage_calls.py \
  --client-id "3MVG9A2kN3Bn17hs..." \
  --username "user@company.com" \
  --jwt-key-file "/path/to/server.key" \
  --instance-url "https://yourcompany.my.salesforce.com" \
  --org-alias "my-org" \
  --output-dir "/path/to/output"
```

### Parameters

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--client-id` | Connected App Consumer Key | Yes | `3MVG9A2kN3Bn17hs...` |
| `--username` | Salesforce username | Yes | `user@company.com` |
| `--jwt-key-file` | Path to JWT private key file | Yes | `/path/to/server.key` |
| `--instance-url` | Salesforce instance URL | Yes | `https://login.salesforce.com` |
| `--org-alias` | Alias for Salesforce CLI | Yes | `my-org` |
| `--output-dir` | Directory for output files | Yes | `/path/to/output` |

### Instance URLs
- **Production/Developer**: `https://login.salesforce.com`
- **Sandbox**: `https://test.salesforce.com`
- **My Domain**: `https://yourdomain.my.salesforce.com`

## Output

### Directory Structure

After running the script, you'll find your files organized like this:

```
your-output-directory/
├── logs/
│   └── extract_usage_20251009.log           # Detailed execution log
└── output/
    └── ApiTotalUsage_20251009_0ATxxxxxxx.csv  # API usage data
```

**Where to find your files:**
- **Log files**: `{your-output-dir}/logs/extract_usage_YYYYMMDD.log`
- **CSV files**: `{your-output-dir}/output/ApiTotalUsage_YYYYMMDD_EventLogFileId.csv`

**Example with `/Users/john/salesforce-data` as output directory:**
```
/Users/john/salesforce-data/
├── logs/
│   └── extract_usage_20251009.log
└── output/
    └── ApiTotalUsage_20251009_0ATxxxxxxx.csv
```

### Log Files (`logs/`)
- **Filename**: `extract_usage_YYYYMMDD.log`
- **Content**: Complete execution log with timestamps
- **Purpose**: Debugging and audit trail

### CSV Files (`output/`)
- **Filename**: `ApiTotalUsage_YYYYMMDD_EventLogFileId.csv`
- **Content**: Raw API usage data from Salesforce
- **Columns**: EVENT_TYPE, TIMESTAMP, REQUEST_ID, USER_ID, API_FAMILY, etc.

### Sample CSV Data
```csv
EVENT_TYPE,TIMESTAMP,REQUEST_ID,ORGANIZATION_ID,USER_ID,API_FAMILY,API_VERSION,API_RESOURCE,CLIENT_NAME,HTTP_METHOD,CLIENT_IP,COUNTS_AGAINST_API_LIMIT,CONNECTED_APP_ID,ENTITY_NAME,STATUS_CODE,CONNECTED_APP_NAME,USER_NAME,TIMESTAMP_DERIVED
ApiTotalUsage,20251009183437.652,xxxxxxxxxxxxxxxxxxxxx,00Dxxxxxxxxxxxxxxxxx,005xxxxxxxxxxxxxxxxx,SOAP,64.0,login,,xxx.xxx.xxx.xxx,1,, ,200,,user@company.com,2025-10-09T18:34:37.652Z
ApiTotalUsage,20251009184000.123,xxxxxxxxxxxxxxxxxxxxx,00Dxxxxxxxxxxxxxxxxx,005xxxxxxxxxxxxxxxxx,REST,64.0,/v64.0/sobjects/Account,MyConnectedApp,GET,xxx.xxx.xxx.xxx,1,3MVxxxxxxxxxxxxxxxxx,Account,200,MyApp,user@company.com,2025-10-09T18:40:00.123Z
```

## Automation

### Cron Job (Linux/macOS)
```bash
# Daily extraction at 2 AM
0 2 * * * /usr/bin/python3 /path/to/extract_total_usage_calls.py \
  --client-id "YOUR_CLIENT_ID" \
  --username "your-username@company.com" \
  --jwt-key-file "/secure/path/server.key" \
  --instance-url "https://yourcompany.my.salesforce.com" \
  --org-alias "my-org" \
  --output-dir "/data/salesforce-logs"
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Set action to run the Python script with parameters

### Script Wrapper
```bash
#!/bin/bash
# wrapper-script.sh

SCRIPT_DIR="/path/to/script"
OUTPUT_DIR="/data/salesforce-logs"
KEY_FILE="/secure/server.key"

python3 "$SCRIPT_DIR/extract_total_usage_calls.py" \
  --client-id "$SF_CLIENT_ID" \
  --username "$SF_USERNAME" \
  --jwt-key-file "$KEY_FILE" \
  --instance-url "$SF_INSTANCE_URL" \
  --org-alias "my-org" \
  --output-dir "$OUTPUT_DIR"
```

## Troubleshooting

### Common Issues

#### Authentication Failures
```
ERROR: Authentication failed: JWT validation failed
```
**Solutions:**
- Verify Connected App configuration
- Check private key file permissions
- Ensure certificate is uploaded to Connected App
- Verify username and client ID

#### No Event Log Files Found
```
INFO: No EventLogFile records found for the specified date range. Exiting.
```
**Solutions:**
- Event Log Files are generated daily (previous day's data)
- Check if your org has API activity
- Verify user permissions for Event Log File access

#### SF CLI Command Failures
```
ERROR: SF CLI command failed: sf org login jwt
```
**Solutions:**
- Install/update Salesforce CLI: `npm install -g @salesforce/cli`
- Check CLI version: `sf --version`
- Verify CLI authentication: `sf org list`

#### Org Alias Not Found
```
ERROR: No org configuration found for name my-org
```
**Solutions:**
- Set up the org alias first (see Configuration section)
- Run `sf org list` to see available aliases
- Ensure the alias name matches exactly what you use in the script

#### Permission Issues
```
ERROR: Output directory is not writable: /path/to/output
```
**Solutions:**
- Check directory permissions: `chmod 755 /path/to/output`
- Verify disk space availability
- Ensure parent directories exist

### Debugging

#### Enable Verbose Logging
The script automatically logs all operations. Check the log file in `logs/extract_usage_YYYYMMDD.log` for detailed information.

#### Manual SF CLI Testing
```bash
# Test authentication only
sf org login jwt \
  --client-id "your_client_id" \
  --username "your_username" \
  --jwt-key-file "/path/to/server.key" \
  --instance-url "https://yourcompany.my.salesforce.com" \
  --alias "test-org"

# Verify connection
sf org display --target-org "test-org"
```

## Data Retention

### Salesforce Event Log Retention
- **Standard**: 1 day (24 hours)
- **Shield**: 30 days
- **Event Monitoring**: 30 days

**Important**: Run the extraction daily to avoid data loss.

### Local Storage Management
```bash
# Clean old files (older than 30 days)
find /path/to/output -name "*.csv" -mtime +30 -delete
find /path/to/output/logs -name "*.log" -mtime +30 -delete
```

## Security Considerations

- **Private Key Protection**: Store JWT private keys securely with restricted permissions (600)
- **Credential Management**: Use environment variables or secure credential stores
- **Network Security**: Ensure secure transmission of authentication tokens
- **Access Control**: Limit file system permissions on output directories

## API Usage Data Analysis

### Common Use Cases
- **API Consumption Monitoring**: Track daily/monthly API usage
- **User Activity Analysis**: Identify high-usage users and applications
- **Performance Optimization**: Find slow or frequently used API calls
- **Compliance Reporting**: Generate usage reports for audits

### Data Fields Explained
- **API_FAMILY**: Type of API (REST, SOAP, Bulk, etc.)
- **COUNTS_AGAINST_API_LIMIT**: Whether call counts against daily limits
- **CLIENT_NAME**: Connected App or client identifier
- **ENTITY_NAME**: Salesforce object accessed (Account, Contact, etc.)
- **HTTP_METHOD**: REST operation (GET, POST, PUT, DELETE)


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Salesforce CLI documentation
3. Submit an issue on the project repository