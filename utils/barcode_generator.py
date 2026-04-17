import random
import string
import hashlib
from database.models import Drug

class BarcodeGenerator:
    """
    Generate and validate barcodes for drugs.
    Supports EAN-13 style and simple internal codes.
    """
    
    @staticmethod
    def generate_ean13(prefix="629", length=12):
        """
        Generate a fake EAN-13 barcode number.
        prefix: 3-digit country/company prefix (default 629 for testing)
        length: total digits before checksum (12)
        """
        if len(prefix) > 12:
            prefix = prefix[:12]
        remaining = length - len(prefix)
        random_part = ''.join(str(random.randint(0, 9)) for _ in range(remaining))
        code_without_checksum = prefix + random_part
        checksum = BarcodeGenerator._calculate_ean13_checksum(code_without_checksum)
        return code_without_checksum + str(checksum)
    
    @staticmethod
    def _calculate_ean13_checksum(code):
        """Calculate EAN-13 checksum digit."""
        total = 0
        for i, digit in enumerate(code):
            num = int(digit)
            if i % 2 == 0:  # odd position (1-indexed)
                total += num
            else:
                total += num * 3
        remainder = total % 10
        if remainder == 0:
            return 0
        else:
            return 10 - remainder
    
    @staticmethod
    def generate_internal_barcode(drug_id, drug_name):
        """
        Generate a simple internal barcode based on drug ID and name hash.
        Format: JESS + drug_id padded to 6 digits + checksum
        """
        drug_id_str = str(drug_id).zfill(6)
        name_hash = hashlib.md5(drug_name.encode()).hexdigest()[:4].upper()
        base = f"JESS{drug_id_str}{name_hash}"
        checksum = sum(ord(c) for c in base) % 10
        return f"{base}{checksum}"
    
    @staticmethod
    def validate_barcode(barcode):
        """
        Basic validation for barcode.
        Returns True if barcode appears valid.
        """
        if not barcode or not isinstance(barcode, str):
            return False
        barcode = barcode.strip()
        if len(barcode) < 6 or len(barcode) > 20:
            return False
        # Allow digits, letters, hyphens
        allowed = set(string.digits + string.ascii_uppercase + '-')
        if not all(c in allowed for c in barcode):
            return False
        return True
    
    @staticmethod
    def generate_unique_barcode(existing_barcodes=None):
        """
        Generate a unique barcode not in the given list.
        """
        if existing_barcodes is None:
            existing_barcodes = []
        for _ in range(100):  # Try 100 times
            barcode = BarcodeGenerator.generate_ean13()
            if barcode not in existing_barcodes:
                # Also ensure not in database
                if not Drug.query.filter_by(barcode=barcode).first():
                    return barcode
        # Fallback: use timestamp-based
        import time
        return f"JESS{int(time.time())}{random.randint(10,99)}"