# ⚠️ Disclaimer

This repository is a public showcase of the project structure and non-sensitive code.

The production version of this bot is **obfuscated using PyArmor** to protect critical logic and enforce licensing. This public version is intended for demonstration and portfolio purposes only.

Unauthorized use or redistribution of obfuscated builds without permission is prohibited.

---

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

Use the **OAuth2 URL Generator** with the following:

* **Scopes**: `bot`
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

Invite your bot to the server using the generated link.

---

## 🎠 Running the Bot Locally

### Requirements

* Python 3.9+
* `discord.py` library

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_token_here
```

Add any other variables if used.

### Run the Bot

```bash
python bot1.py
```

---

## 🎞️ Hosting Guide (Railway or Alternatives)

You can deploy the bot using **[Railway](https://railway.app/)** or any hosting provider that supports Python apps.

### Railway Setup (Recommended)

1. Create an account at [railway.app](https://railway.app/)
2. Create a new project and link your GitHub repo or upload the code manually
3. Set environment variables (e.g. `DISCORD_TOKEN`)
4. Set the start command:

   ```bash
   python bot1.py
   ```

Railway supports free, always-on deployments with an intuitive interface.

---

## 🎮 Commands Overview
#### Examples of the commands in action are shown below.

### 🌟 Standup Commands

```
/preview       Show a preview of the standup card  
/toggle        Enable or disable the standup  
/config        Display current standup configuration  
/summary       View recorded standup responses  
```

--- 

![img.png](img.png)
![img_1.png](img_1.png)
![img_2.png](img_2.png)

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
![img_3.png](img_3.png)
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

* Max 60 open tickets allowed concurrently.
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
