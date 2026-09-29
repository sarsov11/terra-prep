# Area IV (개인 과세) 7개
from tbs_lib import *
from tbs_items_1 import IRC, L

ITEMS = []

BRACKETS = X("e_rates", "2026 tax rate schedule: single (assumed for this exercise)", "table",
             [["Taxable income over", "But not over", "Rate"],
              ["$0", "$12,400", "10%"], ["$12,400", "$50,400", "12%"], ["$50,400", "$105,700", "22%"],
              ["$105,700", "$201,775", "24%"], ["$201,775", "$256,225", "32%"], ["$256,225", "$640,600", "35%"], ["$640,600", "-", "37%"]])

# ---------------------------------------------------------------- IV-T-012 numeric: Form 1040 walk-through with AOC split
ITEMS.append(T(
    "REG-IV-T-012", "IV", "numeric_table",
    "Form 1040: from income to refund, with the American opportunity credit",
    "Marcus Bell is single with no dependents. For 2026 he was a salaried employee and pursued a bachelor's degree part-time. "
    "Assume his modified AGI equals his AGI, and he is eligible for every deduction and credit shown in Exhibit 1.",
    "Complete the 2026 Form 1040 for Marcus using the exhibits. Round to the nearest dollar.",
    [X("e1", "Tax data", "return_excerpt",
       [["Wages (Form W-2, box 1)", "${wages:,}"], ["Taxable interest", "${interest:,}"], ["Health savings account deduction", "${hsa:,}"],
        ["Student loan interest deduction (fully allowed)", "${sli:,}"], ["Standard deduction, single (2026)", "${std:,}"],
        ["American opportunity credit before the refundable split (Form 8863, line 7)", "${aoc:,}"], ["Federal income tax withheld", "${wh:,}"]]),
     BRACKETS],
    [N("c1", "Total income", "wages+interest", "Total income = wages + taxable interest.", ["${wages:,} + ${interest:,} = ${c1:,}"], ["Which items are income and which are adjustments?", "Adjustments come after total income."]),
     N("c2", "Adjusted gross income", "c1-hsa-sli", "AGI = total income minus above-the-line adjustments (HSA deduction and student loan interest deduction).", ["${c1:,} - ${hsa:,} - ${sli:,} = ${c2:,}"], ["Both deductions are adjustments to income.", "Subtract both from total income."],
       traps=[("c1", "You did not subtract the adjustments.")]),
     N("c3", "Taxable income", "c2-std", "Taxable income = AGI - standard deduction.", ["${c2:,} - ${std:,} = ${c3:,}"], ["Marcus does not itemize.", "Subtract the standard deduction."]),
     N("c4", "Regular income tax", "tax_s(c3)", "Apply the bracket schedule to ${c3:,}.", ["10% x $12,400 = $1,240", "12% x ($50,400 - $12,400) = $4,560", "22% x (${c3:,} - $50,400) = ${t22:,}", "Total = ${c4:,}"], ["Use the schedule marginally.", "Fill 10% and 12% brackets first, then 22% on the rest."],
       traps=[("c3*0.22", "You applied a flat 22% to all taxable income.")]),
     N("c5", "Nonrefundable portion of the American opportunity credit", "0.6*aoc", "Only 60% of the credit is nonrefundable; 40% (up to $1,000) is refundable.", ["60% x ${aoc:,} = ${c5:,}"], ["The credit is split.", "60% nonrefundable, 40% refundable."],
       traps=[("aoc", "You treated the entire credit as nonrefundable.")]),
     N("c6", "Total tax after the nonrefundable credit", "c4-c5", "Total tax = regular tax - nonrefundable credit.", ["${c4:,} - ${c5:,} = ${c6:,}"], ["Subtract the nonrefundable credit from the regular tax.", "Use your answers for cells 4 and 5."]),
     N("c7", "Refundable portion of the American opportunity credit", "0.4*aoc", "40% of the credit is refundable (limited to $1,000), Form 8863 line 8.", ["40% x ${aoc:,} = ${c7:,}"], ["It is added to payments.", "40% of the credit, at most $1,000."]),
     N("c8", "Refund (or balance due as a negative number)", "wh+c7-c6", "Refund = withholding + refundable credit - total tax.", ["${wh:,} + ${c7:,} - ${c6:,} = ${c8:,}"], ["Payments include withholding and refundable credits.", "Payments less total tax."],
       traps=[("wh-c6", "You omitted the refundable part of the credit.")])],
    {"wages": 78400, "interest": 1250, "hsa": 3000, "sli": 2000, "std": 16100, "aoc": 2500, "wh": 8100},
    {"area": "IV", "group": "A", "topic": "Form 1040 computation", "task": "Compute taxable income, tax, credits, and refund", "skill": "Application"},
    2, 14, cite=["IRC §62", "IRC §63(c)", "IRC §25A(i)", "IRC §1(j)", "Form 8863"],
    vary={"wages": [72000, 75000, 78400], "wh": [7000, 8100, 9000], "sli": [1500, 2000, 2500], "hsa": [2500, 3000, 3500]},
    guards=["g_agi < 80000", "g_agi2 < 85000"], derived=[("g_agi", "wages+interest-hsa-sli"), ("g_agi2", "wages+interest-hsa"), ("t22", "rnd((rnd(wages+interest-hsa-sli-std)-50400)*0.22)")]))
# t22 는 3번째 구간이 0 이하면 음수가 되므로 guard 에서 과세소득 > 50,400 을 보장
ITEMS[-1]["guards"].append("g_agi-std > 50400")
for c, u in zip(ITEMS[-1]["cells"], ["61", "62", "63", "1", "25A", "25A", "25A", "25A"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- IV-T-013 numeric: Schedule C, SE tax, QBI
ITEMS.append(T(
    "REG-IV-T-013", "IV", "numeric_table",
    "Self-employed consultant: SE tax, AGI, QBI deduction, and tax",
    "Dana Whitfield is single and has no dependents. She works as a self-employed marketing consultant and has no other income. "
    "Her taxable income before the QBI deduction is below the section 199A threshold, so the wage and property limits and the specified service trade or business limits do not apply.",
    "Using the exhibits, compute Dana's 2026 self-employment tax and income tax. Round to the nearest dollar.",
    [X("e1", "Schedule C and other data", "return_excerpt",
       [["Gross receipts", "${rev:,}"], ["Total business expenses", "${exp:,}"], ["Self-employed health insurance premiums (fully deductible under section 162(l))", "${sehi:,}"],
        ["Standard deduction, single (2026)", "${std:,}"], ["Social security wage base (2026)", "$184,500"], ["Social security rate", "12.4%"], ["Medicare rate", "2.9%"],
        ["Net earnings factor", "92.35%"]]),
     BRACKETS],
    [N("c1", "Net profit (Schedule C)", "rev-exp", "Net profit = gross receipts - expenses.", ["${rev:,} - ${exp:,} = ${c1:,}"], ["Schedule C bottom line.", "Receipts less expenses."]),
     N("c2", "Self-employment tax", "se_tax(c1)", "SE earnings = 92.35% x net profit = ${se_e:,}. Tax = 12.4% x SE earnings (below the wage base) + 2.9% x SE earnings.", ["${c1:,} x 92.35% = ${se_e:,}", "15.3% x ${se_e:,} = ${c2:,}"], ["Start with 92.35% of the net profit.", "15.3% because earnings are below the social security wage base."],
       traps=[("c1*0.153", "You did not apply the 92.35% factor to net profit.")]),
     N("c3", "Deduction for one-half of self-employment tax", "se_tax(c1)/2", "Half of the SE tax is an above-the-line deduction (IRC §164(f)).", ["${c2:,} / 2 = ${c3:,}"], ["It is an adjustment to income.", "One-half of your previous answer."], tol=1),
     N("c4", "Adjusted gross income", "c1-c3-sehi", "AGI = net profit - one-half SE tax - self-employed health insurance.", ["${c1:,} - ${c3:,} - ${sehi:,} = ${c4:,}"], ["Three items; two are adjustments.", "Net profit less both adjustments."],
       traps=[("c1-sehi", "You forgot the deduction for one-half of SE tax."), ("c1-c3", "You forgot the health insurance deduction.")]),
     N("c5", "Taxable income before the QBI deduction", "c4-std", "Subtract the standard deduction from AGI.", ["${c4:,} - ${std:,} = ${c5:,}"], ["Dana does not itemize.", "AGI minus standard deduction."]),
     N("c6", "Qualified business income deduction", "0.2*min(c1-c3-sehi, c5)", "Deduction = 20% x lesser of (a) QBI (net profit less half SE tax and SEHI = ${c4:,}) or (b) taxable income before QBI (${c5:,}).", ["QBI = ${c4:,}", "Lesser of ${c4:,} and ${c5:,} = ${lesser:,}", "20% x ${lesser:,} = ${c6:,}"], ["Two limits apply; take the lesser.", "20% of the lesser of QBI or taxable income before QBI."],
       traps=[("0.2*c1", "You used gross net profit. QBI is reduced by half SE tax and the SEHI deduction."), ("0.2*c4", "You used QBI, but taxable income before the QBI deduction is lower and controls.")]),
     N("c7", "Taxable income", "c5-c6", "Taxable income = taxable income before QBI - QBI deduction.", ["${c5:,} - ${c6:,} = ${c7:,}"], ["Subtract the QBI deduction.", "Result feeds the tax schedule."]),
     N("c8", "Income tax (excluding SE tax)", "tax_s(c7)", "Apply the schedule to ${c7:,}.", ["$5,800 through the 12% bracket", "22% x (${c7:,} - $50,400) = ${t22:,}", "Total = ${c8:,}"], ["Marginal rates.", "10% and 12% brackets are full at $50,400."])],
    {"rev": 148000, "exp": 41000, "sehi": 6000, "std": 16100},
    {"area": "IV", "group": "B", "topic": "Self-employment and QBI", "task": "Compute SE tax, adjustments, and the qualified business income deduction", "skill": "Application"},
    3, 16, cite=["IRC §1401", "IRC §1402(a)", "IRC §164(f)", "IRC §162(l)", "IRC §199A"],
    vary={"rev": [125000, 148000, 165000], "exp": [35000, 41000, 52000], "sehi": [4000, 6000, 8000]},
    guards=["60000 <= rev-exp <= 180000"],
    derived=[("se_e", "rnd((rev-exp)*0.9235)"), ("lesser", "rnd(min((rev-exp)-se_tax(rev-exp)/2-sehi, (rev-exp)-se_tax(rev-exp)/2-sehi-std))"),
             ("t22", "rnd((rnd((rev-exp)-se_tax(rev-exp)/2-sehi-std-0.2*((rev-exp)-se_tax(rev-exp)/2-sehi-std))-50400)*0.22)")]))
ITEMS[-1]["guards"].append("(rev-exp)-se_tax(rev-exp)/2-sehi-std-0.2*((rev-exp)-se_tax(rev-exp)/2-sehi-std) > 50400")
for c, u in zip(ITEMS[-1]["cells"], ["1402", "1401", "164", "62", "63", "199A", "63", "1"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- IV-T-014 numeric: itemized deductions with 2026 rules
ITEMS.append(T(
    "REG-IV-T-014", "IV", "numeric_table",
    "Itemized deductions: medical, SALT cap, mortgage interest, charity",
    "Luis and Carmen Ortega file jointly for 2026. Their AGI is ${agi:,}. They are under age 65, and are not subject to any phase-out of itemized deductions other than as described in the exhibit.",
    "Compute the Ortegas' deductible amounts and decide between itemizing and the standard deduction. Round to the nearest dollar.",
    [X("e1", "Expenses paid in 2026", "table",
       [["Item", "Amount"], ["Unreimbursed medical expenses (all qualifying)", "${med:,}"], ["State income tax paid", "${sti:,}"], ["Real property taxes on their home", "${prop:,}"],
        ["Interest paid on a home acquisition loan (loan balance ${loan:,}, taken out in 2022)", "${mort_int:,}"], ["Cash gifts to public charities", "${chg:,}"], ["Standard deduction, married filing jointly (2026)", "${std:,}"]]),
     X("e2", "Law assumptions for 2026", "statute_note",
       "Medical expenses are deductible only above 7.5% of AGI.\n"
       "State and local tax deduction cap for 2026: ${salt_cap:,}. The cap is reduced only if modified AGI exceeds $505,000, which does not apply here.\n"
       "Home acquisition debt limit: $750,000; interest is deductible in the proportion of the limit to the loan balance.\n"
       "For tax years beginning after 2025, charitable contributions of an itemizer are deductible only to the extent they exceed 0.5% of AGI (the 60% cash limit is not an issue here).")],
    [N("c1", "Deductible medical expenses", "max(0, med-0.075*agi)", "Only medical expenses above 7.5% of AGI are deductible: ${med:,} - 7.5% x ${agi:,}.", ["7.5% x ${agi:,} = ${fl:,}", "${med:,} - ${fl:,} = ${c1:,}"], ["Subtract a floor.", "7.5% of AGI."],
       traps=[("med", "You did not apply the 7.5% AGI floor."), ("max(0, med-0.10*agi)", "You used the 10% floor.")]),
     N("c2", "Deductible state and local taxes", "min(sti+prop, salt_cap)", "State income tax plus property tax = ${st:,}, limited to the ${salt_cap:,} cap.", ["${sti:,} + ${prop:,} = ${st:,}", "Lesser of ${st:,} and ${salt_cap:,} = ${c2:,}"], ["Add both taxes, then check the cap.", "The cap is in the law assumptions."],
       traps=[("sti+prop", "You did not apply the SALT cap."), ("min(sti+prop, 10000)", "You used the old $10,000 cap.")]),
     N("c3", "Deductible home mortgage interest", "mort_int*min(loan,750000)/loan", "Interest is limited to acquisition debt of $750,000: ${mort_int:,} x $750,000 / ${loan:,}.", ["$750,000 / ${loan:,} = ratio", "${mort_int:,} x ratio = ${c3:,}"], ["Only debt up to a limit counts.", "Prorate interest by limit/balance."],
       traps=[("mort_int", "You deducted all interest, ignoring the $750,000 limit.")]),
     N("c4", "Deductible charitable contributions", "max(0, chg-0.005*agi)", "Contributions are deductible only above 0.5% of AGI: ${chg:,} - 0.5% x ${agi:,}.", ["0.5% x ${agi:,} = ${cfl:,}", "${chg:,} - ${cfl:,} = ${c4:,}"], ["A new floor applies for 2026.", "0.5% of AGI."],
       traps=[("chg", "You ignored the 0.5% floor.")]),
     N("c5", "Total itemized deductions", "c1+c2+c3+c4", "Sum of the four deductible amounts.", ["${c1:,} + ${c2:,} + ${c3:,} + ${c4:,} = ${c5:,}"], ["Add your four previous answers.", "Then compare with the standard deduction."]),
     N("c6", "Deduction the Ortegas should claim", "max(c5, std)", "Claim the larger of itemized deductions and the standard deduction of ${std:,}.", ["max(${c5:,}, ${std:,}) = ${c6:,}"], ["Choose the greater.", "Compare your total with the standard deduction."]),
     N("c7", "Taxable income", "agi-c6", "Taxable income = AGI - deduction.", ["${agi:,} - ${c6:,} = ${c7:,}"], ["Assume no QBI deduction or other items.", "AGI minus the chosen deduction."])],
    {"agi": 300000, "med": 30000, "sti": 34000, "prop": 9600, "mort_int": 42000, "loan": 900000, "chg": 12000, "std": 32200, "salt_cap": 40400},
    {"area": "IV", "group": "C", "topic": "Itemized deductions", "task": "Compute itemized deductions and compare with the standard deduction", "skill": "Application"},
    3, 14, testable_from="2026-07-01", cite=["IRC §213(a)", "IRC §164(b)(7)", "IRC §163(h)(3)", "IRC §170(b)(1)(I)"],
    law_note="P.L. 119-21: SALT cap $40,000 for 2025, +1%/yr (2026: $40,400); phase-down above $500,000 (2025) / $505,000 (2026) MAGI. 0.5% AGI floor for itemized charity from 2026 (§170(b)(1)(I)). Verified 2026-09-29 against the text of IRC §164(b)(7) ($40,400 cap, $505,000 threshold) and IRC §170(b)(1)(I) on law.cornell.edu.",
    vary={"agi": [260000, 300000, 340000], "med": [26000, 30000, 36000], "sti": [26000, 34000, 38000], "chg": [9000, 12000, 15000]},
    guards=["med > 0.075*agi", "chg > 0.005*agi"], derived=[("fl", "rnd(0.075*agi)"), ("cfl", "rnd(0.005*agi)"), ("st", "sti+prop")]))
for c, u in zip(ITEMS[-1]["cells"], ["213", "164", "163", "170", "63", "63", "63"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- IV-T-015 numeric: capital gains and losses
ITEMS.append(T(
    "REG-IV-T-015", "IV", "numeric_table",
    "Capital loss limits, carryovers, and tax on net long-term gain",
    "Nora Patel is single. In Scenario A she has only the capital transactions below. In Scenario B (unrelated facts for a different year) she has ordinary taxable income and a net long-term capital gain. "
    "Enter losses and carryovers as positive amounts unless the cell says otherwise.",
    "Using the exhibits, complete both scenarios. Round to the nearest dollar.",
    [X("e1", "Scenario A: capital transactions for the year", "table",
       [["Item", "Amount"], ["Short-term capital gains", "${stg:,}"], ["Short-term capital losses", "${stl:,}"], ["Long-term capital gains", "${ltg:,}"], ["Long-term capital losses", "${ltl:,}"]]),
     X("e2", "Scenario B: data and rate thresholds (assumed for 2026, single)", "table",
       [["Item", "Amount"], ["Ordinary taxable income (excluding the long-term gain)", "${ord_ti:,}"], ["Net long-term capital gain (all taxed at preferential rates)", "${ltcg:,}"],
        ["Top of the 0% capital gain bracket (taxable income)", "${z_top:,}"], ["Top of the 15% bracket (taxable income)", "${f_top:,}"]])],
    [N("c1", "Scenario A: net short-term capital gain or (loss); enter a loss as a negative number", "stg-stl", "Short-term gains minus short-term losses.", ["${stg:,} - ${stl:,} = ${c1:,}"], ["Net within each holding-period group first.", "Short-term with short-term."], ecf=False),
     N("c2", "Scenario A: net long-term capital gain or (loss); enter a loss as a negative number", "ltg-ltl", "Long-term gains minus long-term losses.", ["${ltg:,} - ${ltl:,} = ${c2:,}"], ["Long-term with long-term.", "Same as the previous step for the other group."], ecf=False),
     N("c3", "Scenario A: capital loss deductible against ordinary income", "min(3000, -(c1+c2))", "Both nets are losses, so the total net capital loss ${tl:,} is deductible up to $3,000 against ordinary income.", ["Total net loss = ${tl:,}", "Deductible = $3,000"], ["There is an annual limit.", "$3,000 for a single taxpayer."],
       traps=[("-(c1+c2)", "You deducted the entire net loss. The annual limit is $3,000.")]),
     N("c4", "Scenario A: total capital loss carried to next year", "-(c1+c2)-c3", "Carryover = total net capital loss - amount deducted.", ["${tl:,} - $3,000 = ${c4:,}"], ["What remains after the deduction?", "Net loss less the amount deducted."]),
     N("c5", "Scenario A: short-term portion of the carryover", "-c1-min(c3,-c1)", "The $3,000 deduction uses the net short-term loss first; the remaining short-term loss carries over as short-term.", ["Net ST loss ${nst:,} - $3,000 used = ${c5:,}"], ["The deduction uses the short-term loss first.", "Short-term loss less the amount deducted."]),
     N("c6", "Scenario A: long-term portion of the carryover", "-c2-(c3-min(c3,-c1))", "The long-term loss is used only after the short-term loss is exhausted, so the long-term loss carries over in full.", ["Net LT loss ${nlt:,} - amount used from LT ($0) = ${c6:,}"], ["Short-term losses are absorbed first.", "Total carryover less the short-term portion."]),
     N("c7", "Scenario B: net long-term gain taxed at 0%", "min(ltcg, max(0, z_top-ord_ti))", "The 0% bracket has room of ${z_top:,} - ${ord_ti:,} = ${room:,} of taxable income.", ["Room = ${z_top:,} - ${ord_ti:,} = ${room:,}", "Gain in 0% bracket = ${c7:,}"], ["Stack the gain on top of ordinary income.", "Room left below the 0% bracket top."]),
     N("c8", "Scenario B: tax on the net long-term gain (15% rate, none reaches 20%)", "0.15*(ltcg-c7)", "The rest of the gain is taxed at 15%: (${ltcg:,} - ${c7:,}) x 15%.", ["${ltcg:,} - ${c7:,} = ${rest:,}", "15% x ${rest:,} = ${c8:,}"], ["Part of the gain is already in the 0% bracket.", "15% of the gain above the 0% room."],
       traps=[("0.15*ltcg", "You applied 15% to the whole gain, ignoring the 0% bracket.")])],
    {"stg": 8000, "stl": 12000, "ltg": 5000, "ltl": 9000, "ord_ti": 30050, "ltcg": 40000, "z_top": 49450, "f_top": 545500},
    {"area": "IV", "group": "D", "topic": "Capital gains and losses", "task": "Net capital gains and losses, apply limits, carryovers, and preferential rates", "skill": "Application"},
    3, 14, cite=["IRC §1211(b)", "IRC §1212(b)", "IRC §1(h)"],
    vary={"stg": [7000, 8000, 9000], "stl": [11000, 12000, 13000], "ltg": [4000, 5000, 6000], "ltl": [8000, 9000, 10000], "ord_ti": [30050, 32050, 34050], "ltcg": [40000, 44000, 48000]},
    guards=["stg-stl < 0", "ltg-ltl < 0", "-(stg-stl+ltg-ltl) > 3000", "-(stg-stl) > 3000", "ltcg > z_top-ord_ti"],
    derived=[("tl", "-(stg-stl+ltg-ltl)"), ("nst", "stl-stg"), ("nlt", "ltl-ltg"), ("room", "z_top-ord_ti"), ("rest", "ltcg-(z_top-ord_ti)")]))
for c in ITEMS[-1]["cells"]:
    c["link"] = IRC("1211") if c["id"] in ("c3",) else IRC("1212")
ITEMS[-1]["cells"][6]["link"] = IRC("1")
ITEMS[-1]["cells"][7]["link"] = IRC("1")

# ---------------------------------------------------------------- IV-T-016 document review: client return summary
ITEMS.append(T(
    "REG-IV-T-016", "IV", "document_review",
    "Review of a staff summary of return positions (2026 law)",
    "You are the reviewer for a return prepared by a junior staff member for Roman and Ilse Kovac (married filing jointly). "
    "The staff member wrote the explanations below to the client. Assume all facts stated are true.",
    "For each numbered statement, choose the option that makes the statement correct for the 2026 tax year. Choose 'Keep as written' if it is already correct.",
    [X("e1", "Draft email to the clients", "email",
       "1. Alimony Roman pays under the divorce decree from his first marriage (finalized in 2023) is deductible above the line on your return.\n"
       "2. Ilse works as an employee at home for her employer's convenience. Her unreimbursed home office costs are deductible as an itemized deduction.\n"
       "3. Roman's Roth IRA distribution at age 63 from a Roth IRA whose first contribution was made 8 years ago is a qualified distribution and is excluded from income.\n"
       "4. You may claim a child tax credit of $2,000 for each of your two qualifying children.\n"
       "5. Your gambling losses of $9,000 (winnings $12,000) are deductible in full as an itemized deduction, up to your winnings.\n"
       "6. All tips Ilse reported on her Form W-2 are fully deductible, without a dollar limit.")],
    [D("c1", "Statement 1: alimony paid", ["Keep as written", "Revise: alimony under a post-2018 divorce instrument is not deductible by the payer (and not income to the recipient)", "Revise: alimony is deductible only as an itemized deduction"],
       "Revise: alimony under a post-2018 divorce instrument is not deductible by the payer (and not income to the recipient)",
       "For divorce or separation instruments executed after 2018, alimony is not deductible by the payer and not includible by the recipient (former IRC §215 and §71 repealed by TCJA §11051).", ["Look at the date of the decree.", "Post-2018 decrees follow the repeal."],
       {"Keep as written": "The above-the-line alimony deduction applies only to pre-2019 instruments.", "Revise: alimony is deductible only as an itemized deduction": "It is not deductible at all for post-2018 instruments."}),
     D("c2", "Statement 2: employee home office", ["Keep as written", "Revise: unreimbursed employee expenses (including a home office) are not deductible for 2026", "Revise: the costs are deductible on Schedule C"],
       "Revise: unreimbursed employee expenses (including a home office) are not deductible for 2026",
       "Miscellaneous itemized deductions subject to the 2% floor, including unreimbursed employee expenses, are not allowed for tax years after 2017; P.L. 119-21 made the elimination permanent (IRC §67(g)).", ["Employee versus self-employed.", "Suspended and now permanently eliminated."],
       {"Keep as written": "Employee business expenses are not deductible.", "Revise: the costs are deductible on Schedule C": "Ilse is an employee, not self-employed."}),
     D("c3", "Statement 3: Roth IRA distribution", ["Keep as written", "Revise: the earnings are taxable because the account is under 10 years old", "Revise: a Roth distribution is never tax-free"], "Keep as written",
       "A distribution is qualified if made after age 59 1/2 and after the 5-tax-year period beginning with the first contribution year (IRC §408A(d)(2)). Roman is 63 and the account is 8 years old.", ["Two tests: age and the five-year period.", "Both are met."],
       {"Revise: the earnings are taxable because the account is under 10 years old": "The holding period is 5 tax years, not 10.", "Revise: a Roth distribution is never tax-free": "Qualified distributions are tax-free."}),
     D("c4", "Statement 4: child tax credit amount", ["Keep as written", "Revise: $2,200 per qualifying child", "Revise: $3,000 per qualifying child"], "Revise: $2,200 per qualifying child",
       "P.L. 119-21 increased the credit to $2,200 per qualifying child for 2025 and indexes it for inflation after 2025 (IRC §24(h)); Rev. Proc. 2025-32 shows $2,200 for 2026.", ["The amount was increased in 2025.", "$2,200."],
       {"Keep as written": "$2,000 was the prior amount.", "Revise: $3,000 per qualifying child": "That is not the credit amount."}),
     D("c5", "Statement 5: gambling losses", ["Keep as written", "Revise: 90% of the losses are deductible, limited to winnings", "Revise: no gambling losses are deductible for 2026"], "Revise: 90% of the losses are deductible, limited to winnings",
       "For tax years beginning after 2025, gambling losses are deductible only up to 90% of the losses and limited to winnings (IRC §165(d), as amended by P.L. 119-21). Here 90% x $9,000 = $8,100.", ["The law changed for 2026.", "Only part of the losses is allowed."],
       {"Keep as written": "The 100% rule applied through 2025.", "Revise: no gambling losses are deductible for 2026": "Losses are still deductible up to winnings, at 90%."}),
     D("c6", "Statement 6: qualified tips deduction", ["Keep as written", "Revise: the deduction is limited to tips from occupations that customarily and regularly receive tips, up to $25,000, and phases out above $150,000 MAGI ($300,000 joint)", "Revise: the deduction is allowed only as an itemized deduction"],
       "Revise: the deduction is limited to tips from occupations that customarily and regularly receive tips, up to $25,000, and phases out above $150,000 MAGI ($300,000 joint)",
       "P.L. 119-21 allows a deduction for qualified tips (2025-2028): occupations customarily receiving tips, annual cap of $25,000, reduced by $100 per $1,000 of MAGI above $150,000 ($300,000 joint), allowed to nonitemizers too (IRC §224).", ["It is not unlimited.", "Cap, occupation test, and phase-out."],
       {"Keep as written": "The deduction has an occupation test, a $25,000 cap, and a phase-out.", "Revise: the deduction is allowed only as an itemized deduction": "It is available whether or not the taxpayer itemizes."})],
    {}, {"area": "IV", "group": "A", "topic": "Individual return positions", "task": "Identify errors in return explanations under current law", "skill": "Analysis"},
    3, 14, testable_from="2026-07-01", cite=["IRC §67(g)", "IRC §408A(d)", "IRC §24", "IRC §165(d)", "IRC §224"],
    law_note="Statements 4-6 rely on P.L. 119-21 (OBBBA): CTC $2,200, gambling loss 90% rule, qualified tips deduction; testable from 2026-07-01.", tags=["obbba"]))
for c, (cs, u) in zip(ITEMS[-1]["cells"], [("IRC §71 (repealed); TCJA §11051", "215"), ("IRC §67(g)", "67"), ("IRC §408A(d)(2)", "408A"), ("IRC §24(h)", "24"), ("IRC §165(d)", "165"), ("IRC §224", "224")]):
    c["cite"] = cs
    c["link"] = IRC(u)

# ---------------------------------------------------------------- IV-T-017 research
ITEMS.append(T(
    "REG-IV-T-017", "IV", "research",
    "Locate the authority: individual income tax",
    "A client asks six questions about individual income tax rules. Identify the primary authority for each answer.",
    "For each question, enter the Internal Revenue Code citation (for example, 'IRC 1402(a)(13)'). Give a subsection or paragraph only when the question asks for it.",
    [X("e1", "Questions", "email",
       "1. Which section and subsection define a qualified distribution from a Roth IRA?\n"
       "2. Which section provides the American opportunity credit and the lifetime learning credit? (Section only.)\n"
       "3. Which section provides the child tax credit? (Section only.)\n"
       "4. Which section provides the deduction for interest on qualified education loans? (Section only.)\n"
       "5. Which section limits deductions for passive activity losses? (Section only.)\n"
       "6. Which section, subsection, and paragraph provide when a dwelling unit is treated as a residence of the taxpayer for the vacation-home rules (more than 14 days or 10% of rental days)?")],
    [C("c1", "Question 1: qualified Roth IRA distribution", ["408A(d)(2)"], "IRC §408A(d)(2) defines a qualified distribution (five-year period plus age 59 1/2, death, disability, or first-time home purchase).", ["Roth IRAs are in section 408A.", "Subsection (d) covers distribution rules; paragraph (2) defines qualified."], IRC("408A"), partial=["408A", "408A(d)"]),
     C("c2", "Question 2: education credits", ["25A"], "IRC §25A provides the Hope/American opportunity credit and the lifetime learning credit.", ["Subpart A of part IV; credits for personal expenses.", "Section 25A."], IRC("25A"), partial=["25A(a)", "25A(b)"]),
     C("c3", "Question 3: child tax credit", ["24"], "IRC §24 child tax credit.", ["Part IV, subpart A.", "Section 24."], IRC("24"), partial=["24(a)"]),
     C("c4", "Question 4: student loan interest deduction", ["221"], "IRC §221 deduction for interest on education loans.", ["Part VII adjustments.", "Section 221."], IRC("221")),
     C("c5", "Question 5: passive activity loss limit", ["469"], "IRC §469 passive activity losses and credits limited.", ["Subchapter E.", "Section 469."], IRC("469"), partial=["469(a)"]),
     C("c6", "Question 6: vacation-home residence test", ["280A(d)(1)"], "IRC §280A(d)(1): a dwelling unit is used as a residence if personal use exceeds the greater of 14 days or 10% of the days it is rented.", ["Section 280A limits deductions for dwelling units used as residences.", "Subsection (d), paragraph (1)."], IRC("280A"), partial=["280A", "280A(d)"])],
    {}, {"area": "IV", "group": "A", "topic": "Research: individual tax", "task": "Research and cite authority for individual income tax issues", "skill": "Application"},
    2, 10, cite=["IRC §408A", "IRC §25A", "IRC §24", "IRC §221", "IRC §469", "IRC §280A"], tags=["research"]))

# ---------------------------------------------------------------- IV-T-018 dropdown: dependents and filing status
QC3 = ["Qualifying child", "Qualifying relative", "Neither"]
FS = ["Single", "Head of household", "Married filing jointly", "Qualifying surviving spouse"]
ITEMS.append(T(
    "REG-IV-T-018", "IV", "dropdown_judgment",
    "Dependents and filing status",
    "Ana Ruiz is unmarried and paid more than half the cost of keeping up her home for all of 2026. The individuals below are described in the exhibit. "
    "Assume none of them files a joint return, none is a qualifying child of another taxpayer, all are U.S. citizens with valid SSNs, and the 2026 gross income limit for a qualifying relative is $5,300.",
    "For each person, select the relationship test result that applies to Ana. For the last two cells, select the filing status.",
    [X("e1", "Individuals", "table",
       [["Person", "Facts"],
        ["Sofia (daughter)", "Age 22, full-time student for 9 months, lived with Ana 8 months in 2026, provided 30% of her own support, gross income $6,000."],
        ["Rosa (mother)", "Age 70, lives in her own apartment, gross income $4,200, Ana provides 70% of her support."],
        ["Mark (unrelated friend)", "Lived in Ana's home all year as a member of the household (no violation of local law), gross income $3,000, Ana provides over half his support."],
        ["Leo (nephew)", "Age 19, not a student, lived with Ana all year, gross income $9,000, Ana provides over half his support."],
        ["Diego (son)", "Age 26, not a student or disabled, lived with Ana all year, gross income $2,000, Ana provides over half his support."]]),
     X("e2", "Second taxpayer", "notes", "Carlos Vega's wife died in June 2024. He has not remarried. He maintained a home that was the main home of his dependent 9-year-old son for all of 2025 and 2026, and he paid more than half of the cost of keeping up the home. What is Carlos's 2026 filing status?")],
    [D("c1", "Sofia", QC3, "Qualifying child", "Sofia is under 24 and a full-time student (age test), lived with Ana for more than half the year (residency), and did not provide more than half of her own support. Gross income is not tested for a qualifying child.", ["Age test for students is under 24.", "Gross income does not matter for a child."], {"Qualifying relative": "A person who is a qualifying child cannot be a qualifying relative.", "Neither": "All qualifying child tests are met."}),
     D("c2", "Rosa", QC3, "Qualifying relative", "Rosa is a relative who does not live with Ana. She is not a qualifying child (age). Gross income $4,200 is under $5,300, and Ana provides more than half of her support.", ["She fails the age and residency tests for a qualifying child.", "Check the income limit."], {"Qualifying child": "A parent cannot be a qualifying child.", "Neither": "Gross income and support tests are met."}),
     D("c3", "Mark", QC3, "Qualifying relative", "An unrelated person who lives with the taxpayer all year as a member of the household can be a qualifying relative if the income and support tests are met.", ["A relationship test can be met by living in the household.", "Check income and support."], {"Qualifying child": "A qualifying child must be a child, sibling, or descendant.", "Neither": "Member-of-household status satisfies the relationship test."}),
     D("c4", "Leo", QC3, "Neither", "Leo fails the qualifying-child age test (19, not a student) and fails the qualifying-relative gross income test ($9,000 > $5,300).", ["Age 19 and not a student.", "Compare his income to $5,300."], {"Qualifying child": "Under 19 or under 24 for students only.", "Qualifying relative": "His gross income exceeds the limit."}),
     D("c5", "Diego", QC3, "Qualifying relative", "Diego is too old to be a qualifying child (26, not a student), but he can be a qualifying relative: gross income $2,000 < $5,300 and Ana provides more than half his support.", ["Age 26 is too old for the child test.", "Try the relative tests."], {"Qualifying child": "Age 26 fails the child age test.", "Neither": "He meets all qualifying relative tests."}),
     D("c6", "Ana's filing status for 2026", FS, "Head of household", "Ana is unmarried, paid more than half the cost of keeping up her home, and Sofia (a qualifying child) lived with her more than half of the year.", ["Unmarried with a qualifying person.", "Head of household."], {"Single": "She qualifies for the better status.", "Married filing jointly": "Ana is unmarried.", "Qualifying surviving spouse": "Ana is not a surviving spouse."}),
     D("c7", "Carlos's filing status for 2026", FS, "Qualifying surviving spouse", "Carlos may use qualifying surviving spouse status for the two tax years after the year of death (2025 and 2026), if he has not remarried and maintains a home for his dependent child.", ["Look at the year of death.", "Two years after the year of the spouse's death."], {"Head of household": "A surviving spouse with a dependent child can use the more favorable status.", "Single": "He qualifies for a better status.", "Married filing jointly": "His spouse died in 2024, before the 2026 tax year."})],
    {}, {"area": "IV", "group": "A", "topic": "Filing status and dependents", "task": "Determine dependency tests and filing status", "skill": "Application"},
    2, 12, cite=["IRC §152(c)", "IRC §152(d)", "IRC §2(a)", "IRC §2(b)"], tags=["dependents", "filing_status"]))
for c, u in zip(ITEMS[-1]["cells"], ["152", "152", "152", "152", "152", "2", "2"]):
    c["link"] = IRC(u)
