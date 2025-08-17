# Overview

This is a sophisticated Telegram bot powered by Google Gemini AI that provides natural, human-like conversations with personality-driven responses. The bot features advanced conversation management with context retention, broadcasting capabilities for mass messaging, full group chat support, and comprehensive analytics. Built with Python using the aiogram framework, it maintains conversation contexts, detects user language and tone, and adapts responses based on personality traits while avoiding robotic phrasing.

**Recent Major Improvements (August 2025):**
- Repository cleanup: Removed duplicate files, cached files, and unnecessary directories while preserving working bot code
- **Smart rate limiting optimization**: Conversation rate limits removed for instant responses, broadcast rate limits maintained for API protection
- **Enhanced group trigger system**: Added flexible "Junghwan" keyword detection that extracts the name from any text, including compound words
- Enhanced personality system with robust anti-AI language filtering and mandatory identity display
- Complete broadcasting system with delivery tracking and analytics for owner-only mass messaging
- Full group chat support with smart response triggers and context awareness
- Comprehensive README documentation with setup guides and troubleshooting
- Production-ready deployment configuration with health monitoring on port 5000
- Fixed configuration validation and environment variable handling
- Implemented mood and tone recognition for adaptive personality responses
- Added strict flirting control (disabled by default, only when user initiates)
- Enhanced user-defined instruction compliance system
- Added comprehensive owner messaging system with targeted broadcasting and direct messaging
- Stealth broadcasting system - messages appear as natural bot responses without broadcast headers
- Advanced chat monitoring system for owners to view user conversation histories
- User activity tracking with active users list and detailed conversation analytics

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Architecture Pattern
The application follows a modular, component-based architecture with clear separation of concerns:

**Bot Layer (TelegramBot)**: Main orchestrator that coordinates all components and handles Telegram API interactions using aiogram framework with async/await patterns for high performance.

**Conversation Management Layer**: Manages conversation flow and context through ConversationContext objects that store per-user message history, language preferences, tone detection, and conversation state with automatic expiration (2-hour timeout).

**AI Integration Layer (GeminiClient)**: Interfaces with Google Gemini AI using the gemini-2.5-flash model with configurable parameters (temperature: 0.9, top_p: 0.95, top_k: 40, max tokens: 500). Implements circuit breaker pattern for API failure handling.

**Personality System (PersonalityManager)**: Implements dynamic personality traits including confident, casual, friendly, and conversational elements. Creates contextual system prompts that enforce personality consistency and natural conversation flow.

**Broadcasting System (BroadcastManager)**: Provides mass messaging capabilities with delivery tracking, targeting options (users/groups/all), and automatic cleanup of inactive chats. Owner-only functionality with comprehensive analytics.

**User Management (UserManager)**: Handles user registration, chat management, and persistent data storage using JSON files. Tracks user activity, message counts, and maintains chat metadata.

## Data Flow Architecture
1. Message received via aiogram → TelegramBot routes to appropriate handler
2. UserManager registers/updates user and chat information
3. ConversationManager retrieves user context and conversation history
4. Language/tone detection analyzes user input patterns
5. PersonalityManager creates AI prompt with personality traits
6. GeminiClient generates response using conversation context
7. Response cleaned and sent back through Telegram API

## Configuration Management
Centralized settings system (Settings class) with environment variable validation and defaults. Supports bot identity customization, AI model parameters, conversation limits, group chat behavior, and deployment configuration.

## Error Handling & Reliability
- Circuit breaker pattern for AI API failures
- Smart rate limiting: Disabled for conversations, enabled for broadcasts to prevent API abuse
- Graceful error handling with fallback responses
- Health check endpoints for deployment monitoring
- Comprehensive logging with configurable levels

# External Dependencies

## Core APIs
- **Telegram Bot API**: Primary interface via aiogram framework for bot functionality
- **Google Gemini AI API**: AI response generation using gemini-2.5-flash model with genai client library

## Python Libraries
- **aiogram**: Telegram Bot API framework for async bot development
- **google-genai**: Official Google Generative AI client
- **aiohttp**: HTTP client/server for async operations and health endpoints
- **langdetect**: Language detection for automatic response localization
- **python-dotenv**: Environment variable management

## Data Storage
- **JSON file storage**: User data, chat information, and conversation contexts persisted to local files
- **In-memory caching**: Active conversation contexts and user activity stored in memory for performance

## Deployment Infrastructure
- **Health check server**: HTTP endpoints for deployment platform monitoring
- **Environment-based configuration**: Port, logging, and feature toggles via environment variables
- **File-based logging**: Application logs written to bot.log file with rotation