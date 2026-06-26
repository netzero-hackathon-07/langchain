# ECOROUTE Lambda + Bedrock deployment

This guide is for the hackathon AWS account where access keys are blocked.

Local direct Bedrock calls are not available because access key creation is denied.
Use Lambda with the provided IAM role instead.

## Target architecture

```text
Frontend
-> Lambda Function URL or API Gateway
-> Lambda: lambda_function.lambda_handler
-> IAM Role: SafeRole-netzero-07
-> Bedrock Runtime
```

## 1. Create Lambda function

AWS Console:

```text
Lambda
-> Create function
-> Author from scratch
```

Recommended settings:

```text
Function name: ecoroute-router
Runtime: Python 3.12
Architecture: x86_64
Execution role: Use an existing role
Existing role: SafeRole-netzero-07
Region: us-east-1
```

Do not create a new role.

## 2. Upload code

Option A: Console editor

Copy the content of:

```text
backend/lambda_function.py
```

into Lambda's `lambda_function.py`.

Option B: ZIP upload

Run locally:

```powershell
cd "C:\Users\gunhu\OneDrive - 인하대학교\문서\Playground\ecoroute"
.\backend\scripts\package_lambda.ps1
```

Upload:

```text
backend/dist/ecoroute_lambda.zip
```

## 3. Runtime settings

Handler:

```text
lambda_function.lambda_handler
```

Recommended configuration:

```text
Timeout: 30 seconds
Memory: 512 MB
```

## 4. Environment variables

Set these in Lambda:

```text
AWS_REGION=us-east-1
USE_BEDROCK=true
BEDROCK_FALLBACK_MODEL_ID=anthropic.claude-opus-4-8
BEDROCK_MAX_TOKENS=256
```

If the selected model ID fails, the function falls back to `BEDROCK_FALLBACK_MODEL_ID`.

## 5. Test event

Use this Lambda test event:

```json
{
  "body": "{\"query\":\"회의 참석 가능 여부를 정중하게 묻는 이메일 문장을 작성해줘\",\"policy\":\"balanced\"}"
}
```

Expected result:

```json
{
  "query": "...",
  "task_type": "writing_edit",
  "difficulty": "low",
  "selected_model": "...",
  "bedrock_model_id": "...",
  "cost": {
    "saved_usd": 0.0
  },
  "carbon": {
    "saved_g": 0.0
  },
  "answer": "...",
  "is_bedrock": true
}
```

## 6. If Bedrock permission fails

If you see an error like:

```text
AccessDeniedException
not authorized to perform bedrock:InvokeModel
```

ask the organizer to add Bedrock Runtime invoke permission to:

```text
SafeRole-netzero-07
```

Required actions:

```text
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
```

## 7. If model ID fails

If you see an error saying the model ID is invalid or not enabled, change:

```text
BEDROCK_FALLBACK_MODEL_ID
```

to the exact model ID shown in Bedrock Workbench.

Confirmed from the current console:

```text
anthropic.claude-opus-4-8
```

## 8. Function URL

After Lambda test succeeds:

```text
Configuration
-> Function URL
-> Create function URL
-> Auth type: NONE
-> CORS: enabled
```

Then frontend can call:

```text
POST https://{lambda-url}/
Content-Type: application/json

{
  "query": "이 문장을 자연스럽게 고쳐줘",
  "policy": "balanced"
}
```

If Function URL is blocked by policy, use API Gateway instead.
