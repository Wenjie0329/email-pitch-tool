# Email Pitch Tool

A lightweight email outreach automation tool. Send personalized cold emails, set up multi-step follow-up sequences, and track open/click/reply rates.

**Tech stack:** Python (FastAPI) + Vanilla JS + SQLite + Gmail API

## Features

- **Gmail OAuth** - Securely connect your Gmail account via Google's official OAuth 2.0
- **Bulk import contacts** - CSV, Excel, manual input, or paste
- **Personalized templates** - Use variables like `{{first_name}}`, `{{company}}`
- **Plain text + Markdown support** - Write emails naturally with `**bold**`, `[links](url)`, `![images](url)`, or use HTML
- **Multi-step sequences** - Automatic follow-up emails with configurable delays
- **Open/click/reply tracking** - Track engagement via a free Render-hosted tracker
- **Auto sync** - Tracking data syncs every 10 minutes

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/email-pitch-tool.git
cd email-pitch-tool
pip install -r requirements.txt
```

### 2. Set up Google OAuth credentials

This is the most important step. You need to create a Google Cloud project so the app can send emails via your Gmail account.

#### Step 2a: Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top left, then **New Project**
3. Name it anything (e.g. `email-pitch-tool`), click **Create**

#### Step 2b: Enable Gmail API

1. In your project, go to **APIs & Services** > **Library**
2. Search for **Gmail API**
3. Click it, then click **Enable**

#### Step 2c: Configure OAuth consent screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Select **External** user type, click **Create**
3. Fill in:
   - App name: `Email Pitch Tool`
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On the **Scopes** page, click **Add or Remove Scopes**, add:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
6. Click **Save and Continue**
7. On **Test users**, click **Add Users**, add your Gmail address
8. Click **Save and Continue**

> **Note:** While in "Testing" mode, only the test users you added can use the app. This is fine for personal use. To let anyone use it, you'd need to go through Google's verification process.

#### Step 2d: Create OAuth credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Application type: **Web application**
4. Name: `Email Pitch Tool`
5. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:8000/oauth/callback
   ```
6. Click **Create**
7. Click **Download JSON**, save it as `credentials.json` in the project root

Your `credentials.json` should look like `credentials.example.json` in this repo.

> **Security:** Never commit `credentials.json` to Git. It's already in `.gitignore`.

### 3. Run the app

```bash
python app.py
```

Open `http://localhost:8000` in your browser.

### 4. Connect Gmail

1. Click **+ Bindind Gmail Account** in the web UI
2. Log in with the Gmail account you added as a test user
3. Grant permissions

You're ready to send emails!

---

## Set Up Open Rate Tracking (Recommended)

By default, open tracking won't work because the tracking pixel URL points to `localhost`, which email clients can't reach. To fix this, deploy the lightweight tracker service to [Render](https://render.com/) (free).

### Deploy tracker to Render

1. **Create a GitHub repo** named `email-tracker`
2. **Upload** the 3 files from `tracker-render/` folder:
   - `tracker.py`
   - `requirements.txt`
   - `RENDER_DEPLOY.md`
3. **Go to [Render](https://render.com/)** and create a **New Web Service**
4. Connect your `email-tracker` GitHub repo
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn tracker:app`
   - **Instance Type:** Free
6. Click **Create Web Service**
7. Wait for deploy to finish. Your tracker URL will be:
   ```
   https://your-app-name.onrender.com
   ```

### (Optional) Add a PostgreSQL database

The free Render instance restarts periodically, which resets SQLite data. For persistent storage:

1. In Render, click **New +** > **PostgreSQL**
2. Create a free database
3. Copy the **Internal Database URL**
4. Add it as an environment variable `DATABASE_URL` in your Web Service

### Connect local app to tracker

```bash
# Set the tracker URL and start
export TRACKER_URL=https://your-app-name.onrender.com
python app.py
```

Make it permanent:
```bash
echo 'export TRACKER_URL=https://your-app-name.onrender.com' >> ~/.zshrc  # macOS
echo 'export TRACKER_URL=https://your-app-name.onrender.com' >> ~/.bashrc  # Linux
```

You should see `[Scheduler] Tracker sync enabled (every 10 minutes)` when the app starts.

For more details, see [tracker-render/RENDER_DEPLOY.md](tracker-render/RENDER_DEPLOY.md).

---

## Writing Email Templates

The editor supports **plain text** (with Markdown), **HTML**, or a mix.

### Plain text with Markdown (recommended)

Just type naturally. The system auto-detects plain text and converts it properly:

```
Hi {{first_name}},

I came across **{{company}}** and was impressed by what your team is doing.

We help companies like yours solve data challenges at scale.

Check out our case study: [Read more](https://example.com/case-study)

Would love to set up a quick 15-min call. What does your schedule look like?

Best,
Your Name
https://yoursite.com
```

#### Supported Markdown syntax

| Syntax | Result |
|--------|--------|
| `**text**` | **bold** |
| `*text*` | *italic* |
| `[label](url)` | Clickable link |
| `![alt](image-url)` | Embedded image |
| Bare `https://...` URL | Auto-linked |
| Line breaks | Preserved |

### Variables

Use `{{variable_name}}` in both subject and body. Variables are filled from your CSV/Excel columns:

| Variable | Example |
|----------|---------|
| `{{first_name}}` | John |
| `{{company}}` | Acme Inc |
| `{{title}}` | CEO |
| `{{email}}` | john@example.com |

Default values: `{{name|there}}` renders as "there" if `name` is empty.

### HTML mode

If you include any HTML tags (like `<p>`, `<b>`, `<a>`), the body is sent as raw HTML:

```html
<p>Hi {{first_name}},</p>
<p>I noticed <b>{{company}}</b> is growing fast.</p>
<p><a href="https://example.com">Check this out</a></p>
```

---

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TRACKER_URL` | Render tracker URL for open tracking | Recommended | - |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Yes* | - |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Yes* | - |
| `BASE_URL` | App's public URL (for OAuth callback) | No | `http://localhost:8000` |
| `PORT` | App port | No | `8000` |
| `TEST_MODE` | Set `true` to skip sending real emails | No | `false` |

*Not required if you have a `credentials.json` file.

---

## Project Structure

```
email-pitch-tool/
├── app.py                  # FastAPI backend
├── index.html              # Frontend (single-page app)
├── requirements.txt        # Python dependencies
├── credentials.json        # Google OAuth credentials (NOT committed)
├── credentials.example.json# Template for credentials.json
├── .gitignore
│
├── tracker-render/         # Lightweight open-tracking service (deploy to Render)
│   ├── tracker.py          # Flask app
│   ├── requirements.txt
│   └── RENDER_DEPLOY.md    # Deployment guide
│
├── examples/
│   └── example_leads.csv   # Sample CSV for import
│
└── docs/
    └── prd.md              # Product requirements doc
```

---

## Troubleshooting

### Open rate shows 0%

1. Make sure you deployed the tracker to Render and set `TRACKER_URL`
2. Verify the tracker is running: `curl https://your-app.onrender.com/health`
3. Data syncs every 10 minutes -- wait and click "Refresh Stats"
4. Gmail proxies images; some opens may not be tracked due to caching

### OAuth callback fails

Make sure your Google Cloud Console has the correct redirect URI:
- Local: `http://localhost:8000/oauth/callback`

### "Please add test users" error

Your OAuth app is in Testing mode. Go to **Google Cloud Console** > **OAuth consent screen** > **Test users** and add the Gmail address you're trying to connect.

### Database locked errors

The app uses SQLite WAL mode to handle concurrent access. If you still see errors, make sure only one instance of the app is running.

---

## Gmail Sending Limits

- Personal Gmail: ~500 emails/day
- Google Workspace: ~2,000 emails/day
- Recommended send rate: 1 email every 5-10 minutes to avoid spam flags

---

## Compliance

When using this tool, please comply with applicable email regulations:

- **CAN-SPAM Act** (US) - Include unsubscribe option, honest subject lines
- **GDPR** (EU) - Obtain consent, provide data deletion upon request
- **CASL** (Canada) - Get express consent before sending

---

## License

MIT License

---

## Contributing

Issues and pull requests welcome!
