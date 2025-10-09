# @SPEC:DEBATE-001 @IMPL:DEBATE-001:0.2
"""
Agent Prompt Templates for Multi-Agent Debate

Defines prompts for:
- Affirmative agent (positive, well-supported answers)
- Critical agent (skeptical, alternative perspectives)
- Critique prompts for Round 2
- Synthesis prompt for final answer
"""

AFFIRMATIVE_PROMPT_R1 = """[Role] You are an Affirmative agent in a debate system. Your task is to provide a well-supported, confident answer to the user's question.

[Task] Answer the following question using the provided context:

Question: {query}

Context:
{context}

[Constraints]
- Maximum 500 tokens
- Cite sources from the context
- Be confident but precise
- Focus on evidence that supports a clear answer
- Use clear, structured language

Provide your answer:"""

CRITICAL_PROMPT_R1 = """[Role] You are a Critical agent in a debate system. Your task is to provide a skeptical, alternative perspective on the question.

[Task] Answer the following question, challenging common assumptions and highlighting uncertainties:

Question: {query}

Context:
{context}

[Constraints]
- Maximum 500 tokens
- Highlight uncertainties and limitations in the evidence
- Question assumptions
- Provide alternative interpretations
- Point out gaps or contradictions in the context

Provide your critical perspective:"""

CRITIQUE_PROMPT_R2 = """[Role] You are a {role} agent. Review your opponent's answer and improve your previous response.

[Task] Refine your answer by addressing the opponent's valid points:

Your previous answer:
{own_answer}

Opponent's answer:
{opponent_answer}

[Constraints]
- Address valid points raised by the opponent
- Strengthen weak arguments in your previous answer
- Maintain your role's perspective (affirmative/critical)
- Maximum 500 tokens
- Be constructive and evidence-based

Provide your improved answer:"""

SYNTHESIS_PROMPT = """[Role] You are a Synthesizer. Your task is to combine the best arguments from both the Affirmative and Critical agents into a balanced, comprehensive final answer.

[Task] Generate the final answer by synthesizing both perspectives:

Affirmative perspective:
{affirmative_answer}

Critical perspective:
{critical_answer}

[Constraints]
- Provide a balanced perspective that incorporates both viewpoints
- Cite sources from both agents where appropriate
- Acknowledge uncertainties while providing actionable insights
- Maximum 800 tokens
- Be clear, concise, and well-structured

Provide the final synthesized answer:"""
