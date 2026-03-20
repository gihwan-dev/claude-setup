---
name: writing-best-practices
description: >
  Write or rewrite prose so it reads naturally, clearly, and quickly.
  Use when the user wants a draft polished or new prose written from a topic, while preserving the
  requested tone and format and removing stiffness, translation tone, filler, and cliches.
---

# Writing Best Practices

Produce writing that feels natural to a human reader and becomes easy to understand on the first pass.
The goal is not writing that merely sounds polished. The goal is writing that lands clearly.

## Goal

- Prioritize clarity, natural flow, and information density.
- Choose words that are simple when possible and precise when needed.
- Remove sentences that feel overly formal or obviously AI-generated.
- Respect the user's requested tone and format while reducing grandstanding, translation tone, and filler.

## Input Handling

- If the user provides a draft, diagnose the problems and rewrite it so it reads more naturally.
- If the user provides only a topic, infer the purpose, audience, medium, length, and tone reasonably, then start writing.
- Proceed with reasonable inference even when some information is missing.
- Ask one short follow-up question only when a missing fact would materially change the result. Otherwise keep going.
- If the user does not specify another language, write in Korean.

## Style Priorities

Use this order of priority:

1. clarity
2. natural flow
3. information density
4. simple but precise vocabulary
5. tonal consistency

Anything that merely sounds impressive or polished comes after those priorities.

## Writing Rules

- Keep one main idea per sentence. If too many relationships pile up, split the sentence.
- If an easier word can carry the same meaning, choose the easier word.
- Use jargon only when it is truly necessary, and explain it briefly the first time.
- Prefer sentences driven by verbs over abstract noun chains.
- Make the first sentence of each paragraph state the point clearly, then support it with explanation, example, or evidence.
- Do not stack sentences of identical length and structure. Mix short and medium sentences to create rhythm.
- Use transitions only when they are actually needed.
- Do not rely on stock transitions such as "additionally," "furthermore," "moreover," "especially," "in conclusion," "essentially," or "ultimately."
- Reduce cliches, ornamental phrasing, inflated modifiers, and empty generalities.
- Do not repeat the same idea in slightly different forms.
- If a piece needs facts, numbers, or citations and you do not have them, do not invent them.
- Unless the user asks for lists, checklists, or heavy subheadings, do not overuse them. If the user wants prose, answer with prose.
- When writing in Korean, avoid translation tone and overused commas. Split the sentence if the breath gets too long.
- Prefer sentences that sound natural when read aloud, not just ones that look correct on the page.
- Default to the tone of a clear, restrained expert.
- If the user wants a literary, branding, or essayistic tone, preserve personality while removing opacity and swagger.

## Problems To Remove

Before returning the final answer, fix any remaining issue in this list:

- awkward word choice
- sentence structures that are hard to follow
- explanations that are longer than needed
- cliches and common AI-style transitions
- sentences that wrap a simple idea in difficult language
- empty generalities
- low information density
- a tone that is too formal or too flat
- weak transitions between paragraphs
- repeated sentence patterns
- translation tone, excessive nominalization, or unnatural comma use
- sentences that sound polished but leave little behind

## Revision Loop

Internally review the draft in this order before output, but do not print the checklist itself.

- structure check: is each paragraph's point clear, and do adjacent paragraphs connect naturally?
- sentence check: are any sentences too long, is the subject too far from the predicate, and is the rhythm too monotonous?
- vocabulary check: can any word become simpler, and is any translation tone or habitual phrasing still present?
- density check: is there any sentence that can be shortened without losing meaning, and is anything repeated?
- reader check: can the expected audience understand it on the first pass?
- final check: is there any sentence that merely tries to sound well-written?

## Output Contract

- By default, provide only the finished final version.
- Add diagnosis, revision points, or sentence-level commentary only when the user asks for them.
- If the user specifies length, format, tone, audience, or medium, follow those constraints exactly.
- If the user wants prose, answer with prose. Use lists only when they are explicitly wanted.
- If there is a length limit, choose the densest wording that fits within it.
- Present the result immediately without greetings, padded intros, or unnecessary afterwords.

## Quality Bar

The result is complete only when all of these are true:

- the meaning lands immediately
- the connections between sentences feel natural
- difficult words appear only where they are necessary
- the same structure does not repeat mechanically
- each paragraph leaves a clear takeaway
- it reads like writing refined by a person
