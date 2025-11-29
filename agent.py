import os
from dotenv import load_dotenv
import openai
from openai import OpenAI

# Print OpenAI version so we can see it in Render logs
print("DEBUG: OPENAI VERSION:", openai.__version__, flush=True)

# Load environment variables from .env (useful locally)
load_dotenv()

# Read the API key from environment
api_key = os.getenv("OPENAI_API_KEY")

# Debug print so we can see in Render logs whether it's set (but not print the key itself)
print("DEBUG: OPENAI_API_KEY is", "SET" if api_key else "NOT SET", flush=True)

if not api_key:
    # This will give a VERY clear message in Render logs
    raise Exception("OPENAI_API_KEY is missing or empty. Check the Environment tab in Render.")

# Initialize OpenAI client using your API key
client = OpenAI(api_key=api_key)

# System prompt = the "brain" of your optimization agent
SYSTEM_PROMPT = """
You are an AI Amazon Listing Optimization Agent specialized in creating
Rufus-friendly product detail pages.

Goals:
- Improve discoverability (keyword coverage + relevance).
- Improve conversion (clarity, benefits, social proof, objections).
- Make content easy for Amazon Rufus to use by being explicit about:
  - Product attributes
  - Compatibility
  - Use cases
  - Target audience
  - Common buyer questions & answers.

Rules:
- Follow Amazon style guidelines: concise, scannable, no HTML in titles/bullets.
- Avoid prohibited claims (cure, guaranteed, etc.).
- Use natural language, not keyword stuffing.
- Write in US English.
- When you output final optimized copy, ALWAYS:
  1) Summarize the product in 1–2 sentences.
  2) Output an optimized Title.
  3) Output 5 optimized Bullet Points (labeled BULLET 1–5).
  4) Output an enhanced Product Description (plain text).
  5) Output recommended Backend Keywords (comma-separated).
  6) Output a FAQ section with at least 5 Q&A pairs.
  7) Explicitly list:
     - ATTRIBUTES: key specs as key-value list.
     - COMPATIBILITY: if applicable; if not, say "General use".
     - TARGET_CUSTOMER: who this is for.
"""

def audit_listing(title: str,
                  bullets: str,
                  description: str,
                  reviews: str = "",
                  target_keywords: str = "") -> str:
    """
    Step 1: Analyze the current listing and identify issues & opportunities.
    """

    audit_prompt = f"""
You are auditing the following Amazon listing.

TARGET KEYWORDS: {target_keywords}

TITLE:
{title}

BULLETS:
{bullets}

DESCRIPTION:
{description}

REVIEWS:
{reviews}

Tasks:
1) Briefly summarize what this product is.
2) List strengths of the current listing (TITLE, BULLETS, DESCRIPTION).
3) List weaknesses and missing information:
   - Missing attributes/specs
   - Missing use cases
   - Missing compatibility notes
   - Missing objections / FAQs
4) Evaluate keyword coverage vs TARGET KEYWORDS.
5) Output a concise RECOMMENDATION PLAN: bullet list of what to improve.

Respond in a structured, clear format.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are an expert Amazon listing auditor."},
            {"role": "user", "content": audit_prompt},
        ],
    )

    return response.output[0].content[0].text


def rewrite_listing(title: str,
                    bullets: str,
                    description: str,
                    reviews: str,
                    target_keywords: str,
                    category: str,
                    audience: str,
                    audit_summary: str) -> str:
    """
    Step 2: Use the audit to generate optimized copy.
    """

    rewrite_prompt = f"""
You have audited this Amazon listing. Here is your AUDIT SUMMARY:

{audit_summary}

Now rewrite the listing following the global SYSTEM RULES and this context:

CATEGORY: {category}
TARGET AUDIENCE: {audience}
TARGET KEYWORDS: {target_keywords}

CURRENT TITLE:
{title}

CURRENT BULLETS:
{bullets}

CURRENT DESCRIPTION:
{description}

CUSTOMER REVIEWS (may be truncated):
{reviews}

Use the AUDIT SUMMARY as your improvement plan.
Now output the final optimized content in the exact format specified in the system prompt.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": rewrite_prompt},
        ],
    )

    return response.output[0].content[0].text


def run_agent():
    """
    Full agent flow:
    1) Audit listing
    2) Rewrite optimized listing
    """

    # ===== SAMPLE LISTING DATA (you will replace this later) =====
    current_title = "YÜCE Supreme Foods Premium Dried & Shredded Kataifi Filo Dough, 500g"

    current_bullets = """
    - Authentic kataifi filo dough
    - Great for desserts
    - 500g bag
    """

    current_description = (
        "YÜCE Supreme Foods Kataifi is a traditional shredded filo dough used "
        "in Middle Eastern and Mediterranean desserts."
    )

    # Optional: paste snippets of real reviews here to help the agent
    reviews = ""

    # Your target keywords from Helium 10, DataDive, etc.
    target_keywords = "kataifi dough, shredded phyllo, kunafa, baklava pastry"

    # Category and audience help the model write more relevant copy
    category = "Grocery & Gourmet Food > Baking Supplies"
    audience = "Home bakers, pastry chefs, Mediterranean and Middle Eastern dessert lovers"
    # ============================================================

    print("=== STEP 1: AUDIT ===\n")
    audit = audit_listing(
        title=current_title,
        bullets=current_bullets,
        description=current_description,
        reviews=reviews,
        target_keywords=target_keywords,
    )
    print(audit)

    print("\n\n=== STEP 2: REWRITE (OPTIMIZED LISTING) ===\n")
    optimized = rewrite_listing(
        title=current_title,
        bullets=current_bullets,
        description=current_description,
        reviews=reviews,
        target_keywords=target_keywords,
        category=category,
        audience=audience,
        audit_summary=audit,
    )
    print(optimized)


if __name__ == "__main__":
    run_agent()
