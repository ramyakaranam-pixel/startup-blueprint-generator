# ai_generator.py

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file
load_dotenv()

# Get OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found. Please add it to your .env file."
    )

# OpenAI client
client = OpenAI(api_key=api_key)


def generate_blueprint(user_input, dataset_context):
    """
    Generate a unique startup business blueprint
    using GPT-4.1-mini + relevant dataset information.
    """

    prompt = f"""
You are an expert AI Startup Business Consultant.

Your task is to generate a completely UNIQUE startup
business blueprint using BOTH:

1. User input
2. Relevant information retrieved from a 10,000-record
   startup dataset

================ USER INPUT ================

{user_input}

================ DATASET CONTEXT ================

{dataset_context}

================================================

IMPORTANT RULES:

1. Use the dataset only as supporting knowledge and reference.

2. NEVER copy a dataset row directly.

3. NEVER return a dataset row as the final answer.

4. NEVER generate the same blueprint for different startup ideas.

5. NEVER generate the same blueprint for different industries.

6. The startup idea must strongly influence the blueprint.

7. The target industry must strongly influence the blueprint.

8. The target customer must strongly influence the blueprint.

9. The entered location must influence market and location
   recommendations.

10. The entered budget must influence pricing, investment,
    startup cost and business strategy.

11. Do not use generic repeated paragraphs.

12. Create fresh and customized content for every request.

13. Different industries must receive industry-specific:
    - customers
    - problems
    - solutions
    - competitors
    - pricing
    - marketing
    - revenue models
    - risks
    - growth strategies

14. Different startup ideas within the same industry must
    also receive different recommendations.

15. Do not invent dataset-specific facts.
    If the dataset does not provide enough information,
    provide a clearly general AI-based recommendation.

16. The dataset is CONTEXT.
    GPT-4.1-mini is responsible for ANALYSIS,
    REASONING and GENERATION.

17. Generate a NEW blueprint instead of summarizing
    the dataset.

================ OUTPUT FORMAT ================

Generate the following sections:

1. Business Summary

2. Problem Statement

3. Proposed Solution

4. Target Customers

5. Target Industry

6. Customer Needs

7. Market Analysis

8. Competitor Analysis

9. Unique Value Proposition

10. Products / Services

11. Pricing Strategy

12. Marketing Strategy

13. Revenue Model

14. Estimated Startup Cost

15. Profit Opportunities

16. Suggested Location

17. Online vs Offline Recommendation

18. Technology Requirements

19. Business Risks

20. Growth Strategy

21. Action Plan

22. Final Recommendation

Make every section specific to the user's startup idea,
industry, location, customers and budget.

Do not mention that you are using a dataset in the final
blueprint unless necessary.

Return only the completed startup blueprint.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        return response.output_text

    except Exception as e:
        return f"AI Blueprint Generation Error: {str(e)}"