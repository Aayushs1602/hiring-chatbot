"""
agent.py – LLM-based conversation orchestrator for the AI Interviewer.
Uses Groq Llama/Mixtral for blazing fast dynamic question generation and assessment.
Includes enhanced logging and error handling.
"""

import time
import os
import logging
import streamlit as st
from groq import Groq

# Configure standard logging to console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("interview_agent.log")
    ]
)
logger = logging.getLogger("InterviewAgent")

from config import (
    MANDATORY_QUALIFICATIONS,
    PREFERRED_QUALIFICATIONS,
    SYSTEM_PROMPT,
    GREETING_PROMPT,
    MANDATORY_PHASE_PROMPT,
    PREFERRED_PHASE_PROMPT,
    FOLLOWUP_PROMPT,
    DECISION_PROMPT,
    JOB_QA_PROMPT,
    JOB_DESCRIPTION_FULL,
    GUARDRAIL_REDIRECT,
    PHASE_GREETING,
    PHASE_MANDATORY,
    PHASE_PREFERRED,
    PHASE_FOLLOWUP,
    PHASE_DECISION,
    PHASE_JOB_QA,
    PHASE_ENDED,
)
from scoring import QualificationTracker, Status
from guardrails import is_on_topic, is_prompt_injection

# Available models for Groq
AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3-70b-8192",
    "llama-3-8b-8192",
    "mixtral-8x7b-32768",
]


class InterviewAgent:
    """Orchestrates the interview conversation using Groq."""

    def __init__(self, api_key: str, model_id: str = "llama-3.3-70b-versatile"):
        logger.info(f"Initializing InterviewAgent with Groq model: {model_id}")
        
        # Validate API key presence
        if not api_key:
            logger.error("Groq API Key is missing!")
            raise ValueError("Groq API Key is missing. Please check your .env file or sidebar input.")
        
        # Initialize Groq Client
        self.client = Groq(api_key=api_key)
        self.model_id = model_id
        
        self.tracker = QualificationTracker()
        self.phase = PHASE_GREETING
        self.mandatory_index = 0
        self.preferred_index = 0
        self.followup_count = 0
        self.max_followups = 1
        self.conversation_history = []
        self.current_preferred_answers = []

    # ── Public API ──────────────────────────────────────────────────────

    def get_greeting(self) -> str:
        """Generate the initial greeting + first mandatory question."""
        logger.info("Generating greeting...")
        response = self._call_llm(GREETING_PROMPT)
        self.conversation_history.append({"role": "assistant", "content": response})
        self.phase = PHASE_MANDATORY
        return response

    def process_message(self, user_input: str) -> str:
        logger.info(f"Processing candidate message: {user_input[:50]}...")
        self.conversation_history.append({"role": "user", "content": user_input})

        if is_prompt_injection(user_input):
            logger.warning("Prompt injection detected!")
            redirect = GUARDRAIL_REDIRECT + self._get_current_question_reminder()
            self.conversation_history.append({"role": "assistant", "content": redirect})
            return redirect

        if not is_on_topic(user_input):
            logger.info("Message flagged as off-topic.")
            redirect = GUARDRAIL_REDIRECT + self._get_current_question_reminder()
            self.conversation_history.append({"role": "assistant", "content": redirect})
            return redirect

        # Route to the correct phase handler
        if self.phase == PHASE_MANDATORY:
            response = self._handle_mandatory(user_input)
        elif self.phase == PHASE_PREFERRED:
            response = self._handle_preferred(user_input)
        elif self.phase == PHASE_FOLLOWUP:
            response = self._handle_followup(user_input)
        elif self.phase == PHASE_DECISION:
            response = self._handle_decision()
        elif self.phase == PHASE_JOB_QA:
            response = self._handle_job_qa(user_input)
        elif self.phase == PHASE_ENDED:
            response = "The interview has concluded. Thank you for your time! 🙏"
        else:
            response = self._handle_mandatory(user_input)

        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def force_decision(self) -> str:
        logger.info("Force decision triggered.")
        self.phase = PHASE_DECISION
        response = self._handle_decision()
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def get_progress(self) -> dict:
        total_mandatory = len(MANDATORY_QUALIFICATIONS)
        total_preferred = len(PREFERRED_QUALIFICATIONS)
        total_questions = total_mandatory + total_preferred

        answered_mandatory = min(self.mandatory_index, total_mandatory)
        answered_preferred = min(self.preferred_index, total_preferred)

        if self.phase in (PHASE_DECISION, PHASE_JOB_QA, PHASE_ENDED):
            answered = total_questions
        else:
            answered = answered_mandatory + answered_preferred

        return {
            "phase": self.phase,
            "answered": answered,
            "total": total_questions,
            "mandatory_done": answered_mandatory,
            "mandatory_total": total_mandatory,
            "preferred_done": answered_preferred,
            "preferred_total": total_preferred,
            "is_disqualified": self.tracker.is_disqualified(),
            "score": self.tracker.get_total_score(),
        }

    # ── Phase Handlers ──────────────────────────────────────────────────

    def _handle_mandatory(self, user_input: str) -> str:
        if self.mandatory_index >= len(MANDATORY_QUALIFICATIONS):
            logger.info("All mandatory qualifications complete.")
            self.phase = PHASE_PREFERRED
            return self._handle_preferred_transition()

        current_qual = MANDATORY_QUALIFICATIONS[self.mandatory_index]
        logger.info(f"Evaluating mandatory qual: {current_qual['id']}")

        passed = self._evaluate_mandatory_answer(user_input, current_qual)
        self.tracker.update_mandatory(
            current_qual["id"], passed, evidence=user_input.strip()[:200]
        )
        self.mandatory_index += 1

        if not passed:
            logger.info(f"Candidate FAILED mandatory requirement: {current_qual['id']}")
            self.phase = PHASE_DECISION
            eval_text = (
                f"The candidate FAILED this mandatory requirement ({current_qual['label']}). "
                "They are disqualified. Acknowledge their answer politely, briefly explain "
                "this is a mandatory requirement, and let them know you'll now provide the "
                "final assessment."
            )
            prompt = MANDATORY_PHASE_PROMPT.format(
                current_qual=current_qual["label"],
                answer=user_input,
                evaluation_instruction=eval_text,
                next_instruction="Transition to the final decision.",
            )
            disqualify_msg = self._call_llm(prompt)
            decision_msg = self._generate_decision_output()
            self.phase = PHASE_ENDED
            return disqualify_msg + "\n\n---\n\n" + decision_msg

        logger.info(f"Candidate PASSED mandatory requirement: {current_qual['id']}")
        if self.mandatory_index >= len(MANDATORY_QUALIFICATIONS):
            eval_text = "The candidate PASSED this requirement. Acknowledge positively."
            next_text = (
                "All mandatory questions are complete! Transition smoothly by saying "
                "something like 'Great, you meet all the essential requirements! Now I'd "
                "like to learn more about your experience and skills.' Then ask about: "
                f"{PREFERRED_QUALIFICATIONS[0]['label']} — {PREFERRED_QUALIFICATIONS[0]['question']}"
            )
            self.phase = PHASE_PREFERRED
        else:
            next_qual = MANDATORY_QUALIFICATIONS[self.mandatory_index]
            eval_text = "The candidate PASSED this requirement. Acknowledge briefly and positively."
            next_text = f"Now ask the next mandatory question: {next_qual['question']}"

        prompt = MANDATORY_PHASE_PROMPT.format(
            current_qual=current_qual["label"],
            answer=user_input,
            evaluation_instruction=eval_text,
            next_instruction=next_text,
        )
        return self._call_llm(prompt)

    def _handle_preferred_transition(self) -> str:
        if self.preferred_index >= len(PREFERRED_QUALIFICATIONS):
            self.phase = PHASE_DECISION
            return self._handle_decision()

        qual = PREFERRED_QUALIFICATIONS[self.preferred_index]
        prompt = PREFERRED_PHASE_PROMPT.format(
            qual_label=qual["label"],
            qual_question=qual["question"],
        )
        return self._call_llm(prompt)

    def _handle_preferred(self, user_input: str) -> str:
        if self.preferred_index >= len(PREFERRED_QUALIFICATIONS):
            self.phase = PHASE_DECISION
            return self._handle_decision()

        current_qual = PREFERRED_QUALIFICATIONS[self.preferred_index]
        self.current_preferred_answers.append(user_input)

        if self.followup_count < self.max_followups:
            self.followup_count += 1
            self.phase = PHASE_FOLLOWUP
            suggestions = "\n".join(
                f"- {s}" for s in current_qual.get("follow_up_prompts", [])
            )
            prompt = FOLLOWUP_PROMPT.format(
                qual_label=current_qual["label"],
                answer=user_input,
                suggestions=suggestions,
            )
            return self._call_llm(prompt)
        else:
            return self._score_preferred_and_advance(current_qual)

    def _handle_followup(self, user_input: str) -> str:
        current_qual = PREFERRED_QUALIFICATIONS[self.preferred_index]
        self.current_preferred_answers.append(user_input)

        if self.followup_count < self.max_followups:
            self.followup_count += 1
            suggestions = "\n".join(
                f"- {s}" for s in current_qual.get("follow_up_prompts", [])
            )
            prompt = FOLLOWUP_PROMPT.format(
                qual_label=current_qual["label"],
                answer=user_input,
                suggestions=suggestions,
            )
            return self._call_llm(prompt)
        else:
            return self._score_preferred_and_advance(current_qual)

    def _score_preferred_and_advance(self, current_qual: dict) -> str:
        combined_answer = " | ".join(self.current_preferred_answers)
        detail_score = self._evaluate_preferred_answer(combined_answer, current_qual)

        self.tracker.update_preferred(
            current_qual["id"], detail_score, evidence=combined_answer[:300]
        )

        self.preferred_index += 1
        self.followup_count = 0
        self.current_preferred_answers = []
        self.phase = PHASE_PREFERRED

        if self.preferred_index >= len(PREFERRED_QUALIFICATIONS):
            self.phase = PHASE_DECISION
            decision_output = self._generate_decision_output()
            transition = self._call_llm(
                "The candidate just answered the last preferred qualification question. "
                "Acknowledge their answer briefly and positively, then say you've completed "
                "the interview and will now provide the assessment."
            )
            self.phase = PHASE_JOB_QA
            return transition + "\n\n---\n\n" + decision_output
        else:
            next_qual = PREFERRED_QUALIFICATIONS[self.preferred_index]
            prompt = (
                f"Acknowledge the candidate's previous answer briefly and positively, "
                f"then transition to ask about: {next_qual['label']}.\n"
                f"Suggested question: {next_qual['question']}"
            )
            return self._call_llm(prompt)

    def _handle_decision(self) -> str:
        output = self._generate_decision_output()
        self.phase = PHASE_JOB_QA
        return output

    def _handle_job_qa(self, user_input: str) -> str:
        # check for exit intent
        exit_keywords = ["no", "none", "bye", "goodbye", "exit", "done", "thank you", "thanks"]
        if any(kw in user_input.lower() for kw in exit_keywords) and len(user_input.split()) < 5:
             self.phase = PHASE_ENDED
             return "Thank you for your time. The interview process is now complete. Have a great day! 👋"

        # Prepare assessment context
        score = self.tracker.get_total_score()
        decision = self.tracker.get_decision()
        assessment_summary = f"Score: {score}/100, Decision: {decision}"

        prompt = JOB_QA_PROMPT.format(
            job_description=JOB_DESCRIPTION_FULL,
            user_question=user_input,
            assessment_info=assessment_summary
        )
        return self._call_llm(prompt)

    # ── LLM Interaction (Groq implementation) ─────────────────────────

    def _call_llm(self, phase_prompt: str, max_retries: int = 3) -> str:
        """Call Groq API with detailed logging."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        
        recent = self.conversation_history[-8:]
        for msg in recent:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": f"[SYSTEM INSTRUCTION]: {phase_prompt}"})

        logger.info(f"Calling Groq API [Model: {self.model_id}, Phase: {self.phase}]")

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                )
                duration = time.time() - start_time
                logger.info(f"Groq Success (Turnaround: {duration:.2f}s)")
                return response.choices[0].message.content.strip()

            except Exception as e:
                logger.error(f"Groq API Error (Attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    logger.critical("Groq Rate Limit exceeded.")
                    st.toast("⚠️ Groq Rate Limit Exceeded.", icon="🚫")
                
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 2
                    time.sleep(wait)
                    continue
                
                return f"I encountered a technical issue with Groq. (Error: {str(e)[:100]})"
        
        return "Critical API error on Groq."

    # ── Answer Evaluation ───────────────────────────────────────────────

    def _evaluate_mandatory_answer(self, answer: str, qual: dict) -> bool:
        answer_lower = answer.lower().strip()

        for kw in qual.get("fail_keywords", []):
            if kw in answer_lower:
                return False
        for kw in qual.get("pass_keywords", []):
            if kw in answer_lower:
                return True

        eval_prompt = (
            f"The candidate was asked: '{qual['question']}'\n"
            f"They answered: '{answer}'\n\n"
            f"Does this answer indicate they MEET the requirement for: {qual['label']}?\n"
            f"Respond with ONLY 'PASS' or 'FAIL'."
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0,
                max_tokens=10,
            )
            result = response.choices[0].message.content.strip().upper()
            return "PASS" in result
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return True

    def _evaluate_preferred_answer(self, answer: str, qual: dict) -> float:
        eval_prompt = (
            f"Rate the following candidate answer for the qualification: {qual['label']}\n\n"
            f"Question context: {qual['question']}\n"
            f"Candidate's answer(s): {answer}\n\n"
            f"Rate from 0.0 to 1.0 based on:\n"
            f"- 0.0-0.2: No relevant experience or very vague\n"
            f"- 0.3-0.5: Some relevant experience but lacking detail\n"
            f"- 0.6-0.8: Good relevant experience with decent detail\n"
            f"- 0.9-1.0: Excellent, specific, detailed experience\n\n"
            f"Respond with ONLY a decimal number like 0.7"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": eval_prompt}],
                temperature=0,
                max_tokens=10,
            )
            score_str = response.choices[0].message.content.strip()
            score = float(score_str)
            return min(max(score, 0.0), 1.0)
        except Exception as e:
            logger.error(f"Scoring failed: {str(e)}")
            return 0.5

    # ── Helpers ─────────────────────────────────────────────────────────

    def _get_current_question_reminder(self) -> str:
        if self.phase == PHASE_MANDATORY and self.mandatory_index < len(MANDATORY_QUALIFICATIONS):
            q = MANDATORY_QUALIFICATIONS[self.mandatory_index]
            return f"\n\nLet me repeat the question: **{q['question']}**"
        elif self.phase in (PHASE_PREFERRED, PHASE_FOLLOWUP):
            return "\n\nCould you please answer the previous question?"
        return ""

    def _generate_decision_output(self) -> str:
        breakdown = self.tracker.generate_breakdown()
        score = self.tracker.get_total_score()
        decision = self.tracker.get_decision()

        breakdown_str = "**Mandatory Qualifications:**\n"
        for qid, q in breakdown["mandatory"].items():
            icon = "✅" if q["status"] == "Pass" else "❌"
            breakdown_str += f"- {icon} {q['label']}: {q['status']}\n"
        breakdown_str += f"\nMandatory Score: {breakdown['mandatory_score']}/60\n\n"

        breakdown_str += "**Preferred Qualifications:**\n"
        for qid, q in breakdown["preferred"].items():
            if q["status"] == "Pass":
                icon = "✅"
            elif q["status"] == "Partial":
                icon = "🟡"
            elif q["status"] == "Fail":
                icon = "❌"
            else:
                icon = "⬜"
            breakdown_str += f"- {icon} {q['label']}: {q['status']} ({q['score']} pts)\n"
        breakdown_str += f"\nPreferred Score: {breakdown['preferred_score']}/40\n"

        prompt = DECISION_PROMPT.format(
            breakdown=breakdown_str, score=score, decision=decision
        )
        return self._call_llm(prompt)
