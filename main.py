from app import app
import os

# For Vercel/Netlify/Heroku deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
