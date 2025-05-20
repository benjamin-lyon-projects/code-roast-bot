# 🔐 Environment Configuration (`.env`)

To authenticate with the OpenAI API, `code-roast-bot` uses a `.env` file to load your API key securely.

## 📄 `.env` File Format

Create a file named `.env` in the root of your project directory and add the following line:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Replace `sk-xxxxxxxx...` with your actual API key from https://platform.openai.com/account/api-keys.

## 🔒 Important Notes

- **Do not commit your `.env` file** to version control (this project includes a `.gitignore` that ignores it).
- **Never share your API key** publicly — it grants access to your account's usage and billing.


## 📦 Global Configuration

You may place your `.env` file in your **home directory** to apply it globally:
```
~/.env        # macOS/Linux
C:\Users\yourname\.env  # Windows
```
This is supported by default in the latest version of Code Roast Bot.