from flask import Flask, render_template, request, session
from database import init_db, save_analysis, get_all_analyses, get_recent_analyses
import pickle
import re

app = Flask(__name__)
app.secret_key = "fakejobdetector2024"
APP_NAME = "Fake Job Posting Detection Tool"

# Load trained model
with open("model/model.pkl", "rb") as f:
    model = pickle.load(f)

# Initialize database when app starts
init_db()

# Strong flags that can override the model verdict
STRONG_FLAGS = [
    "known scam number detected",
    "suspicious phone number detected",
    "suspicious email address detected",
    "suspicious email format detected",
    "personal email used instead of company email",
    "asks for payment or fees",
    "requests personal info early",
    "cryptocurrency payment",
    "google form or unofficial application"
]

# Warning flags with detailed explanations
WARNING_FLAGS = {
    "requests personal info early": {
        "patterns": [r"\b(ssn|social security|bank account|credit card|passport)\b"],
        "explanation": (
            "Legitimate employers do not ask for sensitive personal information such as your "
            "Social Security Number, bank account details, or passport information during the "
            "application stage. This type of information is only needed after you have been "
            "officially hired and is handled through secure HR systems. If a job posting or "
            "recruiter asks for this upfront, it is a strong indicator that they are attempting "
            "to collect your data for identity theft or financial fraud. Never share this "
            "information before verifying the employer is real."
        )
    },
    "asks for payment or fees": {
        "patterns": [r"\b(upfront fee|registration fee|training fee|deposit required|wire transfer|pay to apply)\b"],
        "explanation": (
            "Real employers pay you — you never pay them. Any job that requires an upfront "
            "payment, deposit, or fee to get started is almost certainly a scam. This is a "
            "classic fraud tactic where scammers convince applicants to send money for things "
            "like training materials, background checks, or equipment, and then disappear. "
            "Legitimate companies cover their own hiring costs. If money is being requested "
            "from you before you have even started working, walk away immediately."
        )
    },
    "vague or no company info": {
        "patterns": [r"\b(no experience required|anyone can apply)\b"],
        "explanation": (
            "Phrases like 'no experience required' or 'anyone can apply' are commonly used "
            "in fraudulent postings to cast a wide net and attract as many applicants as "
            "possible. While some entry level jobs do exist, legitimate postings will still "
            "describe specific responsibilities, team structure, and company background. "
            "A real employer wants the right candidate, not just any candidate. Vague postings "
            "with no detail about the company, its location, or its industry are a red flag "
            "that the poster may not represent a real organization."
        )
    },
    "unusual contact method": {
        "patterns": [r"\b(whatsapp|telegram|text us|direct message)\b"],
        "explanation": (
            "Professional companies communicate through official business email addresses or "
            "phone systems, not personal messaging apps like WhatsApp or Telegram. When a "
            "recruiter insists on communicating through these platforms it is often because "
            "they want to avoid a paper trail and make it harder for you to verify their "
            "identity. Scammers use these apps because accounts are easy to create, hard to "
            "trace, and allow them to impersonate real companies. Always insist on "
            "communicating through official company channels."
        )
    },
    "unrealistic salary or promise": {
        "patterns": [r"\b(earn \$[0-9,]+ per (day|week)|guaranteed income|risk.?free)\b"],
        "explanation": (
            "Promises of unusually high pay for little work, guaranteed income, or risk-free "
            "earnings are major warning signs. Scammers use these claims to make their postings "
            "attractive and create a sense of urgency so you apply without thinking critically. "
            "In reality, no legitimate job can guarantee income or promise risk-free results. "
            "If the salary being offered seems too good to be true for the type of work being "
            "described, it almost certainly is. Research typical salaries for the role on "
            "sites like Glassdoor or LinkedIn before applying."
        )
    },
    "cryptocurrency payment": {
        "patterns": [r"\b(bitcoin|crypto|ethereum|usdt|binance|wallet address)\b"],
        "explanation": (
            "Requests for cryptocurrency payments or mentions of crypto wallets in job postings "
            "are a major modern scam indicator. Legitimate employers never pay salaries or "
            "request payments in cryptocurrency because it is untraceable and irreversible. "
            "Scammers use crypto specifically because once you send it, it cannot be recovered. "
            "If a job mentions crypto in any financial context, treat it as a serious red flag."
        )
    },
    "google form or unofficial application": {
        "patterns": [r"\b(google form|docs\.google|bit\.ly|tinyurl)\b"],
        "explanation": (
            "Legitimate companies use official application portals on their own websites or "
            "established platforms like LinkedIn, Indeed, or Handshake. Asking applicants to "
            "fill out a Google Form or click a shortened URL is a common scam tactic used to "
            "collect personal information without any accountability. Shortened links can also "
            "lead to phishing websites designed to steal your login credentials."
        )
    },
    "remote only interview red flag": {
        "patterns": [r"\b(zoom interview only|no in.?person|fully remote hiring|hired without interview)\b"],
        "explanation": (
            "While remote interviews are common and legitimate, postings that emphasize you "
            "will be hired without any real interview process or that explicitly avoid any "
            "in person or video verification are suspicious. Scammers avoid face to face "
            "contact because it makes them easier to identify and report. A legitimate employer "
            "will always want to properly vet candidates through a real interview process."
        )
    },
    "work from home unrealistic claims": {
        "patterns": [r"\b(set your own hours|be your own boss|work from anywhere|no boss)\b"],
        "explanation": (
            "Phrases like 'set your own hours', 'be your own boss', or 'work from anywhere' "
            "are hallmarks of multi-level marketing schemes and job scams targeting students. "
            "Real remote jobs still have schedules, managers, and accountability. These phrases "
            "are designed to appeal to people seeking flexibility and independence, but they "
            "rarely represent legitimate employment. Always look for specific job duties, "
            "reporting structures, and company details before applying."
        )
    },
}

# Known scam numbers
KNOWN_SCAM_NUMBERS = [
    "+1 (363) 201-2819",
    "+1(205)651-9396",
]

# Known scam email patterns
KNOWN_SCAM_EMAIL_PATTERNS = [
    r"aiden\d+\+\w+@",
    r"\w+\d{3,}\+\w+@",
    r"@pastryofistanbul\.com",
]

# Fake area codes
FAKE_AREA_CODES = ["363", "372", "353", "382"]

def check_flags(text):
    text_lower = text.lower()
    found = []

    # Check general warning flags
    for flag_name, flag_data in WARNING_FLAGS.items():
        for pattern in flag_data["patterns"]:
            if re.search(pattern, text_lower):
                found.append({
                    "flag": flag_name,
                    "explanation": flag_data["explanation"]
                })
                break

    # Check for known scam phone numbers
    for number in KNOWN_SCAM_NUMBERS:
        if number in text:
            found.append({
                "flag": f"known scam number detected: {number}",
                "explanation": (
                    f"The phone number {number} has been previously identified as associated "
                    "with fraudulent job postings. Scammers frequently use virtual or disposable "
                    "phone numbers to avoid being traced. If you have received messages from this "
                    "number do not respond and block it immediately. Never call back unknown "
                    "numbers found in job postings without verifying the company first through "
                    "their official website or LinkedIn page."
                )
            })

    # Check for suspicious area codes
    phone_matches = re.findall(r'\+?1?\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}', text)
    for number in phone_matches:
        digits = re.sub(r'\D', '', number)
        area_code = digits[1:4] if digits.startswith('1') else digits[0:3]
        if area_code in FAKE_AREA_CODES:
            found.append({
                "flag": f"suspicious phone number detected: {number.strip()}",
                "explanation": (
                    f"The area code in {number.strip()} does not correspond to a real US "
                    "telephone area code. Scammers often use virtual phone services that allow "
                    "them to generate numbers with any area code making them appear local or "
                    "legitimate. A fake area code is a strong indicator that the contact "
                    "information in this posting is not from a real business. Verify any "
                    "phone number by searching it online before making contact."
                )
            })

    # Check for suspicious email patterns
    for pattern in KNOWN_SCAM_EMAIL_PATTERNS:
        if re.search(pattern, text_lower):
            found.append({
                "flag": "suspicious email address detected",
                "explanation": (
                    "This posting contains an email address that matches known scam patterns. "
                    "Fraudulent recruiters often use personal emails with random numbers, "
                    "unrelated business domains, or the '+' trick to create throwaway addresses "
                    "that are hard to trace. For example an email like "
                    "aiden45285+invst@pastryofistanbul.com uses a personal name, random numbers, "
                    "a '+' variation, and a completely unrelated domain, none of which belong "
                    "to a real employer. Always verify that the email domain matches the "
                    "company's official website before responding."
                )
            })
            break

    # Check for personal email domains
    personal_email_pattern = r'\b[\w\.\+]+@(gmail|yahoo|hotmail|outlook|aol)\.com\b'
    if re.search(personal_email_pattern, text_lower):
        found.append({
            "flag": "personal email used instead of company email",
            "explanation": (
                "A legitimate company will always contact you from an official business email "
                "address that matches their company domain such as hr@companyname.com. When a "
                "recruiter uses a personal Gmail, Yahoo, or Hotmail address it means either the "
                "company does not exist or the person is not actually affiliated with the company "
                "they claim to represent. This is one of the easiest red flags to spot and one "
                "of the most reliable indicators of a fraudulent posting. Search the company "
                "name independently and find their official contact information to verify."
            )
        })

    # Check for + trick in email
    plus_email_pattern = r'\b[\w]+\d+\+[\w]+@'
    if re.search(plus_email_pattern, text_lower):
        found.append({
            "flag": "suspicious email format detected (+ trick used)",
            "explanation": (
                "The '+' symbol in an email address is used to create variations of the same "
                "inbox, for example name+tag@gmail.com still delivers to name@gmail.com. "
                "Scammers exploit this feature to create many throwaway contact addresses that "
                "all funnel into one inbox making them harder to track and block. No legitimate "
                "employer uses this format for professional communication. If you see a '+' in "
                "a recruiter's email address treat it as a serious red flag and do not respond."
            )
        })

    return found

@app.route("/", methods=["GET"])
def index():
    if "history" not in session:
        session["history"] = []
    return render_template("index.html", app_name=APP_NAME, history=session["history"])

@app.route("/analyze", methods=["POST"])
def analyze():
    job_text = request.form.get("job_text", "")

    prediction = model.predict([job_text])[0]
    probability = model.predict_proba([job_text])[0][1]
    flags = check_flags(job_text)

    # Only override model if a strong flag is detected
    strong_flag_found = any(
        any(strong in item["flag"] for strong in STRONG_FLAGS)
        for item in flags
    )

    if strong_flag_found and prediction == 0:
        probability = max(probability, 0.75)
        prediction = 1

    result = {
        "verdict": "LIKELY FAKE" if prediction == 1 else "LIKELY LEGITIMATE",
        "confidence": f"{probability * 100:.1f}%",
        "flags": flags,
        "job_text": job_text[:300] + "..." if len(job_text) > 300 else job_text
    }

    # Save to SQLite database
    save_analysis(job_text, result["verdict"], result["confidence"], flags)

    # Save to session history
    if "history" not in session:
        session["history"] = []

    session["history"].append({
        "verdict": result["verdict"],
        "confidence": result["confidence"],
        "preview": job_text[:100] + "..." if len(job_text) > 100 else job_text,
        "flag_count": len(flags)
    })
    session.modified = True

    return render_template("result.html", result=result, app_name=APP_NAME)

@app.route("/history")
def history():
    analyses = get_all_analyses()
    return render_template("history.html", analyses=analyses, app_name=APP_NAME)

if __name__ == "__main__":
    app.run(debug=True)
