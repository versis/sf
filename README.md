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

## Learn More

To learn more about the AI SDK or Next.js by Vercel, take a look at the following resources:

- [AI SDK Documentation](https://sdk.vercel.ai/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
