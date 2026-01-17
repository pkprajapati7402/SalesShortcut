# 🧪 Quick Test Setup (No BigQuery Required)

## For TESTING ONLY - Simplified Setup

Good news! You can test the project WITHOUT setting up BigQuery. The code has built-in fallback mechanisms.

## 🚀 Simple Test Setup (3 Steps)

### Step 1: Install Dependencies
```bash
cd /workspaces/SalesShortcut
pip install -r requirements.txt
```

### Step 2: Keep Your Current .env (Already Good!)
Your `.env` file is already configured with:
- ✅ GOOGLE_API_KEY (working)
- ✅ OPENROUTER_API_KEY (working)
- ✅ All other keys set

**No changes needed!**

### Step 3: Run in Test Mode
```bash
# Option A: Run Lead Finder (will use mock data + local JSON fallback)
python -m lead_finder --port 8081

# Option B: Run SDR Agent
python -m sdr --port 8084

# Option C: Run UI Dashboard
python -m ui_client --port 8000
```

## 📝 What Happens in Test Mode?

### Without BigQuery Authentication:
- ✅ **LLM works**: Uses your Google API key (working!)
- ✅ **Google Maps**: Uses mock data (GOOGLE_MAPS_API_KEY is empty)
- ⚠️ **BigQuery**: Falls back to **local JSON files** for data storage
- ✅ **Everything else works**: Email, phone calls, etc.

### Data Storage (Without BigQuery):
The system will save data to local JSON files:
```
lead_finder_output_20260116_123456.json
sdr_bigquery_upload_20260116_123456.json
lead_manager_meeting_20260116_123456.json
```

## 🧪 Quick Test Commands

### Test 1: Lead Finder with Mock Data
```bash
# Terminal 1: Start Lead Finder
python -m lead_finder --port 8081

# Terminal 2: Test search
curl -X POST http://localhost:8081/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee shops in San Francisco",
    "limit": 5
  }'
```

**Expected Result**: Returns mock business data + saves to JSON file

### Test 2: Check Logs
```bash
# Watch the logs - you'll see:
# "BigQuery client not available - using fallback"
# "Saving to local JSON file: lead_finder_output_*.json"
```

## 📊 What You'll See

### In the Terminal:
```
⚠️  BigQuery client not available - using fallback mode
✅ Using mock Google Maps data (GOOGLE_MAPS_API_KEY not set)
✅ Gemini LLM initialized successfully
💾 Saving results to: lead_finder_output_20260116_123456.json
✅ Lead Finder Agent started on port 8081
```

### Data Files Created:
```bash
ls -lh *.json
# You'll see timestamped JSON files with your results
```

## 🎯 This is Perfect for:
- ✅ Testing the system flow
- ✅ Verifying LLM integration works
- ✅ Testing agent interactions
- ✅ UI/UX testing
- ✅ Development and debugging

## 🚫 Limitations (Test Mode):
- ❌ No persistent database (data in JSON files)
- ❌ Can't query historical data
- ❌ No duplicate detection across runs
- ❌ Mock business data (not real)

## 🆙 When You Want Real Production Setup

Later, when you're ready for production, follow: [BIGQUERY_SETUP.md](./BIGQUERY_SETUP.md)

But you don't need that now for testing!

## 🎮 Try It Now!

```bash
# Just run this:
python -m lead_finder --port 8081

# Open another terminal and try:
curl http://localhost:8081/health

# Should return: {"status": "healthy"}
```

## ❓ Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
pip install -r lead_finder/requirements.txt
```

### "Port already in use"
```bash
# Use a different port
python -m lead_finder --port 8091
```

### "Google API Key error"
Your key is already working! If you see errors, check:
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('GOOGLE_API_KEY')[:20] + '...')
"
```

## ✅ Summary

**You DON'T need to**:
- ❌ Install gcloud CLI
- ❌ Set up BigQuery
- ❌ Configure service accounts
- ❌ Enable Google Cloud APIs

**You CAN test**:
- ✅ All agent functionality
- ✅ LLM integration
- ✅ System workflows
- ✅ UI dashboard
- ✅ Mock data processing

**Just run**:
```bash
pip install -r requirements.txt
python -m lead_finder --port 8081
```

That's it! 🎉
