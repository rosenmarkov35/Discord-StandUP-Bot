# 🛠️ StandUP Bot

**StandUP** is a powerful Discord bot designed to streamline team check-ins and ticket management within your server. With scheduled standups, role-based access, and a flexible ticketing system, it helps teams stay organized and accountable.

---

## 📦 Features

### 🌟 Standup System

* Daily or weekly asynchronous standup check-ins
* Fully configurable questions, time, timezone, and days
* Role-based reminders and summary logs
* Interactive embeds and visual feedback for all actions, including standup previews, ticket updates, and responses, creating a user-friendly and informative experience

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

#### Discord Server

* The bot must be invited and installed into a Discord server so create one before continuing.


### Required Roles & Channels

#### TicketMod Role

* Users with this role can manage, assign, and oversee support tickets.
* The role must be named exactly `TicketMod` for permissions to work properly.

#### StandupMod Role

* Grants access to all standup configuration and scheduling commands.
* The role must be named exactly `StandupMod`.

#### mod-tickets Channel

* A private text channel for moderators with the `TicketMod` role.
* The bot posts new ticket embeds here for review and assignment.
* This name must match exactly.

  
    It is suggested to use a private-channel for "StandupMod" members where standup
    check-ins configurtaion via commands is done so commands dont fill the general
    text channels.



---

## 🚀 Discord Bot Setup

To self-host and run StandUP Bot, you’ll first need to create a bot on the [Discord Developer Portal](https://discord.com/developers/applications/). Follow these steps carefully:

### 1. Create a Discord Application

* Visit [https://discord.com/developers/applications/](https://discord.com/developers/applications/)
* Log in with your Discord account
* Click **"New Application"**
* Give your bot a name and click **Create**

### 2. Configure Your Bot

* In the left-hand menu, go to **"Bot"**

* Customize your bot’s **username** and **icon** if desired
* Check **"Public Bot"** if you want anyone to be able to add your bot, not just you.

* Click **"Reset Token"** and copy the token
  **⚠️ Important:** Store it in your `.env` file like so:

  ```
  DISCORD_TOKEN=your_token_here
  ```

  **Never share your bot token publicly!**

* Under **Privileged Gateway Intents**, enable the following:

  * ✅ Server Members Intent
  * ✅ Message Content Intent

### 3. Set Bot Permissions (OAuth2)

* Navigate to **"OAuth2" > "URL Generator"** on the left

* Select the following options:

  **Scopes**

  * ✅ `bot`

  **Bot Permissions**
  *(Enable only the following)*

  * **General Permissions**

    * ✅ Manage Roles
    * ✅ View Channels

  * **Text Permissions**

    * ✅ Send Messages
    * ✅ Create Public Threads
    * ✅ Create Private Threads
    * ✅ Send Messages in Threads
    * ✅ Manage Messages
    * ✅ Manage Threads
    * ✅ Embed Links
    * ✅ Attach Files
    * ✅ Read Message History
    * ✅ Use External Emojis
    * ✅ Add Reactions
    * ✅ Create Polls

  * **Voice Permissions**

    * Leave unchecked

* Under **Integration Type**, ensure that `Guild Install` is selected

* Copy the generated **invite URL** and use it to invite the bot to your server

---

## 🎠 Commands

> Note: Command visibility depends on your role (i.e., `StandupMod`, `TicketMod`, or general user).

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
/timezone      Set your timezone (e.g., UTC+2, UTC-5:30)
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

* Use the `✏️ Edit Content` button in `/preview` to set:

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
## 🎞️ Hosting Guide (Railway)

Clients will receive the StandUP Bot as a **precompiled ZIP package**, ready to deploy. No Git setup is required.

We recommend **[Railway](https://railway.app/)** for easy and reliable deployment of Python bots.

---

### 🧩 Why Railway?

- Simple UI and fast setup
- Supports environment variables
- Always-on deployments
- Free tier available for small-scale usage

---

### ⚙️ Setup Instructions (ZIP Build)

1. **Create a Railway Account**
   - Go to [railway.app](https://railway.app/)
   - Sign up or log in with GitHub

2. **Create a New Project**
   - Click **"New Project"**
   - Select **"Deploy from Repository"** (skip this and choose **"Blank Project"** if you're uploading files manually)

3. **Upload Your Bot Files**
   - Extract the provided `.zip` archive
   - Drag and drop all files (e.g. `bot.pyc`, `requirements.txt`, `license.txt`, `.env`, etc.) into the Railway **"Deployments"** section

4. **Set Up Environment Variables**
   - Go to the **"Variables"** tab
   - Add:
     ```
     DISCORD_TOKEN=your_token_here
     ```
   - Ensure any other `.env` variables used in your bot are also added

5. **Configure Startup Command**
   - Go to the **"Settings"** tab → Scroll to **"Start Command"**
   - Set:
     ```bash
     python bot.pyc
     ```

6. **Deploy**
   - Hit **"Deploy"** and Railway will spin up your bot
   - Monitor logs in real-time via the Railway dashboard

---

### ✅ Notes

- If your ZIP includes obfuscated/compiled Python (`.pyc`) files, make sure you include the required runtime files (`__pycache__` or `requirements.txt`).
- Do **not** include the raw `.env` file in public repositories or ZIPs. Clients should set their secrets using Railway’s UI.
- The bot will automatically handle internal data storage using JSON, so no external DB setup is needed.

For further help with Railway, see their [official docs](https://docs.railway.app/).

---

## ⚠️ Limitations

- The bot currently supports a **maximum of 60 open tickets** at any given time. Once this limit is reached, users will be unable to submit new tickets until some are resolved or closed.
- Please note that **Discord rate limits** may affect how often the bot can send messages or perform certain actions, especially if multiple commands are triggered in rapid succession. The bot handles most rate limits gracefully, but large servers should monitor usage accordingly.
- Tickets, role and thread management rely on **role/channel names being correctly configured** (see [🔧 Prerequisites](#-prerequisites)).

---

## 🧪 Testing Tips

* Use a private test server with test roles set up
* Use `/preview` often to confirm standup layout
* Manually verify ticket threads, assignment tagging, and role access

---

## 📜 License

Placeholder: *MIT / GPL / Custom License here*

---

## 🤝 Acknowledgements

* Placeholder: *Special thanks to contributors, libraries used (e.g. discord.py), or inspirations*

---

## 📇 Contact & Support

For issues, suggestions, or support:

* @marktwen28 on Discord
---

> Built with ❤️ to make async teamwork simple and effective.
