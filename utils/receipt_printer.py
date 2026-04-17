import os
from datetime import datetime
from flask import current_app
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

class ReceiptPrinter:
    """
    Handles receipt generation and printing.
    Supports PDF generation and direct printing (Windows/Mac/Linux).
    """
    
    @staticmethod
    def generate_html_receipt(sale):
        """Generate HTML receipt string from sale object."""
        items_html = ''
        for item in sale.items:
            items_html += f'''
                <tr>
                    <td>{item.drug.name}</td>
                    <td>{item.quantity}</td>
                    <td>${item.unit_price:.2f}</td>
                    <td>${item.total_price:.2f}</td>
                </tr>
            '''
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Receipt {sale.invoice_number}</title>
            <style>
                body {{ font-family: monospace; width: 300px; margin: 0 auto; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .items {{ width: 100%; border-collapse: collapse; }}
                .items th, .items td {{ border-bottom: 1px dashed #ccc; padding: 5px 0; text-align: left; }}
                .total {{ margin-top: 15px; text-align: right; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h3>JESSEY CLINIC PHARMACY</h3>
                <p>123 Health Street, Medical District<br>Tel: +123 456 7890</p>
                <p>Invoice: {sale.invoice_number}<br>Date: {sale.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br>Cashier: {sale.cashier.username}</p>
            </div>
            <table class="items">
                <thead><tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead>
                <tbody>{items_html}</tbody>
            </table>
            <div class="total">
                Subtotal: ${sale.subtotal:.2f}<br>
                Tax: ${sale.tax:.2f}<br>
                <strong>TOTAL: ${sale.total:.2f}</strong><br>
                Payment: {sale.payment_method}
            </div>
            <div class="footer">
                Thank you for choosing Jessey Clinic!<br>Stay healthy.
            </div>
        </body>
        </html>
        '''
        return html
    
    @staticmethod
    def generate_pdf_receipt(sale, output_path=None):
        """
        Generate PDF receipt from sale.
        Requires weasyprint or wkhtmltopdf. Falls back to HTML.
        """
        html_content = ReceiptPrinter.generate_html_receipt(sale)
        
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"receipt_{sale.invoice_number}.pdf")
        
        try:
            # Try using weasyprint first
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(output_path)
            logger.info(f"PDF receipt generated: {output_path}")
            return output_path
        except ImportError:
            try:
                # Try wkhtmltopdf
                import pdfkit
                pdfkit.from_string(html_content, output_path)
                logger.info(f"PDF receipt generated via pdfkit: {output_path}")
                return output_path
            except ImportError:
                logger.warning("No PDF library available. Saving as HTML.")
                html_path = output_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return html_path
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None
    
    @staticmethod
    def print_receipt(sale, printer_name=None):
        """
        Print receipt directly (system dependent).
        """
        pdf_path = ReceiptPrinter.generate_pdf_receipt(sale)
        if not pdf_path:
            return False
        
        try:
            import platform
            system = platform.system()
            
            if system == 'Windows':
                # Use SumatraPDF or default print verb
                os.startfile(pdf_path, 'print')
            elif system == 'Darwin':  # macOS
                subprocess.run(['lp', pdf_path], check=True)
            else:  # Linux
                if printer_name:
                    subprocess.run(['lp', '-d', printer_name, pdf_path], check=True)
                else:
                    subprocess.run(['lp', pdf_path], check=True)
            logger.info(f"Receipt sent to printer: {sale.invoice_number}")
            return True
        except Exception as e:
            logger.error(f"Printing failed: {e}")
            return False