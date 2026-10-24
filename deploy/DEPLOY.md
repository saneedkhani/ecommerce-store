# Deploying ShopWave to PythonAnywhere (free)

The free plan gives you a permanent link like `https://yourname.pythonanywhere.com`, keeps the SQLite
database and uploaded images, and needs no credit card. Total time: about 15 minutes.

## 1. Create an account
Sign up at https://www.pythonanywhere.com/registration/register/beginner/ (the free "Beginner" plan).
Your username becomes your site address, so pick something professional, e.g. `saneedullah`.

## 2. Create the web app
1. Open the **Web** tab and click **Add a new web app**, then **Next**.
2. Choose **Manual configuration** (not "Django").
3. Choose the newest **Python 3.13** (or 3.12) and click **Next**.

## 3. Run the setup script
Open the **Consoles** tab and start a **Bash** console, then paste:
```bash
git clone https://github.com/saneedkhani/ecommerce-store.git ~/ecommerce-store
bash ~/ecommerce-store/deploy/pythonanywhere_setup.sh
```
The script creates a virtual environment, installs the requirements, writes a production `.env`
(new secret key, `DEBUG=False`), sets up the database, collects static files, loads the demo
products and configures the WSGI file. It takes a few minutes.

## 4. Finish the Web tab settings
On the **Web** tab:

| Setting | Value |
|---|---|
| Virtualenv | `/home/<username>/.virtualenvs/shopwave` |
| Static files: `/static/` | `/home/<username>/ecommerce-store/staticfiles` |
| Static files: `/media/` | `/home/<username>/ecommerce-store/media` |
| Force HTTPS | **On** |

Click the green **Reload** button and open `https://<username>.pythonanywhere.com`.

## 5. Create your staff account
Back in the Bash console (type your own password when asked):
```bash
source ~/.virtualenvs/shopwave/bin/activate
cd ~/ecommerce-store
python manage.py createsuperuser
```
Log in at `/accounts/admin-login/` to open the staff dashboard.

## Updating the live site
After pushing changes to GitHub, run in a PythonAnywhere Bash console:
```bash
cd ~/ecommerce-store && git pull && bash deploy/pythonanywhere_setup.sh
```

## Notes
- Free web apps must be renewed once every 3 months: click **Run until 3 months from today** on the Web tab
  (PythonAnywhere emails a reminder).
- If something breaks, check the **error log** link on the Web tab.
- Payment details on the payment page come from `STORE_ACCOUNT_*` variables in `.env` (see `.env.example`).
