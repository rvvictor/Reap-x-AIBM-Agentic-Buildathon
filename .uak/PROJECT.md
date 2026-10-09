# PROJECT · Reap x AIBM Agentic Buildathon (sprint mode)

> Filled in by `/uak-setup`. uak reads the flat fields of the last block from the remote `main`.

## Event
| Field | Value |
|---|---|
| Event / challenge | Reap x AI Builders Mexico Agentic Buildathon · https://aibuilders.mx/reap |
| Start | 2026-10-09 17:00 America/Mexico_City |
| Official deadline | 2026-10-09 21:00 America/Mexico_City · platforms: Gavel form https://gavel-65labs.vercel.app/submit/74oz5tv1cfzllzh392gy1rqzvx4m1vop |
| Freeze | 20:00 (deadline − 1 h; compressed, the 4 h event makes the standard −6 h fall before the start) → `Freeze-Epoch` |
| Clean rehearsal / plan B | 19:30 (deadline − 1 h 30) |
| Internal submission | 20:30 (deadline − 30 min) |
| Humans | Fernando Vargas: team captain, receives the Reap API key via Telegram; Victor Ruiz; Sebastian Jara; Javier Reyna; Dylan Martinez · submission owner: TBD (captain by default) |
| Agents | TBD per human (max 2) |
| Machines | laptops · ports already taken: none known |
| Team | Axolutions · contact vargas.fer2442@gmail.com |
| Product name | TBD (idea still under discussion) |

## Official rubric (weights sum to 100)
Judging criteria and weights are NOT published (unverified). Proxy rows come from the track text and the 9-item checklist on the event page.
| ID | Criterion | Weight | Evidence in the demo |
|---|---|---:|---|
| C1 | Track 1: worthwhile problem, real users would pay, paying with agents feels natural | 50 | demo flow with a real use case |
| C2 | Track 2: bridge between onchain and real world, beyond topping up a wallet | 50 | only if the team enters Track 2 |
| Gate | Agentic module central to the product (Reap API, or wallet module + Agentic module) | gate | Reap sandbox API calls shown live |

## Event rules
| Topic | Confirmed rule | Source |
|---|---|---|
| AI use / prior code | AI use allowed (team). Prior code: not specified | team brief |
| Data and licenses | Sandbox only, no real money. Only merchants from /merchants in the Telegram bot | https://aibuilders.mx/reap |
| Forbidden | Travel bookings, restricted categories (gambling, adult), scraping checkout, raw card data to an LLM, generic search-show-buy chatbot | https://aibuilders.mx/reap |
| Required API | Reap Agentic module (docs.reap.global/agentic-payments/overview), or Payward wallet module + Agentic module | https://aibuilders.mx/reap |
| Format and video limits | Not specified by the event; team limit 1-2 min. Gavel form fields unverified (page needs JavaScript) | team brief |
| Support | Telegram channel; Jose (Reap) technical, Adrian escalation | https://aibuilders.mx/reap |

## Plan B
- A video of the whole flow at `docs/demo-planb.mp4` (v1 at 19:00, final at 19:30). Use it if network or the Reap sandbox API fails.

## Executable config
A human sets `yes`. A missing field means `no`.

```text
Mode: sprint
Backlog-Proposed-Epoch: 0
Backlog-Approved: no
Autonomy: yes
Auto-Merge: yes
Review-Mode: claims
Plan-Channel: claims
Freeze-Epoch: 1791597656
Lease-Seconds: 2700
Review-Lease-Seconds: 14400
Events-Per-Session: 100
Checkpoint-Percent: 60
Merge-Lease-Seconds: 1800
Merge-Wait-Seconds: 180
Max-Parallel-Subagents: 4
Opus-Subagents-Per-Session: 2
Pace: auto
Subagent-Hard-Cap: 6
Strong-Hard-Cap: 3
Subagents-Per-Session: 40
Subagents-Per-Machine: 8
Subagent-Burst-Per-Minute: 6
Max-Worktree-Agents: 6
Blackbox: on
Additive-Paths: -
```
