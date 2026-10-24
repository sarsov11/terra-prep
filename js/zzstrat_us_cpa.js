/* Pass plan — US CPA, REG (2026-10-21 revision, Terra Prep). Tier shares = Terra Prep REG bank by blueprint task (questions built from blueprint task mapping). Business Law has no bank items yet, so no tiers. Revised 2026-10-24 from YouTube instructor and candidate transcripts. */
ZZSTRAT.add({
  "id": "us_cpa",
  "이름": "US CPA — REG",
  "기준": "2026 blueprint",
  "방식": "절대",
  "한줄": "A 75 is not 75 percent. You need about two thirds of the weighted points, and over half of them sit in two Areas: individual and entity tax.",
  "합격선": {
    "설명": "Each section is scored 0 to 99 and 75 passes. There is no curve: AICPA converts your weighted raw performance to the scale, with multiple choice and task-based simulations each worth half of REG. You pass three Core sections (AUD, FAR, REG) plus one Discipline (BAR, ISC or TCP), each a separate 4-hour exam.",
    "과락": "No per-Area minimum. The 75 is for the section as a whole",
    "커트": [
      {
        "연도": 2025,
        "구분": "Raw share commonly estimated to reach 75",
        "점수": 65,
        "비고": "Estimate by review providers. AICPA publishes no conversion table",
        "출처": "Review-provider estimate"
      }
    ],
    "가산점": [
      {
        "항목": "Discipline choice: TCP",
        "점수": "2025 pass rate 77.65%",
        "비고": "Overlaps REG tax content. BAR 41.94%, ISC 67.79%. AICPA notes Discipline rates reflect who chooses them"
      }
    ],
    "목표": 78,
    "만점": 100,
    "목표근거": "Pick one of two targets. The estimated line is about 65 weighted points. REG passed 63.12% of candidates in 2025 (62.61% in 2024), the highest of the three Core sections. Areas IV and V together are 45 to 65 percent of the exam, so the margin has to come from there."
  },
  "선택": [
    {
      "id": "edge",
      "이름": "Just clear the line",
      "목표": 68,
      "설명": "Three points above the commonly estimated two-thirds line. Study Individuals and Entities hard, give Business Law one pass with its multiple choice, and guess on the rest.",
      "범위": {
        "S": "전부",
        "A": "전부",
        "B": "간단",
        "C": "찍기"
      },
      "근거": "At 68 one bad simulation can drop you under the line, and Business Law has no slack in this plan."
    },
    {
      "id": "safe",
      "이름": "Clear with room",
      "목표": 78,
      "설명": "Thirteen points above the estimated line. Cover B content in every Area, practise simulations on top of multiple choice, and skim the short C items.",
      "범위": {
        "S": "전부",
        "A": "전부",
        "B": "전부",
        "C": "간단"
      },
      "근거": "At 78 you can lose a full simulation's worth of points and still pass."
    }
  ],
  "과목": [
    {
      "이름": "IV Individuals",
      "문항": 27,
      "배점": 27,
      "역할": "전략",
      "목표": 23,
      "목표문항": "23 of 27 points",
      "이유": "Weighted 22 to 32 percent, and together with Entities it is over 60 percent of the exam, so most study hours go here. Every question sits on one line of Form 1040: gross income, adjustments to AGI, deductions, credits.",
      "지표": {
        "범위": "보통"
      },
      "선": "Gross income inclusions and exclusions (§61, §102, §103), holding period (§1222, §1223) and filing-status thresholds. These are the multiple choice you cannot miss.",
      "버림": "",
      "예시": [
        {
          "출처": "Terra Prep REG · Individuals",
          "발문": "An individual sells a capital asset that was purchased 14 months earlier, recognizing a gain. Under section 1222, this gain is classified as:",
          "선지": [
            "Section 1231 gain only",
            "A short-term capital gain because it was held less than 2 years",
            "Ordinary income under section 61",
            "A long-term capital gain because it was held more than 1 year"
          ],
          "정답": 4,
          "판정": "필수",
          "설명": "More than one year means long-term. The wrong choices swap in a two-year test or §1231, which applies to business property, not a capital asset."
        },
        {
          "출처": "Terra Prep REG · Individuals",
          "발문": "A taxpayer inherits stock, takes a basis under section 1014, and sells it 3 months after the decedent's death at a gain. Under section 1223(9), the gain is:",
          "선지": [
            "Ordinary income because inherited property is never a capital asset",
            "Not a capital gain because the holding period is too short",
            "Long-term because the taxpayer is deemed to have held the stock more than one year",
            "Short-term because the stock was held less than one year"
          ],
          "정답": 3,
          "판정": "승부",
          "설명": "Inherited property is long-term regardless of the actual holding period. Candidates who apply the plain one-year rule pick the short-term answer; this exception is where the Area IV points are decided."
        }
      ],
      "목표선택": {
        "edge": 20,
        "safe": 23
      },
      "목표문항선택": {
        "edge": "20 of 27 points",
        "safe": "23 of 27 points"
      },
      "등급": {
        "S": "Gross income: inclusions and exclusions (25%)",
        "A": "Adjustments and deductions, loss limitations (37%)",
        "B": "Filing status, tax computation and credits (32%)",
        "C": "Items from pass-through entities (6%)"
      },
      "조언선택": {
        "edge": "Know every inclusion and exclusion section and the loss limitation order (basis, at-risk, passive). Filing status thresholds are one table; read it once.",
        "safe": "Add credits and the tax computation steps so you can finish a Form 1040 simulation without guessing."
      }
    },
    {
      "이름": "V Entities",
      "문항": 28,
      "배점": 28,
      "역할": "전략",
      "목표": 22,
      "목표문항": "22 of 28 points",
      "이유": "Weighted 23 to 33 percent, the largest Area; Breezy Smiles, who passed first try, calls entity tax the material she had to learn almost from scratch. Partnership basis and the S corporation rules come up as simulations, not only as multiple choice.",
      "지표": {
        "범위": "넓음"
      },
      "선": "Partnership basis (debt raises it, S corporation debt does not), ordinary income versus separately stated items, S election eligibility, and the 21 percent corporate rate.",
      "버림": "Multi-year partnership basis roll-forwards with special allocations take a full simulation's worth of time. Do them last.",
      "예시": [
        {
          "출처": "Terra Prep REG · Entities",
          "발문": "Under IRC §11(b), what is the tax rate imposed on the taxable income of a C corporation?",
          "선지": [
            "15 percent",
            "21 percent",
            "35 percent",
            "28 percent"
          ],
          "정답": 2,
          "판정": "필수",
          "설명": "A flat 21 percent since 2018. The 35 percent choice is the old top rate and still catches people working from outdated material."
        },
        {
          "출처": "Terra Prep REG · Entities",
          "발문": "Under IRC §243(c)(1), what dividends-received deduction percentage applies to a dividend from a 20-percent owned corporation (not a qualifying dividend under (a)(3))?",
          "선지": [
            "80 percent",
            "100 percent",
            "65 percent",
            "50 percent"
          ],
          "정답": 3,
          "판정": "승부",
          "설명": "Twenty percent or more ownership gets 65; under 20 gets 50; affiliated groups get 100. The 80 is the pre-2018 figure. Knowing the current tiers cold separates a 75 from a 72."
        }
      ],
      "목표선택": {
        "edge": 19,
        "safe": 22
      },
      "목표문항선택": {
        "edge": "19 of 28 points",
        "safe": "22 of 28 points"
      },
      "등급": {
        "S": "C corporation taxable income and tax; S corporation eligibility and election (40%)",
        "A": "S corporation income items and shareholder basis (25%)",
        "B": "Partnership income and partner basis; book-tax differences (21%)",
        "C": "Tax-exempt organizations, LLCs (14%)"
      },
      "조언선택": {
        "edge": "Learn the C corporation computation and the S election rules cold. For partnerships, know only the basis formula.",
        "safe": "Add partnership basis roll-forwards and the Schedule M-1 reconciliation, which both show up as simulations."
      }
    },
    {
      "이름": "II Business Law",
      "문항": 20,
      "배점": 20,
      "역할": "방어",
      "목표": 14,
      "목표문항": "14 of 20 points",
      "이유": "Weighted 15 to 25 percent and tested mostly as recall. Two candidates who failed REG once name Business Law as what cost them; one pass through the material plus its multiple choice is what passers describe.",
      "지표": {
        "범위": "넓음"
      },
      "선": "Contract formation and the statute of frauds, agency authority, and the basic liability of partners versus shareholders.",
      "버림": "Fine points of secured-transaction priority between multiple perfected creditors.",
      "예시": [],
      "목표선택": {
        "edge": 11,
        "safe": 14
      },
      "목표문항선택": {
        "edge": "11 of 20 points",
        "safe": "14 of 20 points"
      },
      "조언선택": {
        "edge": "Contract formation, agency authority and partner versus shareholder liability. Guess on secured-transaction priority.",
        "safe": "Add debtor-creditor rules and the basics of entity formation."
      }
    },
    {
      "이름": "I Ethics & Procedures",
      "문항": 15,
      "배점": 15,
      "역할": "기본",
      "목표": 11,
      "목표문항": "11 of 15 points",
      "이유": "Weighted 10 to 20 percent and tested as recall: Circular 230, preparer versus taxpayer penalties, deficiency deadlines. Passers call it easier than the ethics in AUD.",
      "지표": {
        "범위": "좁음"
      },
      "선": "The 90-day Tax Court petition window (150 days outside the US), assessment and refund statute periods, and Circular 230 due-diligence duties.",
      "버림": "Appellate filing details for Tax Court decisions are tested rarely.",
      "예시": [
        {
          "출처": "Terra Prep REG · Tax Procedures",
          "발문": "Which of the following statements regarding the notice of deficiency process is correct?",
          "선지": [
            "Once a notice of deficiency is mailed, the Secretary may immediately levy regardless of a Tax Court petition.",
            "A notice of deficiency may only be sent by first-class mail.",
            "A taxpayer generally has 90 days after a notice of deficiency is mailed to file a Tax Court petition, or 150 days if the notice is addressed to a person outside the United States.",
            "The Secretary may rescind a notice of deficiency without the consent of the taxpayer."
          ],
          "정답": 3,
          "판정": "필수",
          "설명": "Ninety days, or 150 outside the country, and no levy while the window is open. One number pair, asked every form."
        },
        {
          "출처": "Terra Prep REG · Tax Procedures",
          "발문": "Which of the following statements about filing a notice of appeal from a Tax Court decision under IRC §7483 is correct?",
          "선지": [
            "A notice of appeal must be filed within 30 days after the decision is entered.",
            "There is no time limit on filing a notice of appeal.",
            "A notice of appeal must be filed directly with the Supreme Court.",
            "If one party files a timely notice of appeal, any other party has 120 days after the decision is entered to file its own notice of appeal."
          ],
          "정답": 4,
          "판정": "버림",
          "설명": "The rule is 90 days, extended to 120 for the other party once one side appeals. It is correct and rarely asked; time spent here is better spent on the DRD or basis rules."
        }
      ],
      "목표선택": {
        "edge": 10,
        "safe": 11
      },
      "목표문항선택": {
        "edge": "10 of 15 points",
        "safe": "11 of 15 points"
      },
      "등급": {
        "S": "Substantiation and disclosure (40%)",
        "A": "Audits, appeals and the judicial process (32%)",
        "B": "Taxpayer penalties (28%)"
      },
      "조언선택": {
        "edge": "Know the deficiency-notice deadlines and the disclosure rules. Penalty percentages can be guessed if time is short.",
        "safe": "Learn the penalty rates and the Circular 230 duties as well."
      }
    },
    {
      "이름": "III Property",
      "문항": 10,
      "배점": 10,
      "역할": "기본",
      "목표": 8,
      "목표문항": "8 of 10 points",
      "이유": "Weighted 5 to 15 percent. Cost basis, gift and inherited basis, wash sales and like-kind exchanges follow a few mechanical rules, so a high hit rate is realistic.",
      "지표": {
        "범위": "좁음"
      },
      "선": "Basis of gifted and inherited property, wash-sale basis carryover, and boot in a like-kind exchange.",
      "버림": "",
      "예시": [
        {
          "출처": "Terra Prep REG · Property Transactions",
          "발문": "Under IRC §1091(d), when a loss on the sale of stock is disallowed under the wash sale rules, the basis of the replacement stock is:",
          "선지": [
            "The basis of the stock sold, adjusted by the difference between the price paid for the replacement stock and the price at which the original stock was sold",
            "The purchase price of the replacement stock only",
            "Zero, because the loss was disallowed",
            "The fair market value of the replacement stock on the date acquired"
          ],
          "정답": 1,
          "판정": "승부",
          "설명": "The disallowed loss is not gone; it moves into the new shares' basis. Simulations ask you to compute it, so know the mechanics, not only the definition."
        }
      ],
      "목표선택": {
        "edge": 8,
        "safe": 8
      },
      "목표문항선택": {
        "edge": "8 of 10 points",
        "safe": "8 of 10 points"
      },
      "등급": {
        "S": "Basis of assets (53%)",
        "A": "Cost recovery: depreciation and amortization (47%)"
      },
      "조언선택": {
        "edge": "Gifted, inherited and wash-sale basis, plus MACRS lives. This Area is small and mechanical; do not leave points here.",
        "safe": "Same scope. Add like-kind exchange boot so a simulation cannot surprise you."
      }
    }
  ],
  "순서": [
    "Passers report 110 to 140 hours over 4 to 8 weeks. Review-course mocks grade harder than the real exam: candidates scoring 58 to 69 percent on mocks passed with 78 to 81.",
    "REG has the most multiple choice of any section. Finish each multiple-choice testlet in under 45 minutes, cap any simulation at 25 to 30 minutes, and reach every simulation, since partial credit counts and one is an unscored pretest."
  ],
  "출처": [
    "AICPA, Learn more about CPA Exam scoring and pass rates",
    "AICPA 2025 quarterly pass rates",
    "REG blueprint Area weights effective 2026 (as reported by review providers)",
    "YouTube instructor and candidate videos (10 transcripts read)"
  ],
  "근거영상": [
    {
      "url": "https://www.youtube.com/watch?v=GWOHAK9tbUI",
      "누구": "Maxwell CPA Review (scored 91)",
      "요지": "Individual and entity tax are over 60% of REG; spend most hours there. 140 hours in 7-8 weeks: 2.5 h of new material on weeknights, 5 h of practice each weekend day"
    },
    {
      "url": "https://www.youtube.com/watch?v=zQ2JslDQMXE",
      "누구": "Maxwell CPA Review",
      "요지": "Partnership basis, ordinary income vs separately stated items, cash-to-accrual and above- vs below-the-line deductions show up on every form"
    },
    {
      "url": "https://www.youtube.com/watch?v=opZc-6o8J3g",
      "누구": "Breezy Smiles (passed REG first try)",
      "요지": "Since 2024 the harder property and 1231/1245/1250 topics moved to TCP. Inflation-adjusted amounts are given on the exam, so learn how to use them, not the numbers"
    },
    {
      "url": "https://www.youtube.com/watch?v=TVh_dGSFYjg",
      "누구": "Just Effa (failed once, then passed with her highest score)",
      "요지": "Do not underestimate Business Law: it is a small share of the material but carries many questions"
    },
    {
      "url": "https://www.youtube.com/watch?v=cveET72a6V8",
      "누구": "Punto Base (passed in 4 weeks, scored 81)",
      "요지": "Business Law is a quarter of the material; one pass plus multiple choice is enough. REG has the most MCQs and ran closest to time. Mock 69 led to an 81"
    },
    {
      "url": "https://www.youtube.com/watch?v=U_pqVj80CFc",
      "누구": "Sean Todd (78 in 20 days)",
      "요지": "Mock exams scored 58% and the real exam 78; review mocks grade harder than the real exam. Aim for about 75% per section in practice"
    },
    {
      "url": "https://www.youtube.com/watch?v=Xc3n0uavmXg",
      "누구": "Lindsey Davis (passed in 1 month)",
      "요지": "Multiple choice did most of the work; 3 weeks of new material, the 4th week for mocks and MCQ review"
    },
    {
      "url": "https://www.youtube.com/watch?v=KY6Ay-EFXpA",
      "누구": "Breezy Smiles",
      "요지": "Cap a document-review simulation at 25-30 minutes and reach every simulation; one simulation is an unscored pretest"
    }
  ]
});
