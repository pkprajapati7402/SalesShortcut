

import markdown
import os
import asyncio
import re
import logging
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

from google.adk.tools import FunctionTool

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image as RLImage, PageTemplate, Frame
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZemZenTemplate:
    """Custom page template for ZemZen branding.

    This class defines the visual layout for each page of the PDF, including a
    gradient background, a white content card, and a branded header/footer.
    """

    def __init__(self, doc):
        """Initializes the ZemZenTemplate.

        Args:
            doc: The ReportLab SimpleDocTemplate instance.
        """
        self.doc = doc
        self.page_count = 0

    def __call__(self, canvas, doc):
        """Draws the page template elements on each page.

        This method is called by ReportLab for every page generated. It handles
        drawing the background, content card, and appropriate header/footer.

        Args:
            canvas: The ReportLab canvas object for drawing.
            doc: The ReportLab SimpleDocTemplate instance.
        """
        self.page_count += 1
        canvas.saveState()

        width, height = A4
        self._draw_gradient_background(canvas, width, height)
        self._draw_content_card(canvas, width, height)

        if self.page_count == 1:
            self._draw_header(canvas, width, height)

        self._draw_footer(canvas, width, height)
        canvas.restoreState()

    def _draw_gradient_background(self, canvas, width, height):
        """Draws a simulated gradient background.

        Args:
            canvas: The ReportLab canvas object.
            width (float): The width of the page.
            height (float): The height of the page.
        """
        steps = 50
        for i in range(steps):
            ratio = i / steps
            r = int(0x66 + (0x76 - 0x66) * ratio)
            g = int(0x7e + (0x4b - 0x7e) * ratio)
            b = int(0xea + (0xa2 - 0xea) * ratio)

            color = colors.Color(r/255.0, g/255.0, b/255.0)
            canvas.setFillColor(color)

            rect_height = height / steps
            canvas.rect(0, height - (i + 1) * rect_height, width, rect_height, fill=1, stroke=0)

    def _draw_content_card(self, canvas, width, height):
        """Draws the white content card background with a shadow.

        Args:
            canvas: The ReportLab canvas object.
            width (float): The width of the page.
            height (float): The height of the page.
        """
        card_margin_x = 2*cm
        card_margin_y = 1.5*cm
        card_width = width - 2*card_margin_x
        card_height = height - card_margin_y - 4.5*cm
        card_x = card_margin_x
        card_y = card_margin_y

        canvas.setFillColor(white)
        canvas.setStrokeColor(colors.Color(0.9, 0.9, 0.9))
        canvas.setLineWidth(1)

        canvas.roundRect(card_x, card_y, card_width, card_height, 8, fill=1, stroke=1)

        shadow_offset = 3
        canvas.setFillColor(colors.Color(0, 0, 0, 0.1))
        canvas.roundRect(card_x + shadow_offset, card_y - shadow_offset, card_width, card_height, 8, fill=1, stroke=0)

        canvas.setFillColor(white)
        canvas.roundRect(card_x, card_y, card_width, card_height, 8, fill=1, stroke=1)

    def _draw_header(self, canvas, width, height):
        """Draws the ZemZen header on the first page.

        Args:
            canvas: The ReportLab canvas object.
            width (float): The width of the page.
            height (float): The height of the page.
        """
        canvas.setFont("Helvetica-Bold", 32)
        canvas.setFillColor(white)

        logo_y = height - 1.5*cm
        canvas.drawCentredString(width/2, logo_y, "🚀 ZemZen")

        canvas.setFont("Helvetica", 14)
        canvas.setFillColor(colors.Color(1, 1, 1, 0.9))
        canvas.drawCentredString(width/2, logo_y - 0.6*cm, "AI-Powered Lead Generation & Management Proposal \n")
        canvas.drawCentredString(width/2, logo_y - 0.9*cm, "\n Prepared by BrightWeb Studio")

    def _draw_footer(self, canvas, width, height):
        """Draws the page number footer on all pages.

        Args:
            canvas: The ReportLab canvas object.
            width (float): The width of the page.
            height (float): The height of the page.
        """
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
        canvas.drawCentredString(width/2, 0.8*cm, f"Page {self.page_count}")

class MarkdownToPDFConverter:
    """Converts Markdown content into ReportLab story elements with custom styling.

    This class handles the parsing of Markdown, converting it to HTML, and then
    transforming the HTML into ReportLab flowables (e.g., Paragraphs, Tables).
    """

    def __init__(self):
        """Initializes the MarkdownToPDFConverter with predefined styles."""
        self.styles = self._create_styles()
        self.story = []

    def _create_styles(self):
        """Creates and returns a dictionary of custom ReportLab ParagraphStyles."""
        styles = getSampleStyleSheet()

        primary_color = HexColor('#2563eb')
        gray_900 = HexColor('#111827')
        gray_700 = HexColor('#374151')
        gray_600 = HexColor('#4b5563')
        gray_200 = HexColor('#e5e7eb')
        gray_100 = HexColor('#f3f4f6')

        custom_styles = {
            'CustomTitle': ParagraphStyle(
                'CustomTitle', parent=styles['Heading1'], fontSize=22, spaceAfter=16,
                spaceBefore=8, textColor=primary_color, fontName='Helvetica-Bold',
                alignment=TA_LEFT, leading=28
            ),
            'CustomHeading1': ParagraphStyle(
                'CustomHeading1', parent=styles['Heading1'], fontSize=16, spaceAfter=12,
                spaceBefore=24, textColor=primary_color, fontName='Helvetica-Bold',
                alignment=TA_LEFT, leading=20
            ),
            'CustomHeading2': ParagraphStyle(
                'CustomHeading2', parent=styles['Heading2'], fontSize=14, spaceAfter=10,
                spaceBefore=20, textColor=primary_color, fontName='Helvetica-Bold',
                alignment=TA_LEFT, leading=18
            ),
            'CustomHeading3': ParagraphStyle(
                'CustomHeading3', parent=styles['Heading3'], fontSize=12, spaceAfter=8,
                spaceBefore=16, textColor=gray_900, fontName='Helvetica-Bold',
                alignment=TA_LEFT, leading=16
            ),
            'CustomBody': ParagraphStyle(
                'CustomBody', parent=styles['Normal'], fontSize=10, spaceAfter=10,
                spaceBefore=2, textColor=gray_700, fontName='Helvetica',
                alignment=TA_LEFT, leading=16
            ),
            'CustomBlockquote': ParagraphStyle(
                'CustomBlockquote', parent=styles['Normal'], fontSize=10, spaceAfter=16,
                spaceBefore=16, textColor=gray_700, fontName='Helvetica', alignment=TA_LEFT,
                leftIndent=24, rightIndent=24, borderColor=primary_color, borderWidth=1,
                borderPadding=12, backColor=HexColor('#f9fafb'), leading=16
            ),
            'CustomCode': ParagraphStyle(
                'CustomCode', parent=styles['Code'], fontSize=9, spaceAfter=12,
                spaceBefore=12, textColor=gray_700, fontName='Courier', backColor=gray_100,
                borderColor=gray_200, borderWidth=1, borderPadding=10, leftIndent=12,
                rightIndent=12, leading=12
            ),
            'CustomItalic': ParagraphStyle(
                'CustomItalic', parent=styles['Normal'], fontSize=10, spaceAfter=12,
                spaceBefore=4, textColor=gray_600, fontName='Helvetica-Oblique',
                alignment=TA_CENTER, leading=14
            ),
            'CustomListItem': ParagraphStyle(
                'CustomListItem', parent=styles['Normal'], fontSize=10, spaceAfter=6,
                spaceBefore=2, textColor=gray_700, fontName='Helvetica', alignment=TA_LEFT,
                leftIndent=20, leading=16
            )
        }

        for style_name, style_obj in custom_styles.items():
            styles.add(style_obj)

        return styles

    def _parse_html_to_elements(self, html_content):
        """Parses HTML content and appends ReportLab elements to the story.

        Args:
            html_content (str): The HTML string to parse.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'ul', 'ol', 'table', 'pre', 'code', 'hr', 'em', 'strong']):
            if element.name == 'h1':
                text = element.get_text().strip()
                if not self.story:
                    self.story.append(Paragraph(text, self.styles['CustomTitle']))
                else:
                    self.story.append(PageBreak())
                    self.story.append(Paragraph(text, self.styles['CustomHeading1']))

            elif element.name == 'h2':
                text = element.get_text().strip()
                self.story.append(Paragraph(text, self.styles['CustomHeading2']))

            elif element.name == 'h3':
                text = element.get_text().strip()
                self.story.append(Paragraph(text, self.styles['CustomHeading3']))

            elif element.name in ['h4', 'h5', 'h6']:
                text = element.get_text().strip()
                self.story.append(Paragraph(text, self.styles['CustomHeading3']))

            elif element.name == 'p':
                text = self._process_inline_elements(element)
                if text.strip():
                    if element.find('em') and len(element.get_text().strip()) < 100 and self.story and isinstance(self.story[-1], Paragraph) and self.story[-1].style == self.styles['CustomTitle']:
                        self.story.append(Paragraph(text, self.styles['CustomItalic']))
                    else:
                        self.story.append(Paragraph(text, self.styles['CustomBody']))

            elif element.name == 'blockquote':
                text = element.get_text().strip()
                self.story.append(Paragraph(text, self.styles['CustomBlockquote']))

            elif element.name in ['ul', 'ol']:
                self._process_list(element)

            elif element.name == 'table':
                self._process_table(element)

            elif element.name == 'pre':
                code_text = element.get_text()
                self.story.append(Paragraph(f'<font name="Courier">{code_text}</font>', self.styles['CustomCode']))

            elif element.name == 'hr':
                self.story.append(Spacer(1, 16))
                from reportlab.platypus import HRFlowable
                hr = HRFlowable(width="100%", thickness=1, color=HexColor('#e5e7eb'), spaceAfter=0, spaceBefore=0)
                self.story.append(hr)
                self.story.append(Spacer(1, 16))

    def _process_inline_elements(self, element):
        """Processes inline HTML elements (bold, italic, code, links) for ReportLab.

        Args:
            element (bs4.Tag): The BeautifulSoup tag element to process.

        Returns:
            str: The HTML string with ReportLab-compatible inline styling.
        """
        html_str = str(element)
        html_str = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', html_str)
        html_str = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', html_str)
        html_str = re.sub(r'<code>(.*?)</code>', r'<font name="Courier" backColor="#f3f4f6">\1</font>', html_str)
        html_str = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'<font color="#2563eb">\2</font>', html_str)
        html_str = re.sub(r'^<p[^>]*>', '', html_str)
        html_str = re.sub(r'</p>$', '', html_str)
        html_str = unescape(html_str)
        return html_str

    def _process_list(self, list_element):
        """Processes HTML list elements (ul, ol) and adds them to the story.

        Args:
            list_element (bs4.Tag): The BeautifulSoup list element.
        """
        self.story.append(Spacer(1, 6))

        items = list_element.find_all('li')
        for i, item in enumerate(items):
            text = self._process_inline_elements(item)
            if list_element.name == 'ul':
                list_text = f'<font name="Helvetica-Bold" size="10" color="{HexColor("#2563eb")}">•</font> {text}'
            else:
                list_text = f'{i+1}. {text}'

            para = Paragraph(list_text, self.styles['CustomListItem'])
            self.story.append(KeepTogether([para]))

        self.story.append(Spacer(1, 10))

    def _process_table(self, table_element):
        """Processes HTML table elements and adds them to the story.

        Args:
            table_element (bs4.Tag): The BeautifulSoup table element.
        """
        rows_data = []

        thead = table_element.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                header_cells = [Paragraph(cell.get_text().strip(), self.styles['CustomBody']) for cell in header_row.find_all(['th', 'td'])]
                rows_data.append(header_cells)

        tbody = table_element.find('tbody') or table_element
        for row in tbody.find_all('tr'):
            if row.parent.name != 'thead':
                cells = [Paragraph(cell.get_text().strip(), self.styles['CustomBody']) for cell in row.find_all(['td', 'th'])]
                if cells:
                    rows_data.append(cells)

        if rows_data:
            num_cols = len(rows_data[0])
            available_width = A4[0] - (2 * 3.2*cm)
            col_widths = [available_width / num_cols] * num_cols

            table = Table(rows_data, colWidths=col_widths)

            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#374151')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [None, HexColor('#f9fafb')]),
                ('BOX', (0,0), (-1,-1), 1, HexColor('#e5e7eb')),
            ]

            table.setStyle(TableStyle(table_style))

            self.story.append(Spacer(1, 12))
            self.story.append(KeepTogether([table]))
            self.story.append(Spacer(1, 16))

    def convert_markdown_to_story(self, markdown_content):
        """Converts markdown content to ReportLab story elements.

        Args:
            markdown_content (str): The Markdown string to convert.

        Returns:
            list: A list of ReportLab flowable objects representing the content.
        """
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        self._parse_html_to_elements(html_content)
        return self.story

def create_sales_proposal_pdf(markdown_offer: str) -> str:
    """Creates a PDF sales proposal file from Markdown offer.

    This function takes Markdown-formatted content, converts it into a styled
    PDF document, and saves it to the current working directory. Returnting the 'offer_file_path' key.

    Args:
        markdown_offer (str): The Markdown content representing the sales proposal.

    Returns:
        str: The absolute file path of the created PDF proposal. Save this as 'offer_file_path' in state.

    Raises:
        Exception: If an error occurs during PDF generation.
    """
    logger.info("⚒️ [TOOL] Starting PDF generation process with `create_sales_proposal_pdf` function.")
    logger.debug(f"Markdown content length: {len(markdown_offer)} characters")
    
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    output_pdf_file = os.path.join(current_dir, "ZemZenProposal.pdf")

    try:
        doc = SimpleDocTemplate(
            output_pdf_file,
            pagesize=A4,
            rightMargin=3.2*cm,
            leftMargin=3.2*cm,
            topMargin=3.2*cm,
            bottomMargin=2.8*cm,
        )

        template_drawer = ZemZenTemplate(doc)

        converter = MarkdownToPDFConverter()
        story = converter.convert_markdown_to_story(markdown_offer)

        # Add initial spacing for aesthetic alignment with the custom page template
        story.insert(0, Spacer(1, 0.8*cm))

        doc.build(story, onFirstPage=template_drawer, onLaterPages=template_drawer)

        logger.info(f"✅ PDF successfully created: {output_pdf_file}")
        return output_pdf_file

    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        raise
    
create_offer_file = FunctionTool(func=create_sales_proposal_pdf)