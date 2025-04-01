# Customer Support System

A complete customer support system with AI-powered responses and human agent support through Telegram bots.

## Overview

This system consists of:

1. **FastAPI Backend** - Provides API endpoints for both public and private interactions
2. **Supabase Database** - Stores issues, messages, admins, and FAQ embeddings
3. **Telegram Bots**:
   - User Bot - For customer interactions
   - Admin Bot - For support staff
4. **OpenAI Integration** - For AI-powered responses and embeddings

## Prerequisites

- Python 3.9+
- Poetry (for dependency management)
- Supabase account
- Telegram Bot tokens (one for users, one for admins)
- OpenAI API key

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd customer-support
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure Environment Variables

Copy the example environment file and update it with your credentials:

```bash
cp app/.env.example app/.env
```

Edit `app/.env` and fill in the following variables:

```
# FastAPI Configuration
API_BASE_URL=http://localhost:8000/api

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_ADMIN_BOT_TOKEN=your_telegram_admin_bot_token

# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
```

### 4. Set Up Supabase Database

1. Create a new project in Supabase
2. Execute the SQL commands from `app/create_tables.sql` in the Supabase SQL editor to create the necessary tables and functions

### 5. Import FAQs (Optional)

To import sample FAQs from the provided CSV file:

```bash
cd app
poetry run python import_faqs.py
```

This will import FAQs from `gameshop_faq.csv` into your database.

## Running the System

### Start the API Server

```bash
cd app
poetry run python main.py
```

The API server will run at http://localhost:8000

### Start the Telegram Bots

In a separate terminal:

```bash
cd app
poetry run python run_bots.py
```

This will start both the user bot and admin bot in separate processes.

## Usage

### User Bot Commands

- `/start` - Start the bot and get introduction
- `/help` - Show available commands
- `/new` - Create a new support issue
- `/status` - Check the status of your current issue
- `/manual` - Request manual assistance from a human agent

Users can simply send messages to the bot to get AI-powered responses or interact with human agents.

### Admin Bot Commands

- `/start` - Start the bot and get introduction
- `/help` - Show available commands
- `/register` - Register yourself as an admin
- `/issues` - List all open issues requiring manual assistance
- `/exit` - Exit the current issue conversation

Admins will receive notifications when issues are switched to manual mode and can respond to user messages.

## Deployment

### Docker Deployment

The system can be easily deployed using Docker Compose:

1. Copy the example environment file and update it with your credentials:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your Telegram bot tokens, Supabase credentials, and OpenAI API key.

3. Build and start the containers:

```bash
docker-compose up -d
```

This will start two containers:
- `api`: The FastAPI server that handles API requests
- `bots`: The Telegram bots (both user and admin bots)

Both containers use the same Docker image but with different entry points.

4. Check the logs to ensure everything is running correctly:

```bash
docker-compose logs -f
```

5. To stop the services:

```bash
docker-compose down
```

