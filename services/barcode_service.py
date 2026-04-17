from database.models import Drug
import re

class BarcodeService:
    @staticmethod
    def lookup_by_barcode(barcode):
        """Find a drug by its barcode."""
        if not barcode:
            return None
        return Drug.query.filter_by(barcode=barcode.strip(), is_active=True).first()
    
    @staticmethod
    def generate_barcode_prefix():
        """Generate a simple barcode prefix (for new products)."""
        import random
        import string
        return ''.join(random.choices(string.digits, k=8))
    
    @staticmethod
    def validate_barcode(barcode):
        """Basic barcode validation (simple check)."""
        if not barcode:
            return False
        barcode = barcode.strip()
        # Allow only digits and hyphens, length between 6 and 20
        if not re.match(r'^[0-9\-]+$', barcode):
            return False
        if len(barcode) < 6 or len(barcode) > 20:
            return False
        return True
    
    @staticmethod
    def search_by_partial_barcode(partial):
        """Search drugs by partial barcode match."""
        if not partial or len(partial) < 2:
            return []
        return Drug.query.filter(
            Drug.barcode.contains(partial),
            Drug.is_active == True
        ).limit(20).all()