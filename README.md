# AI SDK Python Streaming Preview

This template demonstrates the usage of [Data Stream Protocol](https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol) to stream chat completions from a Python endpoint ([FastAPI](https://fastapi.tiangolo.com)) and display them using the [useChat](https://sdk.vercel.ai/docs/ai-sdk-ui/chatbot#chatbot) hook in your Next.js application.

## Card Details AI Generation

This project now includes AI-powered card detail generation using Azure OpenAI API. The following features are supported:

- Automatic generation of card name (creative and evocative)
- Phonetic pronunciation (using IPA symbols)
- Part of speech (typically noun)
- Descriptive text for the color

The system will automatically generate these details when you provide a color name and hex value without specifying your own card details.

## Deploy your own

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel-labs%2Fai-sdk-preview-python-streaming&env=OPENAI_API_KEY&envDescription=API%20keys%20needed%20for%20application&envLink=https%3A%2F%2Fgithub.com%2Fvercel-labs%2Fai-sdk-preview-python-streaming%2Fblob%2Fmain%2F.env.example)

## How to use

Run [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app) with [npm](https://docs.npmjs.com/cli/init), [Yarn](https://yarnpkg.com/lang/en/docs/cli/create/), or [pnpm](https://pnpm.io) to bootstrap the example:

```bash
npx create-next-app --example https://github.com/vercel-labs/ai-sdk-preview-python-streaming ai-sdk-preview-python-streaming-example
```

```bash
yarn create next-app --example https://github.com/vercel-labs/ai-sdk-preview-python-streaming ai-sdk-preview-python-streaming-example
```

```bash
pnpm create next-app --example https://github.com/vercel-labs/ai-sdk-preview-python-streaming ai-sdk-preview-python-streaming-example
```

To run the example locally you need to:

1. Sign up for accounts with the AI providers you want to use (e.g., OpenAI, Anthropic).
2. Obtain API keys for each provider.
3. Set the required environment variables as shown in the `.env.example` file, but in a new file called `.env`.
4. `pnpm install` to install the required Node dependencies.
5. `uv venv` to create a virtual environment using uv (ensure uv is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pip install uv`).
6. `source .venv/bin/activate` to activate the virtual environment (on Windows: `.venv\Scripts\activate`).
7. `uv pip install -r requirements.txt` to install the required Python dependencies using uv.
8. `pnpm dev` to launch the development server.

## Environment Variables

To use the Azure OpenAI integration, you need to set the following environment variables in your `.env.local` file:

```
# OpenAI API - Original configuration
OPENAI_API_KEY=your_openai_api_key_here

# Azure OpenAI API configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

For example, with the o4-mini model:
```
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=ti-o4-mini
```

Make sure the deployment name matches what you created in your Azure OpenAI resource.

### Controlling AI Card Detail Generation

You can control whether the AI attempts to generate card details using the following environment variable:

- `ENABLE_AI_CARD_DETAILS`: 
    - Set to `false` to disable AI generation and use fallback text details.
    - If not set, or set to `true` (or any other value), AI generation will be enabled by default.

```env
# Optional: Control AI card detail generation
ENABLE_AI_CARD_DETAILS=true # set to false to disable AI, defaults to true if not set
```

## AI Card Details Generation

When enabled, the application uses Azure OpenAI to generate creative and poetic card details based on:

1. The selected hex color value
2. The cropped image from the user (required)

The AI analyzes both inputs to create a contextually relevant:
- Color name (max 3 words, all caps)
- Phonetic pronunciation (IPA symbols)
- Part of speech
- Poetic description (25-30 words)

This approach results in cards that are personalized and thematically connected to the actual image content rather than just the color. If no image is provided, the API will return an error message - a cropped image is required for the AI to generate appropriate card details.

### Image Processing for AI

For optimal performance with the Azure OpenAI API:
- The user's cropped image is automatically resized to 512×512 pixels
- The image is converted to JPG format with quality optimization
- The "detail" parameter is set to "low" to further reduce token usage
- The original high-resolution image is still used for the card generation
- This optimization reduces API costs and improves response times

## Debugging

To run the application with debug logging enabled, use:

```bash
pnpm debug
```

This will start both the Next.js frontend and the FastAPI backend with debug logs enabled, showing:

- Detailed API request/response information
- Image processing steps and sizes
- OpenAI token usage
- Exact timing for API calls
- Prompt and completion details

Debug logs are essential for troubleshooting issues with OpenAI API integration or image processing. They provide detailed information about what's happening behind the scenes.

You can also selectively enable debug logs by setting the `LOG_LEVEL` environment variable:

```env
LOG_LEVEL=DEBUG
```

## Timeout Configuration

This project involves several layers where timeouts can occur. Here's a summary of how they are configured:

1.  **Vercel Serverless Function Timeout (`vercel.json`)**:
    *   The `maxDuration` setting in `vercel.json` under `functions -> api/index.py` controls the maximum execution time for the main Python backend function on Vercel.
    *   This is set to **120 seconds** (2 minutes) for Pro plan compatibility.
    *   Example: `"maxDuration": 120`

2.  **Next.js Proxy Timeout (`next.config.js`)**:
    *   The `experimental.proxyTimeout` in `next.config.js` sets the timeout for requests proxied from the Next.js frontend to the backend (FastAPI in this case).
    *   This is set to **120000 milliseconds** (2 minutes) to accommodate the backend function's max duration.
    *   Example: `proxyTimeout: 120000`

3.  **Python FastAPI (Uvicorn) Keep-Alive Timeout (`api/config.py`)**:
    *   For local development, the Uvicorn server (run via `api/index.py`) has a `timeout_keep_alive` setting.
    *   This is configured in `api/config.py` via the `UVICORN_TIMEOUT_KEEP_ALIVE` variable, which defaults to **120 seconds**.
    *   It can be overridden by setting the `UVICORN_TIMEOUT_KEEP_ALIVE` environment variable.
    *   Used in: `api/index.py` when calling `uvicorn.run()`.

4.  **Azure OpenAI Client Timeout (`api/config.py`)**:
    *   The timeout for requests made by the Azure OpenAI Python client is configured in `api/config.py` via the `AZURE_OPENAI_CLIENT_TIMEOUT` variable.
    *   This defaults to **119.0 seconds** (slightly less than the typical 2-minute function timeout to allow for overhead).
    *   It can be overridden by setting the `AZURE_OPENAI_CLIENT_TIMEOUT` environment variable.
    *   Used in: `api/utils/openai_client.py` when initializing `AsyncAzureOpenAI` and in `api/utils/ai_utils.py` for `asyncio.wait_for()` calls.

It is recommended to keep these timeouts aligned, with client timeouts being slightly less than server/function timeouts to allow for graceful error handling.

## Learn More

To learn more about the AI SDK or Next.js by Vercel, take a look at the following resources:

- [AI SDK Documentation](https://sdk.vercel.ai/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
