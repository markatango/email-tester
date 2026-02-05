import re
import dns.resolver
import smtplib
from typing import Tuple, Dict
from email.utils import parseaddr

class EmailValidator:
    """Validate email addresses without sending emails."""
    
    def __init__(self):
        # RFC 5322 compliant email regex (simplified version)
        self.email_regex = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def validate_syntax(self, email: str) -> Tuple[bool, str]:
        """
        Validate email syntax using regex.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not email or not isinstance(email, str):
            return False, "Email must be a non-empty string"
        
        email = email.strip()
        
        # Basic format check
        if not self.email_regex.match(email):
            return False, "Invalid email format"
        
        # Check for valid characters
        local_part, domain = email.rsplit('@', 1)
        
        if len(local_part) > 64:
            return False, "Local part (before @) is too long (max 64 chars)"
        
        if len(domain) > 255:
            return False, "Domain part is too long (max 255 chars)"
        
        # Check for consecutive dots
        if '..' in email:
            return False, "Email contains consecutive dots"
        
        # Check if local part starts or ends with dot
        if local_part.startswith('.') or local_part.endswith('.'):
            return False, "Local part cannot start or end with a dot"
        
        return True, "Syntax is valid"
    
    def validate_domain(self, email: str) -> Tuple[bool, str]:
        """
        Check if the domain exists (DNS A or AAAA record).
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            domain = email.rsplit('@', 1)[1]
            
            # Try to resolve the domain
            try:
                dns.resolver.resolve(domain, 'A')
                return True, "Domain exists"
            except dns.resolver.NoAnswer:
                # Try AAAA (IPv6) if A record doesn't exist
                try:
                    dns.resolver.resolve(domain, 'AAAA')
                    return True, "Domain exists (IPv6)"
                except:
                    return False, "Domain has no A or AAAA records"
                    
        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except dns.resolver.NoNameservers:
            return False, "No nameservers found for domain"
        except dns.resolver.Timeout:
            return False, "DNS query timed out"
        except Exception as e:
            return False, f"DNS error: {str(e)}"
    
    def validate_mx_records(self, email: str) -> Tuple[bool, str]:
        """
        Check if the domain has MX (Mail Exchange) records.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            domain = email.rsplit('@', 1)[1]
            
            # Get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_list = [str(r.exchange) for r in mx_records]
            
            if mx_list:
                return True, f"MX records found: {', '.join(mx_list[:3])}"
            else:
                return False, "No MX records found"
                
        except dns.resolver.NoAnswer:
            return False, "No MX records for domain"
        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except Exception as e:
            return False, f"MX lookup error: {str(e)}"
    
    def validate_smtp(self, email: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Verify email existence by connecting to SMTP server (without sending).
        Note: Many servers block this for privacy/anti-spam reasons.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            domain = email.rsplit('@', 1)[1]
            
            # Get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)
            
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=timeout)
            server.connect(mx_host)
            server.helo(server.local_hostname)
            server.mail('test@example.com')  # Sender (can be anything)
            code, message = server.rcpt(email)  # Recipient to verify
            server.quit()
            
            # 250 = success, 251 = user not local (but will forward)
            if code == 250 or code == 251:
                return True, f"SMTP verification passed (code {code})"
            else:
                return False, f"SMTP verification failed (code {code}): {message.decode()}"
                
        except smtplib.SMTPServerDisconnected:
            return False, "SMTP server disconnected"
        except smtplib.SMTPResponseException as e:
            return False, f"SMTP error ({e.smtp_code}): {e.smtp_error.decode()}"
        except Exception as e:
            return False, f"SMTP verification unavailable: {str(e)}"
    
    def validate_email(self, email: str, check_smtp: bool = False) -> Dict:
        """
        Perform comprehensive email validation.
        
        Args:
            email: Email address to validate
            check_smtp: Whether to perform SMTP verification (may be blocked)
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'email': email,
            'is_valid': True,
            'checks': {}
        }
        
        # 1. Syntax validation
        is_valid, message = self.validate_syntax(email)
        results['checks']['syntax'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            results['is_valid'] = False
            return results
        
        # 2. Domain validation
        is_valid, message = self.validate_domain(email)
        results['checks']['domain'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            results['is_valid'] = False
            return results
        
        # 3. MX records validation
        is_valid, message = self.validate_mx_records(email)
        results['checks']['mx_records'] = {'valid': is_valid, 'message': message}
        if not is_valid:
            results['is_valid'] = False
            return results
        
        # 4. SMTP validation (optional, often blocked)
        if check_smtp:
            is_valid, message = self.validate_smtp(email)
            results['checks']['smtp'] = {'valid': is_valid, 'message': message}
            if not is_valid:
                results['is_valid'] = False
        
        return results


def print_validation_results(results: Dict):
    """Pretty print validation results."""
    print(f"\n{'='*60}")
    print(f"Email: {results['email']}")
    print(f"Overall Valid: {'✓ YES' if results['is_valid'] else '✗ NO'}")
    print(f"{'='*60}")
    
    for check_name, check_result in results['checks'].items():
        status = '✓' if check_result['valid'] else '✗'
        print(f"{status} {check_name.upper()}: {check_result['message']}")
    print()


# Example usage
if __name__ == "__main__":
    validator = EmailValidator()
    
    # Test emails
    test_emails = [
        "user@example.com",           # Valid format
        "invalid.email@",             # Invalid syntax
        "test@nonexistentdomain12345.com",  # Non-existent domain
        "admin@gmail.com",            # Valid email
        "user..name@domain.com",      # Double dots
    ]
    
    print("EMAIL VALIDATION TESTS")
    print("=" * 60)
    
    for email in test_emails:
        # Validate without SMTP (faster, more reliable)
        results = validator.validate_email(email, check_smtp=False)
        print_validation_results(results)
    
    # Example with SMTP check (may fail on many domains)
    print("\n" + "="*60)
    print("SMTP VERIFICATION EXAMPLE (may be blocked by many servers)")
    print("="*60)
    results = validator.validate_email("admin@gmail.com", check_smtp=True)
    print_validation_results(results)