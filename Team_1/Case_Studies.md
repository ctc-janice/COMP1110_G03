# Report and Case Study -- COMP1110 G03

**Introduction**

Navigating public transport in Hong Kong can sometimes be challenging, especially when trying to choose between the cheapest, fastest, or most convenient route. To make this easier to study, we model the transport system as a simple network of stops and segments and built a program that generates possible journeys and ranks them based on the user's preference.

Our approach is simpler than real journey-planning tools such as Google Maps or Citymapper. Those apps rely on live maps and real-time data, while our project uses a handcrafted network with text-based interaction and basic input/output so that the routing logic stays clear and easy to understand.

This report focuses on two parts:
i) a survey of existing tools,
ii) a set of realistic case studies, and an evaluation of what our system can handle and where its limitations are.

***

## Survey of Existing Tools

This survey was designed to compare the existing tools across 5 different factors: ETA (Expected Time of Arrival) Availability, Fare Display, Transfer Handling, Accessibility Information, and Offline Usability.

1. **Google Maps**

Google Maps targets general smartphone users worldwide who want an all‑in‑one navigation app for driving, public transport, walking, and cycling. It is especially popular with tourists and occasional riders who need multimodal directions and basic fare guidance in unfamiliar cities.

a. _ETA Availability_

> Real-time or scheduled ETAs where GTFS (General Transit Feed Specification -- open standardized data format for public transport information) and live feeds are available.

b. _Fare display_

> Shows estimated transit fares in many regions; some cities support in-app payment via Google Pay.

c. _Transfer Handling_

> Supports preferences such as fewer transfers or less walking; handles multi-leg journeys automatically.

d. _Accessibility Information_
Offers wheelchair-accessible transit routes and accessibility attributes for places in supported regions.

e. _Offline Usability_

> Offline maps available, but transit, walking, and cycling directions are unavailable when fully offline.


2. **Citymapper**

Citymapper targets urban public transport users in supported cities who frequently combine metro, buses, trams, walking, and sometimes micromobility. It is popular with commuters and power users who want rich transit options, "GO" step‑by‑step navigation, and real-time updates.

a. _ETA Availability_

> Live ETAs and service updates where operators provide real-time feeds.

b. _Fare display_

> Shows fares for many services but focuses interface primarily on time and convenience rather than detailed cost breakdowns.

c. _Transfer Handling_

> Optimises across modes with options such as fastest, fewer transfers, and live "GO" copilot (Microsoft's AI Tool) guidance.

d. _Accessibility Information_
Provides step-free, wheelchair-accessible routes in many regions, avoiding stairs and wide gaps.

e. _Offline Usability_

> Supports saved journeys, maps, and some metro departures offline once data are downloaded; live updates need data.


3. **MTR Mobile**

MTR Mobile is targeted at passengers of the Hong Kong MTR rail network who want to plan trips, check train times, and access MTR‑specific travel information. It primarily serves local commuters and visitors using the MTR system rather than all modes of public transport in Hong Kong.

a. _ETA Availability_

> Provides scheduled journey times and near real time train info on MTR lines.

b. _Fare display_

> Displays single-journey and other fare information via trap planner and fare charts.

c. _Transfer Handling_

> Handles transfers with the MTR network but not full multi-modal journeys.

d. _Accessibility Information_
Includes station barrier-free information and highlights accessibility facilities via app and website.

e. _Offline Usability_

> Designed for online use over internet/mobile networks; no explicit offline routing mode advertised.


4. **HKBUS.APP**

HKBUS.APP targets Hong Kong bus users who care about real‑time bus and green minibus arrival times for multiple operators. Its typical users include local commuters who already know their route numbers and stops but need reliable ETA information.

a. _ETA Availability_

> Focused on real time bus and minibus ETAs for multiple operators.

b. _Fare display_

> Fare information is secondary; the core focus is arrivals rather than fare comparison.

c. _Transfer Handling_

> Does not compute multi-leg journeys; transfers are managed by the user, not automatically optimised.

d. _Accessibility Information_
No dedicated accessibility routing; accessibility depends on vehicle and stop infrastructure rather than app features.

e. _Offline Usability_

> Real time ETAs require connectivity; no offline schedules or maps are advertised.

***

## Design Takeaways

From the survey, we learned that presenting simple metrics like total travel time, number of transfers, and estimated fare makes route choices easy to understand, as seen in Google Maps, Citymapper, and MTR Mobile. Their support for preferences like "fewer transfers" or "less walking" inspired our three modes: cheapest, fastest, and fewest segments. Even HKBUS.APP shows that basic ETA info helps commuters, so our fixed network can still be useful. We avoided complexities like real-time data, live delays, and full accessibility routing because Topic B focuses on simple models, not commercial apps. Instead, we chose a small, hand-crafted network with depth-limited DFS search and clear scoring, which keeps everything transparent and easy to explain.

***

## Case Studies

### Case Study 1: Fastest Route --- Central to Tsim Sha Tsui

**Scenario**

An HKU student needs to travel from Central to Tsim Sha Tsui to attend a noon class. Speed is the only priority.

**Inputs**

- Origin: HK001 --- Central MTR
- Destination: HK005 --- Tsim Sha Tsui MTR
- Preference: fastest

**System Output**

- Total travel time: 8 minutes
- Total cost: HK\$17.00
- Number of segments: 1

**Route:**

- Central MTR (HK001) → Tsim Sha Tsui MTR (HK005)
    - MTR, 8 min, HK\$17.00

**All Routes Returned**

1. Route 1 --- 8 mins \| HK\$17.00 \| 1 segment
    - Central MTR → Tsim Sha Tsui MTR (MTR, 8 min, HK\$17.00)
2. Route 2 --- 11 mins \| HK\$23.50 \| 2 segments
    - Central MTR → Admiralty MTR (MTR, 3 min, HK\$6.50)
    - Admiralty MTR → Tsim Sha Tsui MTR (MTR, 8 min, HK\$17.00)
3. Route 3 --- 36 mins \| HK\$34.50 \| 5 segments
    - Central MTR → Central Bus Terminal (Walk, 2 min, HK\$0.00)
    - Central Bus Terminal → Causeway Bay MTR (Bus, 20 min, HK\$4.50)
    - Causeway Bay MTR → Wan Chai MTR (MTR, 3 min, HK\$6.50)
    - Wan Chai MTR → Admiralty MTR (MTR, 3 min, HK\$6.50)
    - Admiralty MTR → Tsim Sha Tsui MTR (MTR, 8 min, HK\$17.00)

**What This Shows**

The direct MTR connection from Central to Tsim Sha Tsui is clearly the fastest route, requiring only one segment and no transfers. The alternative MTR‑only route via Admiralty takes slightly longer with no benefit when speed is the sole priority. The third route demonstrates how the DFS search can discover unusually long but technically valid paths; however, the scoring function correctly ranks it last due to its excessive duration and number of segments.

**Limitations**

- Travel times are fixed values stored in `segments.csv` and do not include waiting or platform transfer time.
- Users cannot filter results to show only direct (single‑segment) routes.
- The same route ranking is returned regardless of time of day.

**Comparison to Real Applications**

Google Maps would adjust ETAs dynamically based on service frequency and live delays, whereas this system always returns a fixed estimate.

***

### Case Study 2: Cheapest Route --- Central to Causeway Bay

**Scenario**

An HKU student commutes daily from Central to Causeway Bay and wants to minimise travel cost, even if this leads to a slower journey.

**Inputs**

- Origin: HK001 --- Central MTR
- Destination: HK004 --- Causeway Bay MTR
- Preference: cheapest

**System Output**

- Total travel time: 22 minutes
- Total cost: HK\$4.50
- Number of segments: 2

**Route:**

- Central MTR → Central Bus Terminal (Walk, 2 min, HK\$0.00)
- Central Bus Terminal → Causeway Bay MTR (Bus, 20 min, HK\$4.50)

**All Routes Returned**

1. Route 1 --- HK\$4.50 \| 22 mins \| 2 segments
    - Walk to Central Bus Terminal
    - Bus to Causeway Bay MTR
2. Route 2 --- HK\$19.50 \| 9 mins \| 3 segments
    - Central → Admiralty → Wan Chai → Causeway Bay (all MTR)
3. Route 3 --- HK\$47.00 \| 22 mins \| 4 segments...
    - Central → Tsim Sha Tsui → Admiralty → Wan Chai → Causeway Bay

**What This Shows**

Switching the preference from fastest to cheapest completely changes the ranking. The walk‑and‑bus route becomes optimal due to its extremely low cost, despite being more than twice as long as the fastest option. This case study effectively demonstrates how the scoring system prioritises the selected metric and reorders the same underlying routes accordingly.

**Limitations**

- The system does not explicitly explain cost--time trade‑offs (e.g. "saves HK\$15 but adds 13 minutes").
- There is no bus timetable or waiting‑time estimate; the 20‑minute figure represents travel time only.

**Comparison to Real Applications**

Citymapper highlights "cheapest" routes visually and summarises trade‑offs in a single view, while this system leaves comparison entirely to the user.

***

### Case Study 3: Fewest Transfers --- Central to Causeway Bay After a Long Day

**Scenario**

After a long day, the student wants the simplest possible journey home with minimal thinking and as few route segments as possible.

**Inputs**

- Origin: HK001 --- Central MTR
- Destination: HK004 --- Causeway Bay MTR
- Preference: fewest\_segments

**System Output**

- Total travel time: 22 minutes
- Total cost: HK\$4.50
- Number of segments: 2

**Winning Route:**

- Central MTR → Central Bus Terminal (Walk)
- Central Bus Terminal → Causeway Bay MTR (Bus)

**What This Shows**

Although this route is slower and involves a mode change, it is ranked first because it has the fewest segments in the data model. The deterministic tie‑breaking rule (segments → duration → cost) ensures consistent results across runs and explains why longer but more segmented routes score lower.

**Limitations**

- Every row in `segments.csv` counts as one segment, including short walks.
- The system does not distinguish between staying on the same train line and making a physically disruptive transfer.
- As a result, journeys that feel simpler may appear more complex in the model.

**Comparison to Real Applications**

Google Maps groups consecutive stops on the same service into a single leg and highlights only actual transfers, resulting in a user experience that better reflects real‑world effort.

***

### Case Study 4: Handling Invalid Input Gracefully

**Scenario**

A first‑time user enters a non‑existent stop ID and an unsupported preference value.

**Inputs**

- Origin: HK999 (does not exist)
- Destination: HK001 --- Central MTR
- Preference: quickest (invalid)

**System Output**

- Error: Stop HK999 was not found in the network.
- Error: Invalid preference quickest. Must be one of: fastest, cheapest, fewest\_segments.
- No routing was performed.

**What This Shows**

The input validator detects and reports all errors in a single pass before running the DFS search. Error messages are specific and informative, and the program does not crash or partially execute.

**Limitations**

- The system does not suggest corrections (e.g. "Did you mean fastest?").
- Users cannot browse valid stop IDs from within the program.

**Comparison to Real Applications**

Google Maps supports fuzzy matching and partial inputs, which this prototype intentionally omits to keep logic simple and explicit.

***
