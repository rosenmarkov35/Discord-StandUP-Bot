import os
import sys


def setup_bot():
    print("🤖 Discord Standup Bot Setup")
    print("=" * 40)

    # Check if config already exists
    if os.path.exists('.env'):
        print("✅ Configuration already exists!")
        return

    print("Please create a Discord application at:")
    print("https://discord.com/developers/applications")
    print()

    token = input("Enter your Discord bot token: ").strip()

    if not token:
        print("❌ No token provided!")
        sys.exit(1)

    # Create .env file
    with open('.env', 'w') as f:
        f.write(f"DISCORD_TOKEN={token}\n")

    print("✅ Configuration saved!")
    print("You can now run the bot.")


if __name__ == "__main__":
    setup_bot()