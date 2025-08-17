# Junghwan Telegram Bot 🤖

A sophisticated Telegram bot powered by Google Gemini AI that provides natural, human-like conversations with personality-driven responses, broadcasting capabilities, and comprehensive group chat support.

## ✨ Features

### 🎭 Natural Personality System
- **Human-like responses** - No robotic "I'm here to help" messages
- **Dynamic personality traits** - Adapts to user tone and conversation style
- **Context awareness** - Remembers previous conversations and builds on them
- **Multi-language support** - Automatically detects and responds in user's language

### 💬 Advanced Conversation Management
- **Intelligent context retention** - Maintains conversation history for natural flow
- **Tone detection** - Adapts responses based on formal/casual/excited/sad tone
- **Rate limiting** - Prevents spam with smart cooldown periods
- **Circuit breaker pattern** - Handles API failures gracefully

### 📢 Broadcasting System (Owner Only)
- **Mass messaging** - Send announcements to all users and groups
- **Targeted broadcasts** - Send to users only or groups only
- **Delivery tracking** - Real-time statistics on message delivery
- **Automatic cleanup** - Removes inactive chats from broadcast lists

### 👥 Full Group Chat Support
- **Smart group participation** - Responds when mentioned or replied to
- **Context-aware responses** - Understands group dynamics
- **Configurable activity** - Adjustable response frequency in groups
- **Member management** - Tracks group additions and removals

### 📊 Analytics & Management
- **User statistics** - Track active users, new registrations, and engagement
- **Broadcast analytics** - Monitor delivery rates and engagement
- **Health monitoring** - Built-in health checks for deployment platforms
- **Data persistence** - Automatic backup and recovery of user data

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Telegram Bot Token (from @BotFather)
- Google Gemini API Key (from Google AI Studio)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd junghwan-telegram-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Required Environment Variables**
```env
# Essential Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
BOT_OWNER_ID=your_telegram_user_id_here

# Bot Identity
BOT_NAME=Junghwan
BOT_OWNER_NAME=Your Name
GR_NAME=Your Group Name
```

5. **Run the bot**
```bash
python main.py
```

## 🔧 Configuration

### Bot Identity Settings
- `BOT_NAME` - The bot's display name
- `BOT_USERNAME` - Bot's Telegram username (without @)
- `BOT_OWNER_NAME` - Owner's display name
- `BOT_OWNER_ID` - Owner's Telegram user ID (for admin features)
- `GR_NAME` - Group or organization name
- `BOT_PERSONALITY` - Bot's personality description

### AI Model Configuration
- `GEMINI_MODEL` - Gemini model version (default: gemini-2.5-flash)
- `AI_TEMPERATURE` - Response creativity (0.0-2.0, default: 0.9)
- `AI_TOP_P` - Token selection threshold (0.0-1.0, default: 0.95)
- `AI_TOP_K` - Token selection limit (1-100, default: 40)
- `AI_MAX_TOKENS` - Maximum response length (default: 500)

### Conversation Settings
- `MAX_CONTEXT_MESSAGES` - Chat history limit (default: 10)
- `CONTEXT_TIMEOUT_HOURS` - Context expiration time (default: 2)
- `RATE_LIMIT_MESSAGES` - Messages per minute limit (default: 20)

### Group Chat Settings
- `GROUP_RESPONSE_CHANCE` - Random response probability (0.0-1.0, default: 0.1)
- `GROUP_MAX_MESSAGE_LENGTH` - Max message length in groups (default: 400)

## 📱 Usage

### Basic Commands

| Command | Description | Access Level |
|---------|-------------|--------------|
| `/start` | Initialize bot and get welcome message | Everyone |
| `/help` | Show help information and commands | Everyone |
| `/info` | Display bot information and features | Everyone |
| `/broadcast <message>` | Send message to all users/groups | Owner only |
| `/stats` | View bot usage statistics | Owner only |

### Private Chat
- Simply message the bot directly
- Bot remembers conversation context
- Responds naturally to any topic
- Adapts to your communication style

### Group Chat
- **Mention the bot**: `@YourBotUsername hello`
- **Reply to bot messages**: Reply to any bot message
- **Random responses**: Bot occasionally responds to group messages

### Broadcasting (Owner Only)
```
/broadcast Hello everyone! This is an important announcement.
```

## 🏗️ Architecture

The bot follows a modular, component-based architecture:

### Core Components

#### **TelegramBot** (Main Orchestrator)
- Coordinates all bot components
- Handles Telegram API interactions
- Manages message routing and processing

#### **ConversationManager** 
- Manages conversation context and history
- Handles AI response generation
- Implements rate limiting and circuit breaker

#### **PersonalityManager**
- Enforces natural, human-like responses
- Removes robotic AI language
- Adapts personality based on conversation context

#### **GeminiClient**
- Interfaces with Google Gemini AI
- Implements circuit breaker for reliability
- Post-processes responses for naturalness

#### **BroadcastManager**
- Handles mass messaging capabilities
- Tracks delivery statistics
- Manages inactive chat cleanup

#### **UserManager**
- Stores user and chat data persistently
- Tracks user activity and statistics
- Handles data backup and recovery

### Data Flow
1. **Message Reception** → Telegram → TelegramBot
2. **User Registration** → UserManager updates data
3. **Context Retrieval** → ConversationManager gets history
4. **AI Processing** → PersonalityManager + GeminiClient
5. **Response Delivery** → TelegramBot → User

## 🔒 Security Features

- **Environment variable validation**
- **Rate limiting per user**
- **Owner-only admin commands**
- **Automatic inactive chat cleanup**
- **Circuit breaker for API failures**
- **Data backup and recovery**

## 📊 Monitoring & Analytics

### Health Check Endpoints
- `GET /health` - Basic health status
- `GET /info` - Bot configuration information

### Built-in Analytics
- User registration and activity tracking
- Message count and engagement metrics
- Broadcast delivery statistics
- Group vs private chat usage

## 🚀 Deployment

### Replit Deployment
1. Import project to Replit
2. Set environment variables in Replit Secrets
3. Run with `python main.py`

### Render/Heroku Deployment
1. Connect GitHub repository
2. Set environment variables
3. Deploy with provided Dockerfile

### Docker Deployment
```bash
# Build image
docker build -t junghwan-bot .

# Run container
docker run -d \
  --name junghwan-bot \
  --env-file .env \
  -p 8000:8000 \
  junghwan-bot
```

## 🐛 Troubleshooting

### Common Issues

#### Bot not responding
- Check `TELEGRAM_BOT_TOKEN` is correct
- Verify bot is not running elsewhere (conflict error)
- Ensure `BOT_OWNER_ID` is set correctly

#### AI responses not working
- Verify `GEMINI_API_KEY` is valid
- Check API quota and rate limits
- Review circuit breaker status in logs

#### Broadcasting not working
- Confirm you're the bot owner (`BOT_OWNER_ID`)
- Check for blocked users or inactive chats
- Review broadcast permissions

### Debug Mode
Set `LOG_LEVEL=DEBUG` for detailed logging:
```env
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for natural language processing
- **aiogram** for Telegram Bot API framework
- **Replit** for development and hosting platform

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review logs for error details
- Open an issue on GitHub

---

**Made with ❤️ for natural, human-like bot conversations**