import weasyprint
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional
from src.render.template_engine import TemplateEngine
from src.models.context_model import PageContext, SharedContext
from src.core.asset_manager import AssetManager, AssetType
import fitz


class PDFService:
    def __init__(self, template_engine: TemplateEngine, asset_manager: AssetManager):
        self.template_engine = template_engine
        self.asset_manager = asset_manager

    def generate_page_pdf(self, page_context: PageContext, shared_context: SharedContext, page_index: int) -> tuple:
        """
        Generate a PDF for a single page using the template engine and page context.
        """
        # Prepare the context for template rendering
        # Convert View objects to dict format expected by template
        views_for_template = []
        for view in page_context.views:
            views_for_template.append({
                "side": view.side.value if hasattr(view.side, 'value') else view.side,
                "image": view.image,
                "wall_image": view.wall_image,
                "pano": view.pano
            })

        # Convert table data to template format
        table_data_for_template = None
        if page_context.table_data:
            table_data_for_template = {
                "headers": page_context.table_data.headers,
                "data": page_context.table_data.data
            }

        # Create context for template rendering
        context = {
            "page_title": page_context.page_title,
            "embedded_css": shared_context.embedded_css,
            "generation_date": page_context.generation_date,
            "page_number": page_context.page_number,
            "total_pages": 1,  # For single page PDF
            "document_name": shared_context.document_name,
            "document_id": shared_context.document_id,
            "address_line": shared_context.address_line,
            "powered_by_logo_url": shared_context.powered_by_logo_url,
            "header_logo_url": shared_context.header_logo_url,
            "views": views_for_template,
            "table_data": table_data_for_template,
        }
        # Render the HTML using the base template
        rendered_html = self.template_engine.render("base.html", context)


        # Convert HTML to PDF using WeasyPrint (will be skipped if library is unavailable)
        try:
            html_doc = weasyprint.HTML(string=rendered_html)
            css_doc = weasyprint.CSS(string=shared_context.embedded_css if shared_context.embedded_css else '')
            pdf_bytes = html_doc.write_pdf(stylesheets=[css_doc])
            doc = fitz.open("pdf", pdf_bytes)
            page = doc.load_page(0)
            pix = page.get_pixmap()
            preview_bytes = pix.tobytes("png")
            return pdf_bytes, preview_bytes
        except Exception as e:
            # If WeasyPrint fails, return an empty PDF or basic content
            # This is a fallback when system libraries are not available
            print(e)
            return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(PDF Generation Error) Tj\nET\nendstream\nendobj\n5 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000101 00000 n \n0000000242 00000 n \n0000000418 00000 n \n0000000503 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n581\n%%EOF', b''

    def save_page_pdf(self, page_context: PageContext, shared_context: SharedContext, page_index: int) -> tuple:
        """
        Generate and save or replace a PDF for a page, returning the asset URL.

        Args:
            page_context: The page context containing the data for the PDF
            shared_context: The shared document context
            page_index: The index of the page to save/replace
            replace: If True, replace existing assets; if False, create new ones

        Returns:
            tuple: (pdf_url, preview_url) for the saved PDF
        """
        pdf_bytes, preview = self.generate_page_pdf(page_context, shared_context, page_index)
        # Save to disk for testing
        # test_dir = Path(__file__).parent / "test_pdfs"
        # test_dir.mkdir(parents=True, exist_ok=True)
        # test_pdf_path = test_dir / f"page_{page_index + 1}_{page_context.page_title.replace(' ', '_')}.pdf"
        # with open(test_pdf_path, "wb") as f:
        #     f.write(pdf_bytes)

        # Generate a unique name for the PDF
        pdf_asset_name = f"page_{page_index + 1}_{page_context.page_title.replace(' ', '_')}.pdf"
        preview_name = f"{pdf_asset_name}_preview.png"


        # Save to asset manager
        self.asset_manager.save(pdf_asset_name, pdf_bytes, AssetType.PDF)
        self.asset_manager.save(preview_name, preview, AssetType.PNG)

        # Return the URL for the PDF
        pdf_url = self.asset_manager.get_public_url(pdf_asset_name, AssetType.PDF)
        preview_url = self.asset_manager.get_public_url(preview_name, AssetType.PNG)
        return pdf_url, preview_url