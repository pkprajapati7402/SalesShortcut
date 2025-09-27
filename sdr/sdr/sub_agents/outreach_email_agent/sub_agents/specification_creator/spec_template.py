SPEC_MARKDOWN_TEMPLATE = """
# Acme Home Services — Website Development Proposal  
*Prepared by BrightWeb Studio · June 16 2025*

---

## 0 · Purpose of This Document  
This specification is a **single source of truth** for both client stakeholders *and* the development team.  
It explains **what** we’re building, **why** it matters to Acme Home Services, and **how** we’ll implement it.

---

## 1 · Business & Website Goals  

| Business Goal | Website KPI | Target |
|---------------|-------------|--------|
| Increase qualified leads | Quote-request form submissions | ≥ 30 / month by Day 90 |
| Boost credibility | Avg. session time | ≥ 2 min |
| Reduce phone traffic | % bookings via web | 50 % within 3 months |

---

## 2 · Target Audience & Personas  

| Persona | Needs | Key Tasks on Site |
|---------|-------|-------------------|
| “Busy Homeowner” (35-55) | Quick estimate, trust signals | 1) Compare services  2) Book slot |
| “Property Manager” | Portfolio pricing, reliability | 1) Download service brochure  2) Contact rep |
| “DIY Researcher” | Education, inspiration | 1) Read blog  2) View gallery |

---

## 3 · Core User Flows  

1. **Book an Estimate** → Home → Services → Booking widget → Confirmation e-mail.  
2. **See Proof of Quality** → Home → Gallery (filter “Kitchen”) → Before/After slider.  
3. **Read DIY Tips** → Google search “fix cracked grout” → Blog article → CTA to Services.

---

## 4 · Information Architecture (Sitemap)  

/
├─ home
├─ services
│ ├─ kitchen-remodel
│ ├─ bathroom-remodel
│ └─ outdoor-patio
├─ booking
├─ gallery
├─ reviews
├─ blog
│ ├─ category/maintenance
│ └─ category/design
└─ contact


---

## 5 · Content Requirements  

| Page | Content Owner | Assets Needed |
|------|--------------|---------------|
| Home | Marketing | Hero photo, 3 USP icons, intro copy |
| Service detail | Marketing | 600 words copy, price range table, 3 images |
| Gallery | Marketing | 30 before/after images (1920×1280) |
| Blog | Marketing | 10 seed articles (≥ 800 words each) |

> **Tone & Voice:** friendly, expert, plain-language; avoid jargon.

---

## 6 · Visual & Brand Guidelines  

* **Color Palette:** #1F4CF0 (primary), #FF8A00 (accent), #F6F8FF (background)  
* **Typography:** Inter (headings), Roboto (body).  
* **Logo Usage:** min width 120 px, no recoloring.  
* **Accessibility:** WCAG 2.2 AA contrast (> 4.5 : 1 for text).

---

## 7 · Functional Specifications  

| Feature | Behaviour | Acceptance Criteria |
|---------|-----------|---------------------|
| Booking widget | Calendly embed + custom fields | Submits w/out page reload; sends GA4 event `book_estimate` |
| Reviews feed | Google Business Profile API | Updates nightly via CRON; shows avgRating, count |
| Gallery slider | Before/After draggable | Works on touch + mouse; ≥ 60 FPS on mid-tier phones |
| CMS | Sanity Studio | Non-dev user can add new Service page without code |

---

## 8 · Technical Stack & Integrations  

| Layer | Tech | Notes |
|-------|------|-------|
| Front-end | **Next.js 14**, React 18 | App Router, RSC |
| Styling | Tailwind 3 + ShadCN | Uses `@apply` for theme tokens |
| CMS | Sanity v3 | GROQ queries, live preview |
| Hosting | Vercel Pro | Auto CI/CD, edge caching |
| Forms | Calendly API | Webhook to serverless `/api/confirm` |
| Analytics | GA4 + GTM | Events: `book_estimate`, `click_call`, `contact_submit` |
| Security | reCAPTCHA v3 | Score ≥ 0.7 to accept forms |

Performance budget: **≤ 100 KB JS**, LCP < 2 s on 4G.

---

## 9 · SEO & Analytics Plan  

* **Primary Keywords:** “home remodeling logan ut”, “kitchen remodel utah”  
* Metadata: unique titles (≤ 60 chars) & meta descriptions (≤ 155 chars).  
* XML sitemap auto-generated; robots.txt blocks `/studio/*`.  
* GA4 goals configured for estimate bookings & phone-clicks.

---

## 10 · Accessibility & Compliance  

1. All interactive elements reachable by `Tab`.  
2. Alt text for every image.  
3. ARIA landmarks (`<header>`, `<main>`, `<nav>`).  
4. Cookie banner complying with Utah Consumer Privacy Act.

---

## 11 · Project Timeline  

| Week | Milestone | Output |
|------|-----------|--------|
| 1 | Discovery | Personas, IA, brand kit |
| 2-3 | UX Wireframes | Figma low-fi |
| 4-5 | UI Design | Hi-fi comps, design tokens |
| 6-8 | Development | Next.js build, CMS schemas |
| 9 | QA & Launch | Lighthouse ≥ 90, access-checks |
| 10 | Training | 1-hr Zoom, admin doc PDF |

---

## 12 · Investment Summary  

*Discovery + UX:* **$3 000**  
*UI Design:* **$4 500**  
*Development + CMS:* **$9 000**  
*QA + Launch:* **$1 500**  
**Total Fixed Price:** **$18 000** (50 % up-front, 50 % at go-live)  
*Optional Care Plan:* hosting, backups, SEO reports — **$250 / mo**

---

## 13 · Assumptions & Exclusions  

- Client supplies copy & images before Week 4.  
- Two revision rounds per design phase included.  
- Any custom ERP integration requires separate SOW.

---

## 14 · Acceptance  

| Name | Title | Signature | Date |
|------|-------|-----------|------|
| | | | |

---

### BrightWeb Studio — Who We Are  
120 + high-converting small-business websites since 2016.  
**Contact:** Marcus Lee · marcus@brightweb.studio · (385) 555-0135
"""
