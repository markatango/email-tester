#### Email tester
Simple script to test one or more email address(es), checking for:
* Syntax errors
* Valid Domain
* Checks whether an MX record exists
* Can test whether email is valid by connecting to the SMTP server, if allowed

### Installation
1. Create a virtual environment

`python -m venv venv`

2. Install the required modules

`pip install -r requirements.txt`

3. Add one or more email addresses in the code here:

```
# Test emails
    test_emails = [
        "user@example.com",           # Valid format
        "invalid.email@",             # Invalid syntax
        "test@nonexistentdomain12345.com",  # Non-existent domain
        "admin@gmail.com",            # Valid email
        "user..name@domain.com",      # Double dots
    ]
```
4. Execute the script 

`python email-tester.py`
