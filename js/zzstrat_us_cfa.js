/* Pass plan — CFA Level I (2026-10-20, Terra Prep) format: _형식.md
 * Question counts per topic = midpoint of the 2026 weight range, scaled to 180 questions. */
ZZSTRAT.add({
  id: "us_cfa",
  이름: "CFA Level I",
  기준: "2026 topic weights",
  방식: "상대",
  한줄: "The estimated pass line has sat near 69 percent for the last several windows. Plan for 135 of 180, and earn the margin in Ethics, FSA and Equity, 75 questions between them.",
  합격선: {
    설명: "180 three-option questions in two sessions of 90, about 135 minutes each, with no penalty for wrong answers. CFA Institute sets a minimum passing score for each window and does not publish it; your score report only shows where it fell. There is no per-topic minimum.",
    과락: "No per-topic minimum. One overall pass line per exam window",
    커트: [
      { 연도: 2025, 구분: "Nov window, estimated MPS", 점수: 124, 비고: "About 69.0% of 180. 300hours estimate, not official", 출처: "300hours" },
      { 연도: 2026, 구분: "Feb window, estimated MPS", 점수: 125, 비고: "About 69.5%. Estimate", 출처: "300hours" },
      { 연도: 2026, 구분: "May window, estimated MPS", 점수: 124, 비고: "About 69.0%. Estimate", 출처: "300hours" }
    ],
    가산점: [],
    목표: 135,
    만점: 180,
    목표근거: "Recent estimated pass lines are 124 to 125 questions. Aim for 135, eleven above the highest estimate, because the line moves by window and you never see it in advance. Official pass rates were 43 to 45 percent in 2025 and 39 to 45 percent in 2026."
  },
  과목: [
    {
      이름: "Ethics", 문항: 31, 배점: 31,
      역할: "전략",
      목표: 25, 목표문항: "25 of 31",
      이유: "Weighted 15 to 20 percent, the single largest topic in 2026. Every question maps to one of seven Standards, and the guidance cases repeat in new wording. From 2027 the weight drops to 10 to 15 percent.",
      지표: { 범위: "좁음" },
      선: "Loyalty to the ultimate beneficiary, fair dealing in allocations and recommendations, and the mosaic theory under material nonpublic information.",
      버림: "",
      예시: [
        { 출처: "Terra Prep CFA · Standard III(A)", 발문: "A member manages the assets of a company pension plan. According to the guidance under Standard III(A), to whom is the member's duty of loyalty owed?", 선지: ["The plan's board of directors exclusively, regardless of beneficiary interests", "The ultimate beneficiaries of the pension plan", "The company that established and hired the manager for the pension plan"], 정답: 2,
          판정: "필수", 설명: "Loyalty runs to the beneficiaries, not to whoever hired you. The same principle covers trusts, so one rule answers a family of questions." },
        { 출처: "Terra Prep CFA · Standard III(B)", 발문: "An analyst mentions his firm's upcoming purchase recommendation to several of his best clients over lunch, a week before the report is sent to all clients. This is BEST described as a violation of Standard III(B) because:", 선지: ["Standard III(B) requires that recommendations be communicated to all clients equally rather than fairly", "Selectively disclosing the recommendation to favored clients in advance denies other clients a fair opportunity to act on it", "Analysts are never permitted to discuss research with clients before publication under any circumstances"], 정답: 2,
          판정: "승부", 설명: "The Standard says fairly, not equally. The first choice uses the wrong word on purpose; candidates who read for the gist instead of the wording lose this point." },
        { 출처: "Terra Prep CFA · Standard III(B)", 발문: "When a new issue offered to a firm's clients is oversubscribed, Standard III(B) guidance indicates that members should MOST appropriately:", 선지: ["Fill their own and immediate family members' orders first", "Prorate the issue among all suitable client accounts and forgo sales to themselves or immediate family", "Allocate the full amount to whichever clients placed their orders first, regardless of suitability"], 정답: 2,
          판정: "필수", 설명: "Clients first, prorated, family last. Allocation questions use this answer pattern every window." }
      ]
    },
    {
      이름: "FSA", 문항: 22, 배점: 22,
      역할: "전략",
      목표: 17, 목표문항: "17 of 22",
      이유: "Weighted 11 to 14 percent. Inventory methods, ratio effects and cash-flow classification are mechanical once learned, and the same mechanics feed Equity and Corporate Issuers questions.",
      지표: { 범위: "넓음" },
      선: "FIFO versus LIFO effects in rising prices, operating versus investing versus financing cash flows, and the direction of each common ratio.",
      버림: "Multi-step deferred tax reconciliations. Mark and return.",
      예시: []
    },
    {
      이름: "Equity", 문항: 22, 배점: 22,
      역할: "기본",
      목표: 17, 목표문항: "17 of 22",
      이유: "Weighted 11 to 14 percent. Market structure, index construction and the dividend discount model are short calculations with fixed formulas.",
      지표: { 범위: "보통" },
      선: "Gordon growth valuation, price-weighted versus market-cap index returns, and margin call price.",
      버림: "",
      예시: []
    },
    {
      이름: "Fixed Income", 문항: 22, 배점: 22,
      역할: "기본",
      목표: 15, 목표문항: "15 of 22",
      이유: "Weighted 11 to 14 percent, and the most calculator-heavy topic. Bond pricing, yield measures and duration are worth learning cold; the credit and securitization detail is where time runs out.",
      지표: { 범위: "넓음" },
      선: "Price from yield, the price-yield relationship, and modified duration for a price change estimate.",
      버림: "Long securitization structure questions with several tranches. Answer last.",
      예시: []
    },
    {
      이름: "Portfolio Mgmt", 문항: 18, 배점: 18,
      역할: "기본",
      목표: 14, 목표문항: "14 of 18",
      이유: "Weighted 8 to 12 percent. CAPM, the security market line and the investment policy statement components repeat in nearly identical form.",
      지표: { 범위: "보통" },
      선: "CAPM expected return, systematic versus unsystematic risk, and IPS objectives and constraints.",
      버림: "",
      예시: []
    },
    {
      이름: "Alternatives", 문항: 15, 배점: 15,
      역할: "기본",
      목표: 11, 목표문항: "11 of 15",
      이유: "Weighted 7 to 10 percent. Fee waterfalls and the basic features of private equity, real estate and hedge funds are a contained list.",
      지표: { 범위: "좁음" },
      선: "Management and incentive fee calculations with a hurdle and high-water mark.",
      버림: "",
      예시: []
    },
    {
      이름: "Quant", 문항: 13, 배점: 13,
      역할: "방어",
      목표: 9, 목표문항: "9 of 13",
      이유: "Weighted 6 to 9 percent in 2026, rising to 11 to 14 percent in 2027. Time value of money and basic statistics are must-gets; regression output interpretation is the slow part.",
      지표: { 범위: "넓음" },
      선: "Present and future value, annuities, mean and standard deviation, and hypothesis test conclusions.",
      버림: "Multi-variable regression diagnostics.",
      예시: []
    },
    {
      이름: "Economics", 문항: 13, 배점: 13,
      역할: "방어",
      목표: 9, 목표문항: "9 of 13",
      이유: "Weighted 6 to 9 percent. The range is broad and the questions are conceptual, so the return on study time is lower than in FSA or Equity.",
      지표: { 범위: "넓음" },
      선: "Elasticity, market structures, and currency cross rates.",
      버림: "Detailed international trade policy effects.",
      예시: []
    },
    {
      이름: "Corp Issuers", 문항: 13, 배점: 13,
      역할: "기본",
      목표: 10, 목표문항: "10 of 13",
      이유: "Weighted 6 to 9 percent. Cost of capital and working capital measures reuse FSA skills.",
      지표: { 범위: "좁음" },
      선: "Weighted average cost of capital and cash conversion cycle.",
      버림: "",
      예시: []
    },
    {
      이름: "Derivatives", 문항: 11, 배점: 11,
      역할: "방어",
      목표: 8, 목표문항: "8 of 11",
      이유: "Weighted 5 to 8 percent, the smallest topic. Payoff diagrams and forward pricing are enough to clear it; deeper valuation belongs to Level II.",
      지표: { 범위: "좁음" },
      선: "Option payoffs and profit at expiration, forward price from spot and the risk-free rate.",
      버림: "Binomial valuation over more than one period.",
      예시: []
    }
  ],
  순서: [
    "Each session is 90 questions in about 135 minutes: 90 seconds a question. Answer every question on the first pass; there is no penalty for a wrong answer.",
    "Flag any calculation still unsolved at two minutes and move on. The last 15 minutes of each session go to flagged items."
  ],
  출처: ["CFA Institute, Level I exam (topic weights)", "CFA Institute, candidate examination results 1963 to 2026", "300hours, CFA passing score estimates (unofficial)"]
});
