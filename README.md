# Senior-Capstone-Project-Spring-2026
Design and Development of Fake Job Posting Detection Tool: Modifying Tools To Help Students Avoid Fake Job Postings 

CYB 4800: Senior Capstone Project | Spring 2026
Jynalis Diaz | Instructor: Dr. Sagar Raina

Overview:

Fake job listings are a major threat to students searching for internships and full- or part-time work. Scammers have been creating convincing postings to collect personal information such as resumes, phone numbers, and Social Security numbers from applicants who may not recognize the warning signs.
This project builds on and extends the open-source fake-job-detector by Virajk19, which uses a multi-agent LLM approach to produce a risk score from a job posting. 
While that tool demonstrates that automated detection is achievable, it, like most existing tools, returns a verdict without explaining the reasoning behind it. 
A student or regular user who gets a "65% risk score" learns nothing about why the posting is suspicious or how to spot similar scams in the future.
This project takes that foundation and shifts the focus from detection-only to detection + education. 
The classification engine was rebuilt using Logistic Regression with TF-IDF trained on a merged dataset of ~20,000 real and fake job postings. 
More importantly, a full explanation layer was added on top: every red flag detected is surfaced with a plain-language description of why that pattern is suspicious and what the user should do about it. 
The goal is not just to warn users, it's to teach them to recognize these patterns on their own over time.

Key additions over the original tool:

*Plain-language explanations for every flag, not just a score

*9 expanded rule-based flag categories with regex pattern matching

*STRONG_FLAGS override logic to correct the ML model when a high-confidence red flag is detected

*SQLite scan history so users can review all past analyses

*Borderline confidence caution messages so users are never given a false sense of certainty

*A safety reminder on every clean result to verify the company independently

My Tech Stack:

Layer                     Technology

*Backend                  Python 3, Flask

*Machine Learning         scikit-learn (Logistic Regression + TF-IDF)

*Rule-Based Detection     Python re (regex)

*Database                 SQLite via sqlite3

*Frontend                 HTML, CSS (Jinja2 templates)

*Development Environment  Kali Linux (virtual machine)

Machine Learning Approaches Used:

This model went through two iterations before reaching its final iteration:

v1; Multinomial Naive Bayes + CountVectorizer
Trained on the Kaggle EMSCAD dataset (17,880 postings). 
Naive Bayes treats every word independently and with equal weight, which limits its ability to detect newer scam styles. 
Accuracy: ~78%.

v2; Logistic Regression + TF-IDF (Final)
Upgraded to TF-IDF vectorization, which weights words by how meaningful they are, and Logistic Regression, which handles class imbalance more reliably. 
The training data was expanded by merging the EMSCAD dataset with a newer Kaggle dataset (Yadav, 2025) into a combined file of ~20,880 postings. 
class_weight="balanced" was used to prevent the model from defaulting toward legitimate due to the skewed dataset ratio. 
Final accuracy: ~90–95%.

Future direction: Random Forest classifier, which builds multiple decision trees and is more reliable in borderline cases.

Detection Flag Categories:

The rule-based layer checks for 9 categories of warning patterns:

1. Requests for personal information early (SSN, bank account, passport)
2. Asks for payment or fees (deposits, training fees, wire transfers)
3. Vague or no company info ("no experience required", "anyone can apply")
4. Unusual contact method (WhatsApp, Telegram, direct message)
5. Unrealistic salary or promise (guaranteed income, risk-free earnings)
6. Cryptocurrency payment (Bitcoin, Ethereum, wallet address)
7. Google Form or unofficial application link (shortened URLs, Google Forms)
8. Remote-only interview red flag (hired without interview, Zoom-only with no in-person option)
9. Work from home unrealistic claims ("be your own boss", "set your own hours")

Each flag is matched using regex patterns and returns a detailed plain-language explanation explaining why the pattern is suspicious and what the user should do.

Project Structure:

Web_Tool/
├── app.py                      # Main Flask app — routes, ML model, flag logic
├── database.py                 # SQLite connection, table init, save & retrieve
├── requirements.txt            # Python dependencies
│
├── model/
│   ├── train_model.py          # Final training script (Logistic Regression + TF-IDF)
│   └── model.pkl               # Trained model (generated after running train_model.py)
│
├── data/
│   ├── fake_job_postings.csv           # Kaggle EMSCAD dataset (Bansal, 2018)
│   ├── fake_real_job_postings_3000x25.csv  # Newer dataset (Yadav, 2025)
│   └── combined_job_postings.csv       # Merged training dataset
│
├── templates/
│   ├── index.html              # Home page — paste job posting form
│   ├── result.html             # Results page — verdict, flags, explanations
│   └── history.html            # History page — all past scans
│
└── static/
    └── style.css               # Styling — color-coded verdicts, flag cards, caution messages.

Installation & Setup:

> Developed and tested on **Kali Linux**. Should work on any Python 3 environment.

#1. Clone the repository

```bash
git clone https://github.com/**YOUR_USERNAME**/Senior-Capstone-Project-Spring-2026.git
cd Senior-Capstone-Project-Spring-2026
```

#2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#3. Download the datasets

This project uses two publicly available Kaggle datasets. **Due to file size, raw CSV files are not included in this repository**

- [EMSCAD Dataset — Bansal (2018)](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction) → save as `data/fake_job_postings.csv`
- [Fake vs Real Job Postings — Yadav (2025)](https://www.kaggle.com/datasets/khushikyad001/fake-vs-real-job-postings-synthetic-nlpdataset) → save as `data/fake_real_job_postings_3000x25.csv`

#4. Merge the datasets

```bash
python3 -c "
import pandas as pd
df1 = pd.read_csv('data/fake_job_postings.csv')
df1['text'] = df1['title'].fillna('') + ' ' + df1['description'].fillna('') + ' ' + df1['requirements'].fillna('')
df1 = df1[['text', 'fraudulent']].rename(columns={'fraudulent': 'is_fake'})
df2 = pd.read_csv('data/fake_real_job_postings_3000x25.csv')
df2['text'] = df2['job_title'].fillna('') + ' ' + df2['job_description'].fillna('') + ' ' + df2['requirements'].fillna('')
df2 = df2[['text', 'is_fake']]
combined = pd.concat([df1, df2], ignore_index=True)
combined.to_csv('data/combined_job_postings.csv', index=False)
print('Combined dataset saved.')
"
```

#5. Train the model

```bash
python3 model/train_model.py
```

#6. Run the application

```bash
python3 app.py
```

Then open your browser and go to: `http://localhost:5000`

Testing Results:

The tool was tested on 10 job postings: 6 AI-generated (2 obvious fakes, 2 clearly legitimate, 2 deliberately tricky), 3 real postings from Handshake, and 1 real WhatsApp scam posting.

 Test Case                                       Result   
-Obvious fakes;                                   Mixed, some correctly returned LIKELY FAKE with multiple flags and explanations; others returned LIKELY LEGITIMATE despite being fake, showing the ML model's reliance on known scam vocabulary

-Clear legitimate postings;                       Correctly returned LIKELY LEGITIMATE with safety net reminder to verify independently

-Hard fakes with hidden patterns;                Inconsistent, the tool caught some through the rule-based layer when the ML model missed the pattern, but others slipped through entirely due to professionally written language with no common scam phrases

-Professionally written fake (no scam language);  Returned LIKELY LEGITIMATE, known limitation; if a posting avoids typical scam vocabulary the model has no pattern to match against

-WhatsApp scam posting;                           Flagged: unusual contact method, personal email, suspicious area code that was given to the "model_train.py"

Limitations:

-The ML model relies on patterns present in its training data. Scam postings written without common scam language can yield a false-legitimate verdict.

-Training datasets were collected in 2018 and 2025; scam phrases continue to evolve, and the model would benefit from annual retraining.

-The tool is currently local only and requires manual setup. 

-This tool is meant to guide and educate, not provide a guaranteed verdict. Always verify any employer independently before sharing personal information.

Future Improvements:

-Expand the scam phone number and email blocklist

-Add URL scraping so users can submit a job link directly instead of pasting text

-Build a feedback mechanism so users can flag and report incorrect results for model retraining

-Upgrade to a Random Forest classifier for improved accuracy on borderline cases

-Deploy to a cloud environment (AWS) for public access without local setup

References:

*Bansal, S. (2018). Real or fake? Fake job posting prediction [Dataset]. Kaggle. https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction

*Pillai, A. S. (2023). Detecting fake job postings using bidirectional LSTM. International Research Journal of Modernization in Engineering Technology and Science, 5(3). https://doi.org/10.56726/IRJMETS35202

*Yadav, K. (2025). Fake vs real job postings (synthetic NLP dataset) [Dataset]. Kaggle. https://www.kaggle.com/datasets/khushikyad001/fake-vs-real-job-postings-synthetic-nlpdataset

*Virajk19. (2025). fake-job-detector [Source code]. GitHub. https://github.com/Virajk19/fake-job-detector

*Pallets Projects. (n.d.). Flask documentation. https://flask.palletsprojects.com/en/stable/

*scikit-learn developers. (n.d.). LogisticRegression. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html

License:

This project is licensed under the MIT License. See LICENSE for details.