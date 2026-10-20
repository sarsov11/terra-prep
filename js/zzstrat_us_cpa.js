/* Pass plan — US CPA, REG section (2026-10-20, Terra Prep) format: _형식.md
 * Points below are blueprint weight points (midpoint of each Area range, scaled to 100), not the 0-99 score scale. */
ZZSTRAT.add({
  id: "us_cpa",
  이름: "US CPA — REG",
  기준: "2026 blueprint",
  방식: "절대",
  한줄: "A 75 is not 75 percent. You need about two thirds of the weighted points, and over half of them sit in two Areas: individual and entity tax.",
  합격선: {
    설명: "Each section is scored 0 to 99 and 75 passes. There is no curve: AICPA converts your weighted raw performance to the scale, with multiple choice and task-based simulations each worth half of REG. You pass three Core sections (AUD, FAR, REG) plus one Discipline (BAR, ISC or TCP), each a separate 4-hour exam.",
    과락: "No per-Area minimum. The 75 is for the section as a whole",
    커트: [
      { 연도: 2025, 구분: "Raw share commonly estimated to reach 75", 점수: 65, 비고: "Estimate by review providers. AICPA publishes no conversion table", 출처: "Review-provider estimate" }
    ],
    가산점: [
      { 항목: "Discipline choice: TCP", 점수: "2025 pass rate 77.65%", 비고: "Overlaps REG tax content. BAR 41.94%, ISC 67.79%. AICPA notes Discipline rates reflect who chooses them" }
    ],
    목표: 75,
    만점: 100,
    목표근거: "Aim for 75 of the 100 weighted points. That sits ten points above the commonly estimated two-thirds threshold, so one bad simulation does not sink you. REG passed 63.12% of candidates in 2025 (62.61% in 2024), the highest of the three Core sections. Areas IV and V together are 45 to 65 percent of the exam, so the margin has to come from there."
  },
  과목: [
    {
      이름: "IV Individuals", 문항: 27, 배점: 27,
      역할: "전략",
      목표: 22, 목표문항: "22 of 27 points",
      이유: "Weighted 22 to 32 percent. Gross income, exclusions, basis, holding period and capital gain character repeat on almost every form, and each rule is a single Code section you can quote.",
      지표: { 범위: "보통" },
      선: "Gross income inclusions and exclusions (§61, §102, §103), holding period (§1222, §1223) and filing-status thresholds. These are the multiple choice you cannot miss.",
      버림: "",
      예시: [
        { 출처: "Terra Prep REG · Individuals", 발문: "An individual sells a capital asset that was purchased 14 months earlier, recognizing a gain. Under section 1222, this gain is classified as:", 선지: ["Section 1231 gain only", "A short-term capital gain because it was held less than 2 years", "Ordinary income under section 61", "A long-term capital gain because it was held more than 1 year"], 정답: 4,
          판정: "필수", 설명: "More than one year means long-term. The wrong choices swap in a two-year test or §1231, which applies to business property, not a capital asset." },
        { 출처: "Terra Prep REG · Individuals", 발문: "A taxpayer inherits stock, takes a basis under section 1014, and sells it 3 months after the decedent's death at a gain. Under section 1223(9), the gain is:", 선지: ["Ordinary income because inherited property is never a capital asset", "Not a capital gain because the holding period is too short", "Long-term because the taxpayer is deemed to have held the stock more than one year", "Short-term because the stock was held less than one year"], 정답: 3,
          판정: "승부", 설명: "Inherited property is long-term regardless of the actual holding period. Candidates who apply the plain one-year rule pick the short-term answer; this exception is where the Area IV points are decided." }
      ]
    },
    {
      이름: "V Entities", 문항: 28, 배점: 28,
      역할: "전략",
      목표: 21, 목표문항: "21 of 28 points",
      이유: "Weighted 23 to 33 percent, the largest Area. C corporation rate, the dividends-received deduction, §274 limits and depreciation lives are fixed numbers that show up in both multiple choice and simulations.",
      지표: { 범위: "넓음" },
      선: "The 21 percent corporate rate, the 50/65/100 DRD tiers, MACRS lives (27.5 and 39 years), and the meals and entertainment limits.",
      버림: "Multi-year partnership basis roll-forwards with special allocations take a full simulation's worth of time. Do them last.",
      예시: [
        { 출처: "Terra Prep REG · Entities", 발문: "Under IRC §11(b), what is the tax rate imposed on the taxable income of a C corporation?", 선지: ["15 percent", "21 percent", "35 percent", "28 percent"], 정답: 2,
          판정: "필수", 설명: "A flat 21 percent since 2018. The 35 percent choice is the old top rate and still catches people working from outdated material." },
        { 출처: "Terra Prep REG · Entities", 발문: "Under IRC §243(c)(1), what dividends-received deduction percentage applies to a dividend from a 20-percent owned corporation (not a qualifying dividend under (a)(3))?", 선지: ["80 percent", "100 percent", "65 percent", "50 percent"], 정답: 3,
          판정: "승부", 설명: "Twenty percent or more ownership gets 65; under 20 gets 50; affiliated groups get 100. The 80 is the pre-2018 figure. Knowing the current tiers cold separates a 75 from a 72." }
      ]
    },
    {
      이름: "II Business Law", 문항: 20, 배점: 20,
      역할: "방어",
      목표: 13, 목표문항: "13 of 20 points",
      이유: "Weighted 15 to 25 percent, but contracts, agency, debtor-creditor and entity formation are broad and reward memorization less than the tax Areas. Hold it near two thirds and earn the margin in IV and V.",
      지표: { 범위: "넓음" },
      선: "Contract formation and the statute of frauds, agency authority, and the basic liability of partners versus shareholders.",
      버림: "Fine points of secured-transaction priority between multiple perfected creditors.",
      예시: []
    },
    {
      이름: "I Ethics & Procedures", 문항: 15, 배점: 15,
      역할: "기본",
      목표: 11, 목표문항: "11 of 15 points",
      이유: "Weighted 10 to 20 percent. Circular 230 duties, preparer penalties and deficiency procedure deadlines are a short list of fixed numbers.",
      지표: { 범위: "좁음" },
      선: "The 90-day Tax Court petition window (150 days outside the US), assessment and refund statute periods, and Circular 230 due-diligence duties.",
      버림: "Appellate filing details for Tax Court decisions are tested rarely.",
      예시: [
        { 출처: "Terra Prep REG · Tax Procedures", 발문: "Which of the following statements regarding the notice of deficiency process is correct?", 선지: ["Once a notice of deficiency is mailed, the Secretary may immediately levy regardless of a Tax Court petition.", "A notice of deficiency may only be sent by first-class mail.", "A taxpayer generally has 90 days after a notice of deficiency is mailed to file a Tax Court petition, or 150 days if the notice is addressed to a person outside the United States.", "The Secretary may rescind a notice of deficiency without the consent of the taxpayer."], 정답: 3,
          판정: "필수", 설명: "Ninety days, or 150 outside the country, and no levy while the window is open. One number pair, asked every form." },
        { 출처: "Terra Prep REG · Tax Procedures", 발문: "Which of the following statements about filing a notice of appeal from a Tax Court decision under IRC §7483 is correct?", 선지: ["A notice of appeal must be filed within 30 days after the decision is entered.", "There is no time limit on filing a notice of appeal.", "A notice of appeal must be filed directly with the Supreme Court.", "If one party files a timely notice of appeal, any other party has 120 days after the decision is entered to file its own notice of appeal."], 정답: 4,
          판정: "버림", 설명: "The rule is 90 days, extended to 120 for the other party once one side appeals. It is correct and rarely asked; time spent here is better spent on the DRD or basis rules." }
      ]
    },
    {
      이름: "III Property", 문항: 10, 배점: 10,
      역할: "기본",
      목표: 8, 목표문항: "8 of 10 points",
      이유: "Weighted 5 to 15 percent. Cost basis, gift and inherited basis, wash sales and like-kind exchanges follow a few mechanical rules, so a high hit rate is realistic.",
      지표: { 범위: "좁음" },
      선: "Basis of gifted and inherited property, wash-sale basis carryover, and boot in a like-kind exchange.",
      버림: "",
      예시: [
        { 출처: "Terra Prep REG · Property Transactions", 발문: "Under IRC §1091(d), when a loss on the sale of stock is disallowed under the wash sale rules, the basis of the replacement stock is:", 선지: ["The basis of the stock sold, adjusted by the difference between the price paid for the replacement stock and the price at which the original stock was sold", "The purchase price of the replacement stock only", "Zero, because the loss was disallowed", "The fair market value of the replacement stock on the date acquired"], 정답: 1,
          판정: "승부", 설명: "The disallowed loss is not gone; it moves into the new shares' basis. Simulations ask you to compute it, so know the mechanics, not only the definition." }
      ]
    }
  ],
  순서: [
    "REG is 72 multiple choice in two testlets and 8 simulations in three. Finish each multiple-choice testlet in under 45 minutes to bank time for the simulations, which carry half the score.",
    "Never leave a simulation blank. Partial credit is awarded cell by cell, so fill every required cell before going back to a hard one."
  ],
  출처: ["AICPA, Learn more about CPA Exam scoring and pass rates", "AICPA 2025 quarterly pass rates", "REG blueprint Area weights effective 2026 (as reported by review providers)"]
});
