# PMR-0001 Working Record: Rules-Based AI Player 2

> **Document status:** Working engineering record
> **Source record:** DR-0015, “AI Rules”
> **Lifecycle phase:** Concept and requirements analysis
> **Priority:** Low
> **Target release:** Undetermined
> **Last updated:** 2026-07-24
> **Strategy authority:** Doyle C. Dikes

## 1. Purpose of This Record

This working record is the durable home for the analysis, requirements,
strategy rules, architecture, implementation planning, and verification
planning for a future rules-based computer player in Trickwise Pinochle.

It supplements, but does not replace, DR-0015. DR-0015 preserves the original
feature request and the first strategy observations. This record organizes
those observations into material that can eventually be implemented and
tested.

This record is intended to be updated directly by Doyle and by Codex/GPT during
future design conversations. Important conclusions should be added here rather
than left only in conversation history.

## 2. Change Summary

The proposed modification will add **AI Rules** as a selectable controller for
Player 2. The AI will choose among actions already determined to be legal by
the existing game engine. Its choices will be based on playing observations
and strategy supplied and approved by Doyle.

The initial goal is not to create a perfect Pinochle player. The goal is to
create an understandable, testable player whose decisions increasingly reflect
Doyle's approach to two-player Pinochle.

## 3. Governing Principles

### 3.1 Separation of legality and strategy

The existing game engine remains responsible for:

- Turn order.
- Game phases and turn stages.
- Legal card play.
- Legal Dix exchanges.
- Legal meld declarations.
- Trick resolution.
- Drawing.
- Scoring.
- Round and game completion.

AI Rules is responsible for choosing which legal action is strategically
preferred.

AI Rules must never make an illegal action legal and must never modify game
state directly.

### 3.2 Strategy-source restriction

AI Rules strategy shall be derived exclusively from:

- Doyle's observations and playing experience.
- Strategy statements explicitly supplied by Doyle.
- Clarifications and examples approved by Doyle.
- Logical engineering interpretations that Doyle reviews and confirms.

External Pinochle AI engines, published strategy guides, or other strategy
sources shall not be used to define the AI's playing policy.

The existing Trickwise game rules remain the authority for legal play. This
restriction concerns strategic selection among legal actions, not ordinary
software engineering methods.

### 3.3 Controlled interpretation

Codex/GPT may:

- Preserve Doyle's original wording.
- Restate an observation as a draft structured rule.
- Identify ambiguity, conflicts, missing conditions, and missing exceptions.
- Propose examples and tests.
- Propose software designs that implement confirmed rules.

Codex/GPT shall not silently convert an interpretation into approved playing
policy. A strategy rule remains a draft until Doyle confirms it.

### 3.4 Explainability

The AI should be able to explain important choices in terms of approved rule
identifiers. Explanations are part of verification and may later become an
optional player-facing or diagnostic feature.

### 3.5 No concealed-information advantage

The AI must base decisions only on information available to a human player in
the same position. It must not inspect:

- Player 1's concealed hand.
- The order of cards in the stock.
- Any other concealed state unavailable to a human Player 2.

Whether the UI displays the AI hand face-up or face-down is a presentation
option and must not alter what information the AI receives.

## 4. Operational Concept

### 4.1 Primary use

A user starts or configures a game with:

- Player 1 controlled by the user.
- Player 2 controlled by AI Rules.

When Player 2 becomes eligible to act, the AI:

1. Receives a restricted view of the game.
2. Obtains the legal actions and legal candidates.
3. Applies the confirmed strategy rules relevant to the current situation.
4. Selects one legal action.
5. Returns that action to the authoritative game controller.
6. Records an explanation of the decision.
7. Allows the UI to refresh from the resulting game state.

### 4.2 Diagnostic use

During development, the user may:

- Show or conceal the AI hand.
- Inspect the strategy rules that applied.
- Inspect alternative actions considered.
- See preference scores or decision reasons.
- Compare the AI's choice with the choice Doyle would have made.
- Record a new observation when the AI makes a poor choice.

### 4.3 Out of initial scope

The following are not initial requirements:

- Machine learning.
- Training from large game datasets.
- Use of external Pinochle strategy material.
- Natural-language model calls during every turn.
- Networked or cloud-hosted AI.
- Claims that the AI plays optimally.
- Automatic creation of approved strategy without owner review.

## 5. Confirmed Feature Requirements

### PMR-0001-REQ-001 — Selectable Player 2 controller

Game Options shall allow Player 2 to be configured as:

- Human.
- AI Rules.

### PMR-0001-REQ-002 — AI hand presentation option

When Player 2 is controlled by AI Rules, a sub-option shall control whether
Player 2's cards are displayed face-up or face-down.

### PMR-0001-REQ-003 — AI hand interaction lock

Player 1 shall not be able to select, drag, declare, exchange, or play cards
owned by the AI-controlled Player 2.

### PMR-0001-REQ-004 — Authoritative game engine

AI Rules shall execute actions only through public game-controller operations.
It shall not directly mutate hands, melds, tricks, scores, the stock, or other
controller state.

### PMR-0001-REQ-005 — Legal candidate restriction

The AI shall select only from actions and cards reported as legal by the game
engine.

### PMR-0001-REQ-006 — Concealed-information restriction

The AI decision interface shall exclude Player 1's concealed hand and stock
order.

### PMR-0001-REQ-007 — Decision trace

Each AI decision shall be capable of recording:

- The selected action.
- The selected card or meld, when applicable.
- The strategy rule identifiers that affected the selection.
- A short explanation.
- Alternative candidates considered when diagnostic detail is enabled.

### PMR-0001-REQ-008 — Strategy provenance

Every strategy rule shall preserve:

- Its origin.
- Its approval status.
- Its implementation status.
- Its verification status.

### PMR-0001-REQ-009 — Deterministic verification

Strategy behavior shall be testable with controlled game states and
deterministic tie-breaking.

## 6. Natural-Language-to-Rule Process

The controlled conversion process is:

1. **Owner observation**
   Doyle describes a playing observation, preference, exception, or example in
   natural language.

2. **Source preservation**
   The original wording is retained in this record or a linked conversation
   capture.

3. **Draft interpretation**
   Codex/GPT converts the observation into one or more draft rules containing
   conditions, preferences, rationale, and exceptions.

4. **Ambiguity analysis**
   Missing conditions, conflicts, undefined terms, and unclear priorities are
   listed as open questions.

5. **Owner confirmation**
   Doyle confirms, revises, rejects, or postpones each draft rule.

6. **Formal representation**
   A confirmed rule is represented in a form suitable for evaluation by the
   AI strategy engine.

7. **Test definition**
   Positive, negative, exception, and conflict cases are defined.

8. **Implementation**
   The evaluator is connected to a restricted game-state view and legal
   candidate actions.

9. **Verification**
   Automated tests and observed game play confirm that the implemented
   decision matches the approved rule.

10. **Refinement**
    New observations create revisions, exceptions, or superseding rules with
    retained history.

## 7. Strategy Rule Record Format

Each rule should contain:

| Field | Meaning |
|---|---|
| Rule ID | Stable identifier such as `AIR-001` |
| Title | Short description |
| Source | DR, dated observation, or conversation capture |
| Phase | Deal, Meld Phase, Trick Phase, or other stage |
| Applies when | Required conditions |
| Candidate action | Action being preferred or discouraged |
| Preference | Relative weight or priority |
| Exceptions | Conditions that limit the rule |
| Rationale | Doyle's reason for the strategy |
| Conflicts | Other rules that may compete |
| Examples | Representative game states |
| Approval | Draft, Owner Confirmed, Rejected, or Superseded |
| Implementation | Not Started, Implemented, or Revised |
| Verification | Untested, Tested, or Failed |

## 8. Initial AI Strategy Rule Catalog

The following rules are draft engineering interpretations of DR-0015. They are
not yet approved playing policy.

### AIR-001 — Prefer shedding an ordinary nine

- **Source:** DR-0015.
- **Phase:** Meld Phase.
- **Applies when:**
  - The AI must select a legal card for the current trick.
  - At least one legal candidate is a non-trump nine.
- **Preference:** Prefer playing the non-trump nine early.
- **Rationale:** An ordinary nine has no counter value and is a low-priority
  card to capture into the Won panel.
- **Known exception:** Do not blindly discard the nine when the AI should try
  to win the trick so that it can declare an available or strategically
  important meld.
- **Conflicts:** Meld pursuit, trick-winning strategy, suit-control strategy,
  and any future rule assigning value to retaining the card.
- **Approval:** Draft.
- **Implementation:** Not Started.
- **Verification:** Untested.

### AIR-002 — Exchange an available Dix

- **Source:** DR-0015.
- **Phase:** Meld Phase.
- **Applies when:** The game engine reports that a legal Dix exchange is
  available to the AI.
- **Preference:** Perform the Dix exchange before selecting the trick-play
  action.
- **Rationale:** A legal exchange immediately scores ten points.
- **Known observation:** Repeated exchange opportunities may occur when both
  copies of the Dix become available over successive turns.
- **Conflicts:** None identified yet.
- **Approval:** Draft.
- **Implementation:** Not Started.
- **Verification:** Untested.

### AIR-003 — Treat the Dix differently from an ordinary nine

- **Source:** DR-0015.
- **Phase:** Meld Phase.
- **Applies when:** A trump nine is being evaluated as a candidate card.
- **Preference:** Do not apply the ordinary-nine discard preference without
  first evaluating Dix exchange and Dix meld value.
- **Rationale:** The Dix has scoring opportunities not shared by non-trump
  nines.
- **Conflicts:** AIR-001 and future meld-selection rules.
- **Approval:** Draft.
- **Implementation:** Not Started.
- **Verification:** Untested.

### AIR-004 — Preserve an opportunity to make an important meld

- **Source:** DR-0015.
- **Phase:** Meld Phase.
- **Applies when:**
  - The AI has an available or planned meld.
  - The AI may need to win the current trick to become eligible to declare it.
- **Preference:** Prefer a reasonable attempt to win the trick over shedding a
  zero-counter card.
- **Rationale:** The value of becoming eligible to meld may exceed the value of
  discarding an ordinary nine.
- **Unresolved:** Define “available,” “planned,” “important,” and “reasonable
  attempt to win.”
- **Conflicts:** AIR-001 and future risk/expected-value rules.
- **Approval:** Draft.
- **Implementation:** Not Started.
- **Verification:** Untested.

## 9. Proposed AI Decision Architecture

### 9.1 Existing extension point

The project already defines a `PlayerStrategy` protocol in `ai.py`. A strategy
implementation is expected to choose controller actions through public `Game`
methods rather than changing controller state directly.

This is the correct high-level boundary and should be retained.

### 9.2 Restricted player view

The current strategy protocol receives the complete `Game`, which exposes
concealed state. Introduce a read-only player-oriented snapshot, tentatively
named `PlayerGameView`.

It should include:

- Acting player.
- Own hand and own meld cards.
- Phase and turn stage.
- Trump card and trump suit.
- Current trick.
- Exposed melds.
- Cards already won or otherwise exposed.
- Stock size, but not stock order.
- Scores.
- Available actions.
- Legal cards.
- Legal meld and exchange candidates.

It should exclude:

- Opponent's concealed hand.
- Stock order.
- Private controller internals.

### 9.3 Candidate actions

The decision layer should operate on structured candidate actions rather than
calling controller methods while it is still evaluating alternatives.

Candidate types are expected to include:

- Swap Dix.
- Declare a particular meld with particular cards.
- Play a particular card to the trick.
- Choose a particular final draw.

### 9.4 Rule evaluation

For every legal candidate:

1. Identify applicable confirmed rules.
2. Add preferences and penalties.
3. Preserve each contributing reason.
4. Resolve rule priority and conflicts.
5. Apply deterministic tie-breaking.
6. Select the highest-ranked legal candidate.

Initial implementations may use simple integer preference weights. These
weights are decision-ranking values, not game points.

### 9.5 Execution

After selection, a controller adapter executes the candidate through the
appropriate public `Game` action method and returns the resulting
`ActionResult`.

### 9.6 Decision explanation

A decision result should be capable of containing:

```text
Selected action
Selected card or meld
Applicable strategy rule IDs
Short explanation
Candidate preference totals
Tie-breaking reason, if used
```

Example:

```text
Selected: Play nine of clubs
AIR-001: Prefer shedding a zero-counter nine
AIR-004: Not applicable; no meld opportunity requires winning
```

## 10. UI Design Considerations

### 10.1 Game Options

Proposed controls:

- Player 2 controller:
  - Human.
  - AI Rules.
- AI hand display:
  - Show card faces.
  - Show card backs.
- AI explanation detail:
  - Off.
  - Short explanation.
  - Diagnostic detail.

### 10.2 AI-controlled hand

When Player 2 is controlled by AI Rules:

- Its cards must be locked against Player 1 interaction.
- Face-up display is for observation and debugging.
- Face-down display represents ordinary hidden-hand play.
- The display setting must not affect AI knowledge or decision logic.

### 10.3 Decision presentation

Possible future presentation:

> Player 2 played the nine of clubs to shed a zero-counter card.
> Rule: AIR-001.

A diagnostic view may list other candidates and the rules that affected their
ranking.

## 11. High-Level Software Design

Potential components:

| Component | Responsibility |
|---|---|
| `Game` | Authoritative rules and game state |
| `PlayerGameView` | Safe, read-only information for one player |
| `CandidateAction` | Structured legal action under consideration |
| `RulesBasedStrategy` | Coordinates candidate evaluation and selection |
| `StrategyRule` | Evaluates one strategic preference |
| `DecisionEvaluation` | Preference and explanation for one candidate |
| `AIDecision` | Selected action and complete decision trace |
| Controller adapter | Executes the selected action through `Game` |
| AI options | Stores controller, card-display, and explanation settings |

The strategy implementation should remain independent of PyQt so that it can
be tested without opening the UI.

## 12. Game-Engine Interface Needs

The existing engine already provides useful operations including:

- `available_actions(player)`
- `legal_cards(player)`
- `scoreable_melds(player)`
- `near_melds(player)`
- `swap_dix(...)`
- `declare_meld(...)`
- `play_to_trick(...)`
- `choose_last_draw(...)`

Additional read-only interfaces may be needed for:

- Exact card combinations for each legal meld.
- Structured Dix-exchange candidates.
- Structured final-draw candidates.
- Counter value of a card.
- Whether a candidate beats the current trick.
- Melds affected by playing a particular card.
- Cards and information exposed to a particular player.
- Creation of a safe `PlayerGameView`.

Strategy logic should not be added to these legality queries.

## 13. Verification Approach

Every confirmed strategy rule should have:

- A positive case where the rule applies.
- A negative case where it does not apply.
- An exception case.
- A conflict case involving another rule.
- An assertion about the decision explanation.

### AIR-001 candidate tests

1. **Ordinary discard**
   - Several cards are legal.
   - A non-trump nine is available.
   - No important meld opportunity requires winning.
   - Expected: the nine receives the discard preference.

2. **Meld exception**
   - A nine is available.
   - Winning is reasonably necessary to declare an important meld.
   - Expected: the AI does not blindly choose the nine.

3. **Dix distinction**
   - The only nine candidate is the Dix.
   - A legal exchange is available.
   - Expected: Dix rules apply before the ordinary-nine rule.

4. **Legality override**
   - A nine is held but is not a legal response.
   - Expected: it is never a candidate regardless of preference.

### AIR-002 candidate tests

1. A legal Dix exchange is available; expected action is exchange.
2. A Dix is held but exchange timing is illegal; no exchange candidate exists.
3. Both Dix copies create successive legal opportunities; each opportunity is
   evaluated independently.
4. Decision explanation cites AIR-002.

## 14. Proposed Phased Implementation

### Increment 1 — PMR and Strategy Catalog

- Establish the durable PMR structure.
- Capture and review strategy observations.
- Assign stable rule identifiers.
- Establish approval and verification states.

**Demonstrable result:** The feature has a controlled, reviewable strategy
baseline without changing game play.

### Increment 2 — Restricted PlayerGameView

- Define the information available to a player.
- Exclude opponent hand and stock order.
- Test that concealed information is absent.

**Demonstrable result:** An AI can inspect a legal human-equivalent view without
being able to cheat.

### Increment 3 — Candidate-Action Enumeration

- Represent every legal action as a structured candidate.
- Add missing game-engine queries.
- Ensure candidates map to existing public action methods.

**Demonstrable result:** A test can list every action Player 2 may legally take
in a controlled game state.

### Increment 4 — Decision and Explanation Framework

- Evaluate candidates.
- Accumulate rule preferences and reasons.
- Add deterministic tie-breaking.
- Produce an `AIDecision`.

**Demonstrable result:** A simple test strategy chooses among legal candidates
and explains why.

### Increment 5 — Dix Strategy

- Implement confirmed Dix rules.
- Verify exchange timing and repeated opportunities.

**Demonstrable result:** AI Rules recognizes and performs confirmed Dix
behavior.

### Increment 6 — Ordinary-Nine Strategy

- Implement confirmed rules for shedding and preserving nines.
- Add initial conflict behavior with meld pursuit.

**Demonstrable result:** AI Rules makes and explains simple nine-related
choices.

### Increment 7 — Meld Strategy

- Add confirmed meld priorities, preservation rules, and risk considerations.

### Increment 8 — General Meld-Phase Trick Strategy

- Add confirmed lead and response preferences.
- Refine interaction among discard, capture, draw, and meld objectives.

### Increment 9 — Strict Trick-Phase Strategy

- Add confirmed counter capture, following, trumping, and endgame preferences.

### Increment 10 — Player 2 UI Integration

- Add controller selection.
- Lock AI cards.
- Add face/back display option.
- Add optional explanations.

### Increment 11 — Play Observation and Refinement

- Play controlled games.
- Record poor or surprising decisions.
- Convert observations into new draft rules and tests.
- Revise weights and conflicts through controlled rule revisions.

## 15. Decisions

### DEC-001 — Separate game legality from AI strategy

- **Status:** Accepted concept.
- **Decision:** The game engine determines legal actions; AI Rules ranks and
  selects among them.
- **Reason:** Prevents strategy development from weakening or duplicating the
  authoritative rules engine.

### DEC-002 — Use owner-authored strategy

- **Status:** Accepted.
- **Decision:** Doyle's supplied and approved observations are the sole source
  of playing strategy.
- **Reason:** The goal is to express Doyle's two-player Pinochle approach, not a
  generic external strategy.

### DEC-003 — Require traceable rule approval

- **Status:** Accepted concept.
- **Decision:** GPT-derived interpretations remain drafts until Doyle confirms
  them.
- **Reason:** Prevents an AI interpretation from silently becoming project
  policy.

### DEC-004 — Preserve explainability

- **Status:** Accepted concept.
- **Decision:** AI decisions should retain contributing rule identifiers and
  reasons.
- **Reason:** Supports trust, debugging, learning, and verification.

### DEC-005 — Tailor MIL-STD-498 discipline

- **Status:** Accepted direction.
- **Decision:** Use requirements, design, implementation planning, test
  traceability, packaging, and controlled change without recreating the full
  military documentation set.
- **Reason:** Preserve useful career-proven engineering discipline without
  making documentation larger than the feature.

## 16. Risks

### RISK-001 — Strategy prose remains ambiguous

Natural-language observations may omit conditions obvious to an experienced
player. Mitigate through examples, questions, owner confirmation, and tests.

### RISK-002 — Conflicting strategy rules

Several valid observations may recommend different actions. Mitigate with
visible priorities, candidate scoring, conflict tests, and decision traces.

### RISK-003 — AI accesses concealed state

Passing the complete `Game` object exposes both hands. Mitigate with a
restricted, read-only player view and tests demonstrating the absence of hidden
information.

### RISK-004 — Strategy leaks into the rules engine

Mixing preferences into legality code would make both systems harder to test.
Mitigate by keeping strategy components independent and calling only public
game actions.

### RISK-005 — Excessive documentation

Formal process could outgrow the implementation. Mitigate by maintaining a
small set of living records and adding detail only when it supports a decision,
implementation, or test.

### RISK-006 — Preference weights appear authoritative

Initial numeric weights may look more precise than the underlying observations.
Treat them as adjustable implementation parameters and retain the qualitative
rule rationale.

## 17. Open Questions

1. Confirm or revise draft rules AIR-001 through AIR-004.
2. Define how the AI values an available meld relative to the likelihood of
   winning the current trick.
3. Define whether every legal Dix exchange is always preferred without
   exception.
4. Define the strategic difference between a Dix exchange and using a Dix in a
   meld.
5. Decide whether AI preference weights are fixed in code, stored as
   configuration, or initially hidden behind qualitative priorities.
6. Decide the initial deterministic tie-breaker when candidates remain equal.
7. Decide how much explanation should be visible during ordinary play.
8. Determine whether Player 2 can be changed between Human and AI Rules during
   an active round or only before a new game.
9. Determine whether the face/back display option can change during play.
10. Define the first complete slice of strategy that is sufficient for an AI
    to finish a game without random fallback.

## 18. Working Method for Future Conversations

When a future conversation adds information about AI Rules:

1. Preserve the new owner observation.
2. Update applicable requirements or designs.
3. Add or revise draft strategy rules.
4. Record newly discovered conflicts and questions.
5. Update implementation or verification status only when work actually
   occurs.
6. Add a dated entry to the conversation-capture log.

Suggested request:

> Update PMR-0001 with the AI Rules observations and decisions from this
> conversation. Preserve my wording, mark GPT interpretations as drafts, and
> list questions requiring my confirmation.

## 19. Conversation-Capture Log

### 2026-07-24 — Initial PMR and AI Rules architecture discussion

Captured:

- Recognition that DR-0015 is an originating enhancement record rather than a
  sufficient long-term engineering workspace.
- Proposal for a separate, linked PMR.
- Tailoring of MIL-STD-498-style discipline to a small living record.
- Strategy provenance restriction.
- Natural-language-to-rule conversion and owner-confirmation process.
- Initial draft rules for ordinary nines, the Dix, and meld pursuit.
- Separation of game legality from strategic preference.
- Existing `PlayerStrategy` extension point.
- Need for a restricted player view to prevent concealed-information access.
- Candidate-action evaluation and explainable decision traces.
- Rule-level verification and incremental implementation planning.

No application code was modified as part of this capture.
