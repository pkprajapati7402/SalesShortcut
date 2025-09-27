"""
Gmail Service Account Tool - No manual authentication required.
Uses service account with domain-wide delegation to send emails.
Based on working example with attachment support.
"""

import os
import base64
import mimetypes
import logging
from typing import Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.adk.tools import FunctionTool

from sdr.sdr.config import SERVICE_ACCOUNT_FILE, SALES_EMAIL, GMAIL_SCOPES

# Setup logger for this module
logger = logging.getLogger(__name__)


def create_service_account_credentials():
    """
    Creates service account credentials with domain-wide delegation.
    Handles both local development (JSON file) and cloud deployment scenarios.
    
    Returns:
        google.oauth2.service_account.Credentials: Delegated credentials for the sales email
    """
    try:
        logger.info(f"🔑 Setting up service account authentication for {SALES_EMAIL}...")
        logger.info(f"Setting up service account authentication for {SALES_EMAIL}")
        
        # Try to use environment variable for cloud deployment first
        credentials = None
        
        # Check if SERVICE_ACCOUNT_FILE is set (cloud deployment)
        if os.getenv('SERVICE_ACCOUNT_FILE'):
            logger.info("📁 Using SERVICE_ACCOUNT_FILE environment variable...")
            logger.info(f"Using SERVICE_ACCOUNT_FILE: {os.getenv('SERVICE_ACCOUNT_FILE')}")
            credentials = service_account.Credentials.from_service_account_file(
                os.getenv('SERVICE_ACCOUNT_FILE'), scopes=GMAIL_SCOPES
            )
        # Check if service account file exists locally
        elif os.path.exists(SERVICE_ACCOUNT_FILE):
            logger.info(f"📁 Using local service account file: {SERVICE_ACCOUNT_FILE}")
            logger.info(f"Using local service account file: {SERVICE_ACCOUNT_FILE}")
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=GMAIL_SCOPES
            )
        else:
            # Try default cloud credentials (for Cloud Run with service account attached)
            try:
                logger.info("☁️ Attempting to use default Cloud credentials...")
                logger.info("Attempting to use default Cloud credentials")
                from google.auth import default
                credentials, _ = default(scopes=GMAIL_SCOPES)
            except Exception as default_error:
                logger.error(f"Default credentials failed: {default_error}")
                raise FileNotFoundError(
                    f"No service account credentials found. Tried:\n"
                    f"1. SERVICE_ACCOUNT_FILE env var\n"
                    f"2. Local file: {SERVICE_ACCOUNT_FILE}\n"
                    f"3. Default cloud credentials\n"
                    f"Default credentials error: {default_error}"
                )
        
        # Create delegated credentials for the sales email
        if hasattr(credentials, 'with_subject'):
            delegated_credentials = credentials.with_subject(SALES_EMAIL)
            logger.info(f"Created delegated credentials for {SALES_EMAIL}")
        else:
            # For some credential types, we might not need delegation
            delegated_credentials = credentials
            logger.info("Using non-delegated credentials")
        
        logger.info(f"✅ Service account authentication successful for {SALES_EMAIL}")
        logger.info(f"Service account authentication successful for {SALES_EMAIL}")
        return delegated_credentials
        
    except Exception as e:
        logger.error(f"❌ Service account setup failed: {e}")
        logger.error(f"Service account setup failed: {e}", exc_info=True)
        raise


def send_email(to_email: str, subject: str, body: str, attachment_path: Optional[str] = None) -> dict[str, Any]:
    """
    Send email from sales account with optional attachment using service account.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_path: Optional path to attachment file
        
    Returns:
        dict containing send result with status and message/error info
    """
    try:
        logger.info("🚀 SEND_EMAIL_WITH_ATTACHMENT FUNCTION CALLED!")
        logger.info(f"Function called with: to_email={to_email}, subject={subject[:50] if subject else 'None'}..., body_length={len(body) if body else 0}, attachment_path={attachment_path}")
        logger.info(f"📧 Preparing to send email to {to_email}")
        logger.info(f"   From: {SALES_EMAIL}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"Preparing to send email from {SALES_EMAIL} to {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body length: {len(body)} characters")
        
        if attachment_path:
            logger.info(f"   Attachment: {attachment_path}")
            logger.info(f"Attachment path: {attachment_path}")
        
        # Check if attachment exists
        if attachment_path and not os.path.exists(attachment_path):
            logger.warning(f"⚠️  Warning: Attachment file not found at {attachment_path}")
            logger.warning("   Sending email without attachment...")
            logger.warning(f"Attachment file not found at {attachment_path}")
            attachment_path = None
        
        # Create credentials
        logger.info("Creating service account credentials...")
        credentials = create_service_account_credentials()
        
        # Create Gmail service
        logger.info("Building Gmail service...")
        service = build('gmail', 'v1', credentials=credentials)
        logger.info("Gmail service created successfully")
        
        # Create message with or without attachment
        if attachment_path and os.path.exists(attachment_path):
            logger.info("📎 Adding attachment...")
            message = MIMEMultipart()
            message.attach(MIMEText(body, 'plain'))
            
            # Add attachment
            content_type, encoding = mimetypes.guess_type(attachment_path)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'  # Default type
            
            main_type, sub_type = content_type.split('/', 1)
            
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
            
            attachment_part = MIMEBase(main_type, sub_type)
            attachment_part.set_payload(file_data)
            encoders.encode_base64(attachment_part)
            
            filename = os.path.basename(attachment_path)
            attachment_part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            message.attach(attachment_part)
            logger.info(f"✅ Attachment added: {filename}")
        else:
            # Simple text message if no attachment
            message = MIMEText(body, 'plain')
        
        # Set email headers
        message['to'] = to_email
        message['from'] = SALES_EMAIL
        message['subject'] = subject
        
        # Send email
        logger.info("📤 Sending email...")
        logger.info("Encoding email message...")
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        logger.info(f"Raw message length: {len(raw_message)} characters")
        
        logger.info("Calling Gmail API to send email...")
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        message_id = result.get('id')
        thread_id = result.get('threadId')
        
        logger.info("✅ EMAIL SENT SUCCESSFULLY!")
        logger.info(f"   Message ID: {message_id}")
        logger.info(f"   Thread ID: {thread_id}")
        logger.info(f"Email sent successfully! Message ID: {message_id}, Thread ID: {thread_id}")
        
        if attachment_path and os.path.exists(attachment_path):
            logger.info(f"   📎 Attachment: {os.path.basename(attachment_path)} included")
            logger.info(f"Attachment included: {os.path.basename(attachment_path)}")
        logger.info(f"   📬 Check {to_email} inbox!")
        
        return {
            "status": "success",
            "message_id": message_id,
            "thread_id": thread_id,
            "message": f"Email sent successfully from {SALES_EMAIL} to {to_email}",
            "attachment_included": attachment_path is not None and os.path.exists(attachment_path)
        }
        
    except HttpError as error:
        error_details = str(error)
        logger.error(f"❌ Gmail API error: {error_details}")
        logger.error(f"Gmail API error: {error_details}", exc_info=True)
        return {
            "status": "failed",
            "error": f"Gmail API error: {error_details}",
            "message": f"Failed to send email from {SALES_EMAIL} to {to_email}"
        }
        
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        logger.error(f"Email sending failed: {e}", exc_info=True)
        return {
            "status": "failed", 
            "error": str(e),
            "message": f"Failed to send email from {SALES_EMAIL} to {to_email}"
        }

def send_email_with_attachment(crafted_email: dict[str, Any], attachment_path: Optional[str] = None, tool_context=None) -> dict[str, Any]:
    """
    Tool function to send email with optional attachment.

    Args:
        crafted_email: dict containing email details with keys 'to', 'subject', and 'body'
        attachment_path: Optional path to attachment file
        tool_context: Tool execution context to check state

    Returns:
        dict containing send result with status and message/error info
    """
    logger.info(f"[TOOL] Crafted email received: {crafted_email}")
    logger.info(f"[TOOL] Attachment path received: {attachment_path}")
    
    # Check if email was already sent successfully (similar to human_creation tool pattern)
    try:
        existing_email_result = tool_context.state.get("email_sent_result", "") if tool_context else ""
    except Exception:
        existing_email_result = None
    
    if existing_email_result and isinstance(existing_email_result, dict) and existing_email_result.get("status") == "success":
        logger.info(f"Skipping email send: email already sent successfully: {existing_email_result}")
        return existing_email_result
    
    # Ensure crafted_email has required fields
    if not crafted_email or not isinstance(crafted_email, dict):
        error_msg = f"Invalid crafted_email format. Must be a dict with 'to', 'subject', and 'body'. Received: {type(crafted_email)} - {crafted_email}"
        logger.error(f"[TOOL ERROR] {error_msg}")
        return {
            "status": "failed",
            "error": error_msg
        }
    to_email = crafted_email.get('to')
    subject = crafted_email.get('subject', '')
    body = crafted_email.get('body', '')
    
    # Validate required fields
    if not to_email:
        error_msg = f"Missing required 'to' field in crafted_email. Received: {crafted_email}"
        logger.error(f"[TOOL ERROR] {error_msg}")
        return {
            "status": "failed",
            "error": error_msg
        }
    
    logger.info(f"[TOOL] Calling send_email with: to={to_email}, subject='{subject}', body_length={len(body)}, attachment={attachment_path}")
    result = send_email(to_email, subject, body, attachment_path)
    
    # Store result in state to prevent re-execution if successful
    if tool_context and result.get("status") == "success":
        try:
            tool_context.state["email_sent_result"] = result
            logger.info("Stored successful email result in state to prevent re-execution")
        except Exception as e:
            logger.warning(f"Could not store email result in state: {e}")
    
    return result

send_email_with_attachment_tool = FunctionTool(func=send_email_with_attachment)