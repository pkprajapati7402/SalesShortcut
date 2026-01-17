# Cost Optimization Guide

This project has been configured to run cost-effectively within a $10 OpenRouter credit budget.

## Current Model Configuration

### Primary Models (Free/Very Cheap)
- **MODEL**: `gemini-2.0-flash-lite` - Free tier available via Google AI Studio
- **MODEL_THINK**: `gemini-2.0-flash-thinking-exp` - Free tier for reasoning tasks

### Cost Breakdown
Google Gemini models via Google AI Studio API are **FREE** up to generous rate limits:
- **gemini-2.0-flash-lite**: 1500 requests/day, 1,000,000 tokens/minute
- **gemini-2.0-flash-thinking-exp**: Free experimental model

## OpenRouter Configuration (Optional Fallback)

If you want to use OpenAI or Anthropic models through OpenRouter:

### Recommended Cost-Effective Models
1. **openai/gpt-4o-mini** - ~$0.15 per 1M input tokens, $0.60 per 1M output tokens
2. **anthropic/claude-3-haiku** - ~$0.25 per 1M input tokens, $1.25 per 1M output tokens
3. **google/gemini-2.0-flash** - ~$0.075 per 1M tokens (also available free via Google)

### Estimated Costs ($10 Budget)
With GPT-4o-mini at average 100K tokens per lead cycle:
- **Input**: ~$0.015 per cycle
- **Output**: ~$0.06 per cycle
- **Total**: ~$0.075 per complete lead cycle
- **Budget**: ~133 complete lead cycles with $10

### Using OpenRouter in Code

Your `.env` is already configured with:
```bash
OPENROUTER_API_KEY=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
OPENAI_API_BASE=https://openrouter.ai/api/v1
ANTHROPIC_API_BASE=https://openrouter.ai/api/v1
```

## Model Selection Strategy

### Recommended Configuration (Current)
```bash
MODEL=gemini-2.0-flash-lite              # Fast, free, good quality
MODEL_THINK=gemini-2.0-flash-thinking-exp # Free reasoning model
```

### Alternative: OpenRouter with Budget Models
```bash
MODEL=google/gemini-2.0-flash-lite       # Via OpenRouter
MODEL_THINK=openai/gpt-4o-mini           # For complex reasoning
```

### Alternative: Ultra-Cheap OpenRouter
```bash
MODEL=meta-llama/llama-3.2-3b-instruct   # ~$0.06/$0.06 per 1M tokens
MODEL_THINK=openai/gpt-4o-mini           # ~$0.15/$0.60 per 1M tokens
```

## Cost Monitoring

### Track Your Usage
1. **Google AI Studio**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) - Check quota usage
2. **OpenRouter**: [https://openrouter.ai/credits](https://openrouter.ai/credits) - Check credit balance

### Optimization Tips
1. **Use Gemini models via Google AI Studio** (current config) - Completely free
2. **Reduce temperature** for deterministic outputs (less retries)
3. **Use MODEL_THINK only for complex reasoning** tasks
4. **Cache results** where possible to avoid re-processing
5. **Batch operations** instead of individual API calls

## API Key Priority

The system will attempt to use APIs in this order:
1. **Google AI Studio API** (GOOGLE_API_KEY) - Primary, Free
2. **OpenRouter** (OPENROUTER_API_KEY) - Fallback if needed
3. Direct OpenAI/Anthropic - Only if base URLs are changed

## Estimated Total Cost

With current configuration using Google Gemini (free tier):
- **Setup Cost**: $0
- **Per Lead Cycle**: $0 (within free tier limits)
- **Monthly Cost**: $0 (up to 1500 requests/day)

**Your $10 OpenRouter credit is available as a backup** if you exceed Google's free tier or want to experiment with other models.

## Monitoring Usage

To monitor your API usage:

```bash
# Check Google AI quota
# Visit: https://aistudio.google.com/app/apikey

# Check OpenRouter credits
# Visit: https://openrouter.ai/credits

# Check local logs
tail -f logs/lead_finder.log
tail -f logs/sdr.log
```

## Need to Change Models?

Update your `.env` file:

```bash
# For Google models (recommended - free)
MODEL=gemini-2.0-flash-lite

# For OpenRouter models (paid, but cheap)
MODEL=google/gemini-2.0-flash-lite
MODEL=openai/gpt-4o-mini
MODEL=anthropic/claude-3-haiku
MODEL=meta-llama/llama-3.2-3b-instruct
```

## Summary

✅ **Current Setup**: Using Google Gemini free tier  
✅ **Cost**: $0/month within free limits  
✅ **Backup**: $10 OpenRouter credit available  
✅ **Estimated Cycles**: Unlimited (free tier) or ~133 cycles with OpenRouter  
✅ **Best Practice**: Stay on Google Gemini for maximum cost efficiency
