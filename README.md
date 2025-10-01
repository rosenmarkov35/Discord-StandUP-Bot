# 🛠️ StandUP Bot

**StandUP** is a powerful Discord bot designed to streamline team check-ins and ticket management within your server. With scheduled standups, role-based access, and a flexible ticketing system, it helps teams stay organized and accountable.

The bot also features multiple tiers which deliver different features such as grouping users and/or teams to separate the standup check-ins schedules at different times with different configurations and more. Other features include further customization of the UI, broader and larger limits for most of the core features.

All production versions/tiers of the project are obfuscated and compiled to prevent sharing or piracy in any way and as a further safety measure an API is used to check unique licenses provided to each instance of the app or its owner ( the client ). The license management can be automated or manual and the keys also have expiry dates and reflect the bot tier. 

---

## 📦 Features

### 🌟 Standup System

* Daily or weekly asynchronous standup check-ins
* Fully configurable questions, time, timezone, and days
* Role-based reminders and summary logs
* Interactive embeds and visual feedback for all actions, including standup previews, ticket updates, and responses

### 🎟️ Ticket Management

* Users can submit tickets with a single command
* Mods can assign tickets to roles/members
* Dedicated thread creation for each ticket
* Structured embed updates and comment tracking

### 🔒 Role-based Access

* `StandupMod` role: full control over standup configuration
* `TicketMod` role: manage and assign tickets

---

## 🔧 Prerequisites

Before using StandUP Bot, make sure the following roles, channels, and settings are configured. These are required for the bot to function correctly.

### Discord Server

* The bot must be invited and installed into a Discord server.

### Required Roles & Channels

#### TicketMod Role

* Users with this role can manage, assign, and oversee support tickets.
* The role must be named exactly `TicketMod`.

#### StandupMod Role

* Grants access to all standup configuration and scheduling commands.
* The role must be named exactly `StandupMod`.

#### mod-tickets Channel

* A private text channel for moderators with the `TicketMod` role.
* The bot posts new ticket embeds here for review and assignment.
* This name must match exactly.

> ✅ Tip: Create a private channel for `StandupMod` usage so configuration commands don’t clutter public channels.

---

## 🚀 Discord Bot Setup

To self-host and run StandUP Bot, you’ll first need to create a bot on the [Discord Developer Portal](https://discord.com/developers/applications/). Follow these steps carefully:

### 1. Create a Discord Application

* Visit [https://discord.com/developers/applications/](https://discord.com/developers/applications/)
* Click **"New Application"**, give your bot a name, and create it.

### 2. Configure Your Bot

* Go to the **"Bot"** section.
* Enable **Server Members Intent** and **Message Content Intent**.
* Click **"Reset Token"** and store it in your `.env` file like so:

  ```env
  DISCORD_TOKEN=your_token_here
  ```

> ⚠️ Never share your bot token publicly!

### 3. Set Bot Permissions (OAuth2)

Go to the **`OAuth2`** section on the sidebar.

Scroll down and under "**OAuth2 URL Generator**" select only the **`bot`** checkbox/scope in the right column.

Then scroll down to "**Bot Permissions**" and check the following permissions:
* **Bot Permissions**:

  * Manage Roles
  * View Channels
  * Send Messages
  * Create Public Threads
  * Create Private Threads
  * Send Messages in Threads
  * Manage Messages
  * Manage Threads
  * Embed Links
  * Attach Files
  * Read Message History
  * Use External Emojis
  * Add Reactions

Again scroll down and select "**Guild Install**" and copy the generated URL below.

> ✅ **Now you can open the URL and using your Discord profile, invite the newly created Bot/Application to your server.**
---

# 🛠 Standup Bot – Installation & Hosting Guide

This section explains how to run the Standup Bot either on your own computer or using a hosting service like DigitalOcean. The bot is distributed as a public Docker image.


## ⚙️ Option A – Self-Hosting (Your Computer)

> How to open the terminal/cmd on your system:  \
> \
> **Windows** - Press `Windows + R`, type "cmd", and press Enter to open Command Prompt.  \
> \
> **Linux** - Press `Ctrl + Alt + T` to open Terminal.  \
\
> **Mac** - Press `Command + Space`, type "Terminal", and press Enter.


### Step 1 – Install Docker

**Windows**

1. Download Docker Desktop: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Install and open Docker Desktop.
3. Make sure it says "Docker Engine is running".

**Mac**

1. Download Docker Desktop for Mac: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
2. Install and open Docker Desktop.
3. Ensure Docker is running.

**Linux (Ubuntu/Debian)**

```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker
```

Check Docker:

```bash
docker --version
```

### Step 2 – Pull the Bot Image Locally

```bash
docker pull kuzeiburqta/standup-bot:latest
```


### Step 3 – Run the Bot Locally

```bash
docker run -d --name standup-bot
  -e DISCORD_TOKEN=<your_discord_bot_token>
  -e LICENSE=<your_license>
  --restart unless-stopped
  kuzeiburqta/standup-bot:latest
```
> Write this command in the console on one line and replace **`<your_discord_bot_token>`** with the token you created at [https://discord.com/developers/applications](https://discord.com/developers/applications/) and **`<your_license>`** with the license you have been given.

### Step 4 – Check if it’s Running

```bash
docker ps
docker logs -f standup-bot
```

Seeing these messages means the bot successfully connected to Discord and is running as expected.

```bash
INFO:__main__:Starting bot...
INFO:discord.client:logging in using static token
INFO:discord.gateway:Shard ID None has connected to Gateway (Session ID: <hidden>)
```

**Stop the bot:**

```bash
docker stop standup-bot
```

**Start the bot again:**

```bash
docker start standup-bot
```

---

## ☁️ Option B – Hosting with DigitalOcean (Recommended for 24/7 Uptime)

### How It Works

* You rent a VPS (Droplet) – a computer in the cloud.
* It runs 24/7 without needing your PC on.
* You connect via SSH.
* You install Docker on it and run the bot exactly as above.

### Step 1 – Create a Droplet (Server)

1. Go to [https://digitalocean.com](https://digitalocean.com).
2. Create an account (payment info required – billed hourly, around \$4–5/month).
3. Create a Droplet:

   * OS: Ubuntu latest version
   * Plan: Regular CPU (\$4/month is fine)
   * Datacenter: Nearest to you
   * Authentication: SSH key or password (simpler)
   * Hostname: Set your hostname to whatever you want
4. Click **Create Droplet**.
5. Once your droplet is live, click on it and open the **`Console`** in the top right or click **`Launch Droplet Console`**. 


### Step 2 – Install Docker on the Server

In the console write these lines one by one.
```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker
```

Check:

```bash
docker --version
```

### Step 3 – Pull the Bot Image on the Server

```bash
docker pull kuzeiburqta/standup-bot:latest
```

### Step 4 – Run the Bot on the Server

```bash
docker run -d --name standup-bot
  -e DISCORD_TOKEN=<your_discord_bot_token>
  -e LICENSE=<your_license>
  --restart unless-stopped
  kuzeiburqta/standup-bot:latest
```
> Write this command in the console on one line and replace **`<your_discord_bot_token>`** with the token you created at [https://discord.com/developers/applications](https://discord.com/developers/applications/) and **`<your_license>`** with the license you have been given.

> ⁉️ If you try pasting in the console normally - `Ctrl+V` it won't work instead use `Ctrl+Shift+V`

### Step 5 – Check If It’s Running

```bash
docker ps
docker logs -f standup-bot
```

**Stop:**

```bash
docker stop standup-bot
```

**Start:**

```bash
docker start standup-bot
```

✅ That’s it! With DigitalOcean, the bot stays online 24/7 until you stop it.

---

## Usage / Demo



## 🎮 Commands Overview


### 🌟 Standup Commands

```
/preview       Show a preview of the standup card  
/toggle        Enable or disable the standup  
/config        Display current standup configuration  
/summary       View recorded standup responses  
```

### 🕒 Schedule Setup

```
/time          Set the daily standup time  
/timezone      Set your timezone  
/days          Choose which days the standup runs  
```

### 📢 Role & Channel Setup

```
/role          Set the role that receives standup notifications  
/channel       Set the channel where standup is posted  
```

### 🗓️ Announcements

```
/announce      Manually announce the next standup  

```

### 📝 Content Configuration

Use the `✏️ Edit Content` button in `/preview` to set:

* Standup title
* Standup description
* Questions

### 🎟️ Ticket Management

```
/assign        Assign a ticket to members or roles  
/ticketchannel Set the mod-channel where ticket threads are created  
```

### 🙋 General Commands

```
/ticket        Submit a ticket to the moderators  
/help          Show all available commands  
```

---

## ⚠️ Limitations

* Max 60 open tickets allowed concurrently. (T1)
* Discord rate limits may delay message sending during bursts.
* Proper role and channel names are required for full functionality.

---

## 🧪 Testing Tips

* Use a private test server
* Confirm role permissions
* Use `/preview` regularly to verify setup
* Test ticket creation and thread generation

---

## 🤝 Acknowledgements

* Built with [discord.py](https://github.com/Rapptz/discord.py)
