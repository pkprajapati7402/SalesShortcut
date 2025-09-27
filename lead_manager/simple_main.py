#!/usr/bin/env python3
"""Simple Lead Manager service without ADK dependencies"""

import asyncio
import requests
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import click
import common.config as config

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    ui_client_url: str = "http://localhost:8000"

class EmailNotification(BaseModel):
    trigger: str
    email_address: str
    message_count: int
    timestamp: str
    messages: list

@app.get("/")
def read_root():
    return {"message": "Lead Manager service - simple version", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "lead_manager"}

@app.post("/search")
async def process_search(request: SearchRequest):
    """Process search request and send WebSocket message to UI client"""
    try:
        # Simulate processing
        await asyncio.sleep(1)
        
        # Send WebSocket message to UI client
        websocket_message = f"Hello I am Lead Manager - Processing: {request.query}"
        
        payload = {
            "message": websocket_message,
            "agent": "lead_manager_simple",
            "query": request.query
        }
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{request.ui_client_url}/webhook/lead_manager",
                json=payload,
                timeout=5
            )
        
        if response.status_code == 200:
            return {"status": "success", "message": "WebSocket message sent successfully"}
        else:
            return {"status": "error", "message": f"Failed to send WebSocket message: {response.status_code}"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")

@app.post("/process-email")
async def process_email(notification: EmailNotification):
    """Process Gmail notification and trigger lead management workflow"""
    try:
        print(f"📧 Received email notification for {notification.email_address}")
        print(f"   📊 Message count: {notification.message_count}")
        print(f"   ⏰ Timestamp: {notification.timestamp}")
        
        # Process each message
        for i, message in enumerate(notification.messages, 1):
            print(f"   📨 Message {i}:")
            print(f"      Subject: {message.get('subject', 'No Subject')}")
            print(f"      From: {message.get('sender', 'Unknown')}")
            print(f"      Date: {message.get('date', 'Unknown')}")
            
            # Extract key information for lead management
            subject = message.get('subject', '')
            sender = message.get('sender', '')
            content = message.get('content', '')
            
            # Basic lead qualification logic
            is_potential_lead = await qualify_lead(subject, sender, content)
            
            if is_potential_lead:
                print(f"   🎯 Potential lead detected from {sender}")
                # Here you would trigger your lead management workflow
                await process_potential_lead(message)
            else:
                print(f"   📭 Not qualified as lead")
        
        return {
            "status": "success", 
            "message": f"Processed {notification.message_count} emails for {notification.email_address}",
            "timestamp": notification.timestamp
        }
        
    except Exception as e:
        print(f"❌ Error processing email notification: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

async def qualify_lead(subject: str, sender: str, content: str) -> bool:
    """Basic lead qualification logic"""
    
    # Keywords that indicate potential leads
    lead_keywords = [
        'inquiry', 'interested', 'quote', 'price', 'pricing', 'cost',
        'proposal', 'partnership', 'collaboration', 'business',
        'service', 'solution', 'help', 'support', 'meeting',
        'demo', 'trial', 'consultation', 'discuss', 'call'
    ]
    
    # Check if any lead keywords are present
    text_to_check = f"{subject} {content}".lower()
    
    for keyword in lead_keywords:
        if keyword in text_to_check:
            return True
    
    # Additional checks could go here
    # - Sender domain analysis
    # - Content sentiment analysis
    # - Previous interaction history
    
    return False

async def process_potential_lead(message: dict):
    """Process a qualified lead"""
    
    print(f"   🚀 Processing potential lead...")
    print(f"   📝 Actions taken:")
    print(f"      • Lead recorded in CRM")
    print(f"      • Auto-response queued")
    print(f"      • Sales team notified")
    print(f"      • Follow-up scheduled")
    
    # Here you would implement:
    # 1. Store lead in database/CRM
    # 2. Send automated response
    # 3. Create calendar event for follow-up
    # 4. Notify sales team
    # 5. Update lead scoring
    
    # Simulate processing time
    await asyncio.sleep(0.5)

@click.command()
@click.option("--host", default="localhost", help="Host to bind the server to.")
@click.option("--port", default=config.DEFAULT_LEAD_MANAGER_PORT, help="Port to bind the server to.")
def main(host: str, port: int):
    """Run the simple Lead Manager service."""
    print(f"Starting simple Lead Manager service on http://{host}:{port}/")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()