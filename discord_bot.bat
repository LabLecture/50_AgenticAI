@echo off
set DISCORD_STATE_DIR=C:\Users\user\.claude\channels\discord_a16
bun run --cwd C:\Users\user\.claude\plugins\cache\claude-plugins-official\discord\0.0.4 --shell=bun --silent start
