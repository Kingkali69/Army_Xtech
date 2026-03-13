# Windows Proxy Fix - Quick Guide

If you're getting proxy errors when trying to access OMNI, here's how to fix it.

---

## Quick Fix (Easiest)

**Just type these URLs directly in your browser:**

1. **Operations Console:** `http://127.0.0.1:8888`
2. **AI Chat:** `http://127.0.0.1:8889`

Using `127.0.0.1` instead of `localhost` usually bypasses proxy settings.

---

## If That Doesn't Work

### Option 1: Disable Proxy for Localhost

1. Press `Windows Key + I` (opens Settings)
2. Go to **Network & Internet** → **Proxy**
3. Scroll down to **Manual proxy setup**
4. Find **"Use a proxy server for your LAN"**
5. **Uncheck** that box
6. Click **Save**
7. Try the URLs again: `http://localhost:8888`

### Option 2: Add Localhost to Proxy Bypass

1. Press `Windows Key + I` (opens Settings)
2. Go to **Network & Internet** → **Proxy**
3. Scroll down to **Manual proxy setup**
4. Find **"Use a proxy server for your LAN"**
5. Click **Advanced**
6. In **"Exceptions"** or **"Bypass proxy server for"**, add:
   ```
   localhost;127.0.0.1;*.local
   ```
7. Click **OK** → **Save**
8. Try the URLs again

---

## Check if Servers Are Running

Open **Command Prompt** (cmd) and run:

```cmd
netstat -an | findstr "8888 8889"
```

You should see:
```
TCP    0.0.0.0:8888           0.0.0.0:0              LISTENING
TCP    0.0.0.0:8889           0.0.0.0:0              LISTENING
```

If you see those, the servers ARE running - it's just a browser/proxy issue.

---

## Manual Access (If Auto-Open Fails)

Even if the browser doesn't open automatically, you can:

1. Open your browser manually (Chrome, Edge, Firefox)
2. Type in the address bar:
   - `http://127.0.0.1:8888` (Operations Console)
   - `http://127.0.0.1:8889` (AI Chat)

---

## Still Not Working?

1. **Check Windows Firewall:**
   - Windows Security → Firewall → Allow an app
   - Make sure Python is allowed

2. **Check if ports are in use:**
   ```cmd
   netstat -an | findstr "8888 8889"
   ```
   If nothing shows, servers aren't running

3. **Check launcher logs:**
   - Look for any error messages in the launcher window
   - Check if Python is installed and in PATH

---

## The Real Fix

I've updated the Windows launchers to use `127.0.0.1` instead of `localhost`, which should bypass proxy issues automatically.

**Just re-download the repo or pull the latest changes.**

---

**TL;DR:** Type `http://127.0.0.1:8888` in your browser. That usually works.
