# Area III (재산거래 과세) 5개
from tbs_lib import *
from tbs_items_1 import IRC, L

ITEMS = []

# ---------------------------------------------------------------- III-T-007 numeric: basis rules (gift, gift tax, inheritance)
ITEMS.append(T(
    "REG-III-T-007", "III", "numeric_table",
    "Basis and gain or loss on gifted and inherited property",
    "Elena Cruz received three blocks of stock in 2026 and sold each one during the year. She has no other transactions. "
    "Enter a loss as a negative number.",
    "Using the exhibit, compute Elena's basis and recognized gain or (loss) for each block. Round to the nearest dollar.",
    [X("e1", "Acquisition and sale data", "table",
       [["Item", "Amount"],
        ["Lot A (gift from her aunt, no gift tax paid): aunt's adjusted basis", "${A_db:,}"],
        ["Lot A: fair market value on the date of gift", "${A_fmv:,}"],
        ["Lot A: sale price in Sale 1", "${A_p1:,}"],
        ["Lot A: alternative sale price in Sale 2", "${A_p2:,}"],
        ["Lot B (gift from her uncle): uncle's adjusted basis", "${B_db:,}"],
        ["Lot B: fair market value on the date of gift", "${B_fmv:,}"],
        ["Lot B: gift tax the uncle paid on the gift", "${gtax:,}"],
        ["Lot B: amount of the gift for gift tax purposes (his annual exclusion was already used)", "${B_gift:,}"],
        ["Lot B: sale price", "${B_p:,}"],
        ["Lot C (inherited from her father): fair market value at date of death", "${C_fmv:,}"],
        ["Lot C: sale price", "${C_p:,}"]]),
     X("e2", "Note", "notes", "Treat Sale 1 and Sale 2 as alternative facts for Lot A (Elena sold Lot A only once). No alternate valuation date was elected for Lot C.")],
    [N("c1", "Lot A: basis used to compute a gain", "A_db", "Gifted property with FMV below the donor's basis has a dual basis. To compute a gain, the carryover (donor's) basis of ${A_db:,} is used.",
       ["FMV at gift ${A_fmv:,} < donor basis ${A_db:,}: dual basis", "Gain basis = donor's basis"], ["Look at FMV versus the donor's basis.", "Depreciated gift property: donor basis for gains, FMV for losses."],
       traps=[("A_fmv", "You used the FMV at the date of gift. That is the loss basis.")]),
     N("c2", "Lot A: basis used to compute a loss", "A_fmv", "The loss basis is the lower of donor basis or FMV at the gift date, here ${A_fmv:,} (IRC §1015(a)).",
       ["Loss basis = lesser of donor basis and FMV = ${A_fmv:,}"], ["Which of the two numbers is lower?", "FMV at gift date."],
       traps=[("A_db", "You used the gain basis. When FMV at the gift date is lower, a loss is measured from FMV.")]),
     N("c3", "Lot A, Sale 1: recognized gain or (loss)", "dual_basis(A_p1, c1, c2)", "Sale 1 price ${A_p1:,} is between the loss basis ${A_fmv:,} and the gain basis ${A_db:,}, so there is neither gain nor loss.",
       ["Price above loss basis and below gain basis", "Gain = 0 and loss = 0"], ["Test the price against both bases.", "Between the two bases means zero."],
       traps=[("A_p1-A_db", "You used only the donor's basis, which shows a loss. The dual-basis rule gives zero when the price falls between the two bases.")], tol=0),
     N("c4", "Lot A, Sale 2: recognized gain or (loss)", "dual_basis(A_p2, c1, c2)", "Sale 2 price ${A_p2:,} is below the loss basis ${A_fmv:,}: loss = ${A_p2:,} - ${A_fmv:,}.",
       ["Loss = price - loss basis", "${A_p2:,} - ${A_fmv:,} = ${c4:,}"], ["Which basis applies when the price is below FMV at the gift date?", "Price minus FMV at gift date."],
       traps=[("A_p2-A_db", "You used the donor's basis for the loss. A loss uses the lower FMV.")]),
     N("c5", "Lot B: adjusted basis after the gift-tax adjustment", "B_db+gtax*(B_fmv-B_db)/B_gift",
       "The donee's basis increases by the part of the gift tax paid attributable to net appreciation: gift tax x (FMV - donor basis) / amount of gift (IRC §1015(d)(6)).",
       ["Net appreciation = ${B_fmv:,} - ${B_db:,}", "Increase = ${gtax:,} x net appreciation / ${B_gift:,}", "Basis = ${B_db:,} + increase = ${c5:,}"],
       ["Only part of the gift tax is added to basis.", "Increase = gift tax x net appreciation / amount of gift."],
       traps=[("B_db+gtax", "You added the entire gift tax. Only the portion attributable to net appreciation is added.")]),
     N("c6", "Lot B: recognized gain", "B_p-c5", "Gain = price - adjusted basis. The price is above the gain basis.",
       ["${B_p:,} - ${c5:,} = ${c6:,}"], ["Price less the basis from the previous cell.", "Use the gift-tax-adjusted basis."],
       traps=[("B_p-B_db", "You ignored the gift-tax adjustment to basis.")]),
     N("c7", "Lot C: recognized gain", "C_p-C_fmv", "Inherited property takes a basis equal to FMV at death (IRC §1014(a)), so gain = ${C_p:,} - ${C_fmv:,}.",
       ["Basis = FMV at date of death = ${C_fmv:,}", "Gain = ${c7:,}"], ["Basis of inherited property is stepped up (or down).", "FMV at the date of death."])],
    {"A_db": 42000, "A_fmv": 30000, "A_p1": 36000, "A_p2": 25000, "B_db": 20000, "B_fmv": 50000, "gtax": 4500, "B_gift": 50000, "B_p": 60000, "C_fmv": 90000, "C_p": 97000},
    {"area": "III", "group": "A", "topic": "Basis of assets", "task": "Determine basis of gifted and inherited property and gain or loss on disposition", "skill": "Application"},
    2, 12, cite=["IRC §1015(a)", "IRC §1015(d)(6)", "IRC §1014(a)"],
    vary={"A_db": [40000, 42000, 45000], "A_p1": [34000, 36000, 38000], "A_p2": [22000, 25000, 27000], "gtax": [3000, 4500, 6000], "B_p": [58000, 60000, 65000], "C_p": [93000, 97000, 101000]},
    guards=["A_fmv < A_p1 < A_db", "A_p2 < A_fmv", "B_p > c5_guard"], derived=[("c5_guard", "B_db+gtax")]))
for c, u in zip(ITEMS[-1]["cells"], ["1015", "1015", "1015", "1015", "1015", "1015", "1014"]):
    c["link"] = IRC(u)

# ---------------------------------------------------------------- III-T-008 numeric: like-kind exchange with boot
ITEMS.append(T(
    "REG-III-T-008", "III", "numeric_table",
    "Like-kind exchange of real property with boot and liabilities",
    "Marlow Holdings LLC (a partnership for tax purposes is not involved; treat Marlow as a single taxpayer) exchanged an office building held for investment "
    "for a different investment office building in a qualifying deferred exchange in 2026. The replacement property was identified and acquired within the required time limits.",
    "Using the exhibit, compute the tax results of the exchange. Round to the nearest dollar.",
    [X("e1", "Exchange data", "table",
       [["Item", "Amount"],
        ["Relinquished building: fair market value", "${fmv_old:,}"],
        ["Relinquished building: adjusted basis", "${adj:,}"],
        ["Mortgage on relinquished building, assumed by the other party", "${mort_old:,}"],
        ["Replacement building: fair market value", "${fmv_new:,}"],
        ["Mortgage on replacement building, assumed by Marlow", "${mort_new:,}"],
        ["Cash received by Marlow", "${cash:,}"]])],
    [N("c1", "Amount realized", "fmv_new+cash+mort_old-mort_new",
       "Amount realized = FMV of property received + cash + liabilities relieved - liabilities assumed = ${fmv_new:,} + ${cash:,} + ${mort_old:,} - ${mort_new:,}.",
       ["${fmv_new:,} + ${cash:,} = ${s1:,}", "+ ${mort_old:,} - ${mort_new:,} = ${c1:,}"], ["Include the mortgage relief and the mortgage assumed.", "Liabilities assumed by Marlow offset liabilities relieved."],
       traps=[("fmv_new+cash", "You left out the net liability relief.")]),
     N("c2", "Realized gain", "c1-adj", "Realized gain = amount realized - adjusted basis.", ["${c1:,} - ${adj:,} = ${c2:,}"], ["Amount realized less adjusted basis.", "Use the previous cell."]),
     N("c3", "Boot received (cash plus net liability relief)", "cash+max(0, mort_old-mort_new)",
       "Boot = cash ${cash:,} + net mortgage relief (${mort_old:,} - ${mort_new:,}). Liabilities assumed offset liabilities relieved.",
       ["Net relief = ${mort_old:,} - ${mort_new:,} = ${nr:,}", "Boot = ${cash:,} + ${nr:,} = ${c3:,}"], ["Boot includes debt relief that is not offset by debt assumed.", "Cash plus net liability relief."],
       traps=[("cash", "You counted cash only. Net relief from the mortgage is also boot."), ("cash+mort_old", "You did not offset the mortgage assumed on the replacement building.")]),
     N("c4", "Recognized gain", "min(c2,c3)", "Recognized gain = lesser of realized gain or boot received (IRC §1031(b)).", ["min(${c2:,}, ${c3:,}) = ${c4:,}"], ["It is limited by both numbers.", "Lesser of realized gain and boot."]),
     N("c5", "Deferred gain", "c2-c4", "Deferred gain = realized gain - recognized gain.", ["${c2:,} - ${c4:,} = ${c5:,}"], ["What part of the realized gain is not taxed now?", "Realized less recognized."]),
     N("c6", "Basis of the replacement building", "fmv_new-c5",
       "Basis of the replacement property = FMV - deferred gain. Check: old basis ${adj:,} - cash ${cash:,} + gain recognized ${c4:,} - liabilities relieved ${mort_old:,} + liabilities assumed ${mort_new:,}.",
       ["${fmv_new:,} - ${c5:,} = ${c6:,}", "Cross-check using the carryover formula gives the same amount"], ["Basis keeps the deferred gain alive.", "FMV of the new property less deferred gain."],
       traps=[("fmv_new", "You used FMV, which would eliminate the deferred gain.")])],
    {"fmv_old": 600000, "adj": 350000, "mort_old": 100000, "fmv_new": 520000, "mort_new": 60000},
    {"area": "III", "group": "B", "topic": "Like-kind exchanges", "task": "Compute recognized gain and basis in a like-kind exchange", "skill": "Application"},
    3, 14, cite=["IRC §1031(a)", "IRC §1031(b)", "IRC §1031(d)", "Reg. §1.1031(d)-2"],
    vary={"fmv_new": [500000, 520000, 540000], "mort_new": [40000, 60000, 80000], "adj": [300000, 350000, 380000]},
    guards=["cash >= 10000", "c2 > c3", "c3 > 0"], derived=[("cash", "(fmv_old-mort_old)-(fmv_new-mort_new)"), ("s1", "fmv_new+cash"), ("nr", "max(0, mort_old-mort_new)")]))
# 위 params 에는 cash 가 파생값이라 발문 표에도 파생값이 들어간다. c1 등은 guard 계산에 필요해 derived 에서 참조할 수 없으므로 guard 는 아래 보조 파생값으로 대체.
ITEMS[-1]["derived"] += [("g_c1", "fmv_new+cash+mort_old-mort_new"), ("g_c2", "g_c1-adj"), ("g_c3", "cash+max(0,mort_old-mort_new)")]
ITEMS[-1]["guards"] = ["cash >= 10000", "g_c2 > g_c3", "g_c3 > 0"]
ITEMS[-1]["scenario"] = ("Marlow Holdings Inc., a C corporation, exchanged an office building held for investment for a different investment office building in a qualifying deferred exchange in 2026. "
                        "The replacement property was identified and acquired within the required time limits.")
for c in ITEMS[-1]["cells"]:
    c["link"] = IRC("1031")

# ---------------------------------------------------------------- III-T-009 document review: recapture, holding period, related parties
ITEMS.append(T(
    "REG-III-T-009", "III", "document_review",
    "Character of gain and loss: review of a client memo",
    "You are reviewing a draft memo to Harlan Reid, an individual who sold several assets in 2026.",
    "For each numbered statement, choose the option that makes the statement correct. Choose 'Keep as written' if it is already correct.",
    [X("e1", "Draft memo to client", "memo",
       "1. Your gain on the sale of the used machinery, to the extent of depreciation you claimed, is unrecaptured section 1250 gain taxed at a maximum 25% rate.\n"
       "2. Your gain on the sale of the office building, depreciated straight line, that is attributable to depreciation taken is unrecaptured section 1250 gain, taxed at a maximum rate of 25%, and there is no ordinary income recapture under section 1250 for straight-line depreciation.\n"
       "3. Your net section 1231 gain for 2026 is treated as ordinary income to the extent of nonrecaptured net section 1231 losses from the previous 3 years.\n"
       "4. The land you held for investment and sold after 9 months at a gain is a long-term capital gain.\n"
       "5. The stock you inherited from your mother and sold six months after her death produces a long-term capital gain or loss, regardless of how long you held it.\n"
       "6. The loss on your sale of a building to a corporation you own 60% by value is a deductible capital loss in 2026.")],
    [D("c1", "Statement 1: machinery gain",
       ["Keep as written", "Revise: the gain up to depreciation taken is ordinary income under section 1245", "Revise: the entire gain is section 1231 gain taxed at 0%, 15%, or 20%"],
       "Revise: the gain up to depreciation taken is ordinary income under section 1245",
       "Personal property (machinery) is section 1245 property: gain up to prior depreciation is recaptured as ordinary income. Unrecaptured section 1250 gain applies only to real property.",
       ["Machinery is personal property.", "Section 1245 recaptures all depreciation as ordinary income."],
       {"Keep as written": "Unrecaptured §1250 gain applies to depreciable real property, not machinery.", "Revise: the entire gain is section 1231 gain taxed at 0%, 15%, or 20%": "§1245 recapture is ordinary income to the extent of depreciation before §1231 treatment."}),
     D("c2", "Statement 2: office building, straight-line depreciation", ["Keep as written", "Revise: the gain attributable to depreciation is ordinary income under section 1250", "Revise: the gain is taxed at a maximum 20% with no special rate"], "Keep as written",
       "Gain on depreciable real property attributable to straight-line depreciation is unrecaptured §1250 gain (max 25% for individuals) and there is no ordinary recapture under §1250 because only excess (accelerated) depreciation is recaptured.",
       ["Straight-line versus accelerated.", "Ordinary recapture under §1250 covers only additional depreciation."],
       {"Revise: the gain attributable to depreciation is ordinary income under section 1250": "Only additional depreciation over straight line is ordinary income under §1250.", "Revise: the gain is taxed at a maximum 20% with no special rate": "The portion attributable to depreciation is taxed at up to 25%."}),
     D("c3", "Statement 3: section 1231 look-back", ["Keep as written", "Revise: 5 years", "Revise: 10 years"], "Revise: 5 years",
       "Net §1231 gain is recharacterized as ordinary income to the extent of nonrecaptured net §1231 losses of the five preceding years (IRC §1231(c)).",
       ["The look-back is longer than three years.", "Five years."], {"Keep as written": "The look-back is 5 years.", "Revise: 10 years": "The look-back is 5 years, not 10."}),
     D("c4", "Statement 4: holding period of land", ["Keep as written", "Revise: it is a short-term capital gain because the holding period was one year or less", "Revise: it is a section 1231 gain"], "Revise: it is a short-term capital gain because the holding period was one year or less",
       "Long-term treatment requires holding the asset more than one year. Land held for investment for 9 months produces a short-term gain, taxed at ordinary rates.",
       ["Count the holding period.", "More than one year is required."], {"Keep as written": "Nine months is not more than a year.", "Revise: it is a section 1231 gain": "§1231 requires a holding period of more than one year for property used in a business."}),
     D("c5", "Statement 5: inherited stock", ["Keep as written", "Revise: it is short-term because the holding period was under one year", "Revise: it is long-term only if held over one year after death"], "Keep as written",
       "Property acquired from a decedent is treated as held more than one year (IRC §1223(9)), whenever it is sold.",
       ["Special rule for inherited property.", "Automatic long-term treatment."], {"Revise: it is short-term because the holding period was under one year": "Inherited property gets automatic long-term treatment.", "Revise: it is long-term only if held over one year after death": "The one-year test does not apply to inherited property."}),
     D("c6", "Statement 6: sale to a controlled corporation", ["Keep as written", "Revise: the loss is disallowed because the buyer is a related person", "Revise: the loss is deductible but only as an ordinary loss"], "Revise: the loss is disallowed because the buyer is a related person",
       "A loss on a sale between a taxpayer and a corporation owned more than 50% by the taxpayer is disallowed (IRC §267(a)(1), (b)(2)). The buyer may use the disallowed loss to reduce gain on its later sale (§267(d)).",
       ["Ownership above 50% makes them related persons.", "Loss disallowed."], {"Keep as written": "Loss on related-party sales is disallowed.", "Revise: the loss is deductible but only as an ordinary loss": "Character is irrelevant when the loss is disallowed."})],
    {}, {"area": "III", "group": "C", "topic": "Character of gain and loss", "task": "Identify recapture, holding period, and related-party rules", "skill": "Analysis"},
    2, 12, cite=["IRC §1245", "IRC §1250", "IRC §1231(c)", "IRC §1223(9)", "IRC §267"], tags=["recapture"]))
for c, (cs, u) in zip(ITEMS[-1]["cells"], [("IRC §1245(a)", "1245"), ("IRC §1(h)(6); §1250", "1250"), ("IRC §1231(c)", "1231"), ("IRC §1222", "1222"), ("IRC §1223(9)", "1223"), ("IRC §267(a)(1), (b)(2)", "267")]):
    c["cite"] = cs
    c["link"] = IRC(u)

# ---------------------------------------------------------------- III-T-010 research
ITEMS.append(T(
    "REG-III-T-010", "III", "research",
    "Locate the authority: property transactions",
    "A client's controller asks six questions about the tax treatment of property transactions. Identify the primary authority that answers each one.",
    "For each question, enter the Internal Revenue Code citation (for example, 'IRC 1223(9)'). Provide the subsection or paragraph only when the question asks for it.",
    [X("e1", "Questions", "email",
       "1. Which section allows an individual to exclude gain on the sale of a principal residence? (Section only.)\n"
       "2. Which section and subsection give the general rule for the basis of property acquired from a decedent?\n"
       "3. Which section and subsection disallow a loss on a wash sale of stock?\n"
       "4. Which section, subsection, and paragraph disallow a loss on a sale between related persons?\n"
       "5. Which section and subsection provide that no gain or loss is recognized on an exchange of real property held for productive use in a trade or business or for investment?\n"
       "6. Which section and subsection state that income from an installment sale is taken into account under the installment method?")],
    [C("c1", "Question 1: exclusion of gain on the sale of a principal residence", ["121", "121(a)"], "IRC §121(a) excludes up to $250,000 ($500,000 joint) of gain if ownership and use tests are met.", ["Part III of subchapter B.", "Section 121."], IRC("121")),
     C("c2", "Question 2: basis of property acquired from a decedent", ["1014(a)", "1014(a)(1)"], "IRC §1014(a)(1): basis is the FMV at the decedent's death (or alternate valuation date).", ["Section 1014, first subsection.", "Subsection (a)."], IRC("1014"), partial=["1014"]),
     C("c3", "Question 3: wash sale loss disallowance", ["1091(a)"], "IRC §1091(a) disallows the loss if substantially identical stock is acquired within 30 days before or after the sale.", ["Section 1091.", "Subsection (a) states the rule."], IRC("1091"), partial=["1091"]),
     C("c4", "Question 4: related-party loss disallowance", ["267(a)(1)"], "IRC §267(a)(1) disallows losses on sales or exchanges between persons specified in subsection (b).", ["Section 267, subsection (a).", "Paragraph (1)."], IRC("267"), partial=["267", "267(a)"]),
     C("c5", "Question 5: nonrecognition on like-kind exchanges", ["1031(a)(1)", "1031(a)"], "IRC §1031(a)(1) applies to real property held for productive use in trade or business or for investment (personal property is excluded after 2017).", ["Section 1031.", "Subsection (a), paragraph (1)."], IRC("1031"), partial=["1031"]),
     C("c6", "Question 6: installment method", ["453(a)"], "IRC §453(a) requires the installment method for installment sales unless the taxpayer elects out under §453(d).", ["Section 453.", "Subsection (a)."], IRC("453"), partial=["453"])],
    {}, {"area": "III", "group": "A", "topic": "Research: property transactions", "task": "Research and cite authority for property transactions", "skill": "Application"},
    2, 10, cite=["IRC §121", "IRC §1014", "IRC §1091", "IRC §267", "IRC §1031", "IRC §453"], tags=["research"]))

# ---------------------------------------------------------------- III-T-011 dropdown: cost recovery
REC = ["3-year", "5-year", "7-year", "15-year", "27.5-year", "39-year", "Not depreciable"]
ITEMS.append(T(
    "REG-III-T-011", "III", "dropdown_judgment",
    "Cost recovery: recovery periods and bonus depreciation",
    "Juniper Properties LLC is a calendar-year business that placed several assets into service in 2026. All assets were acquired new, after January 19, 2025, for business or rental use in the United States.",
    "For each asset, select the MACRS recovery period. For the last item, select the bonus depreciation percentage.",
    [X("e1", "Assets placed in service", "table",
       [["Asset", "Use"],
        ["Computer equipment", "Office"],
        ["Office furniture", "Office"],
        ["Apartment building (residential rental)", "Rental"],
        ["Warehouse building (nonresidential)", "Used in business"],
        ["Land under the warehouse", "Used in business"],
        ["Paved parking lot and fencing (land improvements)", "Used in business"],
        ["New machinery acquired February 3, 2026, placed in service February 2026", "Used in business"]]),
     X("e2", "Law note", "statute_note", "Public Law 119-21 (2025) made 100% bonus depreciation under section 168(k) permanent for qualified property acquired after January 19, 2025. Treat this law as effective for the 2026 exam window starting July 1, 2026.")],
    [D("c1", "Recovery period: computer equipment", REC, "5-year", "Computers and peripheral equipment are 5-year property (IRC §168(e)(3)(B)).", ["Computers are listed by name in the Code.", "Five years."], {}),
     D("c2", "Recovery period: office furniture", REC, "7-year", "Office furniture and fixtures are 7-year property (Rev. Proc. 87-56 asset class 00.11).", ["Default class for property with no class life.", "Seven years."], {}),
     D("c3", "Recovery period: apartment building", REC, "27.5-year", "Residential rental property is depreciated straight line over 27.5 years (IRC §168(c)).", ["Residential rental, mid-month convention.", "27.5 years."], {}),
     D("c4", "Recovery period: warehouse building", REC, "39-year", "Nonresidential real property is depreciated straight line over 39 years (IRC §168(c)).", ["Not residential.", "39 years."], {}),
     D("c5", "Recovery period: land under the warehouse", REC, "Not depreciable", "Land is not depreciable; it has no determinable useful life (Reg. §1.167(a)-2).", ["Does land wear out?", "No cost recovery."], {}),
     D("c6", "Recovery period: parking lot and fencing", REC, "15-year", "Land improvements such as sidewalks, roads, fences, and parking lots are 15-year property (asset class 00.3).", ["Improvements to land are not land.", "15-year property, 150% declining balance."], {}),
     D("c7", "Bonus depreciation percentage for the machinery", ["0% (no bonus)", "20%", "40%", "60%", "100%"], "100%", "Under P.L. 119-21, qualified property acquired after January 19, 2025 qualifies for 100% bonus depreciation, permanently.", ["Look at the law note and the acquisition date.", "The phase-down of TCJA was repealed for this property."], {})],
    {}, {"area": "III", "group": "D", "topic": "Cost recovery", "task": "Determine MACRS recovery periods and bonus depreciation", "skill": "Application"},
    2, 10, testable_from="2026-07-01", cite=["IRC §168(c)", "IRC §168(e)", "IRC §168(k)", "Notice 2026-11"],
    law_note="OBBBA (P.L. 119-21) §70301 restores 100% bonus for property acquired after 2025-01-19; testable from 2026-07-01 (AICPA six-month rule).", tags=["macrs", "bonus"]))
for c, u in zip(ITEMS[-1]["cells"], ["168", "168", "168", "168", "167", "168", "168"]):
    c["link"] = IRC(u)

# [검산반영] III-T-011: 오답 보기마다 해설(SPEC 5-6)
_PER = {"3-year": "3-year property covers items such as certain tractor units and racehorses, not this asset.",
        "5-year": "5-year property covers items such as cars, light trucks, and computers.",
        "7-year": "7-year property is the default class for furniture, fixtures, and most machinery.",
        "15-year": "15-year property covers land improvements such as paving and fencing.",
        "27.5-year": "27.5 years applies only to residential rental real property.",
        "39-year": "39 years applies to nonresidential real property (the building, not the land).",
        "Not depreciable": "Only land and other property with no determinable life is not depreciable."}
_BON = {"60%": "60% was the TCJA phase-down rate for 2024 placed-in-service property, not for property acquired after January 19, 2025.",
        "20%": "20% was the TCJA phase-down rate for 2026 under prior law, which P.L. 119-21 replaced for property acquired after January 19, 2025.",
        "40%": "40% is only an optional election for property placed in service in the first tax year ending after January 19, 2025; the default rate is 100%.",
        "0% (no bonus)": "Bonus depreciation was not eliminated; it is permanent at 100% for this property."}
for _t in ITEMS:
    if _t["id"] == "REG-III-T-011":
        for _c in _t["cells"]:
            if not _c["wrong_msgs"]:
                _tbl = _BON if _c["id"] == "c7" else _PER
                _c["wrong_msgs"] = {o: (_tbl[o] + " The correct answer is %s." % _c["answer"]) for o in _c["options"] if o != _c["answer"]}
