/* Pass plan — CFA Level I (2026-10-21 revision, Terra Prep). Topic tiers = official 2026 topic weights. Ethics inner tiers = share of Standards in the Terra Prep Ethics bank. Revised 2026-10-25 from YouTube candidate transcripts. */
ZZSTRAT.add({
  "id": "us_cfa",
  "이름": "CFA Level I",
  "기준": "2026 topic weights",
  "방식": "상대",
  "한줄": "The estimated pass line has sat near 69 percent for the last several windows. Ethics, FSA, Equity and Fixed Income are 97 of the 180 questions, and that is where either target is won.",
  "이야기": [
    "Level I is **180** three-option questions in two sessions, with no penalty for a wrong answer.",
    "The pass line is not published. Outside estimates put it near **69%**, about **125** questions.",
    "Ethics, FSA, Equity and Fixed Income are **97** of the 180 questions. Either target is won there.",
    "Fixed Income, FSA, Portfolio Management, Quant and Derivatives are the topics passers rank hardest.",
    "Equity, Alternatives and Corporate Issuers are the easy marks. Take every one of them.",
    "Start with Quant for time value of money. Finish with Economics and Ethics, which are memorization.",
    "You get about **90 seconds** a question. Strike out, flag, move on, and leave nothing blank.",
    "Passers report about **300 hours** over three to seven months."
  ],
  "합격선": {
    "설명": "180 three-option questions in two sessions of 90, about 135 minutes each, with no penalty for wrong answers. CFA Institute sets a minimum passing score for each window and does not publish it; your score report only shows where it fell. There is no per-topic minimum.",
    "과락": "No per-topic minimum. One overall pass line per exam window",
    "커트": [
      {
        "연도": 2025,
        "구분": "Nov window, estimated MPS",
        "점수": 124,
        "비고": "About 69.0% of 180. 300hours estimate, not official",
        "출처": "300hours"
      },
      {
        "연도": 2026,
        "구분": "Feb window, estimated MPS",
        "점수": 125,
        "비고": "About 69.5%. Estimate",
        "출처": "300hours"
      },
      {
        "연도": 2026,
        "구분": "May window, estimated MPS",
        "점수": 124,
        "비고": "About 69.0%. Estimate",
        "출처": "300hours"
      }
    ],
    "가산점": [],
    "목표": 140,
    "만점": 180,
    "목표근거": "Pick one of two targets. Recent estimated pass lines are 124 to 125 of 180 (300hours, unofficial). Official pass rates were 43 to 45 percent in 2025 and 39 to 45 percent in 2026."
  },
  "선택": [
    {
      "id": "edge",
      "이름": "Just clear the line",
      "목표": 128,
      "설명": "Three above the highest recent estimated pass line (125). Learn the S and A topics fully, skim the B topics, guess on Derivatives.",
      "범위": {
        "S": "전부",
        "A": "전부",
        "B": "간단",
        "C": "찍기"
      },
      "근거": "128 leaves three questions of margin, and the line moves by window. A hard Fixed Income section can erase that margin on its own."
    },
    {
      "id": "safe",
      "이름": "Clear with room",
      "목표": 140,
      "설명": "Fifteen above the highest recent estimate, 78 percent. Every topic gets full study except the deeper parts of Derivatives.",
      "범위": {
        "S": "전부",
        "A": "전부",
        "B": "전부",
        "C": "간단"
      },
      "근거": "At 140 you can miss ten more questions than planned and still clear every recent estimated line."
    }
  ],
  "과목": [
    {
      "이름": "Ethics",
      "문항": 31,
      "배점": 31,
      "역할": "전략",
      "목표": 26,
      "목표문항": "26 of 31",
      "이유": "Weighted 15 to 20 percent, the single largest topic in 2026, and pure reading with no calculator. Passers leave it for last so the Standards are fresh on exam day. Instructors also say Ethics decides candidates who sit right at the line; CFA Institute has not confirmed this.",
      "지표": {
        "범위": "좁음"
      },
      "선": "Loyalty to the ultimate beneficiary, fair dealing in allocations and recommendations, and the mosaic theory under material nonpublic information.",
      "버림": "",
      "예시": [
        {
          "출처": "Terra Prep CFA · Standard III(A)",
          "발문": "A member manages the assets of a company pension plan. According to the guidance under Standard III(A), to whom is the member's duty of loyalty owed?",
          "선지": [
            "The plan's board of directors exclusively, regardless of beneficiary interests",
            "The ultimate beneficiaries of the pension plan",
            "The company that established and hired the manager for the pension plan"
          ],
          "정답": 2,
          "판정": "필수",
          "설명": "Loyalty runs to the beneficiaries, not to whoever hired you. The same principle covers trusts, so one rule answers a family of questions."
        },
        {
          "출처": "Terra Prep CFA · Standard III(B)",
          "발문": "An analyst mentions his firm's upcoming purchase recommendation to several of his best clients over lunch, a week before the report is sent to all clients. This is BEST described as a violation of Standard III(B) because:",
          "선지": [
            "Standard III(B) requires that recommendations be communicated to all clients equally rather than fairly",
            "Selectively disclosing the recommendation to favored clients in advance denies other clients a fair opportunity to act on it",
            "Analysts are never permitted to discuss research with clients before publication under any circumstances"
          ],
          "정답": 2,
          "판정": "승부",
          "설명": "The Standard says fairly, not equally. The first choice uses the wrong word on purpose; candidates who read for the gist instead of the wording lose this point."
        },
        {
          "출처": "Terra Prep CFA · Standard III(B)",
          "발문": "When a new issue offered to a firm's clients is oversubscribed, Standard III(B) guidance indicates that members should MOST appropriately:",
          "선지": [
            "Fill their own and immediate family members' orders first",
            "Prorate the issue among all suitable client accounts and forgo sales to themselves or immediate family",
            "Allocate the full amount to whichever clients placed their orders first, regardless of suitability"
          ],
          "정답": 2,
          "판정": "필수",
          "설명": "Clients first, prorated, family last. Allocation questions use this answer pattern every window."
        }
      ],
      "목표선택": {
        "edge": 25,
        "safe": 26
      },
      "목표문항선택": {
        "edge": "25 of 31",
        "safe": "26 of 31"
      },
      "등급": {
        "S": "Standard I Professionalism, Standard III Duties to Clients (43%)",
        "A": "Standards IV, V and VI: employers, analysis, conflicts (39%)",
        "B": "Standard II Market integrity, Standard VII CFA membership (17%)"
      },
      "조언선택": {
        "edge": "Work the guidance cases for Standards I and III until the wording traps (fairly versus equally) stop catching you.",
        "safe": "Cover all seven Standards and the recommended procedures for compliance."
      }
    },
    {
      "이름": "FSA",
      "문항": 22,
      "배점": 22,
      "역할": "전략",
      "목표": 18,
      "목표문항": "18 of 22",
      "이유": "Weighted 11 to 14 percent. Inventory methods, ratio effects and cash-flow classification are mechanical once learned, and the same mechanics feed Equity and Corporate Issuers questions.",
      "지표": {
        "범위": "넓음"
      },
      "선": "FIFO versus LIFO effects in rising prices, operating versus investing versus financing cash flows, and the direction of each common ratio.",
      "버림": "Multi-step deferred tax reconciliations. Mark and return.",
      "예시": [],
      "목표선택": {
        "edge": 17,
        "safe": 18
      },
      "목표문항선택": {
        "edge": "17 of 22",
        "safe": "18 of 22"
      },
      "등급": {
        "S": "Whole topic (weight 11 to 14 percent)"
      },
      "조언선택": {
        "edge": "Inventory, cash-flow classification and ratio direction. Skip multi-step deferred tax items.",
        "safe": "Add deferred taxes, leases and long-lived asset impairment."
      }
    },
    {
      "이름": "Equity",
      "문항": 22,
      "배점": 22,
      "역할": "기본",
      "목표": 18,
      "목표문항": "18 of 22",
      "이유": "Weighted 11 to 14 percent, and passers call it one of the easier topics to score on. Index construction and the dividend discount model are short calculations with fixed formulas.",
      "지표": {
        "범위": "보통"
      },
      "선": "Gordon growth valuation, price-weighted versus market-cap index returns, and margin call price.",
      "버림": "",
      "예시": [],
      "목표선택": {
        "edge": 17,
        "safe": 18
      },
      "목표문항선택": {
        "edge": "17 of 22",
        "safe": "18 of 22"
      },
      "등급": {
        "S": "Whole topic (weight 11 to 14 percent)"
      },
      "조언선택": {
        "edge": "Dividend discount model, index weighting and margin calls.",
        "safe": "Add industry analysis and the multiples approaches."
      }
    },
    {
      "이름": "Fixed Income",
      "문항": 22,
      "배점": 22,
      "역할": "기본",
      "목표": 16,
      "목표문항": "16 of 22",
      "이유": "Weighted 11 to 14 percent and one of the five topics passers rank hardest. It reuses the time value of money from Quant; bond pricing and duration are worth learning cold, while securitization detail is where time runs out.",
      "지표": {
        "범위": "넓음"
      },
      "선": "Price from yield, the price-yield relationship, and modified duration for a price change estimate.",
      "버림": "Long securitization structure questions with several tranches. Answer last.",
      "예시": [],
      "목표선택": {
        "edge": 15,
        "safe": 16
      },
      "목표문항선택": {
        "edge": "15 of 22",
        "safe": "16 of 22"
      },
      "등급": {
        "S": "Whole topic (weight 11 to 14 percent)"
      },
      "조언선택": {
        "edge": "Price from yield, duration and convexity estimates. Leave securitization structures for last.",
        "safe": "Add credit analysis and the securitization basics."
      }
    },
    {
      "이름": "Portfolio Mgmt",
      "문항": 18,
      "배점": 18,
      "역할": "기본",
      "목표": 15,
      "목표문항": "15 of 18",
      "이유": "Weighted 8 to 12 percent. CAPM, the security market line and the investment policy statement components repeat in nearly identical form.",
      "지표": {
        "범위": "보통"
      },
      "선": "CAPM expected return, systematic versus unsystematic risk, and IPS objectives and constraints.",
      "버림": "",
      "예시": [],
      "목표선택": {
        "edge": 14,
        "safe": 15
      },
      "목표문항선택": {
        "edge": "14 of 18",
        "safe": "15 of 18"
      },
      "등급": {
        "A": "Whole topic (weight 8 to 12 percent)"
      },
      "조언선택": {
        "edge": "CAPM, the security market line and IPS components.",
        "safe": "Add behavioral biases and risk management terms."
      }
    },
    {
      "이름": "Alternatives",
      "문항": 15,
      "배점": 15,
      "역할": "기본",
      "목표": 12,
      "목표문항": "12 of 15",
      "이유": "Weighted 7 to 10 percent. Fee waterfalls and the basic features of private equity, real estate and hedge funds are a contained list.",
      "지표": {
        "범위": "좁음"
      },
      "선": "Management and incentive fee calculations with a hurdle and high-water mark.",
      "버림": "",
      "예시": [],
      "목표선택": {
        "edge": 11,
        "safe": 12
      },
      "목표문항선택": {
        "edge": "11 of 15",
        "safe": "12 of 15"
      },
      "등급": {
        "A": "Whole topic (weight 7 to 10 percent)"
      },
      "조언선택": {
        "edge": "Fee calculations with hurdle and high-water mark.",
        "safe": "Add real estate and commodity return components."
      }
    },
    {
      "이름": "Quant",
      "문항": 13,
      "배점": 13,
      "역할": "방어",
      "목표": 10,
      "목표문항": "10 of 13",
      "이유": "Weighted 6 to 9 percent in 2026, rising to 11 to 14 percent in 2027. Study it first: time value of money runs through Fixed Income, Equity and Corporate Issuers. The statistics half matters mainly for Portfolio Management.",
      "지표": {
        "범위": "넓음"
      },
      "선": "Present and future value, annuities, mean and standard deviation, and hypothesis test conclusions.",
      "버림": "Multi-variable regression diagnostics.",
      "예시": [],
      "목표선택": {
        "edge": 8,
        "safe": 10
      },
      "목표문항선택": {
        "edge": "8 of 13",
        "safe": "10 of 13"
      },
      "등급": {
        "B": "Whole topic (weight 6 to 9 percent in 2026, 11 to 14 in 2027)"
      },
      "조언선택": {
        "edge": "Time value of money and basic statistics only.",
        "safe": "Add hypothesis testing and simple regression output."
      }
    },
    {
      "이름": "Economics",
      "문항": 13,
      "배점": 13,
      "역할": "방어",
      "목표": 8,
      "목표문항": "8 of 13",
      "이유": "Weighted 6 to 9 percent. The range is broad and the questions are conceptual, so the return on study time is lower than in FSA or Equity.",
      "지표": {
        "범위": "넓음"
      },
      "선": "Elasticity, market structures, and currency cross rates.",
      "버림": "Detailed international trade policy effects.",
      "예시": [],
      "목표선택": {
        "edge": 8,
        "safe": 8
      },
      "목표문항선택": {
        "edge": "8 of 13",
        "safe": "8 of 13"
      },
      "등급": {
        "B": "Whole topic (weight 6 to 9 percent)"
      },
      "조언선택": {
        "edge": "Elasticity, market structures and currency cross rates.",
        "safe": "Same scope plus monetary and fiscal policy effects."
      }
    },
    {
      "이름": "Corp Issuers",
      "문항": 13,
      "배점": 13,
      "역할": "기본",
      "목표": 10,
      "목표문항": "10 of 13",
      "이유": "Weighted 6 to 9 percent, but passers count it among the easy marks with Equity and Alternatives. Cost of capital and working capital reuse FSA skills.",
      "지표": {
        "범위": "좁음"
      },
      "선": "Weighted average cost of capital and cash conversion cycle.",
      "버림": "",
      "예시": [],
      "목표선택": {
        "edge": 9,
        "safe": 10
      },
      "목표문항선택": {
        "edge": "9 of 13",
        "safe": "10 of 13"
      },
      "등급": {
        "A": "Whole topic (weight 6 to 9 percent; passers count it among the easy marks)"
      },
      "조언선택": {
        "edge": "WACC and the cash conversion cycle.",
        "safe": "Add capital structure and governance terms."
      }
    },
    {
      "이름": "Derivatives",
      "문항": 11,
      "배점": 11,
      "역할": "방어",
      "목표": 7,
      "목표문항": "7 of 11",
      "이유": "Weighted 5 to 8 percent, the smallest topic, and passers say it slows people down. Payoff diagrams and forward pricing are enough to clear it; move on if it eats your time.",
      "지표": {
        "범위": "좁음"
      },
      "선": "Option payoffs and profit at expiration, forward price from spot and the risk-free rate.",
      "버림": "Binomial valuation over more than one period.",
      "예시": [],
      "목표선택": {
        "edge": 4,
        "safe": 7
      },
      "목표문항선택": {
        "edge": "4 of 11",
        "safe": "7 of 11"
      },
      "등급": {
        "C": "Whole topic (weight 5 to 8 percent)"
      },
      "조언선택": {
        "edge": "Guess. With three options a guess is worth a third of a point.",
        "safe": "Option payoffs at expiration and forward pricing only."
      }
    }
  ],
  "순서": [
    "Passers report about 300 hours, one as many as 400, over three to seven months: 1 hour on weekdays and 3 hours on weekend days, rising to 4 to 5 hours a day in the final month. Mocks go in the last four to eight weeks.",
    "Each session is 90 questions in about 135 minutes, 90 seconds a question. Strike out what you can, flag anything still open, and move on; come back once 60 to 70 percent of the session is done. There is no penalty for a wrong answer, so leave nothing blank."
  ],
  "출처": [
    "CFA Institute, Level I exam (topic weights)",
    "CFA Institute, candidate examination results 1963 to 2026",
    "300hours, CFA passing score estimates (unofficial)",
    "YouTube candidate videos (4 transcripts read, 3 of them from speech-to-text)"
  ],
  "근거영상": [
    {
      "url": "https://www.youtube.com/watch?v=VKVN5LQlU8c",
      "누구": "Haaris Zamir, CFA (90th percentile)",
      "요지": "Fixed Income, FSA, Portfolio Management, Quant and Derivatives are the hardest; Equity, Alternatives and Corporate Issuers are easy marks. Start with Quant for time value of money, end with Economics and Ethics. 90 seconds a question: strike out, flag, move on"
    },
    {
      "url": "https://www.youtube.com/watch?v=DhXMBF2b5go",
      "누구": "Brandon Hill (95th percentile, cleared 70% in all 10 topics)",
      "요지": "About 400 hours over 6 months: 1-2 h a day early, 2-3 h from three months out, 4-5 h a day in the final month. 3,000 Kaplan questions and one mock a week in the last month"
    },
    {
      "url": "https://www.youtube.com/watch?v=ek0D6tn3sNU",
      "누구": "JM Invest (90th percentile)",
      "요지": "Six to seven months at 1 hour each weekday and 3 hours each weekend day. Mocks from 7-8 weeks out; with a curriculum this broad, one or two mocks prove little"
    },
    {
      "url": "https://www.youtube.com/watch?v=trWCvWqWUJg",
      "누구": "Sarah Sivan (passed first attempt)",
      "요지": "300 hours is the rule of thumb; give Level I at least three months. Learn the BA II Plus functions cold, since there are about 90 seconds per question. CFA Institute mocks match the real difficulty"
    }
  ]
});
