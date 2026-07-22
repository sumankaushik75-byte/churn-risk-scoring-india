const pptxgen = require("pptxgenjs");

const NAVY = "0B3D5C";      // primary, dominant background/dark
const TEAL = "1C7293";      // secondary
const ICE = "CFE3EC";       // light supporting tint
const RED = "8B1E2A";       // risk accent (matches the prototype's red risk tier)
const AMBER = "A8631B";     // matches amber medium-risk tier
const GREEN = "13755A";     // matches green low-risk tier
const WHITE = "FFFFFF";
const INK = "1A1A1A";
const MUTED = "5B6B73";
const CARD_BG = "F4F7F8";

function freshShadow() {
  return { type: "outer", color: "0B3D5C", opacity: 0.18, blur: 8, offset: 3, angle: 90 };
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5

// ============================================================= SLIDE 1: THE PROBLEM
let s1 = pres.addSlide();
s1.background = { color: NAVY };

s1.addText("SLIDE 1", {
  x: 0.6, y: 0.45, w: 3, h: 0.35, fontFace: "Calibri", fontSize: 12, bold: true,
  color: "7FA8BE", charSpacing: 2,
});
s1.addText("The Problem", {
  x: 0.6, y: 0.8, w: 9, h: 0.9, fontFace: "Cambria", fontSize: 40, bold: true, color: WHITE,
});
s1.addText(
  "In India's prepaid telecom market, high-value customers leave with zero warning. "
  + "There is no contract to cancel — they simply stop recharging, and by the time a "
  + "number goes silent, it is already too late to win them back.",
  {
    x: 0.6, y: 1.75, w: 8.2, h: 1.1, fontFace: "Calibri", fontSize: 16, color: ICE,
    lineSpacing: 22,
  }
);

const stats = [
  { big: "14–16M", small: "mobile-number-portability\nrequests every month, sustained\nsince mid-2025", color: TEAL },
  { big: "2.2M", small: "active subscribers Vodafone Idea\nlost in a single month as tariff\nhikes pushed switching", color: RED },
  { big: "80%", small: "of an Indian telecom's revenue\ncomes from just the top 30% of\ncustomers by recharge spend", color: GREEN },
];
const cardW = 3.7, gap = 0.35, startX = 0.6, cardY = 3.15, cardH = 2.55;
stats.forEach((st, i) => {
  const x = startX + i * (cardW + gap);
  s1.addShape(pres.ShapeType.roundRect, {
    x, y: cardY, w: cardW, h: cardH, rectRadius: 0.09,
    fill: { color: "0F4A70" }, line: { type: "none" }, shadow: freshShadow(),
  });
  s1.addText(st.big, {
    x: x + 0.25, y: cardY + 0.3, w: cardW - 0.5, h: 1.0,
    fontFace: "Cambria", fontSize: 40, bold: true, color: st.color === TEAL ? "6FD3E8" : (st.color === RED ? "FF8A8A" : "7FE3C8"),
  });
  s1.addText(st.small, {
    x: x + 0.25, y: cardY + 1.35, w: cardW - 0.5, h: 1.1,
    fontFace: "Calibri", fontSize: 12.5, color: ICE, lineSpacing: 16,
  });
});
s1.addText(
  "Sources: TRAI monthly telecom subscription reports (2025–26); published India/SE Asia telecom high-value-customer revenue concentration.",
  { x: 0.6, y: 6.95, w: 12, h: 0.35, fontFace: "Calibri", fontSize: 9, color: "6E93A8", italic: true }
);

// ============================================================= SLIDE 2: SCOPE
let s2 = pres.addSlide();
s2.background = { color: WHITE };

s2.addText("SLIDE 2", {
  x: 0.6, y: 0.4, w: 3, h: 0.35, fontFace: "Calibri", fontSize: 12, bold: true,
  color: TEAL, charSpacing: 2,
});
s2.addText("Scope of the Problem", {
  x: 0.6, y: 0.72, w: 10, h: 0.8, fontFace: "Cambria", fontSize: 34, bold: true, color: NAVY,
});

s2.addText("Precise scope, not “all customers everywhere”", {
  x: 0.6, y: 1.65, w: 8, h: 0.4, fontFace: "Calibri", fontSize: 13, bold: true, color: MUTED,
});
s2.addShape(pres.ShapeType.roundRect, {
  x: 0.6, y: 2.05, w: 7.3, h: 1.5, rectRadius: 0.08,
  fill: { color: CARD_BG }, line: { color: "DCE4E7", width: 1 }, shadow: freshShadow(),
});
s2.addText(
  [
    { text: "Industry: ", options: { bold: true, color: NAVY } },
    { text: "Indian / Southeast Asian prepaid mobile telecom\n", options: { color: INK } },
    { text: "Process: ", options: { bold: true, color: NAVY } },
    { text: "monthly retention targeting for the top 30% of customers by recharge spend\n", options: { color: INK } },
    { text: "Prediction: ", options: { bold: true, color: NAVY } },
    { text: "will this specific high-value customer go silent (zero usage) next month?", options: { color: INK } },
  ],
  { x: 0.85, y: 2.22, w: 6.8, h: 1.2, fontFace: "Calibri", fontSize: 13, lineSpacing: 19 }
);

s2.addText("Who is this for?", { x: 0.6, y: 3.85, w: 4, h: 0.35, fontFace: "Calibri", fontSize: 14, bold: true, color: NAVY });
s2.addText(
  "Retention teams at a prepaid operator, with limited capacity to call or message customers — "
  + "not a mass campaign to the whole subscriber base.",
  { x: 0.6, y: 4.25, w: 6.9, h: 0.9, fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 17 }
);
s2.addText("Where, exactly?", { x: 0.6, y: 5.25, w: 4, h: 0.35, fontFace: "Calibri", fontSize: 14, bold: true, color: NAVY });
s2.addText(
  "Prepaid only, not postpaid: prepaid customers can leave with no cancellation notice, which is "
  + "the specific, harder version of this problem.",
  { x: 0.6, y: 5.65, w: 6.9, h: 0.9, fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 17 }
);

// Narrowing funnel, right side
const funnel = [
  { label: "All prepaid customers", value: "99,999", w: 4.1 },
  { label: "High-value (top 30% by recharge)", value: "30,011", w: 3.15 },
  { label: "Flagged high-risk this month", value: "≈ 6,000", w: 2.2 },
];
let fy = 2.05;
funnel.forEach((f, i) => {
  const fx = 8.4 + (4.1 - f.w) / 2;
  s2.addShape(pres.ShapeType.roundRect, {
    x: fx, y: fy, w: f.w, h: 0.95, rectRadius: 0.07,
    fill: { color: i === 2 ? RED : (i === 1 ? TEAL : NAVY) }, line: { type: "none" },
    shadow: freshShadow(),
  });
  s2.addText(f.value, {
    x: fx, y: fy + 0.08, w: f.w, h: 0.45, align: "center",
    fontFace: "Cambria", fontSize: 20, bold: true, color: WHITE,
  });
  s2.addText(f.label, {
    x: fx, y: fy + 0.53, w: f.w, h: 0.4, align: "center",
    fontFace: "Calibri", fontSize: 9.5, color: ICE,
  });
  fy += 1.2;
});
s2.addText("Narrowing to who actually matters", {
  x: 8.4, y: 5.75, w: 4.1, h: 0.35, align: "center",
  fontFace: "Calibri", fontSize: 11, italic: true, color: MUTED,
});

// ============================================================= SLIDE 3: CURRENT INDUSTRY PRACTICE
let s3 = pres.addSlide();
s3.background = { color: WHITE };

s3.addText("SLIDE 3", {
  x: 0.6, y: 0.4, w: 3, h: 0.35, fontFace: "Calibri", fontSize: 12, bold: true,
  color: TEAL, charSpacing: 2,
});
s3.addText("Current Industry Practice", {
  x: 0.6, y: 0.72, w: 10, h: 0.8, fontFace: "Cambria", fontSize: 34, bold: true, color: NAVY,
});

const cols = [
  {
    title: "Before AI",
    color: MUTED,
    bullets: [
      "No prediction at all: prepaid has no cancellation event to trigger on",
      "Bulk recharge-reminder SMS blasts once a number goes quiet",
      "Same generic win-back offer sent to everyone, regardless of cause",
    ],
  },
  {
    title: "Current AI (Airtel, Jio)",
    color: TEAL,
    bullets: [
      "Airtel + Amdocs AIOps: call-centre volume -60%, order fallout -90% in 6 months",
      "Airtel's Xtelify sells an AI platform marketed on cutting churn, lifting ARPU",
      "Jio's in-house JioBrain runs experience analytics across ~500M subscribers",
      "Real results, but proprietary — methodology and numbers aren't published",
    ],
  },
  {
    title: "Our prototype",
    color: GREEN,
    bullets: [
      "Same core idea: a live per-customer risk score from usage + recharge data",
      "Built and shown end to end: real public dataset, 6 benchmarked configurations",
      "Engineered explicitly for the 8.6% churn rate and leakage risk, not an afterthought",
      "Deployed as a real, inspectable API — not a vendor result taken on faith",
    ],
  },
];
const colW = 3.95, colGap = 0.25, colX0 = 0.6, colY = 1.75, colH = 4.9;
cols.forEach((c, i) => {
  const x = colX0 + i * (colW + colGap);
  s3.addShape(pres.ShapeType.roundRect, {
    x, y: colY, w: colW, h: colH, rectRadius: 0.08,
    fill: { color: i === 2 ? "EAF4EF" : CARD_BG },
    line: { color: i === 2 ? "BEE0CF" : "DCE4E7", width: 1 },
    shadow: freshShadow(),
  });
  s3.addShape(pres.ShapeType.roundRect, {
    x: x + 0.25, y: colY + 0.25, w: 1.9, h: 0.42, rectRadius: 0.21,
    fill: { color: c.color }, line: { type: "none" },
  });
  s3.addText(c.title, {
    x: x + 0.25, y: colY + 0.25, w: 1.9, h: 0.42, align: "center", valign: "middle",
    fontFace: "Calibri", fontSize: 12.5, bold: true, color: WHITE,
  });
  const items = c.bullets.map((b, j) => ({
    text: b,
    options: { bullet: { code: "2022" }, breakLine: j < c.bullets.length - 1, paraSpaceAfter: 10 },
  }));
  s3.addText(items, {
    x: x + 0.3, y: colY + 0.9, w: colW - 0.6, h: colH - 1.1,
    fontFace: "Calibri", fontSize: 11.5, color: INK, lineSpacing: 15, valign: "top",
  });
});
s3.addText(
  "We replicate the core capability Airtel and Jio's platforms sell — and extend it by making the class-imbalance handling, leakage prevention, and model-selection reasoning fully transparent and checkable.",
  { x: 0.6, y: 6.8, w: 12.1, h: 0.5, fontFace: "Calibri", fontSize: 11.5, italic: true, color: MUTED }
);

// ============================================================= SLIDE 4: LIVE DEMO
let s4 = pres.addSlide();
s4.background = { color: NAVY };

s4.addText("SLIDE 4", {
  x: 0.6, y: 0.4, w: 3, h: 0.35, fontFace: "Calibri", fontSize: 12, bold: true,
  color: "7FA8BE", charSpacing: 2,
});
s4.addText("Live Demo", {
  x: 0.6, y: 0.72, w: 8, h: 0.8, fontFace: "Cambria", fontSize: 34, bold: true, color: WHITE,
});
s4.addText(
  "Switching to the live prototype now — a real customer's 3-month recharge and usage profile, "
  + "scored live by the actual trained model, not a canned example.",
  { x: 0.6, y: 1.55, w: 8, h: 0.65, fontFace: "Calibri", fontSize: 13.5, color: ICE, lineSpacing: 18 }
);

s4.addImage({ path: "screenshots/calculator_final.png", x: 0.6, y: 2.35, w: 5.55, h: 4.63 });
s4.addImage({ path: "screenshots/crop_rankedlist.png", x: 6.35, y: 2.35, w: 5.55, h: 4.63 });

s4.addShape(pres.ShapeType.roundRect, {
  x: 0.6, y: 7.05, w: 11.3, h: 0.32, rectRadius: 0.05,
  fill: { color: "0F4A70" }, line: { type: "none" },
});
s4.addText(
  [
    { text: "Live at: ", options: { bold: true, color: "7FE3C8" } },
    { text: "[add hosted URL here once deployed]   ", options: { color: ICE } },
    { text: "Fallback: ", options: { bold: true, color: "7FE3C8" } },
    { text: "uvicorn api:app --reload --port 8000, then open the prototype HTML", options: { color: ICE } },
  ],
  { x: 0.75, y: 7.05, w: 11, h: 0.32, fontFace: "Calibri", fontSize: 10.5, valign: "middle" }
);

pres.writeFile({ fileName: "AI_Analytics_Presentation.pptx" }).then(() => {
  console.log("Saved: AI_Analytics_Presentation.pptx");
});
