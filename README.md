# JitoSOL exit-flow documentation review

**Reviewed: 2026-10-16 · Public documentation and limited interface observation · AI-assisted research**

This portfolio sample identifies three opportunities to make JitoSOL's fees and exit process easier to understand. They are documentation recommendations, not confirmed protocol defects. Each recommendation includes a reproducible reading path, suggested wording, and acceptance criteria.

## Scope and evidence

Four official Jito documentation pages were reviewed:

| ID | Official source | Relevant section |
| --- | --- | --- |
| D1 | [Unstaking Overview](https://www.jito.network/docs/jitosol/get-started/unstaking-jitosol-flow/unstaking-overview/) | Method Comparison; How Direct Unstaking Works |
| D2 | [General FAQs](https://www.jito.network/docs/jitosol/faqs/general-faqs/) | Staking and Unstaking; Fees |
| D3 | [Technical FAQs](https://www.jito.network/docs/jitosol/faqs/technical-faqs/) | Differences between direct unstaking and selling on Jupiter; token mechanics |
| D4 | [JitoSOL Glossary](https://www.jito.network/docs/jitosol/resources/jitosol-glossary/) | Epoch; Management Fee; Withdrawal Fee; Slippage |

The browser check of [the staking interface](https://www.jito.network/staking/) encountered a **Welcome to Jito** dialog requiring acceptance of its terms. The terms were not accepted. Selecting **Decline** displayed **Terms of Service required** and prevented use of the interface. No Unstake interaction, wallet connection, amount entry, transaction simulation, signing, or transaction took place.

The initial page rendering behind the dialog exposed Stake-related labels: **Direct Mint**, **Via DFlow**, and **DFlow Slippage**. This is limited evidence about the initial Stake rendering, not evidence about the current Unstake route or its behavior.

The browser screenshot was retained in the local review materials. It records the terms gate on 2026-10-16, not a completed wallet or transaction flow.

## 1. Separate the protocol withdrawal fee from total swap cost

**Observation.** D2 says selling through Jupiter avoids the direct-withdrawal fee, while also warning about spread and slippage. D1's comparison table lists a typical trading cost below 0.3% and a 0.1% direct-unstaking fee. These statements concern different cost components and are not inherently contradictory. The short fee language can nevertheless be misread as an all-in cost comparison.

**Reproduce by reading.**

1. Open D2 and read the answer under **What fees does JitoSOL collect?**
2. Read its earlier warning about spread/slippage for large transactions.
3. Open D1 and compare the **Typical Fee** column with D3's variable-market-spread description.

**Suggested replacement for the short fee explanation.**

> A DEX swap avoids the stake pool's 0.1% direct-withdrawal fee. It can still have trading costs, price impact, and network or priority fees. Check the current route and net output before signing. Slippage tolerance is an execution limit, not an additional fixed fee. A typical trading-cost example is not a guaranteed all-in rate.

**Acceptance criteria.**

- The comparison distinguishes the direct-withdrawal fee, market execution costs, and network costs.
- Any illustrative percentage is labeled as an estimate with its included and excluded costs stated.
- The text does not imply that avoiding the protocol withdrawal fee makes a swap free.

**Normal behavior excluded.** Different net outputs between a swap and protocol redemption are not, by themselves, a bug. This review did not obtain or compare executable quotes.

## 2. Explain the full direct-exit workflow beside the waiting-time estimate

**Observation.** D1 describes initiation into a stake account, deactivation, and a later withdrawal. D2 summarizes the delay as roughly one epoch, about two days; D3 and D4 use an approximately two-to-three-day epoch estimate. The practical question is when the account becomes withdrawable and which action remains, rather than whether a fixed number of hours has elapsed.

**Reproduce by reading.**

1. Open D1 at **How Direct Unstaking Works** and follow the three numbered stages.
2. Compare its waiting-time wording with D2's first unstaking answer.
3. Compare both with D3's exit-method table and D4's **Epoch** and **Cooldown Period** definitions.

**Suggested replacement for the short direct-exit explanation.**

> Direct unstaking has three stages: move the stake from the pool into a stake account, deactivate that account, then withdraw the SOL once the account is withdrawable. The guide describes availability after the relevant epoch boundary. Epoch durations are approximate; check the account's current status rather than treating a two-day estimate as a guaranteed deadline. Waiting alone does not perform the final withdrawal.

**Acceptance criteria.**

- The short FAQ names deactivation and final withdrawal and links to the detailed guide.
- Timing language uses a consistent approximation across the four pages.
- The guide explains the condition that starts the waiting period and how to identify the next required action.
- A product or protocol maintainer verifies the suggested wording against the currently supported exit implementation before publication.

**Normal behavior excluded.** A cooldown and multiple wallet interactions are documented features of direct unstaking. An approximate two-day versus two-to-three-day description is a documentation precision issue, not evidence of delayed funds or a protocol failure.

## 3. State the management-fee calculation base explicitly

**Observation.** D2 describes a management fee equal to 4% of staking and MEV rewards after validator commissions, followed by an approximate annual equivalent of 0.3% of deposited SOL. D4 also defines the management fee in terms of rewards. The approximate principal-equivalent number would be clearer if its assumptions were visible.

**Reproduce by reading.**

1. Open D2 at **Fees** and identify the base to which 4% applies.
2. Compare the following approximate principal-equivalent example with D4's **Management Fee** definition.
3. Read D3's token-mechanics explanation to distinguish reward accrual through the exchange rate from additional wallet-token distributions.

**Suggested replacement for the numerical explanation.**

> The management fee is 4% of staking and MEV rewards after validator commissions; it is not 4% of deposited principal. For illustration, 7.5 SOL of rewards after validator commissions and before this management fee would produce a 0.30 SOL management fee: 7.5 × 4%. Relative to a 100 SOL starting deposit, that example is 0.3%. Actual amounts depend on rewards. This fee is separate from direct-withdrawal and transaction costs.

**Acceptance criteria.**

- The fee base and order relative to validator commissions are stated alongside the percentage.
- The example identifies its assumptions and is not presented as a promised yield or fixed annual charge on principal.
- Management fees, withdrawal fees, and transaction costs remain separate concepts.

**Normal behavior excluded.** D3 explains that rewards accrue through the JitoSOL-to-SOL exchange rate. An unchanged JitoSOL token count or an exchange rate different from 1:1 does not, by itself, show missing rewards.

## Unconfirmed route-label question

D1 directs readers to an immediate **Jupiter** option in the Unstake tab. The initial public Stake rendering showed **DFlow** labels. Stake and Unstake can legitimately use different routes, and the terms gate prevented inspection of the Unstake tab. **No route mismatch is confirmed, and this item is not counted as a finding.**

To resolve it, an authorized reviewer who accepts the site's terms can inspect the Unstake options without connecting a wallet or signing anything, record the displayed route and date, and compare that specific screen with D1. A documentation change is warranted only if the current Unstake screen actually differs.

Another excluded comparison: D2's ten-hour Interceptor hold applies to depositing an existing stake account. It is separate from the epoch-based direct-exit flow and from an ordinary SOL deposit.

## Reproducible documentation check

`audit.py` is a Python standard-library CLI that performs at most four sequential, read-only HTTP GETs, one for each fixed documentation URL above. It sends no credentials and does not use a cookie jar. Redirects are refused so a run cannot silently contact extra URLs. Requests have a configurable bounded timeout and a 2 MiB response limit. The tool extracts static document text from `main`, then `article`, or a labeled body fallback while excluding semantic navigation elements, scripts, and similar non-content elements. It does not evaluate CSS visibility or execute JavaScript, so its output is not a representation of the fully rendered browser page.

```console
python audit.py --self-test
python audit.py --output audit-results.json --timeout 15
```

The JSON records each URL, HTTP status, page title, extraction scope, text length/hash, and target-phrase counts. It also records failures without inventing page content. The output path is the only file written by a live run.

**Keyword matches establish only that text was present in the fetched page. They cannot establish a bug, a current fee configuration, a UI state, a successful transaction, or payment eligibility.** A missing match may reflect different wording, dynamic rendering, a blocked request, or extraction limitations.

The offline parser checks do not make network requests. They exercise main-content selection, exclusion of navigation and script text, title/entity decoding, fallback labeling, and phrase counting. The live audit result describes that specific fetch, not continuous monitoring.

### Verification recorded on 2026-10-16

- **Offline checks:** all 5 tests passed using the bundled Python runtime.
- **Initial sandbox run:** socket access was rejected with Windows error 10013 before any HTTP response. This was an execution-environment restriction, not evidence that Jito's pages were unavailable.
- **Approved live rerun:** the same command fetched the four fixed URLs once each, without credentials or cookies, using a 10-second request timeout. All four returned **HTTP 200**; the CLI exited with status 0. The run lasted from **13:53:39 to 13:53:54 UTC** (21:53 in Asia/Shanghai).
- **Evidence file:** [audit-results.json](audit-results.json) contains the final successful run, including titles, counts, and text hashes. The documentation was also read through the official pages linked above.

| Source | HTTP status | Extraction scope | Extracted characters |
| --- | --- | --- | ---: |
| D1: Unstaking Overview | 200 | `body_fallback` | 5,884 |
| D2: General FAQs | 200 | `body_fallback` | 6,931 |
| D3: Technical FAQs | 200 | `body_fallback` | 14,500 |
| D4: JitoSOL Glossary | 200 | `body_fallback` | 7,602 |

All four pages used the explicitly labeled body fallback because no nonempty `main` or `article` extraction was available. Consequently, counts can include navigation or page furniture implemented without semantic tags. The run validates HTTP retrieval and static extraction, not a perfect article boundary or rendered UI behavior. The absence of a DFlow keyword in these responses does not establish which route the live Unstake interface uses.

## Disclosure

This report and its companion script were prepared with AI-assisted research, drafting, and verification. Interface observations describe the limited browser session above; they do not claim that the account owner personally used the product or traded. The work is an independent portfolio sample. It was not commissioned by Jito, has not been accepted as a bounty submission, and does not establish any reward entitlement. No external publication or project-team communication is performed by the script.
