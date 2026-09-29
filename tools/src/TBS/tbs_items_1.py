# Area I (윤리·직무책임·연방세 절차) 3개, Area II (경영법) 3개
from tbs_lib import *

def IRC(sec):
    return "https://www.law.cornell.edu/uscode/text/26/" + sec

def CIR(sec):
    return "https://www.law.cornell.edu/cfr/text/31/" + sec

def L(c, cite, url=None):
    c["cite"] = cite
    if url:
        c["link"] = url
    return c

ITEMS = []

# ---------------------------------------------------------------- I-T-001 numeric
ITEMS.append(T(
    "REG-I-T-001", "I", "numeric_table",
    "Late-filing and late-payment penalties",
    "Priya Nair, a calendar-year individual, did not request an extension for her 2025 Form 1040, which was due April 15, 2026. "
    "She has never been late before and no exception (reasonable cause, military, disaster) applies.",
    "Using Exhibits 1 and 2, compute the penalties assessed under the failure-to-file and failure-to-pay provisions. Ignore interest, "
    "the minimum failure-to-file penalty, and any estimated-tax penalty. Round to the nearest dollar.",
    [X("e1", "Return summary (2025 Form 1040)", "return_excerpt",
       [["Total tax (line 24)", "${tax:,}"], ["Federal income tax withheld", "${wh:,}"], ["Estimated payments", "$0"],
        ["Balance due shown on return", "${bal:,}"]]),
     X("e2", "Filing and payment history", "notes",
       "Scenario A: Priya filed the return and paid the full balance due on August 3, 2026.\n"
       "Scenario B (alternative facts): Priya filed the return and paid the full balance due on November 10, 2026.\n"
       "In both scenarios, no part of the balance was paid before the filing date and no penalty was abated.")],
    [N("c1", "Scenario A: number of months (or partial months) the return and payment were late", "4",
       "A partial month counts as a full month. April 16 to May 15 is month 1; July 16 to August 15 is month 4, and August 3 falls in month 4.",
       ["Month 1 ends May 15; month 2 ends June 15; month 3 ends July 15", "August 3 is inside month 4 (July 16 to August 15)", "Answer: 4"],
       ["Each month or part of a month counts in full.", "Count month boundaries from the April 16 start: the 15th of each following month."],
       traps=[("3", "You counted whole months only. A partial month counts as a full month.")], tol=0, fmt="n", ecf=False),
     N("c2", "Scenario A: failure-to-file penalty", "bal*(0.05-0.005)*c1",
       "The failure-to-file penalty is 5% per month, but it is reduced by the 0.5% failure-to-payment penalty for each month both apply. Net 4.5% x 4 months x ${bal:,}.",
       ["Net monthly FTF rate = 5.0% - 0.5% = 4.5%", "4.5% x {c1} months x ${bal:,} = ${c2:,}"],
       ["Two penalties overlap in the early months. What happens to the 5% rate?", "Net FTF rate is 4.5% per month while the FTP penalty is also running."],
       traps=[("bal*0.05*c1", "You used the full 5% and did not reduce it by the 0.5% FTP penalty (the FTP and FTF penalties overlap).")]),
     N("c3", "Scenario A: failure-to-pay penalty", "bal*0.005*c1",
       "Failure to pay is 0.5% of the unpaid tax per month or partial month, up to 25%.",
       ["0.5% x {c1} months x ${bal:,} = ${c3:,}"],
       ["The FTP rate is small; it runs for each month the tax is unpaid.", "0.5% per month or part of a month."]),
     N("c4", "Scenario A: total penalties", "c2+c3",
       "Total = FTF + FTP. Combined they equal 5% per month, or {c1} x 5% x ${bal:,}.",
       ["${c2:,} + ${c3:,} = ${c4:,}", "Check: 5% x {c1} x ${bal:,} = ${c4:,}"],
       ["Add the two penalties.", "Combined rate for the first five months is 5% per month."]),
     N("c5", "Scenario B (filed November 10, 2026): failure-to-file penalty", "bal*0.045*min(7,5)",
       "November 10 is month 7 (October 16 to November 15). The FTF penalty stops after 5 months (25% cap; net 4.5% x 5 = 22.5% while overlapping FTP).",
       ["Months late = 7; FTF applies only 5 months", "4.5% x 5 x ${bal:,} = ${c5:,}"],
       ["The failure-to-file penalty has a maximum number of months.", "FTF caps at 25% total (5 months at 5%). Only 5 months of net 4.5% apply here."],
       traps=[("bal*0.045*7", "You applied the FTF penalty for all 7 months. It caps at 5 months.")]),
     N("c6", "Scenario B: total penalties (FTF + FTP)", "c5+bal*0.005*7",
       "FTP keeps running for all 7 months (0.5% x 7 = 3.5%; the cap is 25% after 50 months). Total = FTF {c5:,} + FTP.",
       ["FTP = 0.5% x 7 x ${bal:,} = ${ftp7:,}", "Total = ${c5:,} + ${ftp7:,} = ${c6:,}"],
       ["FTP is not capped until much later.", "FTP months = 7; total penalty rate = 22.5% + 3.5% = 26%."],
       traps=[("bal*0.05*7", "You used 5% for all 7 months.")])],
    {"tax": 31000, "wh": 17000},
    {"area": "I", "group": "C", "topic": "Federal tax procedures: penalties", "task": "Compute failure-to-file and failure-to-pay penalties", "skill": "Application"},
    2, 10,
    cite=["IRC §6651(a)(1)", "IRC §6651(a)(2)", "IRC §6651(c)(1)"],
    vary={"tax": [26000, 29000, 31000, 34000, 37000, 40000], "wh": [12000, 17000, 20000]},
    guards=["bal >= 6000"],
    derived=[("bal", "tax-wh"), ("ftp7", "rnd(bal*0.005*7)")],
    tags=["penalties", "6651"]))
ITEMS[-1]["cells"][0]["cite"] = "IRC §6651(a)"
ITEMS[-1]["cells"][1]["link"] = IRC("6651")

# ---------------------------------------------------------------- I-T-002 document review
def _dr_opts(a, b, c):
    return [a, b, c]

ITEMS.append(T(
    "REG-I-T-002", "I", "document_review",
    "Circular 230 practice memo review",
    "You are a senior at Halvorsen & Wu, CPAs, a firm that prepares individual and business returns. The firm's tax director drafted a memo "
    "to staff on Treasury Department Circular 230 and preparer penalties. You review it before it is distributed.",
    "For each numbered statement in the memo, choose the option that makes the statement correct. Choose 'Keep as written' if the statement is already correct.",
    [X("e1", "Draft staff memo", "memo",
       "TO: Tax staff    FROM: Tax Director    RE: Practice standards (draft)\n\n"
       "1. When a client's prior-year depreciation schedule conflicts with this year's asset list, a practitioner who has relied on the client for years may rely on the schedule without inquiry.\n"
       "2. If we learn that a client omitted income from a previously filed return, we must promptly advise the client of the omission and the consequences, but we are not required to file an amended return or notify the IRS.\n"
       "3. Written informed consent for a conflict of interest must be retained and available to the IRS for at least 24 months after the representation ends.\n"
       "4. A practitioner who publishes a fee schedule must adhere to the published fees for at least 90 calendar days after the last date of publication.\n"
       "5. The penalty for a return-preparer understatement caused by an unreasonable position (without willful or reckless conduct) is the greater of $500 or 25% of the income derived from the return.\n"
       "6. For an income tax return position that is disclosed on the return (and is not a tax shelter or reportable transaction), a preparer needs at least a reasonable basis to avoid the return-preparer penalty."),
     X("e2", "Firm policy note", "notes", "Assume all engagements are for federal income tax return preparation by a CPA who is a practitioner under Circular 230 and a tax return preparer under the Code.")],
    [D("c1", "Statement 1: reliance on client information",
       ["Keep as written", "Revise: the practitioner must make reasonable inquiries when information appears incorrect, inconsistent, or incomplete", "Revise: the practitioner must independently audit every client figure against source documents"],
       "Revise: the practitioner must make reasonable inquiries when information appears incorrect, inconsistent, or incomplete",
       "A practitioner may rely in good faith on client information without verifying it, but may not ignore the implications of information known to him or her and must make reasonable inquiries when information appears incorrect, inconsistent, or incomplete (Circular 230 §10.34(d)).",
       ["Good-faith reliance is allowed. What limits it?", "Look at the words 'appears incorrect, inconsistent, or incomplete'."],
       {"Keep as written": "Reliance is not unlimited. A known conflict triggers a duty of reasonable inquiry.", "Revise: the practitioner must independently audit every client figure against source documents": "Overstated. There is no duty to audit everything; the duty is reasonable inquiry when a red flag appears."}),
     D("c2", "Statement 2: discovered error on a prior return",
       ["Keep as written", "Revise: the practitioner must file an amended return without the client's consent", "Revise: the practitioner must report the omission to the IRS within 30 days"],
       "Keep as written",
       "Section 10.21 requires prompt advice to the client of the noncompliance, error, or omission and its consequences (including penalties). It does not require the practitioner to amend the return or disclose to the IRS, and the confidentiality rule of IRC §7216 generally prohibits disclosure without the client's consent.",
       ["Think about who decides whether to correct the return.", "Advising the client is required; acting on the client's behalf without consent is not."],
       {"Revise: the practitioner must file an amended return without the client's consent": "The practitioner cannot amend a client's return without the client's consent.", "Revise: the practitioner must report the omission to the IRS within 30 days": "There is no duty to report the client to the IRS; disclosure is generally prohibited without consent."}),
     D("c3", "Statement 3: retention period for conflict-of-interest consent",
       ["Keep as written", "Revise: 12 months", "Revise: 36 months"],
       "Revise: 36 months",
       "Under §10.29(c), the written informed consent must be retained by the practitioner and made available to the IRS for at least 36 months after the conclusion of the representation.",
       ["A three-year window matches the general assessment period.", "The regulation says at least 36 months."],
       {"Keep as written": "24 months is too short; the requirement is 36 months.", "Revise: 12 months": "12 months is too short; the requirement is 36 months."}),
     D("c4", "Statement 4: published fee schedules",
       ["Keep as written", "Revise: 30 calendar days", "Revise: 12 months"],
       "Revise: 30 calendar days",
       "A practitioner may publish fee information but must adhere to published fees for at least 30 calendar days after the last date of publication (Circular 230 §10.30(b)).",
       ["Advertising rule; the period is short.", "It is a 30-day rule."],
       {"Keep as written": "90 days overstates the requirement. It is 30 calendar days.", "Revise: 12 months": "A year is far longer than the rule. It is 30 calendar days."}),
     D("c5", "Statement 5: preparer penalty amount, unreasonable position",
       ["Keep as written", "Revise: the greater of $1,000 or 50% of the income derived", "Revise: the greater of $5,000 or 75% of the income derived"],
       "Revise: the greater of $1,000 or 50% of the income derived",
       "IRC §6694(a) penalty is the greater of $1,000 or 50% of the income the preparer derives from the return. The $5,000 / 75% amounts apply to willful or reckless conduct under §6694(b).",
       ["Two tiers exist; this one is the lower tier.", "Lower tier: $1,000 or 50%."],
       {"Keep as written": "The amounts $500 and 25% are not the current §6694(a) amounts.", "Revise: the greater of $5,000 or 75% of the income derived": "That is the willful or reckless tier, §6694(b). The statement excludes willful or reckless conduct."}),
     D("c6", "Statement 6: standard for a disclosed position",
       ["Keep as written", "Revise: the preparer needs substantial authority even if the position is disclosed", "Revise: the preparer needs a more-likely-than-not level of confidence"],
       "Keep as written",
       "For a nonshelter position, a preparer avoids the §6694(a) penalty if there is substantial authority, or the position is disclosed and has a reasonable basis.",
       ["Disclosure lowers the required standard.", "Undisclosed: substantial authority. Disclosed: reasonable basis."],
       {"Revise: the preparer needs substantial authority even if the position is disclosed": "Substantial authority is the standard for undisclosed positions.", "Revise: the preparer needs a more-likely-than-not level of confidence": "That is the standard for tax shelters and reportable transactions."})],
    {}, {"area": "I", "group": "B", "topic": "Circular 230 and preparer penalties", "task": "Identify practitioner duties and preparer penalties", "skill": "Analysis"},
    2, 12, cite=["31 CFR §10.21", "31 CFR §10.29", "31 CFR §10.30", "31 CFR §10.34", "IRC §6694"], tags=["circular230", "6694"]))
for c, (cite, url) in zip(ITEMS[-1]["cells"], [("31 CFR §10.34(d)", CIR("10.34")), ("31 CFR §10.21", CIR("10.21")), ("31 CFR §10.29(c)", CIR("10.29")),
                                               ("31 CFR §10.30(b)", CIR("10.30")), ("IRC §6694(a)", IRC("6694")), ("IRC §6694(a)(2)", IRC("6694"))]):
    c["cite"] = cite
    c["link"] = url

# ---------------------------------------------------------------- I-T-003 research
ITEMS.append(T(
    "REG-I-T-003", "I", "research",
    "Locate the authority: procedures and penalties",
    "A client asks six questions about penalties and procedures. You must identify the Internal Revenue Code section or Circular 230 section that answers each one.",
    "For each question, enter the citation of the most specific primary authority that answers it. "
    "Enter Code sections as, for example, 'IRC 6672(a)'. Enter Circular 230 sections as, for example, '31 CFR 10.29'. Include a subsection only when the question asks for it.",
    [X("e1", "Client questions", "email",
       "From: client\n1. Which Code section imposes the accuracy-related penalty of 20% on an underpayment due to negligence? Give the section and subsection that states the 20% rate.\n"
       "2. Which Code section sets the general 3-year period during which the IRS may assess tax after a return is filed? (Give section and subsection.)\n"
       "3. Which Code section penalizes a return preparer for an understatement due to an unreasonable position? (Give section and subsection.)\n"
       "4. Which Code section makes it a crime, and imposes a penalty, for a preparer to disclose or use tax return information without consent, other than as allowed? (Section only.)\n"
       "5. Which Circular 230 section governs conflicts of interest for practitioners? (31 CFR section only.)\n"
       "6. Which Code section imposes the failure-to-file penalty (5% per month)? (Give section and subsection.)")],
    [C("c1", "Question 1: accuracy-related penalty, 20% rate", ["6662(a)"], "IRC §6662(a) imposes the 20% accuracy-related penalty; §6662(b) lists the causes, including negligence.", ["Chapter 68, subchapter A, Part II.", "Section 6662, the first subsection states the rate."], IRC("6662"), partial=["6662"]),
     C("c2", "Question 2: general assessment period", ["6501(a)"], "IRC §6501(a): tax must be assessed within 3 years after the return was filed.", ["Chapter 66, limitations.", "Section 6501, subsection (a)."], IRC("6501"), partial=["6501"]),
     C("c3", "Question 3: preparer penalty, unreasonable position", ["6694(a)"], "IRC §6694(a) penalty for understatement due to unreasonable positions; (b) is willful or reckless conduct.", ["Chapter 68, Part I subchapter B.", "Section 6694, first subsection."], IRC("6694"), partial=["6694"]),
     C("c4", "Question 4: unauthorized disclosure or use of return information", ["7216"], "IRC §7216 criminal penalty; §6713 is the parallel civil penalty. The question asks for the criminal provision.", ["Chapter 75, crimes.", "Section 7216."], IRC("7216")),
     C("c5", "Question 5: conflicts of interest under Circular 230", ["10.29"], "31 CFR §10.29: a practitioner may not represent conflicting interests without informed written consent.", ["Subpart B of Circular 230.", "Section 10.29."], CIR("10.29"), ask="31 CFR section"),
     C("c6", "Question 6: failure-to-file penalty", ["6651(a)(1)"], "IRC §6651(a)(1) failure to file; (a)(2) failure to pay; (a)(3) failure to pay after notice.", ["Chapter 68 addition to tax.", "Section 6651, paragraph (1) of subsection (a)."], IRC("6651"), partial=["6651", "6651(a)"])],
    {}, {"area": "I", "group": "C", "topic": "Federal tax procedures: authority", "task": "Research and cite authoritative sources", "skill": "Application"},
    2, 10, cite=["IRC §6662", "IRC §6501", "IRC §6694", "IRC §7216", "31 CFR §10.29", "IRC §6651"], tags=["research"]))

# ---------------------------------------------------------------- II-T-004 dropdown (UCC 9)
ITEMS.append(T(
    "REG-II-T-004", "II", "dropdown_judgment",
    "Secured transactions: attachment, perfection, priority",
    "Tomas Appliances Inc. sells refrigerators and delivery vans in State X, which has adopted UCC Article 9. Tomas has borrowed from several lenders and sells to retail customers.",
    "For each scenario in the exhibits, select the correct outcome.",
    [X("e1", "Financing history", "notes",
       "Lender A (First Bank): security agreement covers all present and after-acquired inventory. Financing statement filed March 1, 2026.\n"
       "Lender B (Coolco, a supplier): sold Tomas a new shipment of refrigerators on credit on June 10, 2026, and took a security interest in that shipment to secure the price."),
     X("e2", "Scenarios", "notes",
       "1. B filed a financing statement on June 5, and sent Lender A an authenticated notice on June 5 that it would acquire a purchase-money security interest in the refrigerators. Tomas took delivery June 10. As to the June shipment, who has priority?\n"
       "2. Alternative facts: B filed its financing statement on June 15, five days after delivery, and gave no notice to A. As to the June shipment, who has priority?\n"
       "3. Lena, a retail customer, bought a refrigerator from Tomas's showroom in the ordinary course of business. She knew that First Bank had a lien on Tomas's inventory. As to the refrigerator, does First Bank's security interest continue?\n"
       "4. First Bank also holds a perfected security interest in a delivery van (equipment). Tomas sold the van to Sam, a friend, outside the ordinary course of business. First Bank did not authorize the sale. Does the security interest continue?\n"
       "5. First Bank's financing statement was filed March 1, 2026. If no continuation statement is filed, when does perfection by that filing lapse?\n"
       "6. Nia bought a $900 washing machine for personal use from Tomas on credit. Tomas retained a purchase-money security interest in it. To perfect, must Tomas file a financing statement?")],
    [D("c1", "Scenario 1: priority in the June shipment", ["Lender B (Coolco)", "Lender A (First Bank)", "Equal; they share pro rata"], "Lender B (Coolco)",
       "A purchase-money security interest in inventory has priority over a conflicting earlier-filed interest if the PMSI holder perfects by the time the debtor receives possession and gives A authenticated notice before delivery (UCC §9-324(b)).",
       ["First to file is only the default rule.", "PMSI super-priority in inventory requires filing plus advance notice to prior filers."],
       {"Lender A (First Bank)": "A filed first, but B met the PMSI conditions (perfected and notified before delivery).", "Equal; they share pro rata": "Article 9 has no pro rata sharing for competing perfected security interests."}),
     D("c2", "Scenario 2: priority in the June shipment", ["Lender A (First Bank)", "Lender B (Coolco)", "Equal; they share pro rata"], "Lender A (First Bank)",
       "B did not perfect by the time Tomas took possession and gave no notice, so it loses PMSI super-priority. The default rule is first to file or perfect (§9-322(a)(1)); A filed first.",
       ["Was B's PMSI status preserved?", "Late filing and no notice means the default first-to-file rule applies."],
       {"Lender B (Coolco)": "B missed the PMSI conditions: it filed after delivery and gave no notice.", "Equal; they share pro rata": "Article 9 has no pro rata sharing for competing perfected security interests."}),
     D("c3", "Scenario 3: sale to a buyer in ordinary course", ["No; Lena takes free of the security interest", "Yes; First Bank can repossess the refrigerator because it is perfected", "Yes, because Lena knew of the lien"], "No; Lena takes free of the security interest",
       "A buyer in ordinary course takes free of a security interest created by the seller, even if perfected and even if the buyer knows it exists (UCC §9-320(a)). The bank's remedy is the sale proceeds.",
       ["Buyers of inventory from a merchant are protected.", "The buyer's knowledge that a lien exists does not defeat the protection."],
       {"Yes; First Bank can repossess the refrigerator because it is perfected": "Perfection does not defeat a buyer in ordinary course.", "Yes, because Lena knew of the lien": "Knowledge of the security interest's existence is irrelevant; only knowledge that the sale violates the security agreement matters."}),
     D("c4", "Scenario 4: sale of equipment outside the ordinary course", ["Yes; the security interest continues in the van", "No; Sam takes free because he gave value", "No; the security interest is automatically terminated by any sale"], "Yes; the security interest continues in the van",
       "A security interest continues in collateral notwithstanding sale unless the secured party authorized the disposition free of the security interest (UCC §9-315(a)(1)). Sam is not a buyer in ordinary course of a merchant selling that kind of goods.",
       ["Continuing lien is the default rule.", "Exceptions require the secured party's authorization or buyer-in-ordinary-course status."],
       {"No; Sam takes free because he gave value": "Giving value is not enough. The lien continues absent authorization.", "No; the security interest is automatically terminated by any sale": "Sale does not terminate the security interest without authorization."}),
     D("c5", "Scenario 5: lapse of the March 1, 2026 filing", ["March 1, 2031", "March 1, 2029", "March 1, 2036"], "March 1, 2031",
       "A financing statement is effective for 5 years after filing, unless a continuation statement is filed within the six months before the fifth anniversary (UCC §9-515(a), (d)).",
       ["The effective period is a fixed number of years.", "Five years."],
       {"March 1, 2029": "That would be 3 years. The period is 5 years.", "March 1, 2036": "That would be 10 years. Article 9 has no general 10-year period; 30 years applies only to public-finance and manufactured-home transactions (UCC §9-515(b))."}),
     D("c6", "Scenario 6: PMSI in consumer goods", ["No; a PMSI in consumer goods is automatically perfected on attachment", "Yes; filing is the only method of perfection for consumer goods", "Yes; the seller must take possession of the washing machine"], "No; a PMSI in consumer goods is automatically perfected on attachment",
       "A purchase-money security interest in consumer goods is perfected automatically on attachment (UCC §9-309(1)). Filing is not required, though the buyer of consumer goods can still defeat an unfiled interest in some resales.",
       ["Consumer goods purchases have a special rule.", "Automatic perfection for PMSI in consumer goods."],
       {"Yes; filing is the only method of perfection for consumer goods": "Automatic perfection makes filing unnecessary for a PMSI in consumer goods.", "Yes; the seller must take possession of the washing machine": "Possession is not required; the interest is perfected on attachment."})],
    {}, {"area": "II", "group": "C", "topic": "Debtor-creditor relationships: secured transactions", "task": "Determine perfection and priority", "skill": "Application"},
    3, 14, cite=["UCC §9-324(b)", "UCC §9-320(a)", "UCC §9-315(a)", "UCC §9-515", "UCC §9-309(1)"], tags=["ucc9"]))
for c, s in zip(ITEMS[-1]["cells"], ["UCC §9-324(b)", "UCC §9-322(a)(1); §9-324(b)", "UCC §9-320(a)", "UCC §9-315(a)(1)", "UCC §9-515(a),(d)", "UCC §9-309(1)"]):
    c["cite"] = s

# ---------------------------------------------------------------- II-T-005 dropdown (UCC 2)
ITEMS.append(T(
    "REG-II-T-005", "II", "dropdown_judgment",
    "Sales of goods under UCC Article 2",
    "Northwind Supply Co. and Baker Bikes LLC are merchants in State X, which has adopted UCC Article 2. The parties exchanged several communications about a bicycle-parts purchase.",
    "For each scenario, select the correct outcome.",
    [X("e1", "Facts and correspondence", "email",
       "1. On May 2, Baker orally agreed to buy $8,000 of parts from Northwind. On May 5 Northwind mailed a signed written confirmation to Baker. Baker received it on May 8 and did not object. Baker later refused to perform. Is the contract enforceable against Baker?\n"
       "2. On June 1 Northwind gave Baker a signed writing: 'This price is good for six months.' No consideration was paid. Northwind revoked the offer on September 15. Is the revocation effective?\n"
       "3. Baker's purchase order stated terms. Northwind's acknowledgment accepted but added an arbitration clause. Baker's order limited acceptance to its terms only in a sentence that was not signed. Baker did not object. Is the arbitration clause part of the contract? (Assume both are merchants and arbitration materially alters the contract.)\n"
       "4. The contract was 'FOB Northwind's warehouse (shipment contract).' The goods were destroyed in transit after being delivered to the carrier in good condition, without fault of either party. Who bears the loss?\n"
       "5. The parts delivered were defective in a minor way; delivery time was still open (five days remained). Baker rejected them. Can Northwind cure?\n"
       "6. Ed, a neighbor who is not a merchant in lawnmowers, sold Baker his old mower for $200. Did an implied warranty of merchantability arise?")],
    [D("c1", "Scenario 1: merchant's confirmation", ["Yes; the merchant confirmation satisfies the statute of frauds against Baker", "No; there is no signed writing by Baker", "No; oral contracts for goods are never enforceable"], "Yes; the merchant confirmation satisfies the statute of frauds against Baker",
       "Between merchants, a written confirmation sent within a reasonable time satisfies the statute of frauds against the recipient unless the recipient objects in writing within 10 days of receipt (UCC §2-201(2)).",
       ["Merchants have a special rule.", "10 days to object to a merchant confirmation."],
       {"No; there is no signed writing by Baker": "The merchant's exception replaces the need for Baker's signature.", "No; oral contracts for goods are never enforceable": "The statute of frauds only applies at $500 or more and has exceptions."}),
     D("c2", "Scenario 2: firm offer", ["Yes; a firm offer is irrevocable only up to three months, and the three months had run", "No; the offer was irrevocable for the full six months", "No; a signed writing cannot be revoked until it expires"], "Yes; a firm offer is irrevocable only up to three months, and the three months had run",
       "A merchant's signed written assurance to hold an offer open is irrevocable without consideration for the stated period, but never more than three months (UCC §2-205). Northwind's offer was irrevocable until about September 1; the September 15 revocation is effective.",
       ["A special UCC rule replaces consideration, but it has a time cap.", "Maximum irrevocability period is three months."],
       {"No; the offer was irrevocable for the full six months": "Six months exceeds the statutory maximum of three.", "No; a signed writing cannot be revoked until it expires": "The statute caps irrevocability at three months regardless of the stated period."}),
     D("c3", "Scenario 3: additional term (arbitration)", ["No; a material alteration does not become part of the contract without express assent", "Yes; Baker's silence is assent", "Yes; additional terms always become part of the contract"], "No; a material alteration does not become part of the contract without express assent",
       "Between merchants, additional terms become part of the contract unless the offer limits acceptance, they materially alter it, or the offeror objects (UCC §2-207(2)). Arbitration is treated as a material alteration.",
       ["Battle of the forms.", "Material alterations require express agreement."],
       {"Yes; Baker's silence is assent": "Silence does not add a material term.", "Yes; additional terms always become part of the contract": "Additional terms are excluded when they materially alter the contract."}),
     D("c4", "Scenario 4: risk of loss in transit", ["Baker (buyer)", "Northwind (seller)", "Shared equally"], "Baker (buyer)",
       "In a shipment contract, risk of loss passes to the buyer when the goods are duly delivered to the carrier (UCC §2-509(1)(a)).",
       ["Shipment contract versus destination contract.", "Risk passes on delivery to the carrier."],
       {"Northwind (seller)": "That would be true for a destination contract, not a shipment contract.", "Shared equally": "The UCC allocates risk to one party."}),
     D("c5", "Scenario 5: right to cure", ["Yes; the seller may notify the buyer and cure within the contract time", "No; perfect tender means the buyer's rejection ends the contract", "No; a cure is only allowed for a major defect"], "Yes; the seller may notify the buyer and cure within the contract time",
       "The buyer may reject nonconforming goods (perfect tender rule, UCC §2-601), but if the time for performance has not expired, the seller may seasonably notify the buyer of intent to cure and deliver conforming goods (UCC §2-508(1)).",
       ["Rejection is not the end if time remains.", "Cure within the contract time."],
       {"No; perfect tender means the buyer's rejection ends the contract": "The seller's right to cure within the contract time qualifies perfect tender.", "No; a cure is only allowed for a major defect": "The cure right applies to any nonconformity, not only major defects."}),
     D("c6", "Scenario 6: implied warranty of merchantability", ["No; the seller is not a merchant with respect to goods of that kind", "Yes; every sale of goods carries the warranty", "Yes; because the price was over $100"], "No; the seller is not a merchant with respect to goods of that kind",
       "The implied warranty of merchantability arises only when the seller is a merchant with respect to goods of that kind (UCC §2-314(1)). A casual seller is not.",
       ["Who makes the promise implied?", "Merchant status of the seller."],
       {"Yes; every sale of goods carries the warranty": "Only merchants make it.", "Yes; because the price was over $100": "Price is irrelevant."})],
    {}, {"area": "II", "group": "B", "topic": "Contracts: sale of goods (UCC Art. 2)", "task": "Apply UCC Article 2 rules", "skill": "Application"},
    3, 14, cite=["UCC §2-201(2)", "UCC §2-205", "UCC §2-207", "UCC §2-509", "UCC §2-508", "UCC §2-314"], tags=["ucc2"]))
for c, s in zip(ITEMS[-1]["cells"], ["UCC §2-201(2)", "UCC §2-205", "UCC §2-207(2)", "UCC §2-509(1)(a)", "UCC §2-508(1)", "UCC §2-314(1)"]):
    c["cite"] = s

# ---------------------------------------------------------------- II-T-006 document review (bankruptcy)
ITEMS.append(T(
    "REG-II-T-006", "II", "document_review",
    "Bankruptcy overview memo review",
    "You are reviewing a client memo prepared by a colleague on Chapter 7 and Chapter 11 bankruptcy concepts for a business client, Redwood Fabricators Inc.",
    "For each numbered statement, choose the option that makes the statement correct. Choose 'Keep as written' if it is already correct.",
    [X("e1", "Draft client memo", "memo",
       "1. The filing of a bankruptcy petition automatically stays most collection actions against the debtor.\n"
       "2. A trustee may avoid a preferential transfer made to a creditor within 60 days before the petition was filed (or within 12 months for an insider).\n"
       "3. A debtor who receives a Chapter 7 discharge may not receive another Chapter 7 discharge in a case commenced within 4 years of the earlier case.\n"
       "4. In distribution of estate assets, general unsecured creditors are paid before administrative expenses of the estate.\n"
       "5. In a Chapter 11 case, a trustee must always be appointed to run the debtor's business.\n"
       "6. If collateral sells for less than the secured debt, the secured creditor holds a general unsecured claim for the deficiency.")],
    [D("c1", "Statement 1: automatic stay", ["Keep as written", "Revise: the stay arises only after the court holds a hearing", "Revise: the stay applies only to secured creditors"], "Keep as written",
       "The filing of a petition operates as an automatic stay of most collection activity (11 U.S.C. §362(a)) without a court order.", ["Effective immediately on filing.", "No hearing is needed."],
       {"Revise: the stay arises only after the court holds a hearing": "The stay is automatic upon filing.", "Revise: the stay applies only to secured creditors": "It applies to most creditors."}),
     D("c2", "Statement 2: preference period", ["Keep as written", "Revise: 90 days (or 1 year for an insider)", "Revise: 6 months (or 2 years for an insider)"], "Revise: 90 days (or 1 year for an insider)",
       "A preferential transfer within 90 days before the petition (one year for insiders) may be avoided (11 U.S.C. §547(b)(4)).", ["The period is roughly one quarter.", "90 days and one year."],
       {"Keep as written": "60 days is not the period; it is 90 days.", "Revise: 6 months (or 2 years for an insider)": "Periods are 90 days and 1 year."}),
     D("c3", "Statement 3: repeat Chapter 7 discharge", ["Keep as written", "Revise: 8 years", "Revise: 2 years"], "Revise: 8 years",
       "A Chapter 7 discharge is not granted if the debtor received a Chapter 7 discharge in a case commenced within 8 years before the current petition (11 U.S.C. §727(a)(8)).", ["The waiting period is longer than the statement says.", "8 years between filing dates."],
       {"Keep as written": "4 years applies to other combinations (e.g., Chapter 7 then Chapter 13 discharge); Chapter 7 to Chapter 7 is 8 years.", "Revise: 2 years": "Too short."}),
     D("c4", "Statement 4: order of payment", ["Keep as written", "Revise: administrative expenses are paid before general unsecured creditors", "Revise: general unsecured creditors are paid before secured creditors"], "Revise: administrative expenses are paid before general unsecured creditors",
       "Administrative expenses of the estate have priority over general unsecured claims (11 U.S.C. §507(a)(2)); secured creditors are paid from their collateral first.", ["Priority ranks costs of running the estate ahead of ordinary claims.", "Unsecured general claims are near the end."],
       {"Keep as written": "General unsecured claims rank after priority claims such as administrative expenses.", "Revise: general unsecured creditors are paid before secured creditors": "Secured creditors are paid from their collateral first."}),
     D("c5", "Statement 5: Chapter 11 management", ["Keep as written", "Revise: the debtor usually remains a debtor in possession unless a trustee is appointed for cause", "Revise: creditors elect a trustee automatically"], "Revise: the debtor usually remains a debtor in possession unless a trustee is appointed for cause",
       "In Chapter 11 the debtor ordinarily continues as debtor in possession (11 U.S.C. §1107); a trustee is appointed only for cause such as fraud or gross mismanagement (§1104(a)).", ["Chapter 11 aims to reorganize, not liquidate.", "Debtor in possession."],
       {"Keep as written": "A trustee is the exception, not the rule.", "Revise: creditors elect a trustee automatically": "Creditors do not automatically elect a trustee."}),
     D("c6", "Statement 6: deficiency after collateral sale", ["Keep as written", "Revise: the secured creditor loses the deficiency entirely", "Revise: the deficiency is a priority claim"], "Keep as written",
       "A secured claim is secured only to the extent of the collateral's value; the shortfall is an unsecured claim (11 U.S.C. §506(a)(1)).", ["Secured to the extent of value.", "The remainder is unsecured."],
       {"Revise: the secured creditor loses the deficiency entirely": "The creditor still has an unsecured claim.", "Revise: the deficiency is a priority claim": "A deficiency is a general unsecured claim."})],
    {}, {"area": "II", "group": "C", "topic": "Debtor-creditor relationships: bankruptcy", "task": "Identify bankruptcy rules", "skill": "Analysis"},
    2, 12, cite=["11 U.S.C. §362", "11 U.S.C. §547", "11 U.S.C. §727", "11 U.S.C. §507", "11 U.S.C. §1107", "11 U.S.C. §506"], tags=["bankruptcy"]))
for c, s in zip(ITEMS[-1]["cells"], ["11 U.S.C. §362(a)", "11 U.S.C. §547(b)", "11 U.S.C. §727(a)(8)", "11 U.S.C. §507(a)(2)", "11 U.S.C. §1107, §1104(a)", "11 U.S.C. §506(a)(1)"]):
    c["cite"] = s
