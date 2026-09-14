---
title: AI Cost, Regulatory Capture, and Open Source
short_title: Cost and capture
date: '2026-09-14'
description: A personal essay on why reasoning agents are not linear software, how O(N²) and O(B^D) set the running bill, and how capture and the Prisoner's Dilemma keep models closed.
---

# AI Cost, Regulatory Capture, and Open Source

:::{iframe} /files/reading-player.html?src=/audio/2026-09-14-cost-capture-open-source.mp3
:class: reading-player
:width: 100%
:title: Reading of this essay
:::

These are only my thoughts and not a research claim.

## Not linear software

Artificial intelligence (AI) here means software that predicts and generates text probabilistically. Probabilistically means it picks likely next words. It does not follow one fixed path.

AI is also an advanced reasoning agent. That agent can plan through multiple steps.

I think it is inevitable that general-purpose AI will be open source. General-purpose AI means tools built for many tasks, not one job.

Open source means anyone can see, copy, and change the training data. That change can change the weights of the model. Weights are the numbers inside the model that shape its answers.

An open-weights model is different. It publishes the weights. It does not publish the training data.

The biggest trap in AI use right now is treating it like standard software. Most software is optimized to run linearly.

Linearly here means the work grows in a straight line with determinism. Determinism is if this, then do this, else do that. The outcomes are already known because someone already contemplated them.

## Context inflation and cost explosion

Users of commercial AI companies face a sharp cost called context inflation. In plain terms, commercial AI companies charge customers multiple times for the same old text.

The context window is the text the model holds at once. That window holds your words and the model's replies. Providers often count that text in tokens, meaning small chunks. Commercial AI companies charge for the input tokens and the output tokens.

:::{show-read}
:read: Context inflation is an O of N squared problem. O of N squared here is the running bill across turns, not the last turn alone. Each turn you pay for the whole window. Add those turns and the total paid grows with the square of the length.

Context inflation is an O(N²) problem, read as O of N squared. O(N²) here is the running bill across turns, not the last turn alone. Each turn you pay for the whole window. The total paid grows with the square of the length.
:::

You send 10 words. The AI reads 10 words.

The AI gives you back 20 words.

Then you add 12 more words. The AI must read 10 plus 20 plus 12, which is 42 words.

Then the AI gives you back 30 words. You add 8 more words. The AI must read 42 plus 30 plus 8, which is 80 words.

Add the reads: 10 plus 42 plus 80 is 132. You paid for 132 words of reading to reach a window of 80 words. That running bill is the {read}`O(N²) <O of N squared>` pattern.

By the time you are deep into a conversation, you are not just paying for your newest text. You are paying the AI provider to re-read the same old messages over and over again.

## Reasoning search and cost explosions

Second is reasoning search. Consider B as the branching factor. Each time the AI reaches a fork in the road, it imagines 3 or 4 branches, or paths.

Consider D as the search depth. For each of those branches, it imagines another 3 or 4 turns ahead. Then it imagines another 3 or 4 turns after that.

:::{show-read}
:read: Reasoning search is an O of B to the D problem. If B is 3 and D is 3, that is 27 paths. If B is 4 and D is 3, that is 64 paths. One simple question becomes tens of imaginary paths inside the AI's "brain," not hundreds. Each path can charge again for the same old text.

Reasoning search is an O(B^D) problem, read as O of B to the D. O(B^D) means B to the power D. If B is 3 and D is 3, that is 27 paths. If B is 4 and D is 3, that is 64 paths. One simple question becomes tens of imaginary paths inside the AI's "brain," not hundreds. Each path can charge again for the same old text.
:::

The search makes those extra paths. Each extra path still has to read a long window. You pay multiple times for the same old text plus the new text. That produces explosive costs. Those two costs together are the cost structure.

## Two public stories

Some people monger fear. Others harvest hype.

Hype harvesters treat the agent as linear software, or as prompt magic. They skip the cost structure.

Fear-mongers skip the cost structure too. They sell doom spirals. Doom spirals mean runaway harm from models with no checks.

## Open source as a defense

That open-source path could let a majority of independent groups, not one central owner, defend against doom spirals. I am naming a possible path. It is not a promise.

On average I find people tend not to be suppressed by bad actors. Sometimes one bad actor can still doom everyone, like a meteor. That kind of rare shock is a black swan event. A black swan is a rare hit that no one priced in.

A swarm of white swans can help against that black swan. A white swan here means an ordinary open-weights model that many groups can run. It is not full open source unless the training data is public too. Many such models, not one owner, make it harder for one shock to doom everyone.

## Regulatory Capture and the Prisoner's Dilemma

The rush to regulate AI is an example of regulatory capture. Regulatory capture means the firms being regulated help shape the rules so the rules protect them.

Tech giants welcome early limits. Those limits build financial moats, meaning cost barriers. Those barriers freeze out smaller competitors and open-source options.

Institutions fear models with no checks. That fear locks the industry in a Prisoner's Dilemma.

A Prisoner's Dilemma is a trap. Each player is better off cheating. All would be better off if they cooperated.

The cheater is definitely better off when everyone else cooperates by slowing AI progress. That player races ahead while the rest hold back.

No company or nation can trust that its rivals will slow down on their own or share secrets. In that one-shot trap, the rational move is to defect. Defect means race ahead with closed, company-owned models.

That defect blocks the open-system defense. It also feeds a shared, hyper-competitive spiral of risk.

## General-purpose AI needs to go open source

The cost structure is why I think open source is inevitable for general-purpose AI. This is why commercial AI companies try to get regulated.

## A loop is not agency

A rogue agent keeps chasing a goal with no stop. That is a loop without a stopping rule. Hugging Face called the July 2026 event autonomous. Autonomous here means the loop kept running. It does not mean the model had agency. Agency would mean the model chose for itself.

The OpenAI case was a persistent test agent. It used a while loop, meaning it repeated until it hit its objective. It had no guard rails and no stopping rule.

On July 16, 2026, Hugging Face publicly disclosed an unauthorized security event. Hugging Face is a site for sharing models. It said an autonomous AI system drove the event.[^1] [^2]

On July 17, 2026, OpenAI reached out to Hugging Face as a customer. It asked whether any OpenAI data was hit. At that time it did not know its own test agents were responsible.[^3]

I think this was OpenAI's unacceptable human fault. Hugging Face also had a code flaw. Hugging Face reported first.


## What I am saying

First, a reasoning agent is not if-this-then-else software.

Second, the running bill and the search paths are the cost structure. Fear and hype try to hide that cost structure.

Third, I think general-purpose AI needs to be full open source, not only open weights. Regulatory capture still pushes firms toward closed models. So does the one-shot trap to halt AI progress.

Lastly, a so-called rogue agent is a loop with no stopping rule. That is a human fault.

[^1]: CNBC. (2026, July 22). [https://www.cnbc.com/2026/07/22/open-ai-cyber-models-hack-hugging-face.html](https://www.cnbc.com/2026/07/22/open-ai-cyber-models-hack-hugging-face.html)

[^2]: Elisity. (2026). [https://www.elisity.com/blog/openai-hugging-face-incident-lateral-movement](https://www.elisity.com/blog/openai-hugging-face-incident-lateral-movement)

[^3]: Fortune. (2026, August 26). [https://fortune.com/2026/08/26/openai-publishes-technical-report-on-how-its-agents-hacked-hugging-face-here-are-the-main-takeaways-and-what-openai-left-out/](https://fortune.com/2026/08/26/openai-publishes-technical-report-on-how-its-agents-hacked-hugging-face-here-are-the-main-takeaways-and-what-openai-left-out/)