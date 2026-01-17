# BigQuery Setup Guide

This guide will help you set up BigQuery for the SalesShortcut project.

## 📋 Prerequisites

- Google Cloud Project: `safe-link-439210` ✅ (already configured)
- gcloud CLI installed
- BigQuery API enabled in your project

## 🚀 Quick Setup (Choose One Method)

### Method 1: Application Default Credentials (Development - Recommended)

**Best for**: Local development, testing

```bash
# Step 1: Login to Google Cloud
gcloud auth application-default login --project=safe-link-439210

# Step 2: That's it! Your project is ready to use BigQuery
```

**Verify it works:**
```bash
# Test BigQuery connection
gcloud auth application-default print-access-token
```

---

### Method 2: Service Account (Production)

**Best for**: Production deployments, Cloud Run, automated systems

#### Step 1: Enable BigQuery API
```bash
gcloud services enable bigquery.googleapis.com --project=safe-link-439210
```

#### Step 2: Create Service Account
```bash
gcloud iam service-accounts create salesshortcut-sa \
  --display-name="SalesShortcut Service Account" \
  --description="Service account for SalesShortcut BigQuery operations" \
  --project=safe-link-439210
```

#### Step 3: Grant Permissions

Grant BigQuery permissions:
```bash
# BigQuery Admin (full access - recommended for development)
gcloud projects add-iam-policy-binding safe-link-439210 \
  --member="serviceAccount:salesshortcut-sa@safe-link-439210.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

Or for more restrictive permissions:
```bash
# BigQuery Data Editor + Job User (production)
gcloud projects add-iam-policy-binding safe-link-439210 \
  --member="serviceAccount:salesshortcut-sa@safe-link-439210.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding safe-link-439210 \
  --member="serviceAccount:salesshortcut-sa@safe-link-439210.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

#### Step 4: Create Key File
```bash
# Create .secrets directory
mkdir -p .secrets

# Download service account key
gcloud iam service-accounts keys create .secrets/salesshortcut-key.json \
  --iam-account=salesshortcut-sa@safe-link-439210.iam.gserviceaccount.com \
  --project=safe-link-439210

# Secure the file
chmod 600 .secrets/salesshortcut-key.json

# Add to gitignore (already done, but verify)
echo ".secrets/" >> .gitignore
```

#### Step 5: Update .env

Uncomment this line in your `.env` file:
```bash
GOOGLE_APPLICATION_CREDENTIALS=.secrets/salesshortcut-key.json
```

---

## ✅ Verification

### Test BigQuery Connection

Run this command to test your setup:

```bash
# Test with Python
python3 << EOF
from google.cloud import bigquery
import os

# This will use either ADC or service account from .env
project = "safe-link-439210"
client = bigquery.Client(project=project)

# List datasets
datasets = list(client.list_datasets())
if datasets:
    print("✅ BigQuery connection successful!")
    print(f"   Found {len(datasets)} dataset(s):")
    for dataset in datasets:
        print(f"   - {dataset.dataset_id}")
else:
    print("✅ BigQuery connection successful! (No datasets yet)")
    print("   Datasets will be created automatically when you run the app")
EOF
```

### Or use gcloud command:

```bash
# List BigQuery datasets
bq ls --project_id=safe-link-439210

# Should show: lead_finder_data, lead_manager_data, sdr_data (if created)
# Or show empty list (datasets auto-create on first use)
```

---

## 🗄️ Database Structure

The application will automatically create these datasets and tables:

### **Dataset: `lead_finder_data`**
- **Table: `business_leads`** - Discovered potential leads
  - Columns: place_id, name, address, phone, website, category, rating, etc.

### **Dataset: `lead_manager_data`**
- **Table: `hot_leads`** - Qualified interested leads
  - Columns: email, name, business_info, interest_level, etc.
- **Table: `meetings_arranged`** - Scheduled meetings
  - Columns: meeting_id, lead_email, meeting_time, status, etc.

### **Dataset: `sdr_data`**
- **Table: `sdr_results`** - Outreach interactions
  - Columns: sdr_run_id, business_name, call_category, proposal, transcript, etc.

---

## 🔍 View Your Data

### BigQuery Console
Visit: [https://console.cloud.google.com/bigquery?project=safe-link-439210](https://console.cloud.google.com/bigquery?project=safe-link-439210)

### Query Example
```sql
-- View all discovered leads
SELECT 
  name, 
  address, 
  phone, 
  website,
  created_at
FROM `safe-link-439210.lead_finder_data.business_leads`
ORDER BY created_at DESC
LIMIT 10;
```

```sql
-- View hot leads
SELECT 
  email,
  name,
  interest_level,
  created_at
FROM `safe-link-439210.lead_manager_data.hot_leads`
WHERE interest_level = 'high'
ORDER BY created_at DESC;
```

```sql
-- View SDR call results
SELECT 
  business_name,
  call_category,
  timestamp
FROM `safe-link-439210.sdr_data.sdr_results`
ORDER BY timestamp DESC
LIMIT 10;
```

---

## 🛠️ Troubleshooting

### Error: "Permission denied"
```bash
# Re-authenticate
gcloud auth application-default login --project=safe-link-439210

# Or verify service account permissions
gcloud projects get-iam-policy safe-link-439210 \
  --flatten="bindings[].members" \
  --filter="bindings.members:salesshortcut-sa@safe-link-439210.iam.gserviceaccount.com"
```

### Error: "Dataset not found"
✅ This is normal! Datasets and tables are created automatically on first use.

### Error: "API not enabled"
```bash
# Enable BigQuery API
gcloud services enable bigquery.googleapis.com --project=safe-link-439210
```

### Check current authentication
```bash
# For ADC
gcloud auth application-default print-access-token

# For service account
export GOOGLE_APPLICATION_CREDENTIALS=.secrets/salesshortcut-key.json
python3 -c "from google.cloud import bigquery; print('✅ Service account works!')"
```

---

## 💰 Cost Considerations

BigQuery pricing:
- **Storage**: $0.02 per GB per month (first 10GB free)
- **Queries**: $5 per TB processed (first 1TB free per month)

Expected costs for SalesShortcut:
- **Storage**: < $0.10/month (small dataset)
- **Queries**: $0 (well within free tier)
- **Total**: ~$0/month for typical usage

---

## 🚀 Next Steps

1. ✅ Choose authentication method (ADC recommended for development)
2. ✅ Run authentication setup
3. ✅ Test connection with verification script
4. ✅ Run the application - datasets/tables will auto-create
5. ✅ View data in BigQuery console

## 📚 Additional Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [BigQuery Pricing](https://cloud.google.com/bigquery/pricing)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
