# SkillShare Authorization Audit

Legend:

- 🟢 Protected correctly
- 🟡 Needs review or policy decision
- 🔴 Needs a fix

| Route | Action | Who should access it? | Current protection | Status | Notes |
|---|---|---|---|---|---|
| `/` | View home | Anyone | Redirects logged-in users | 🟢 | |
| `/add-user` | Create account | Logged-out users | Redirects authenticated users | 🟢 | |
| `/login` | Log in | Logged-out users | Redirects authenticated users | 🟢 | |
| `/logout` | Log out | Logged-in users | No `@login_required` | 🟡 | Consider adding login protection |
| `/dashboard` | View own dashboard | Current logged-in user | `@login_required`, queries current user data | 🟢 | |
| `/users` | View all users | Policy decision | Public | 🟡 | Review privacy/data exposed |
| `/explore` | Browse offers/requests | Anyone | Public read-only | 🟢 | |
| `/requests/search-similar` | Search open requests | Anyone | Public read-only JSON | 🟡 | Review whether student names should be public |
| `/requests/new` | Create request | Logged-in user | `@login_required`, uses `current_user.id` | 🟢 | |
| `/offers/<offer_id>` | View offer | Anyone | Public read-only | 🟢 | |
| `/offers/<offer_id>/schedule` | Schedule session | Offer owner | Login + `offer.teacher_id == current_user.id` | 🟢 | |
| `/sessions/<session_id>/rsvp` | RSVP | Logged-in user except offer owner | Login + ownership/self-RSVP checks | 🟢 | |
| `/profile` | View own profile | Current user | Login + redirects using `current_user.id` | 🟢 | |
| `/profile/<user_id>` | View profile | Policy decision | Public | 🟡 | Decide whether profiles should require login |
| `/profile/edit` | Edit own profile | Current user | Login + only modifies `current_user` | 🟢 | |
| `/requests/<request_id>/upvote` | Toggle upvote | Logged-in user except request owner | Login + ownership check + unique constraint | 🟢 | |
| `/sessions/<session_id>/feedback` | Leave feedback | Confirmed attendee after session | Login + enrollment + session state checks | 🟢 | |
| `/sessions/<session_id>/attendance` | Mark attendance | Offer owner | Login + offer ownership check | 🟢 | |
| `/sessions/<session_id>/recording` | Add recording | Offer owner | Login + offer ownership check | 🟢 | |
| `/offers/new` | Create offer | Logged-in user | Login + uses `current_user.id` | 🟢 | |
| `/offers/<offer_id>/lessons` | Manage lessons | Offer owner | Login + ownership + format check | 🟢 | |
| `/offers/<offer_id>/comments` | Add comment | Logged-in user | Login + creates comment as `current_user` | 🟢 | |
| `/sessions/<session_id>/cancel` | Cancel session | Offer owner | Login + offer ownership + session state checks | 🟢 | |