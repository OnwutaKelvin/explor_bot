# PM2 Bot Restart Setup

Use PM2 to keep the Telegram bot running and restart it after crashes.

## Install PM2

```powershell
npm install -g pm2
```

## Start the bot

From this folder:

```powershell
pm2 start ecosystem.config.js
```

If you want PM2 to use the project virtual environment on Windows:

```powershell
$env:PM2_PYTHON = ".\venv\Scripts\python.exe"
pm2 start ecosystem.config.js
```

On Linux:

```bash
PM2_PYTHON=./venv/bin/python pm2 start ecosystem.config.js
```

## Useful commands

```powershell
pm2 status
pm2 logs explor-bot
pm2 restart explor-bot
pm2 stop explor-bot
pm2 delete explor-bot
```

PM2 logs are written to:

- `logs/pm2-out.log`
- `logs/pm2-error.log`

The bot's application logs are still written to:

- `logs/bot.log`
- `logs/errors.log`

## Restart on machine reboot

On a server, run:

```powershell
pm2 startup
pm2 save
```

PM2 will print the exact startup command for your operating system. Run that command, then run `pm2 save`.
