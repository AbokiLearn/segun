module.exports = {
    apps: [
        {
            name: 'telegram-api',
            script: '/app/telegram-server/src/run_api.sh',
            env: {
                NODE_ENV: 'production',
            },
        },
        {
            name: 'telegram-bot',
            script: '/app/telegram-server/src/run_bot.sh',
            env: {
                NODE_ENV: 'production',
            },
        },
    ],
};
