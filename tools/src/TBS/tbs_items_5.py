# Area V (법인·파트너십·S법인 등 사업체 과세) 6개
from tbs_lib import *
from tbs_items_1 import IRC, L

ITEMS = []

# ---------------------------------------------------------------- V-T-019 numeric: C corporation taxable income
ITEMS.append(T(
    "REG-V-T-019", "V", "numeric_table",
    "C corporation: book-to-tax adjustments and taxable income",
    "Kestrel Components Inc. is a calendar-year C corporation (no affiliated group). For its 2025 return it starts from book income before federal income tax. "
    "All items are as described in the exhibit; assume no other items and use the 21% corporate rate.",
    "Compute the corporation's taxable income and regular tax using the exhibit. Round to the nearest dollar.",
    [X("e1", "Book income and reconciling items (2025)", "table",
       [["Item", "Amount"],
        ["Book income before federal income tax (after all items below)", "${book:,}"],
        ["Municipal bond interest included in book income (tax-exempt)", "${muni:,}"],
        ["Meals expense deducted in book income (50% limit applies for tax)", "${meals:,}"],
        ["Tax depreciation in excess of book depreciation", "${dep:,}"],
        ["Dividends from a 25%-owned domestic corporation, included in book income", "${divs:,}"],
        ["Cash contributions to public charities, deducted in book income", "${chg:,}"],
        ["Net operating loss carryforward from 2023 (post-2017 loss)", "${nol:,}"]]),
     X("e2", "Ordering rules", "notes",
       "Charitable contributions are limited to 10% of taxable income computed before the charitable deduction and the dividends-received deduction, and without regard to any NOL carryback.\n"
       "The dividends-received deduction is a percentage of the dividends received, limited to the same percentage of taxable income computed without the NOL and the DRD.\n"
       "The NOL deduction is limited to 80% of taxable income computed without the NOL deduction (but after the DRD).")],
    [N("c1", "Charitable contribution deduction allowed for 2025", "min(chg, 0.10*(book+chg-muni+0.5*meals-dep-nol))",
       "Base for the 10% limit = taxable income before the charity deduction and the DRD but after the NOL carryforward deduction (Form 1120 instructions, line 19: only NOL carrybacks are ignored). Income before those items = book income + contributions added back - muni interest + nondeductible meals - excess tax depreciation = ${cbase:,}; less the ${nol:,} NOL deduction = ${cb2:,}. Limit = 10% x ${cb2:,}.",
       ["Income before charity, DRD, and NOL = ${book:,} + ${chg:,} - ${muni:,} + ${nd:,} - ${dep:,} = ${cbase:,}", "Less the NOL deduction of ${nol:,} (fully allowed, see cell 5) = ${cb2:,}", "10% x ${cb2:,} = ${lim:,}", "Allowed = lesser of ${chg:,} and ${lim:,} = ${c1:,}"],
       ["The base is taxable income before charity and the DRD but after the NOL carryforward deduction; only NOL carrybacks are ignored.", "Adjust book income: add back the charity, remove muni interest, add back half the meals, subtract excess depreciation, then subtract the NOL deduction."],
       traps=[("chg", "You deducted the entire contribution and ignored the 10% limit."), ("min(chg, 0.10*book)", "You applied 10% to book income rather than to adjusted taxable income."), ("min(chg, 0.10*(book+chg-muni+0.5*meals-dep))", "You ignored the NOL carryforward deduction. Only NOL carrybacks are left out of the 10% base; a carryforward reduces it.")]),
     N("c2", "Charitable contribution carryforward", "chg-c1", "The excess over the limit carries forward for five years (IRC §170(d)(2)).", ["${chg:,} - ${c1:,} = ${c2:,}"], ["What part was not allowed this year?", "Contribution less allowed deduction."]),
     N("c3", "Taxable income before the dividends-received deduction and NOL deduction", "book+chg-muni+0.5*meals-dep-c1",
       "Start from the base (which already adds back the charity and the other reconciling items) and subtract the allowed charity deduction.", ["${cbase:,} - ${c1:,} = ${c3:,}"], ["Use the base from cell 1.", "Base less the allowed charity deduction."]),
     N("c4", "Dividends-received deduction", "min(0.65*divs, 0.65*c3)", "A 20%-or-more owned domestic corporation qualifies for the 65% DRD (IRC §243(c)); the limit is 65% of taxable income before the DRD and NOL, which is not binding here.",
       ["65% x ${divs:,} = ${drd:,}", "Limit 65% x ${c3:,} = ${drdlim:,}", "DRD = ${c4:,}"], ["The DRD percentage depends on ownership.", "20% to under 80% ownership: 65%."],
       traps=[("0.5*divs", "You used 50%, which applies below 20% ownership."), ("divs", "You used 100%, which applies only to affiliated group members.")]),
     N("c5", "NOL deduction allowed", "min(nol, 0.8*(c3-c4))", "The NOL is limited to 80% of taxable income after the DRD: 80% x ${ti0:,} = ${nlim:,}. The ${nol:,} NOL is below that limit, so all of it is deductible.", ["Taxable income before NOL = ${c3:,} - ${c4:,} = ${ti0:,}", "80% limit = ${nlim:,}", "NOL allowed = lesser of ${nol:,} and ${nlim:,} = ${c5:,}"], ["A post-2017 NOL has an income-based limit.", "80% of taxable income after the DRD."],
       traps=[("0.8*nol", "You took 80% of the NOL. The 80% limit applies to taxable income, not to the NOL itself.")]),
     N("c6", "Taxable income", "c3-c4-c5", "Taxable income = income before DRD and NOL - DRD - NOL.", ["${c3:,} - ${c4:,} - ${c5:,} = ${c6:,}"], ["Subtract both deductions.", "Use your answers to cells 3, 4, and 5."]),
     N("c7", "Regular income tax at 21%", "0.21*c6", "Corporate rate of 21% (IRC §11(b)).", ["21% x ${c6:,} = ${c7:,}"], ["Flat rate.", "21% of taxable income."])],
    {"book": 900000, "muni": 30000, "meals": 40000, "dep": 70000, "divs": 100000, "chg": 120000, "nol": 300000},
    {"area": "V", "group": "A", "topic": "C corporation taxable income", "task": "Compute corporate taxable income including charity limit, DRD, and NOL", "skill": "Application"},
    3, 16, cite=["IRC §170(b)(2)", "IRC §243(a)(1)", "IRC §243(c)", "IRC §172(a)(2)", "IRC §11(b)", "IRC §274(n)"],
    law_note="Tax year 2025 by design: the 1% floor on corporate charitable deductions (IRC §170(b)(2)(A), P.L. 119-21) applies to tax years beginning after 2025, so it is not part of this TBS. The 10% limit is figured after the NOL carryforward deduction (Form 1120 instructions, line 19); the NOL here is small enough that the 80% cap does not bind, which avoids a circular computation.",
    vary={"book": [800000, 900000, 1000000], "chg": [100000, 120000, 140000], "divs": [80000, 100000, 120000], "nol": [250000, 300000, 350000]},
    guards=["chg > 0.10*(cbase-nol)", "nol < 0.8*ti0"],
    derived=[("nd", "rnd(0.5*meals)"), ("cbase", "rnd(book+chg-muni+0.5*meals-dep)"), ("cb2", "rnd(book+chg-muni+0.5*meals-dep-nol)"), ("lim", "rnd(0.10*(book+chg-muni+0.5*meals-dep-nol))"),
             ("drd", "rnd(0.65*divs)"), ("drdlim", "rnd(0.65*(book+chg-muni+0.5*meals-dep-min(chg,0.10*(book+chg-muni+0.5*meals-dep-nol))))"),
             ("ti0", "rnd(book+chg-muni+0.5*meals-dep-min(chg,0.10*(book+chg-muni+0.5*meals-dep-nol))-min(0.65*divs,0.65*(book+chg-muni+0.5*meals-dep-min(chg,0.10*(book+chg-muni+0.5*meals-dep-nol)))))"),
             ("nlim", "rnd(0.8*(book+chg-muni+0.5*meals-dep-min(chg,0.10*(book+chg-muni+0.5*meals-dep-nol))-min(0.65*divs,0.65*(book+chg-muni+0.5*meals-dep-min(chg,0.10*(book+chg-muni+0.5*meals-dep-nol))))))")]))
for c, u in zip(ITEMS[-1]["cells"], ["170", "170", "63", "243", "172", "63", "11"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- V-T-020 numeric: partnership outside basis
ITEMS.append(T(
    "REG-V-T-020", "V", "numeric_table",
    "Partnership: outside basis, distributions, and loss limitation",
    "Kai Tanaka became a partner in Bayline Partners LP on January 2, Year 1, by contributing cash. The partnership uses the calendar year. Ignore the at-risk and passive activity rules, and self-employment tax.",
    "Using the exhibits, compute Kai's outside basis and the results of the distributions and losses. Enter results as positive amounts unless the cell says otherwise. Round to the nearest dollar.",
    [X("e1", "Year 1 and initial data", "table",
       [["Item", "Amount"], ["Cash contributed on January 2, Year 1", "${cash:,}"], ["Kai's share of partnership liabilities on January 2, Year 1", "${liab0:,}"],
        ["Kai's share of ordinary business income, Year 1", "${inc:,}"], ["Kai's share of tax-exempt interest, Year 1", "${tex:,}"],
        ["Kai's share of nondeductible expenses, Year 1", "${nond:,}"], ["Kai's share of a charitable contribution made by the partnership, Year 1", "${chr:,}"],
        ["Increase in Kai's share of partnership liabilities during Year 1", "${liab_up:,}"], ["Cash distribution to Kai on December 31, Year 1", "${dist1:,}"]]),
     X("e2", "Years 2 and 3 data", "table",
       [["Item", "Amount"], ["Cash distribution to Kai on June 30, Year 2 (no other Year 2 income items)", "${dist2:,}"], ["Kai's share of the partnership's ordinary loss for Year 2 (incurred evenly)", "${loss2:,}"],
        ["Cash distribution to Kai in Year 3 (Year 3 has no income or loss items)", "${dist3:,}"]])],
    [N("c1", "Kai's initial outside basis", "cash+liab0", "Basis = cash contributed + share of partnership liabilities (treated as a contribution of cash, IRC §752(a)).", ["${cash:,} + ${liab0:,} = ${c1:,}"], ["Liabilities count for a partner's basis.", "Cash plus share of liabilities."],
       traps=[("cash", "You left out Kai's share of partnership liabilities.")]),
     N("c2", "Outside basis at the end of Year 1", "c1+inc+tex-nond-chr+liab_up-dist1", "Basis increases for income, tax-exempt income, and increases in liabilities; decreases for nondeductible expenses, separately stated deductions, and distributions.",
       ["${c1:,} + ${inc:,} + ${tex:,} - ${nond:,} - ${chr:,} + ${liab_up:,} - ${dist1:,} = ${c2:,}"], ["Do increases first, then decreases.", "Tax-exempt income increases basis; charity and nondeductible items decrease it."],
       traps=[("c1+inc-dist1", "You omitted tax-exempt income, nondeductible expenses, the charitable contribution, and the liability change."), ("c1+inc+tex-nond-chr-dist1", "You omitted the increase in liabilities.")]),
     N("c3", "Outside basis in Year 2 after the June 30 distribution and before the loss", "c2-dist2", "Distributions reduce basis before the year's losses are considered.", ["${c2:,} - ${dist2:,} = ${c3:,}"], ["Order matters within the year.", "Distributions before losses."]),
     N("c4", "Year 2 loss Kai can deduct", "min(loss2, c3)", "Loss deduction is limited to outside basis (IRC §704(d)).", ["min(${loss2:,}, ${c3:,}) = ${c4:,}"], ["Compare loss with basis.", "Lesser of the loss and basis."],
       traps=[("loss2", "You deducted the full loss.")]),
     N("c5", "Suspended loss carried to Year 3", "loss2-c4", "The disallowed loss is suspended and carried forward indefinitely.", ["${loss2:,} - ${c4:,} = ${c5:,}"], ["Loss not deducted.", "Loss less deduction."]),
     N("c6", "Outside basis at the end of Year 2", "c3-c4", "Basis is reduced by the deductible loss.", ["${c3:,} - ${c4:,} = ${c6:,}"], ["Basis cannot go below zero.", "Basis before the loss less the loss deducted."]),
     N("c7", "Year 3: gain recognized on the cash distribution", "max(0, dist3-c6)", "Cash distributed in excess of outside basis is gain from the sale of the partnership interest (IRC §731(a)(1)). Suspended losses do not reduce this gain.", ["${dist3:,} - ${c6:,} = ${c7:,}"], ["Basis is exhausted.", "Distribution over basis is gain."])],
    {"cash": 80000, "liab0": 20000, "inc": 30000, "tex": 2000, "nond": 1500, "chr": 3000, "liab_up": 10000, "dist1": 25000, "dist2": 40000, "loss2": 85000, "dist3": 20000},
    {"area": "V", "group": "C", "topic": "Partnership basis and distributions", "task": "Compute outside basis, loss limits, and gain on distributions", "skill": "Application"},
    3, 16, cite=["IRC §722", "IRC §752(a)", "IRC §705(a)", "IRC §704(d)", "IRC §731(a)(1)"],
    vary={"inc": [24000, 30000, 36000], "dist2": [30000, 40000, 50000], "loss2": [80000, 85000, 95000], "dist3": [15000, 20000, 25000]},
    guards=["loss2 > gb2-dist2"], derived=[("gb2", "cash+liab0+inc+tex-nond-chr+liab_up-dist1")]))
for c, u in zip(ITEMS[-1]["cells"], ["722", "705", "705", "704", "704", "705", "731"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- V-T-021 numeric: S corp basis
ITEMS.append(T(
    "REG-V-T-021", "V", "numeric_table",
    "S corporation: stock and debt basis, distributions, and loss limits",
    "Ava Lindqvist owns 40% of Cobalt Fabrication Inc., which has been an S corporation since its formation and has no accumulated earnings and profits. "
    "All amounts in the exhibits are Ava's share. Ignore the at-risk and passive activity rules.",
    "Using the exhibits, compute Ava's basis, gain, and deductible loss. Round to the nearest dollar.",
    [X("e1", "Year 1 data (Ava's share)", "table",
       [["Item", "Amount"], ["Stock basis on January 1, Year 1", "${sb:,}"], ["Ordinary business income", "${inc:,}"], ["Tax-exempt interest", "${texempt:,}"],
        ["Nondeductible expenses", "${nondc:,}"], ["Cash distribution actually made in Year 1", "${dist:,}"],
        ["Alternative fact for cell 2 only: the Year 1 distribution had been", "${dist_alt:,}"]]),
     X("e2", "Year 2 data (Ava's share)", "table",
       [["Item", "Amount"], ["Ordinary business loss", "${loss:,}"], ["Basis in loans Ava made directly to the corporation (debt basis), start of Year 2", "${debt:,}"], ["Note", "The loans are bona fide; ignore any repayment in Year 2."]])],
    [N("c1", "Stock basis after Year 1 income items, before distributions and nondeductible expenses", "sb+inc+texempt", "Basis increases for ordinary income and tax-exempt income first (IRC §1367(a)(1)).", ["${sb:,} + ${inc:,} + ${texempt:,} = ${c1:,}"], ["Increases come first.", "Both income items increase basis."]),
     N("c2", "Alternative fact: gain Ava recognizes if the Year 1 distribution were ${dist_alt:,}", "max(0, dist_alt-c1)", "A distribution from an S corporation with no E&P is a return of basis; the excess over stock basis is capital gain (IRC §1368(b)(2)). Basis for this test is measured after the increases.", ["${dist_alt:,} - ${c1:,} = ${c2:,}"], ["Compare distribution to basis.", "Distribution above stock basis is capital gain."]),
     N("c3", "Actual Year 1: stock basis at December 31, Year 1", "c1-dist-nondc", "Distributions then nondeductible expenses reduce basis (never below zero).", ["${c1:,} - ${dist:,} - ${nondc:,} = ${c3:,}"], ["Order: increases, distributions, then nondeductible expenses and losses.", "Subtract both."],
       traps=[("c1-dist", "You forgot the nondeductible expenses.")]),
     N("c4", "Year 2: loss deductible against stock basis", "min(loss, c3)", "Loss reduces stock basis first, but not below zero.", ["min(${loss:,}, ${c3:,}) = ${c4:,}"], ["Stock basis is used first.", "Lesser of loss and stock basis."]),
     N("c5", "Year 2: loss deductible against debt basis", "min(loss-c4, debt)", "Excess loss then reduces debt basis (IRC §1366(d)(1)(B)).", ["min(${loss:,} - ${c4:,}, ${debt:,}) = ${c5:,}"], ["Second layer of basis.", "Remaining loss up to debt basis."]),
     N("c6", "Year 2: suspended loss carried forward", "loss-c4-c5", "Loss in excess of stock and debt basis is suspended (IRC §1366(d)(2)).", ["${loss:,} - ${c4:,} - ${c5:,} = ${c6:,}"], ["Loss not absorbed.", "Total loss less both deductions."],
       traps=[("loss-c4", "You did not use debt basis.")])],
    {"sb": 30000, "inc": 40000, "texempt": 4000, "nondc": 2000, "dist": 60000, "dist_alt": 90000, "loss": 80000, "debt": 10000},
    {"area": "V", "group": "B", "topic": "S corporation basis and distributions", "task": "Compute stock and debt basis, distribution gain, and loss limitation", "skill": "Application"},
    3, 14, cite=["IRC §1367(a)", "IRC §1368(b)", "IRC §1366(d)"],
    vary={"inc": [36000, 40000, 44000], "dist": [55000, 60000, 65000], "dist_alt": [86000, 90000, 95000], "loss": [70000, 80000, 90000], "debt": [8000, 10000, 12000]},
    guards=["sb+inc+texempt-dist-nondc > 0", "dist_alt > sb+inc+texempt", "loss > (sb+inc+texempt-dist-nondc)+debt"]))
for c, u in zip(ITEMS[-1]["cells"], ["1367", "1368", "1367", "1366", "1366", "1366"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- V-T-022 document review: S corporation
ITEMS.append(T(
    "REG-V-T-022", "V", "document_review",
    "S corporation eligibility and termination: memo review",
    "You are reviewing a memo written by a staff accountant to the owners of Greenfield Tools Inc., a C corporation considering an S election.",
    "For each numbered statement, choose the option that makes the statement correct. Choose 'Keep as written' if it is already correct.",
    [X("e1", "Draft memo", "memo",
       "1. An S corporation may have no more than 75 shareholders.\n"
       "2. If the corporation has voting and nonvoting common stock with identical rights to distributions and liquidation proceeds, it has two classes of stock and is ineligible for S status.\n"
       "3. A nonresident alien may be a shareholder of an S corporation if he or she consents to the election on Form 2553.\n"
       "4. To be effective for its first tax year, the S election generally must be filed no later than the 15th day of the third month of that tax year.\n"
       "5. A C corporation that converts to S status pays the built-in gains tax on gains recognized within 10 years after the conversion date.\n"
       "6. An S election terminates if the corporation has accumulated earnings and profits from a C year and passive investment income above 25% of gross receipts for 2 consecutive years.")],
    [D("c1", "Statement 1: shareholder limit", ["Keep as written", "Revise: 100 shareholders (family members count as one)", "Revise: 250 shareholders"], "Revise: 100 shareholders (family members count as one)",
       "An S corporation may have no more than 100 shareholders; family members can elect to be treated as one shareholder (IRC §1361(b)(1)(A), (c)(1)).", ["Number was increased long ago.", "100."],
       {"Keep as written": "The limit is 100, not 75.", "Revise: 250 shareholders": "The limit is 100."}),
     D("c2", "Statement 2: voting and nonvoting stock", ["Keep as written", "Revise: differences in voting rights alone do not create a second class of stock", "Revise: nonvoting stock is never allowed"], "Revise: differences in voting rights alone do not create a second class of stock",
       "An S corporation may have voting and nonvoting common stock, since all shares confer identical rights to distributions and liquidation proceeds (IRC §1361(c)(4)).", ["What defines a class of stock?", "Rights to distribution and liquidation proceeds."],
       {"Keep as written": "Voting differences alone do not create a second class.", "Revise: nonvoting stock is never allowed": "Nonvoting common stock is allowed."}),
     D("c3", "Statement 3: nonresident alien shareholder", ["Keep as written", "Revise: a nonresident alien is not an eligible shareholder", "Revise: a nonresident alien is eligible only if the S corporation has no other shareholders"], "Revise: a nonresident alien is not an eligible shareholder",
       "Eligible shareholders are individuals who are U.S. citizens or residents, estates, and certain trusts and exempt organizations; nonresident aliens are not eligible (IRC §1361(b)(1)(C)).", ["Look at who may hold S stock.", "Citizenship or residency requirement."],
       {"Keep as written": "Consent does not cure ineligibility.", "Revise: a nonresident alien is eligible only if the S corporation has no other shareholders": "There is no such exception."}),
     D("c4", "Statement 4: election deadline", ["Keep as written", "Revise: the 15th day of the fourth month", "Revise: the last day of the tax year"], "Keep as written",
       "Form 2553 must be filed at any time during the preceding tax year or by the 15th day of the third month (2 months and 15 days) of the tax year to be effective for that year (IRC §1362(b)).", ["Two months and 15 days.", "15th day of the third month."],
       {"Revise: the 15th day of the fourth month": "That is one month too late.", "Revise: the last day of the tax year": "Late elections are allowed only through relief procedures."}),
     D("c5", "Statement 5: built-in gains recognition period", ["Keep as written", "Revise: 5 years", "Revise: 15 years"], "Revise: 5 years",
       "The recognition period for the section 1374 tax is 5 years beginning with the first day of the first S corporation year (permanent since 2015).", ["The period is shorter.", "5 years."],
       {"Keep as written": "Ten years was the period under pre-2009 law; the current period is five.", "Revise: 15 years": "The recognition period is 5 years."}),
     D("c6", "Statement 6: passive income termination", ["Keep as written", "Revise: 3 consecutive years", "Revise: 5 consecutive years"], "Revise: 3 consecutive years",
       "An S election terminates if the corporation has C-corporation earnings and profits and passive investment income exceeds 25% of gross receipts for 3 consecutive taxable years (IRC §1362(d)(3)).", ["Test is over multiple years.", "3 consecutive years."],
       {"Keep as written": "Two years is too short.", "Revise: 5 consecutive years": "Termination occurs after 3 consecutive years."})],
    {}, {"area": "V", "group": "B", "topic": "S corporation eligibility, election, and termination", "task": "Identify eligibility, election, and termination rules", "skill": "Analysis"},
    2, 12, cite=["IRC §1361", "IRC §1362", "IRC §1374"], tags=["scorp"]))
for c, (cs, u) in zip(ITEMS[-1]["cells"], [("IRC §1361(b)(1)(A)", "1361"), ("IRC §1361(c)(4)", "1361"), ("IRC §1361(b)(1)(C)", "1361"), ("IRC §1362(b)", "1362"), ("IRC §1374(d)(7)", "1374"), ("IRC §1362(d)(3)", "1362")]):
    c["cite"] = cs
    c["link"] = IRC(u)

# ---------------------------------------------------------------- V-T-023 document review: partnership
ITEMS.append(T(
    "REG-V-T-023", "V", "document_review",
    "Partnership formation and operations: memo review",
    "You are reviewing a memo prepared by a staff accountant for the partners of Lakeview Ventures, a newly formed general partnership that also has a limited partner.",
    "For each numbered statement, choose the option that makes the statement correct. Choose 'Keep as written' if it is already correct.",
    [X("e1", "Draft memo", "memo",
       "1. When a partner contributes appreciated property to the partnership for an interest, the partnership's basis in the property equals its fair market value on the date of contribution.\n"
       "2. Guaranteed payments to a partner for services are treated as distributions and are not deductible by the partnership.\n"
       "3. A partner is taxed on his or her distributive share of partnership income only when the income is distributed to the partner.\n"
       "4. A current cash distribution to a partner in excess of the partner's outside basis results in gain to the partner.\n"
       "5. A general partner's distributive share of ordinary business income is generally subject to self-employment tax, while a limited partner's distributive share generally is not.\n"
       "6. A partner's holding period for a partnership interest received in exchange for a contributed capital asset includes the holding period of the contributed asset.")],
    [D("c1", "Statement 1: partnership's basis in contributed property", ["Keep as written", "Revise: the partnership takes the contributing partner's adjusted basis (carryover basis)", "Revise: the partnership's basis is the FMV, but only if the property is depreciable"], "Revise: the partnership takes the contributing partner's adjusted basis (carryover basis)",
       "No gain or loss is recognized on a contribution for a partnership interest (IRC §721(a)), and the partnership's basis is the contributor's adjusted basis (IRC §723).", ["Nonrecognition on contribution.", "Carryover basis."],
       {"Keep as written": "FMV basis would trigger gain recognition; the partnership takes a carryover basis.", "Revise: the partnership's basis is the FMV, but only if the property is depreciable": "Depreciability does not change the carryover basis rule."}),
     D("c2", "Statement 2: guaranteed payments", ["Keep as written", "Revise: guaranteed payments are ordinary income to the partner and deductible (or capitalized) by the partnership", "Revise: guaranteed payments are capital gain to the partner"], "Revise: guaranteed payments are ordinary income to the partner and deductible (or capitalized) by the partnership",
       "A guaranteed payment for services or the use of capital is treated as made to a nonpartner for the partner's income and the partnership's deduction or capitalization (IRC §707(c)).", ["Payments determined without regard to partnership income.", "Treated like payments to an outsider."],
       {"Keep as written": "Guaranteed payments are not distributions; the partnership deducts them.", "Revise: guaranteed payments are capital gain to the partner": "They are ordinary income."}),
     D("c3", "Statement 3: when the partner is taxed", ["Keep as written", "Revise: the partner is taxed on the distributive share whether or not it is distributed", "Revise: the partner is taxed only on the last day of the partnership year in cash"], "Revise: the partner is taxed on the distributive share whether or not it is distributed",
       "A partnership is a pass-through: partners report their distributive shares of income whether or not distributed (IRC §702(a), §704).", ["Pass-through means...", "Taxed as earned."],
       {"Keep as written": "Taxation does not depend on distribution.", "Revise: the partner is taxed only on the last day of the partnership year in cash": "It is not a cash-basis pass-through requirement."}),
     D("c4", "Statement 4: cash distribution over basis", ["Keep as written", "Revise: the excess reduces basis below zero", "Revise: the excess is taxed as ordinary income in all cases"], "Keep as written",
       "Money distributed in excess of the partner's adjusted basis in the partnership interest is gain from the sale of the interest (IRC §731(a)(1)).", ["Basis cannot be negative.", "Excess is gain."],
       {"Revise: the excess reduces basis below zero": "Outside basis cannot go below zero.", "Revise: the excess is taxed as ordinary income in all cases": "It is generally capital gain (subject to hot assets)."}),
     D("c5", "Statement 5: self-employment tax", ["Keep as written", "Revise: general partners are exempt and limited partners are subject", "Revise: neither is subject to self-employment tax"], "Keep as written",
       "A general partner's distributive share of trade or business income is net earnings from self-employment; a limited partner's distributive share generally is excluded (IRC §1402(a)(13)), except for guaranteed payments for services.", ["Limited partners are passive.", "General partners are subject."],
       {"Revise: general partners are exempt and limited partners are subject": "Reversed.", "Revise: neither is subject to self-employment tax": "General partners are subject."}),
     D("c6", "Statement 6: holding period of the partnership interest", ["Keep as written", "Revise: the holding period starts on the date of the contribution regardless of the asset", "Revise: the holding period is always long-term"], "Keep as written",
       "The holding period of a partnership interest received for a contribution of capital assets or section 1231 property includes the holding period of the contributed property (IRC §1223(1)).", ["Tacking rule.", "Applies to capital and §1231 assets."],
       {"Revise: the holding period starts on the date of the contribution regardless of the asset": "Tacking applies to capital and §1231 assets.", "Revise: the holding period is always long-term": "It depends on the contributed property's holding period."})],
    {}, {"area": "V", "group": "C", "topic": "Partnership formation and operation", "task": "Identify partnership contribution, guaranteed payment, distribution, and SE tax rules", "skill": "Analysis"},
    2, 12, cite=["IRC §721", "IRC §723", "IRC §707(c)", "IRC §731", "IRC §1402(a)(13)", "IRC §1223(1)"], tags=["partnership"]))
for c, (cs, u) in zip(ITEMS[-1]["cells"], [("IRC §721(a); §723", "723"), ("IRC §707(c)", "707"), ("IRC §702(a)", "702"), ("IRC §731(a)(1)", "731"), ("IRC §1402(a)(13)", "1402"), ("IRC §1223(1)", "1223")]):
    c["cite"] = cs
    c["link"] = IRC(u)

# ---------------------------------------------------------------- V-T-024 research
ITEMS.append(T(
    "REG-V-T-024", "V", "research",
    "Locate the authority: corporations and pass-through entities",
    "The owners of a closely held business ask six questions about corporate and pass-through tax rules. Identify the primary authority for each.",
    "For each question, enter the Internal Revenue Code citation (for example, 'IRC 1223(1)'). Give a subsection or paragraph only when the question asks for it.",
    [X("e1", "Questions", "email",
       "1. Which section and subsection provide that no gain or loss is recognized when property is transferred to a corporation solely for stock and the transferors control the corporation immediately afterward?\n"
       "2. Which section and subsection define a corporate 'dividend' (distribution out of earnings and profits)?\n"
       "3. Which section and subsection limit a partner's deduction for partnership losses to the adjusted basis of the partner's interest?\n"
       "4. Which section and subsection impose the tax on net recognized built-in gain of an S corporation?\n"
       "5. Which section, subsection, and paragraph list the decreases in an S shareholder's stock basis (distributions, losses, deductions)?\n"
       "6. Which section, subsection, and paragraph provide that a partner recognizes gain when money distributed exceeds the adjusted basis of the partner's interest?")],
    [C("c1", "Question 1: incorporation nonrecognition", ["351(a)"], "IRC §351(a) nonrecognition on transfers to a controlled corporation.", ["Subchapter C, part III.", "Section 351, subsection (a)."], IRC("351"), partial=["351"]),
     C("c2", "Question 2: definition of dividend", ["316(a)"], "IRC §316(a) defines dividend as any distribution out of E&P accumulated after February 28, 1913, or E&P of the taxable year.", ["Section 316.", "Subsection (a)."], IRC("316"), partial=["316"]),
     C("c3", "Question 3: partner loss limitation", ["704(d)"], "IRC §704(d): a partner's distributive share of loss is allowed only to the extent of the adjusted basis at the end of the year.", ["Section 704 covers partner's distributive share.", "Subsection (d)."], IRC("704"), partial=["704"]),
     C("c4", "Question 4: built-in gains tax", ["1374(a)"], "IRC §1374(a) imposes the tax on net recognized built-in gain.", ["Section 1374.", "Subsection (a)."], IRC("1374"), partial=["1374"]),
     C("c5", "Question 5: decreases in S stock basis", ["1367(a)(2)"], "IRC §1367(a)(2) lists decreases (distributions, losses and deductions, nondeductible expenses, oil and gas depletion).", ["Section 1367.", "Subsection (a), paragraph (2)."], IRC("1367"), partial=["1367", "1367(a)"]),
     C("c6", "Question 6: gain on distribution over basis", ["731(a)(1)"], "IRC §731(a)(1): gain is recognized to the extent money distributed exceeds the adjusted basis.", ["Section 731.", "Subsection (a), paragraph (1)."], IRC("731"), partial=["731", "731(a)"])],
    {}, {"area": "V", "group": "A", "topic": "Research: entity taxation", "task": "Research and cite authority for corporate, S corporation, and partnership issues", "skill": "Application"},
    2, 10, cite=["IRC §351", "IRC §316", "IRC §704(d)", "IRC §1374", "IRC §1367", "IRC §731"], tags=["research"]))
