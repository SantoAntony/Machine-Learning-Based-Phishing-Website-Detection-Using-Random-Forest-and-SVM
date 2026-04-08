# config_creds.py

firebaseConfig = {
    "apiKey":            "AIzaSyBFl3yjzyQl_Bgld3NHzd5v5SHDQ8qzKHg",
    "authDomain":        "phishing-detector-496cd.firebaseapp.com",
    "databaseURL":       "https://phishing-detector-496cd-default-rtdb.firebaseio.com",
    "projectId":         "phishing-detector-496cd",
    "storageBucket":     "phishing-detector-496cd.firebasestorage.app",
    "messagingSenderId": "151349951542",
    "appId":             "1:151349951542:web:af0cfd9b76f135f8e52c97",
    "measurementId":     "G-BJF07KDMJ3"
}

firebaseConfigCreds = firebaseConfig

# ── Contact & Report forms (demo only) ──────────────────────────────────────

contactForm = """
<div class="contact-form">
  <h3>Send us a message</h3>
  <p style="opacity:0.8;margin-top:-8px;">(Demo form) This doesn't submit anywhere yet.</p>
  <label>Your name</label>
  <input type="text" name="name" placeholder="Jane Doe" style="width:100%;padding:10px;margin:6px 0 12px 0;" />
  <label>Your email</label>
  <input type="email" name="email" placeholder="jane@example.com" style="width:100%;padding:10px;margin:6px 0 12px 0;" />
  <label>Message</label>
  <textarea name="message" placeholder="How can we help?" rows="6" style="width:100%;padding:10px;margin:6px 0 12px 0;resize:vertical;"></textarea>
  <button type="button" style="padding:10px 14px;cursor:not-allowed;opacity:0.7;" title="Configure a backend to enable submissions">
    Submit (disabled)
  </button>
</div>
"""

reportForm = """
<div class="report-form">
  <h3>Report a suspicious link</h3>
  <p style="opacity:0.8;margin-top:-8px;">(Demo form) This doesn't submit anywhere yet.</p>
  <label>Phishing URL</label>
  <input type="url" name="url" placeholder="https://example.com" style="width:100%;padding:10px;margin:6px 0 12px 0;" />
  <label>Notes (optional)</label>
  <textarea name="notes" placeholder="Why do you think it's phishing?" rows="5" style="width:100%;padding:10px;margin:6px 0 12px 0;resize:vertical;"></textarea>
  <button type="button" style="padding:10px 14px;cursor:not-allowed;opacity:0.7;" title="Configure a backend to enable submissions">
    Submit (disabled)
  </button>
</div>
"""