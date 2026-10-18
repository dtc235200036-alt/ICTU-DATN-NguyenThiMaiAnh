# Feature Research

**Domain:** University thesis/graduation-project (capstone) management system + AI similarity/plagiarism detection
**Researched:** 2026-09-27
**Confidence:** HIGH (workflow/features are standardized across many university systems and commercial products — Creatrix Campus, OpenEduCat, FYP portals, Coopy/Turnitin-style checkers — cross-verified across multiple independent sources); MEDIUM on exact AI-feature depth (vendor marketing pages, not audited implementations)

## Domain Context

Two converging product categories were researched:
1. **Thesis/FYP (Final Year Project) management systems** — academic workflow tools (Creatrix Campus Thesis Management, OpenEduCat, COMSATS FYP Portal, HKUST FYPMS, various published "Design and Implementation of Graduation Thesis Management System" papers).
2. **Plagiarism/similarity checkers** — Turnitin Similarity (global gold standard for passage-level matching + originality score) and Vietnamese-market equivalents (Coopy at HUST/SoICT — internal Vietnamese-language corpus matching; "Kiểm Tra Tài Liệu" — Vietnamese SaaS checker; Vietnamese universities' internal "kiểm soát trùng lặp" policies, typically a 20–30% threshold).

This project's scope (per PROJECT.md) is a bounded, in-faculty version of both: 5 UCs (Topic, Outline/Đề cương, Progress, Defense, Archive) run by 3 roles (Student, Lecturer/Supervisor, Department/Faculty Admin), with AI limited to comparing **within the faculty's own thesis archive** (not the open internet, not cross-institution) — explicitly modeled on Coopy's closed-corpus approach rather than Turnitin's web-scale approach.

## Feature Landscape

### Table Stakes (Users Expect These)

Features every thesis/FYP management system has. Missing these makes the system feel broken for a graduation-defense demo.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Topic proposal by lecturer AND/OR registration by student | Every FYP system supports at least one direction (GV đề xuất or SV tự đề xuất); this project requires both | MEDIUM | Topic needs states: draft → submitted → approved/rejected → assigned |
| Department/faculty approval + supervisor assignment for topics | Core gatekeeping step in every reviewed system ("multi-tier hierarchical approvals... from HODs down to students") | MEDIUM | One admin action assigns GVHD; must prevent one student having 2 active topics, one topic having 2 students (unless group topics explicitly allowed — check with stakeholder) |
| Outline (đề cương) submission with file upload (DOCX/PDF) | Universal step between topic approval and active work; explicitly required by PI 3.3/3.4 | LOW-MEDIUM | Versioned upload (v1, v2...) needed because of "revise and resubmit" cycle below |
| Supervisor review/approve/reject-with-comments on outline | "Inline review feedback channels" is standard; without this the workflow has no exit condition | MEDIUM | Needs a revision loop: reject → student edits → resubmit → re-review |
| Progress tracking with periodic student reports + supervisor feedback | Dashboards "show every active thesis... with automatic risk flags" — a defining feature of thesis mgmt category | MEDIUM | Simplify for demo: N fixed checkpoints (e.g., biweekly) rather than open-ended free-form logging |
| Defense committee formation (assign lecturers as members) | Universal; explicitly required (PI 3.3) — committee = pool of lecturer accounts per PROJECT.md decision | MEDIUM | No separate "committee member" role — reuse Lecturer role with a committee-assignment record per defense session |
| Defense scheduling (room/time/session, list of theses per session) | Standard ("scheduling tool proposes time slots... coordinates room booking") | MEDIUM | For demo scope, manual scheduling by admin is sufficient — no auto-conflict-solver needed |
| Score/result entry per committee member + aggregated grade | Universal final step of every defense-mgmt module | LOW-MEDIUM | Needs simple rubric or single overall score field; aggregation rule (avg / weighted) must be decided |
| Role-based access control (Student / Lecturer / Admin) | Explicit requirement (PI 3.4); every reviewed system has "role-specific dashboards and approval steps" | MEDIUM | Foundational — almost every other feature depends on this |
| Thesis archive / repository with search across past cohorts (khóa) | Explicit UC (PI 3.3); standard "document management" feature in every system reviewed | MEDIUM | Needs metadata fields (year/khóa, topic, student, supervisor, keywords) + full-text or filtered search |
| File storage & versioning for outline/report documents | "Enhanced document management and version control" cited as standard | LOW-MEDIUM | Can be simple filesystem/blob storage with a version-linked DB row; no need for full DMS |
| Notifications on state changes (approval, rejection, deadline) | "Automated email alerts, real-time in-app notifications" is table stakes across all systems reviewed | LOW-MEDIUM | For demo, in-app notification list is sufficient; email is a nice-to-have, not required |
| Similarity/duplicate check triggered on submission (topic title, outline, report) | This is the project's own stated core value — but the *trigger points* (on submit) are table stakes for any duplicate-checker integration, as seen in Coopy/Turnitin/KiemTraTaiLieu | HIGH | This is the AI differentiator's *delivery mechanism* — the check itself is a differentiator (see below), but "runs automatically at submission" is expected once you claim to have it |
| Similarity result shown as: matched item(s) + % overlap + highlighted passage | Standard originality-report UX across all checkers reviewed (Turnitin, Coopy, Kiểm Tra Tài Liệu) | HIGH | Users expect at minimum: score, source, and which text matched — a bare percentage with no reference is considered incomplete |

### Differentiators (Competitive Advantage)

Not required for a generic thesis-tracker, but these directly deliver this project's Core Value and CLO/PI grading criteria — this is where the demo should shine.

| Feature | Value Proposition | Complexity | Notes |
|---------|--------------------|------------|-------|
| Semantic (embedding-based) topic-title duplicate warning at registration time | Catches near-duplicate topics phrased differently ("Xây dựng hệ thống..." vs "Phát triển ứng dụng...") — plain string match misses this; this is what most FYP portals do NOT do (they only do exact-title collision checks) | HIGH | Needs Vietnamese-capable sentence embedding model (e.g., a multilingual or Vietnamese-tuned sentence-transformers model) + vector similarity search against archive of past topic titles; must return top-N similar topics + score, not just pass/fail |
| Passage-level duplicate detection across outline/report vs faculty archive (not web) | Directly addresses academic integrity for the specific corpus that matters to a Vietnamese CNTT faculty; mirrors Coopy's "closed internal corpus" model rather than expensive Turnitin licensing | HIGH | Needs document parsing (DOCX + PDF) → chunking → embedding or n-gram/shingling comparison → per-chunk score + matched source doc + aggregate %; this is the single most technically demanding feature in the whole project |
| Local, self-hosted AI (no paid API dependency) | Cost constraint + data-privacy constraint (student theses stay in-faculty); also satisfies SOA architecture requirement (separate AI microservice) | MEDIUM-HIGH | Already decided in PROJECT.md — sentence-transformers/local embedding + vector search (e.g., FAISS or pgvector-style); no third-party cloud API |
| Similarity check integrated into approval workflow (supervisor sees score before approving outline) | Turns a standalone "checker tool" into a workflow gate, which most generic FYP portals do NOT do (plagiarism check is usually an afterthought bolt-on, not inline) | MEDIUM | Requires the similarity result to be surfaced directly on the supervisor's review screen, not a separate report the reviewer must remember to run |
| Cross-cohort search of the archive as duplicate-check source (leverages seeded 300 past topics + 50 past documents) | Makes the demo tangible — reviewers/graders can see a real "found a similar 2023 thesis" moment | LOW-MEDIUM | Mostly a data/seeding concern, not a new feature — but it's the differentiator that makes AI checks *demonstrable* rather than theoretical |
| SOA microservice separation (Web API vs AI service) with clear API contract | Explicit architecture requirement (PI 2.2/3.2); also a genuine engineering differentiator vs monolithic student projects | MEDIUM | Not a user-facing feature, but graded directly (CLO 3, PI 3.2) — treat as a "feature" for roadmap purposes since it drives phase structure |

### Anti-Features (Commonly Requested, Often Problematic — Do NOT Build)

| Feature | Why It Seems Appealing | Why Problematic (for this project) | Alternative |
|---------|------------------------|--------------------------------------|-------------|
| Web/Internet-wide plagiarism check (like real Turnitin) | "More thorough" checking feels more impressive | Explicitly out of scope in PROJECT.md; massive scope/cost increase (web crawling, licensing, index size) with zero grading benefit — the rubric only asks for in-faculty duplicate detection | Compare only against the seeded faculty archive; document this boundary clearly in the report so evaluators know it's intentional, not a gap |
| Separate "Committee Member" role/account type | Feels more "correct" to model reality | PROJECT.md explicitly rejects this — adds an extra role to design, seed, and test for a distinction (temporary duty vs identity) that adds no grading value; RBAC complexity balloons for no CLO/PI benefit | Lecturer accounts get a per-defense-session "assigned as committee member" record; permissions for grading scoped to that assignment, not a new role |
| Real-time chat/messaging between student and supervisor | "Communication features" show up as a selling point in commercial FYP portals (COMSATS, Creatrix) | Out of scope: 10-week timeline, not graded by any PI/CLO item, and duplicates what students already use (Zalo/email) for a demo project | Use the existing review-comment field on outline/progress submissions as the only "communication" channel — sufficient for demo |
| Automatic AI-driven committee/room scheduling optimizer | "Smart scheduling that avoids conflicts" sounds impressive and some commercial systems (ScienceDirect paper on "data-driven thesis defense scheduling") pursue this | High complexity (constraint solver) for a feature not in PI list; admin manually assigning ~10-30 defenses for a demo dataset is trivial by hand | Simple manual scheduling form (pick lecturers + date/time + room) with basic conflict validation (no double-booking same lecturer/time) — good enough and much lower risk |
| Group/team topics (multiple students per thesis) | Real capstone systems often support teams (COMSATS FYP, SmartFYP) | Not mentioned anywhere in PROJECT.md scope; adds significant data-model and approval-workflow complexity (who submits? who gets graded?) for zero PI credit | Model 1 student : 1 topic : 1 supervisor as the only supported cardinality unless stakeholder explicitly asks otherwise |
| AI-generated topic suggestions / "recommend supervisor by domain" (seen in some advanced FYP portal marketing) | Sounds like a nice AI-forward differentiator | Out of scope per PROJECT.md (only 2 AI checks are specified: topic-title semantic match + outline/report duplicate detection); adds a third ML feature with its own data/eval needs, diluting the 8-week AI phase budget | Keep AI scope to exactly the two specified checks; if time remains after core AI works, this is a legitimate "if time permits" stretch, not baseline |
| Mobile native app | Occasionally requested for "students want it on their phone" | Explicitly out of scope in PROJECT.md; adds a second frontend codebase for a Web-only graded deliverable | Responsive Web (React) is sufficient — explicitly what the đề cương requires |
| SSO / integration with the university's real training-management system | Feels "production-ready" and more realistic | Explicitly out of scope; real SSO integration requires access/credentials to systems outside student's control and is not gradable within a 10-week solo capstone | Standalone auth (JWT/session) seeded with demo accounts for 100 students / 30 lecturers |

## Feature Dependencies

```
RBAC (Student/Lecturer/Admin)
    └──requires──> Auth/session system
                       └──requires──> User + Role data model (seeded 100 SV / 30 GV)

Topic proposal & registration (UC1)
    └──requires──> RBAC
    └──enhances──> Semantic topic-title duplicate check (needs an archive of past topic titles to compare against)
                       └──requires──> Thesis Archive (UC5) seeded with 300 past topics

Topic approval + supervisor assignment (UC1)
    └──requires──> Topic proposal & registration
    └──unlocks──> Outline submission (UC2) — a student cannot submit đề cương before topic is approved+assigned

Outline submission + review (UC2)
    └──requires──> Topic approval + supervisor assignment
    └──requires──> DOCX/PDF parsing pipeline (shared with report duplicate check)
    └──enhances──> Passage-level duplicate check (needs archive of past outlines/reports to compare against)
                       └──requires──> Thesis Archive (UC5) seeded with 50 past documents

Progress tracking (UC3)
    └──requires──> Outline approved (work only tracked once đề cương is accepted)

Report submission (part of UC3/UC4 boundary — final report precedes defense)
    └──requires──> Passage-level duplicate check pipeline (same engine as outline check)
    └──unlocks──> Defense mgmt (UC4) — committee cannot be assigned/scored until final report is submitted

Defense committee formation + scheduling (UC4)
    └──requires──> RBAC (Lecturer pool to draw committee members from)
    └──requires──> Report submission complete

Score/result entry (UC4)
    └──requires──> Defense committee formation + scheduling

Thesis Archive (UC5)
    └──requires──> Score/result entry (a thesis is only "archived" once graded/completed)
    └──also pre-seeded independently with historical data (300 topics / 50 docs) to bootstrap AI checks from day one — this seed does NOT depend on the live workflow being built first

AI similarity service (both checks)
    └──requires──> Document parsing (DOCX/PDF → text)
    └──requires──> Vietnamese embedding model + vector index
    └──requires──> Thesis Archive seed data to have something to compare against
    └──conflicts with──> Web-wide plagiarism check (anti-feature; scope is capped at faculty archive)
```

### Dependency Notes

- **Topic approval blocks Outline submission:** Every reviewed system enforces this gate (you can't write an outline for a topic that isn't yours yet) — the roadmap must sequence UC1 fully working (including assignment) before UC2 begins.
- **AI checks require Archive seed data before they're meaningful:** The 300-topic/50-document seed (PI 4.2) is not just a "deployment" nicety — it's a functional dependency for the AI similarity phase to be demonstrable at all. Seeding should happen early enough that AI development/testing has real data to validate against, not be left to the final "triển khai" phase only.
- **Report submission is the fork point between Progress (UC3) and Defense (UC4):** the final report is where the passage-level duplicate checker runs a second time (first run was on the outline) — reuse the same parsing/embedding pipeline rather than building two.
- **Defense (UC4) depends on report completion, which depends on progress (UC3), which depends on outline (UC2), which depends on topic (UC1):** the 5 UCs are naturally sequential for a single thesis's lifecycle, though the *system* must support many theses at different UC stages simultaneously (a dashboard/queue view per role, not a single-thesis wizard).
- **RBAC is the one feature nearly everything else depends on** — must be built first or very early, confirmed by every reviewed system treating "role-specific dashboards and approval steps" as foundational infrastructure, not a feature module.

## MVP Definition

### Launch With (v1 — required for graduation defense demo, maps directly to PROJECT.md Active requirements)

- [ ] RBAC: Student / Lecturer / Department Admin — foundation for every other feature
- [ ] UC1 Topic mgmt: propose (GV or SV) → register (SV) → approve + assign supervisor (Admin)
- [ ] UC2 Outline mgmt: submit (DOCX/PDF) → review/approve/reject-with-comment (GV) → resubmit loop
- [ ] UC3 Progress mgmt: periodic report submission (SV) → feedback (GV)
- [ ] UC4 Defense mgmt: committee formation (Admin, from Lecturer pool) → scheduling → score/result entry
- [ ] UC5 Archive mgmt: store + search past theses across khóa (cohorts)
- [ ] AI-1: semantic topic-title similarity check at registration, with top-N matches + score
- [ ] AI-2: passage-level duplicate check on outline/report submission, with matched source + highlighted passage + aggregate %
- [ ] Seed data: 100 SV, 30 GV, 300 topics, 50 outline/report files with deliberate duplicate pairs (needed to *prove* AI-1/AI-2 work, not just exist)
- [ ] Deployment behind Apache reverse proxy with HTTPS (PI 4.1) — required for the "triển khai" grading criterion, not optional infra

### Add After Validation (v1.x — only if core UC1–5 + AI checks are solid with time remaining)

- [ ] Email notifications (currently in-app only)
- [ ] Configurable similarity-threshold policy (e.g., admin sets 20% vs 30% warning line) rather than a hardcoded threshold
- [ ] Basic conflict-detection UI for defense scheduling (warn if lecturer double-booked) beyond simple validation
- [ ] Exportable defense grading sheet / report generation (PDF of committee scores)

### Future Consideration (v2+ — explicitly out of scope for this capstone)

- [ ] Web-scale plagiarism comparison (Turnitin-style) — out of scope per PROJECT.md; would require external licensing/crawling infrastructure disproportionate to a 10-week solo project
- [ ] Group/team topics — no current requirement; would restructure the core data model
- [ ] Real-time messaging — no CLO/PI credit; review-comment fields suffice
- [ ] Mobile app — explicitly Web-only scope
- [ ] SSO integration with university systems — explicitly out of scope, demo-only auth is sufficient

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|----------------------|----------|
| RBAC + Auth | HIGH | MEDIUM | P1 |
| UC1 Topic mgmt (propose/register/approve/assign) | HIGH | MEDIUM | P1 |
| UC2 Outline mgmt (submit/review/revise) | HIGH | MEDIUM | P1 |
| UC3 Progress mgmt | MEDIUM | MEDIUM | P1 |
| UC4 Defense mgmt (committee/schedule/score) | HIGH | MEDIUM | P1 |
| UC5 Archive mgmt (store/search) | MEDIUM | MEDIUM | P1 |
| AI-1 Semantic topic-title duplicate check | HIGH (core value) | HIGH | P1 |
| AI-2 Passage-level outline/report duplicate check | HIGH (core value) | HIGH | P1 |
| Seed data (100/30/300/50 with deliberate duplicates) | HIGH (proves AI works) | LOW-MEDIUM | P1 |
| Apache reverse proxy + HTTPS deployment | MEDIUM (grading requirement) | MEDIUM | P1 |
| Email notifications | LOW-MEDIUM | LOW | P2 |
| Configurable similarity threshold | MEDIUM | LOW | P2 |
| Defense scheduling conflict warnings | LOW-MEDIUM | LOW-MEDIUM | P2 |
| Exportable grading sheet/report PDF | LOW-MEDIUM | LOW | P2 |
| Web-wide plagiarism comparison | LOW (out of scope) | VERY HIGH | P3 (do not build) |
| Group/team topics | LOW (not requested) | HIGH | P3 (do not build) |
| Real-time chat | LOW | MEDIUM | P3 (do not build) |

**Priority key:**
- P1: Must have for the graduation defense demo (directly maps to PROJECT.md Active requirements / PI codes)
- P2: Should have if time remains after P1 is solid and tested
- P3: Explicitly deferred/rejected — do not build for this milestone

## Role × Use-Case Feature Map

| Use Case | Student | Lecturer/Supervisor (incl. committee member) | Department/Faculty Admin |
|----------|---------|-----------------------------------------------|----------------------------|
| **UC1 Topic mgmt** | Propose a topic (optional); browse/register an approved topic; see AI similarity warning at registration | Propose a topic; view proposed/registered topics in their domain | Review & approve/reject topics; assign supervisor to student; resolve title-collision flags |
| **UC2 Outline mgmt** | Upload đề cương (DOCX/PDF); view AI duplicate-check result before submitting; revise & resubmit on rejection | Review đề cương; see AI similarity result inline; approve or reject-with-comment | (Visibility/reporting only — approval authority sits with supervisor) |
| **UC3 Progress mgmt** | Submit periodic progress report; view supervisor feedback | Review progress reports; give feedback/rating per checkpoint | Monitor overall progress dashboard across all students (risk flags for missed checkpoints) |
| **UC4 Defense mgmt** | View assigned defense schedule; submit final report (triggers AI-2 again) | Serve as committee member (when assigned): view report, enter score/comments | Form committee (pick lecturers); schedule date/time/room; finalize aggregated results |
| **UC5 Archive mgmt** | Search/browse past theses (read-only, for reference/inspiration) | Search/browse past theses (read-only) | Full archive management: add/curate seed data, oversee retention across khóa |
| **AI-1 Topic similarity** | Triggered automatically on topic registration; sees own result | Sees result when reviewing a topic proposal | Sees result when approving topics; can override warning |
| **AI-2 Doc similarity** | Triggered automatically on đề cương/report upload; sees own result | Sees result inline while reviewing đề cương/report | Can query similarity reports across the faculty archive for audit purposes |

## Sources

- [Thesis Management System | OpenEduCat](https://openeducat.org/feature-thesis-management-system/) — HIGH confidence (specific open-source feature list)
- [Thesis Management System | Creatrix Campus](https://www.creatrixcampus.com/thesis-management-system) — MEDIUM confidence (vendor marketing, cross-verified against other sources)
- [Design of University Graduation Project Management System Based on Micro Service Architecture (ResearchGate)](https://www.researchgate.net/publication/357307141_Design_of_University_Graduation_Project_Management_System_Based_on_Micro_Service_Architecture) — HIGH confidence (peer-reviewed design paper, directly relevant to this project's SOA requirement)
- [Design and Implementation of Graduation Thesis Management System (ResearchGate)](https://www.researchgate.net/publication/319250215_Design_and_Implementation_of_Graduation_Thesis_Management_System) — HIGH confidence (peer-reviewed)
- [Data driven-based thesis defense scheduling system (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0952197625016999) — MEDIUM confidence (informed the defense-scheduling anti-feature call)
- [The Development of a Final Year Project Management System for IT Programmes (ResearchGate)](https://www.researchgate.net/publication/283757588_The_Development_of_a_Final_Year_Project_Management_System_for_Information_Technology_Programmes) — HIGH confidence (peer-reviewed, IT-program-specific, closely matches this project's domain)
- [FYP Management System (HKUST)](https://fypms.cse.ust.hk/) — MEDIUM confidence (live production system, feature set inferred from public description)
- [COMSATS FYP Portal proposal (Scribd)](https://www.scribd.com/document/904079861/Scope-Document-Fyp-Portal-Fa18-Bcs-086-078-Sp18-111-Docx) — MEDIUM confidence (student scope document, useful for anti-feature signal on team/group topics)
- [SmartFYP GitHub project](https://github.com/fat2004med/smartfyp_project) — LOW-MEDIUM confidence (student project, illustrative only)
- [Coopy - Đại học Bách khoa Hà Nội (SoICT)](https://soict.hust.edu.vn/coopy.html) — HIGH confidence (directly comparable Vietnamese closed-corpus similarity checker, model for this project's AI scope)
- [Coopy - Hệ thống kiểm tra trùng lặp nội dung](http://coopy.soict.ai/) — HIGH confidence
- [Quy định kiểm tra trùng lặp, đạo văn tại các trường đại học](https://kiemtratailieu.vn/blog/tong-hop-quy-dinh-ve-kiem-tra-trung-lap-dao-van/) — MEDIUM confidence (informs the 20–30% Vietnamese-university threshold convention)
- [Turnitin Similarity product page](https://www.turnitin.com/products/similarity/) — HIGH confidence (industry-standard reference for originality-report UX)
- [Understanding the similarity score – Turnitin Guides](https://guides.turnitin.com/hc/en-us/articles/23435833938701-Understanding-the-similarity-score) — HIGH confidence (official documentation)

---
*Feature research for: University thesis/graduation-project management system + AI similarity detection (Khoa CNTT, ICTU)*
*Researched: 2026-09-27*
