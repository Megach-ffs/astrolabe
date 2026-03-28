# AI_USAGE

So, we have used AI mostly for planning and debugging purposes 

For example, we have used AI for generating code for AI agent of our application
Then we manually tested and checked it
During this process we found bug that AI just put placeholders instead of API keys
To fix that we manually created AI API token inside Google AI labs
Then we created file secrets.toml, from where the Application sees the secrets

```toml

# AI Assistant (Gemini)
[ai]
gemini_api_key = "<YOUR_GEMINI_API_KEY_HERE>"

```

Then similarly, to connect to Google spreadsheets and fetch data from it
we used AI, and during our review, we find out that the code tried to use
Google that was never real, and bunch of placeholders instead of real API keys
In order to fix that we first created dedicated google account
Then we have created new project on Google Cloud Platform
Where we enabled services such as Google Drive API and Google Spreadsheets API
And put right credentials so that these function will work

```toml

[gcp_service_account]
type = "service_account"
project_id = "<YOUR_PROJECT_ID>"
private_key_id = "<YOUR_PRIVATE_KEY_ID>"
private_key = "-----BEGIN PRIVATE KEY-----\n<YOUR_PRIVATE_KEY_HERE>\n-----END PRIVATE KEY-----\n"
client_email = "<YOUR_SERVICE_ACCOUNT_EMAIL>"
client_id = "<YOUR_CLIENT_ID>"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "<YOUR_CLIENT_X509_CERT_URL>"

```

Also we have used AI to create prompts for the AI agent of our application
Then we manually verified these promts
During this process we found bugs
The response for that prompts were quite different, then those values that our application can take
And we had to adjust these prompts, so they return great structured responses
So that the AI features of our AI agent work

HERE is one of the fixed prompts:

```python

CHART_SYSTEM_PROMPT = """You are a data visualization assistant.

Based on the data profile, suggest 3 useful charts that would reveal insights.

Available chart types: Histogram, Box Plot, Scatter Plot, Line Chart, Bar Chart, Heatmap

Rules:
- Only reference actual column names from the dataset
- x_column and y_column must be real column names or null
- For Histogram: x_column is the numeric value. y_column is null. color_column is an optional categorical group.
- For Box Plot: x_column is the NUMERIC value to distribute. y_column is null. color_column is the optional CATEGORICAL group.
- For Scatter Plot: x_column is numeric, y_column is numeric, color_column is optional categorical.
- For Line Chart: x_column is time/order, y_column is numeric, color_column is optional categorical.
- For Bar Chart: x_column is categorical, y_column is numeric, color_column is optional categorical.
- For Heatmap: x_column and y_column are numeric. color_column must be null.
- Each suggestion should reveal different insights
- Keep reasons concise (1 sentence)"""

```
