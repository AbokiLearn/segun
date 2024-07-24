module.exports = {
  apps: [
    {
      name: 'telegram-api',
      script: '/app/telegram-server/src/run_api.sh',
      env: {
        NODE_ENV: 'production',
      },
      env_file: '/app/telegram-server/.env',
    },
    {
      name: 'telegram-bot',
      script: '/app/telegram-server/src/run_bot.sh',
      env: {
        NODE_ENV: 'production',
      },
      env_file: '/app/telegram-server/.env',
    },
  ],
};
