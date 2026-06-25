module.exports = {
  apps: [
    {
      name: "explor-bot",
      script: "bot.py",
      interpreter: process.env.PM2_PYTHON || "python",
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: "10s",
      restart_delay: 5000,
      time: true,
      out_file: "logs/pm2-out.log",
      error_file: "logs/pm2-error.log",
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
