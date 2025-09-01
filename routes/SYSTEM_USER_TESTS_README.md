# System User Testing Documentation

This directory contains standalone test scripts for validating system user access using the `system_user.json` file.

## Files Overview

### 1. `test_system_user.py`
A comprehensive test suite that validates system user token functionality.

### 2. `system_user_example.py`
A practical demonstration script showing how to use the system user token for Facebook API access.

### 3. `system_user.json`
Configuration file containing the system user access token.

## Running the Tests

### Prerequisites
```bash
pip install requests
```

### Running the Test Suite
```bash
cd routes
python test_system_user.py
```

### Running the Example Script
```bash
cd routes
python system_user_example.py
```

## Test Coverage

The test suite (`test_system_user.py`) covers the following scenarios:

### File Operations
- ✅ Reading `system_user.json` file successfully
- ✅ Handling missing file scenarios
- ✅ Validating JSON structure and format
- ✅ Detecting and warning about key name typos

### Token Validation
- ✅ Validating token format (length, prefix)
- ✅ Testing Facebook API validation with valid tokens
- ✅ Testing Facebook API rejection of invalid tokens
- ✅ Using the actual token from the file for validation

### API Operations
- ✅ Getting app information using system user token
- ✅ Checking app permissions
- ✅ Helper function for loading tokens

### Error Handling
- ✅ File not found scenarios
- ✅ Invalid JSON handling
- ✅ Missing token key handling
- ✅ API error responses

## Example Output

### Successful Test Run
```
============================================================
SYSTEM USER ACCESS TESTS
============================================================
test_get_app_info_with_system_token ... ✓ Successfully retrieved app info: Test Facebook App
test_load_system_user_helper_function ... ✓ Helper function successfully loaded token: EAAMU4HhUxE4BPa1l1rS...
test_read_system_user_file_success ... ✓ Successfully read system user file with token: EAAMU4HhUxE4BPa1l1rS...
test_system_user_file_structure ... ✓ File structure validation passed
⚠ Warning: Found typo in key name 'system_user_access_toke' (should be 'system_user_access_token')

Tests run: 10
Failures: 0
Errors: 0
```

### Example Script Output
```
============================================================
SYSTEM USER ACCESS DEMONSTRATION
============================================================
1. Loading system user token...
   ✓ Token loaded: EAAMU4HhUxE4BPa1l1rS...S8vc8gZDZD

2. Validating system user token...
   ✓ Token is valid
   App ID: 122102873642996564
   App Name: Byambatsogt Enkhbat

3. Checking app permissions...
   ✓ Found 26 permissions:
     - read_insights: granted
     - publish_video: granted
     - pages_manage_cta: granted
     ... and 23 more

4. Fetching managed pages...
   ✓ Found 1 pages:
     - Эхлэл (ID: 682084288324866, Category: Information Technology Company)
============================================================
```

## Key Features

### 1. Typo Detection
The tests automatically detect and handle the typo in the original `system_user.json` file:
- Original: `"system_user_access_toke"` (missing 'n')
- Expected: `"system_user_access_token"`

### 2. Comprehensive Validation
- Token format validation (Facebook tokens start with 'EAA')
- API connectivity testing with mocked responses
- Real token validation using the actual file content
- Permission checking capabilities

### 3. Error Handling
- Graceful handling of missing files
- JSON parsing error detection
- API error response handling
- Network timeout protection

### 4. Helper Functions
The example script provides reusable functions:
- `load_system_user_token()` - Load token from file
- `validate_system_user_token()` - Validate with Facebook API
- `get_app_permissions()` - Retrieve app permissions
- `get_app_pages()` - Get managed pages

## Troubleshooting

### Common Issues

1. **File Not Found Error**
   ```
   FileNotFoundError: System user file not found: system_user.json
   ```
   - Ensure `system_user.json` exists in the routes directory
   - Check file permissions

2. **Invalid JSON Error**
   ```
   ValueError: Invalid JSON in system user file
   ```
   - Verify JSON syntax in `system_user.json`
   - Check for trailing commas or syntax errors

3. **Missing Token Key Error**
   ```
   KeyError: No system user access token found in file
   ```
   - Ensure the file contains either `system_user_access_token` or `system_user_access_toke` key

4. **API Connection Errors**
   ```
   Request failed: [Connection error details]
   ```
   - Check internet connectivity
   - Verify Facebook Graph API is accessible
   - Check if token has expired

### Token Expiration
System user tokens can expire. If you get OAuth errors:
1. Generate a new system user token from Facebook Developer Console
2. Update the `system_user.json` file with the new token
3. Re-run the tests to verify the new token

## Integration with Main Application

These test scripts can be integrated into your CI/CD pipeline or used for:
- Regular token validation
- Pre-deployment checks
- System health monitoring
- Token refresh validation

## Security Notes

- Keep `system_user.json` secure and never commit it to public repositories
- Regularly rotate system user tokens
- Monitor token usage and permissions
- Use environment variables for production deployments
