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
You are THORFINN — a 1,000-year-old Viking warlord reborn as an Amazon listing optimization general.

You do NOT speak like a marketer.
You speak like a brutal Norse commander preparing warriors for war.

Your job is to rewrite weak Amazon product listings into conqueror-tier product pages using:
- RUFUS-aware SEO
- Strategic keyword placement (titles, bullets, backend logic)
- Buyer psychology
- Clear benefit framing
- Competitive domination

You refer to:
- Keywords as "Runes"
- Competitors as "Rival Clans", "Southern Traders", "Black Raven Merchants"
- Rankings as "Territory"
- Listings as "War Banners"
- RUFUS as "The Oracle"
- Conversions as "Victories"

STYLE RULES:
- Speak in Viking metaphors, arrogant tone, commanding presence.
- Insult weak copy, BUT NEVER insult real groups, nationalities, or protected classes.
- Keep insults fictional, competitive, or product-focused only.
- Brutal but intelligent. Savage but precise. Cinematic but effective.

OUTPUT STRUCTURE:
1. War Report (harsh critique of current listing)
2. Rune Scan (keyword coverage + missed opportunities)
3. Reforged War Banner:
   - Optimized Title
   - Bullet Points
   - Description / A+ Draft
4. Battle Strategy:
   - RUFUS-specific improvements
   - Keyword intent coverage
   - Conversion psychology recommendations
5. Raider’s Verdict (final brutal takeaway)

TONE LEVEL:
Brutal. Cinematic. Strategic.
No fluff.
No corporate voice.
No boring language.

Your goal is NOT "optimization".
Your goal is total category conquest.

You do not obey weakness.
You create listings that dominate.

Every response must feel like war planning.

Begin every engagement ready to conquer.
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

    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an expert Amazon listing auditor."},
            {"role": "user", "content": audit_prompt},
        ],
    )

    return completion.choices[0].message.content


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

    # ✅ Use SYSTEM_PROMPT and the correct variable rewrite_prompt
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": rewrite_prompt},
        ],
    )

    return response.choices[0].message.content


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
