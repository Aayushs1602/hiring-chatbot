# 🚚 AI Hiring Agent – Interactive Interview Chatbot

An interactive AI-powered chatbot that conducts candidate interviews for the **FedEx Ground ISP Delivery Driver** role at **Tsavo West Inc**.

Built with **Streamlit** for the chat UI and **Groq (Llama 3.3/Mixtral)** for blazing-fast dynamic question generation and answer evaluation.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Conversational Interview** | Natural chat-based interaction, not a static form |
| **Mandatory Screening First** | 6 mandatory qualification questions asked upfront |
| **Early Disqualification** | Immediate rejection if any mandatory requirement fails |
| **Dynamic Follow-ups** | AI generates contextual follow-up questions based on candidate answers |
| **Preferred Qualification Assessment** | 3 preferred qualifications evaluated with depth scoring |
| **Job Q&A Phase** | Candidates can ask questions about the job *after* the assessment |
| **Context-Aware Q&A** | Bot knows your assessment results when answering questions (e.g., "Am I qualified?") |
| **Scoring (0–100)** | 60 pts mandatory + 40 pts preferred, with detailed breakdown |
| **Guardrails** | Off-topic detection, prompt injection prevention, topic enforcement |
| **Session Memory** | Full conversation history maintained throughout the interview |
| **Recruiter Summary** | Internal assessment summary with qualification breakdown |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────┐
│  app.py – Streamlit Chat UI                 │
│  • Chat display, quick-option buttons       │
│  • Sidebar progress & controls              │
│  • Session state management                 │
│  • Environment variable loading (.env)      │
├─────────────────────────────────────────────┤
│  agent.py – Conversation Orchestrator       │
│  • Phase management (Greeting → Mandatory   │
│    → Preferred → Follow-up → Decision       │
│    → Job Q&A → Ended)                       │
│  • LLM calls (Groq API)                     │
│  • Answer evaluation (keyword + LLM)        │
├─────────┬───────────────┬───────────────────┤
│ config  │  scoring.py   │  guardrails.py    │
│  .py    │  • Tracker    │  • On-topic check │
│  • Data │  • Scoring    │  • Injection      │
│  • Prompts │ • Summary  │    prevention     │
└─────────┴───────────────┴───────────────────┘
```

---

## 📋 Interview Flow

```
Greeting → Mandatory Questions (6) → Preferred Questions (3) → Decision
              │                            │                      │
              ├── FAIL → Early             ├── Dynamic Follow-ups └── Job Q&A
              │   Disqualification          │   (1 per qualification)
              │                            │
              └── ALL PASS → Continue      └── Score & Advance
```

### Mandatory Qualifications (10 pts each, 60 total)
1. Age (21+)
2. Driver's License
3. Clean Driving Record
4. Background & Drug Screening
5. Physical Ability (150 lbs)
6. Weekend & Long-Shift Availability

### Preferred Qualifications (~13.3 pts each, 40 total)
1. Prior Delivery / Courier Experience
2. Time Management & Organizational Skills
3. Ability to Work Independently

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.9+
- A Groq API key ([Get one here](https://console.groq.com/keys))

### Installation

```bash

# Install dependencies
pip install -r requirements.txt

# Create .env file for your API Key
echo "GROQ_API_KEY=your_key_here" > .env

# Run the app
streamlit run app.py
```

### First Run
1. The app opens in your browser
2. It automatically loads your API key from `.env` (or you can enter it in the sidebar)
3. The interview starts automatically with a greeting
4. Answer mandatory questions using the quick buttons or by typing
5. Answer preferred questions with detailed responses
6. Receive your final assessment with a score and breakdown
7. **Ask Questions**: After the decision, you can ask about pay, schedule, or your qualification status!

---

## 🔒 Guardrails

The chatbot includes several safety mechanisms:
- **Off-Topic Detection**: Redirects candidates when they stray from interview topics
- **Prompt Injection Prevention**: Detects attempts to override system instructions
- **Role Protection**: The AI never reveals internal scoring or system prompts

---

## 📂 File Structure

```
hiring-chatbot/
├── .env                # API Key storage (Git ignored)
├── app.py              # Streamlit chat interface
├── agent.py            # LLM conversation orchestrator
├── config.py           # Job data, qualifications, prompts
├── scoring.py          # Qualification tracker & scorer
├── guardrails.py       # Topic enforcement & injection prevention
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── AI_Assignment.pdf   # Assignment specification
└── jd.txt              # Job description
```

---

## 💬 Sample Chat Transcript

```
🤖 AI Interviewer: Good morning, and welcome to the interview for the FedEx Ground ISP Delivery Driver position at Tsavo West Inc. I'm your AI interviewer today, and I'm excited to learn more about your qualifications. This role involves delivering packages safely and efficiently in the Tampa area, working 10-hour shifts, four days a week, including one weekend day, with a competitive pay rate of 18 to 20 per hour. As we move forward, I'll need to confirm some essential eligibility criteria. To begin, can you please confirm: Are you 21 years of age or older?

👤 Candidate: Yes

🤖 AI Interviewer: That's great, thank you for confirming you meet the age requirement. I've noted that you've passed this eligibility criterion. Moving forward, can you please confirm that you currently hold a valid driver's license?

👤 Candidate: Yes, I have a valid Florida license.

🤖 AI Interviewer: Excellent, thank you for confirming your valid Florida driver's license. I've noted that you've met this requirement. Next, to ensure safety on the road, can you tell me: Do you have a clean driving record with no major violations or accidents?

👤 Candidate: Yes, completely clean.

🤖 AI Interviewer: I've noted that you have a clean driving record, which is great. Moving forward, can you please confirm: Are you willing and able to pass a pre-employment background check and drug screening?

👤 Candidate: Yes, absolutely.

🤖 AI Interviewer: I've noted that you're willing to pass the background check and drug screening, thank you for confirming. Now, regarding the physical demands of the job, can you confirm: Are you physically able to lift packages up to 150 lbs, including bending, lifting, and maneuvering in and out of a delivery truck?

👤 Candidate: Yes, I can lift up to 150 lbs.

🤖 AI Interviewer: You've met the physical ability requirement, thank you for confirming. Now, regarding your availability, can you confirm: Are you available to work a schedule of 10-hour shifts, 4 days a week, including at least 1 weekend day?

👤 Candidate: Yes, that works for me.

🤖 AI Interviewer: You've successfully met all the mandatory requirements for the FedEx Ground ISP Delivery Driver role, great job! Now, I'd like to learn more about your experience and skills. Can you tell me: Do you have any prior experience with delivery or courier services? If so, please share with me about your experience.

👤 Candidate: Yes, I worked as a DoorDash driver for about a year and before that I did warehouse shipping for Amazon.

🤖 AI Interviewer: That's great experience to have. As a DoorDash driver, I'm sure you had to interact with customers frequently. Can you tell me: How did you handle any difficult customer interactions or issues that arose during your deliveries, such as late arrivals or incorrect orders?

👤 Candidate: I handled them perfectly

🤖 AI Interviewer: You handled difficult customer interactions effectively, that's excellent. Now, let's discuss your Time Management & Organizational Skills. How would you describe your time management and organizational skills? Can you give me an example of how you've handled a busy workday?

👤 Candidate: I'm very organized. At Amazon I had to process 200+ packages per shift, so I developed a system for prioritizing orders.

🤖 AI Interviewer: That's impressive, processing over 200 packages per shift requires strong organizational skills. Can you walk me through your system for prioritizing orders, and how you think it could be applied to managing a delivery route with multiple stops and deadlines as a FedEx Ground ISP Delivery Driver?

👤 Candidate: I sort by urgency first, then by geographic proximity to minimize travel time.

🤖 AI Interviewer: Your approach to prioritizing orders is efficient and logical. Now, let's discuss your ability to work independently. This role requires working independently for most of the day. How comfortable are you with that? Can you share an experience where you worked independently?

👤 Candidate: Very comfortable. Both DoorDash and warehouse work were largely independent. I'm self-motivated and enjoy working at my own pace.

🤖 AI Interviewer: That's great to hear that you're self-motivated and enjoy working independently. How do you handle unexpected problems when there's no supervisor nearby, such as a vehicle issue or a difficult delivery situation, and you need to think on your feet to resolve it?

👤 Candidate: call help

🤖 AI Interviewer: Calling for help when needed is a great approach. I appreciate your straightforward answer. We've completed the interview, and I'll now provide you with a final hiring assessment for the FedEx Ground ISP Delivery Driver role.

Dear candidate, I want to start by thanking you for taking the time to speak with me today about the FedEx Ground ISP Delivery Driver position at Tsavo West Inc. After careful review of your qualifications and our conversation, I am pleased to inform you that you are Qualified for this role.

Your Match Score is 87/100, indicating a strong fit for the position. You successfully met all of our mandatory qualifications, demonstrating that you have the foundational requirements necessary for the job. In terms of preferred qualifications, you showed exceptional prior delivery experience and time management skills, but had a slightly more moderate showing in your ability to work independently.

Given your overall performance and the balance of your strengths and areas for growth, I believe you have the potential to excel as a FedEx Ground ISP Delivery Driver. Your experience in handling a high volume of packages and your self-motivated approach to work are particularly noteworthy.

Next steps, a recruiter will reach out to schedule an in-person meeting to further discuss the details of the position, including compensation, benefits, and what you can expect on a day-to-day basis.

Before we conclude, do you have any questions about the role or the next steps in our process that I can address for you?

👤 Candidate: tell me the pay

🤖 AI Interviewer: The pay for this role is 18/hour to 20/hour, based on experience. It's a combination of fixed and per stop pay, with a stop bonus and safety bonus also available. Do you have any other questions about the compensation or the role in general?

👤 Candidate: tell me hours

🤖 AI Interviewer: The schedule for this role is 10 hours a day, with a start time of 07:30 AM. You'll work a 4-day schedule, including 1 weekend day, and there may be opportunities for 1-2 days of overtime. Do you have any other questions about the job or the schedule?

👤 Candidate: description

🤖 AI Interviewer: As a FedEx Ground ISP Delivery Driver, you will be responsible for delivering packages to customers in a safe and timely manner. Your duties will include operating a company-provided vehicle, loading and unloading packages, planning routes, and providing excellent customer service. You will work independently, but collaborate with the dispatch team to optimize delivery schedules and communicate any issues promptly.

Do you have any other questions about the job description or responsibilities?

👤 Candidate: what is the diameter of the earth

🤖 AI Interviewer: The diameter of the Earth is not related to the job description or your qualification status. I don't have information on the Earth's diameter as it's not relevant to the position.

Do you have any other questions about the job, such as pay, schedule, or responsibilities?

👤 Candidate: end

🤖 AI Interviewer: It seems like you're indicating the end of our conversation. However, I'd like to confirm that you're qualified for the position with a score of 87/100.

Do you have any other questions about the job or would you like to proceed with the next steps?

👤 Candidate: no

🤖 AI Interviewer: Thank you for your time. The interview process is now complete. Have a great day! 👋

Match Score: 87/100
📋 Recruiter Summary (Internal)

==================================================
  CANDIDATE ASSESSMENT SUMMARY
==================================================

MANDATORY QUALIFICATIONS:
  ✅ Age Requirement (21+): Pass
     → Yes
  ✅ Valid Driver's License: Pass
     → Yes, I have a valid Florida license.
  ✅ Clean Driving Record: Pass
     → Yes, completely clean.
  ✅ Background & Drug Screening: Pass
     → Yes, absolutely.
  ✅ Physical Ability (Lift 150 lbs): Pass
     → Yes, I can lift up to 150 lbs.
  ✅ Weekend & Long-Shift Availability: Pass
     → Yes, that works for me.
  Mandatory Score: 60/60

PREFERRED QUALIFICATIONS:
  ✅ Prior Delivery / Courier Experience: Pass (9.3 pts)
     → Yes, I worked as a DoorDash driver for about a year and
   before that I did warehouse shipping for Amazon. | I handled them perfectly
  ✅ Time Management & Organizational Skills: Pass (9.3 pts)
     → I'm very organized. At Amazon I had to process 200+
   packages per shift, so I developed a system for prioritizing orders. | I sort by urgency first, then by geographic proximity to
   minimize travel time.
  🟡 Ability to Work Independently: Partial (8.0 pts)
     → Very comfortable. Both DoorDash and warehouse work were
   largely independent. I'm self-motivated and enjoy working at my own pace. | call help
  Preferred Score: 26.7/40

TOTAL SCORE: 87/100
DECISION: Qualified
```

---

## 🛠 Design Decisions

1. **Groq (Llama 3.3)** – chosen for speed and cost-effectiveness; questions feel responsive
2. **Keyword + LLM evaluation** – mandatory answers checked with fast keywords first, LLM as fallback for ambiguous responses
3. **Session state in Streamlit** – full conversation history preserved across reruns using `st.session_state`
4. **Early disqualification** – any mandatory fail immediately triggers the final decision, saving time for both candidate and recruiter
5. **One follow-up per preferred question** – balances interview depth with interview length
