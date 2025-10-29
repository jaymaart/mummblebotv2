# MummbleBot

A Discord bot that monitors TikTok accounts and posts new videos to Discord channels.

## Features

- Monitor TikTok accounts for new videos
- Automatically post new videos to configured Discord channels
- Configurable check intervals
- Docker support for easy deployment
- Minecraft server integration with whitelist functionality

## Deployment

### Prerequisites

- Docker and Docker Compose
- Discord Bot Token
- A Discord server where you have admin permissions

### Quick Start

1. Create a `.env` file with your Discord token:
```env
DISCORD_TOKEN=your_discord_token_here
# Optional: Set your timezone
TZ=UTC
```

2. Pull and run the container:
```bash
docker-compose pull
docker-compose up -d
```

### Discord Setup

1. Invite the bot to your server with appropriate permissions
2. Use the `/tiktok_config` command to configure TikTok monitoring:
```
 /tiktok_config tiktok_username:username channel:#your-channel check_interval:300
```

#### Minecraft Server Integration

The bot includes Minecraft server integration with automatic whitelisting:

1. **Configure your Minecraft server RCON:**
   - Enable RCON in `server.properties`
   - Set `enable-rcon=true`
   - Configure `rcon.password` and `rcon.port`

2. **Set environment variables:**
   ```env
   MINECRAFT_RCON_HOST=your.server.ip
   MINECRAFT_RCON_PORT=25575
   MINECRAFT_RCON_PASSWORD=your_rcon_password
   ```

3. **Use the Minecraft command:**
   - Send server info: `/minecraft`
   - Send to specific channel: `/minecraft channel:#channel-name`

The command creates an embed with server details and a "Whitelist Me" button that opens a modal for users to enter their Minecraft username.

### Unraid Setup

1. Create a new directory for the bot:
```bash
mkdir -p /path/to/mummblebot
cd /path/to/mummblebot
```

2. Create the necessary files:
```bash
# Create .env file
echo "DISCORD_TOKEN=your_token_here" > .env
echo "TZ=your_timezone" >> .env

# Download docker-compose.yml
wget https://raw.githubusercontent.com/your-username/mummblebot/main/docker-compose.yml
```

3. Create the config directory:
```bash
mkdir config
```

4. Start the container:
```bash
docker-compose up -d
```

## Building from Source

If you want to build the image yourself:

```bash
git clone https://github.com/your-username/mummblebot.git
cd mummblebot
docker-compose up -d --build
```

## Environment Variables

- `DISCORD_TOKEN`: Your Discord bot token (required)
- `TZ`: Timezone (optional, defaults to UTC)
- `GITHUB_REPOSITORY`: Your GitHub username and repository name (optional, for pulling the correct image)

## License

MIT